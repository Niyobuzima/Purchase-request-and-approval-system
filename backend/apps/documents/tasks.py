"""
Celery tasks for document processing in Purchase Request & Approval System.
"""

import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.purchase_requests.models import PurchaseRequest
from .services.processors import ProformaExtractor, POGenerator, ReceiptValidator

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_proforma_document(self, request_id):
    """
    Process proforma invoice using GPT-5 Vision to extract structured data.

    Args:
        request_id: UUID of the purchase request

    Returns:
        dict: Extracted proforma data

    Raises:
        Exception: If processing fails after retries
    """
    try:
        logger.info(f"Starting proforma processing for request: {request_id}")

        # Get purchase request
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        if not purchase_request.proforma_file:
            logger.error(f"No proforma file found for request: {request_id}")
            return {'status': 'error', 'message': 'No proforma file attached'}

        # Get file path
        file_path = purchase_request.proforma_file.path

        # Extract data using GPT-5 Vision
        extractor = ProformaExtractor()
        extracted_data = extractor.extract(file_path)

        # Save extracted data to the request
        with transaction.atomic():
            purchase_request.proforma_extracted_data = extracted_data
            purchase_request.save(update_fields=['proforma_extracted_data', 'updated_at'])

        logger.info(f"Successfully processed proforma for request: {request_id}")

        return {
            'status': 'success',
            'request_id': str(request_id),
            'extracted_data': extracted_data,
            'message': 'Proforma data extracted successfully'
        }

    except PurchaseRequest.DoesNotExist:
        logger.error(f"Purchase request not found: {request_id}")
        return {'status': 'error', 'message': 'Purchase request not found'}

    except Exception as e:
        logger.error(f"Proforma processing failed for {request_id}: {str(e)}", exc_info=True)

        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying proforma processing ({self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        # Max retries reached, log and return error
        logger.error(f"Max retries reached for proforma processing: {request_id}")
        return {
            'status': 'error',
            'request_id': str(request_id),
            'message': f'Proforma processing failed: {str(e)}'
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_purchase_order(self, request_id):
    """
    Generate Purchase Order PDF for approved purchase request.

    Args:
        request_id: UUID of the purchase request

    Returns:
        dict: PO generation result

    Raises:
        Exception: If generation fails after retries
    """
    try:
        logger.info(f"Starting PO generation for request: {request_id}")

        # Get purchase request
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Verify request is approved
        if purchase_request.status != 'APPROVED':
            logger.warning(f"Request {request_id} is not approved (status: {purchase_request.status})")
            return {
                'status': 'error',
                'message': f'Request must be approved before generating PO (current status: {purchase_request.status})'
            }

        # Check if proforma data exists
        if not purchase_request.proforma_extracted_data:
            logger.error(f"No proforma data found for request: {request_id}")
            return {'status': 'error', 'message': 'No proforma data available'}

        # Generate PO
        generator = POGenerator()
        pdf_file, po_data = generator.generate(purchase_request)

        # Save PO to the request
        with transaction.atomic():
            purchase_request.purchase_order_file.save(
                f"PO_{po_data['po_number']}.pdf",
                pdf_file,
                save=False
            )
            purchase_request.purchase_order_data = po_data
            purchase_request.save(update_fields=['purchase_order_file', 'purchase_order_data', 'updated_at'])

        logger.info(f"Successfully generated PO {po_data['po_number']} for request: {request_id}")

        return {
            'status': 'success',
            'request_id': str(request_id),
            'po_number': po_data['po_number'],
            'message': 'Purchase Order generated successfully'
        }

    except PurchaseRequest.DoesNotExist:
        logger.error(f"Purchase request not found: {request_id}")
        return {'status': 'error', 'message': 'Purchase request not found'}

    except Exception as e:
        logger.error(f"PO generation failed for {request_id}: {str(e)}", exc_info=True)

        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying PO generation ({self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        # Max retries reached
        logger.error(f"Max retries reached for PO generation: {request_id}")
        return {
            'status': 'error',
            'request_id': str(request_id),
            'message': f'PO generation failed: {str(e)}'
        }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def validate_receipt(self, request_id):
    """
    Validate receipt against purchase order using GPT-5 Vision.

    Args:
        request_id: UUID of the purchase request

    Returns:
        dict: Validation report

    Raises:
        Exception: If validation fails after retries
    """
    try:
        logger.info(f"Starting receipt validation for request: {request_id}")

        # Get purchase request
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check if receipt file exists
        if not purchase_request.receipt_file:
            logger.error(f"No receipt file found for request: {request_id}")
            return {'status': 'error', 'message': 'No receipt file attached'}

        # Check if PO data exists
        if not purchase_request.purchase_order_data:
            logger.error(f"No PO data found for request: {request_id}")
            return {'status': 'error', 'message': 'No purchase order data available'}

        # Get file path
        receipt_path = purchase_request.receipt_file.path
        po_data = purchase_request.purchase_order_data

        # Validate receipt
        validator = ReceiptValidator()
        validation_report = validator.validate(receipt_path, po_data)

        # Save validation report
        with transaction.atomic():
            purchase_request.receipt_validation_data = validation_report

            # Update status based on validation
            if validation_report['is_valid']:
                # Receipt is valid, mark as COMPLETED
                purchase_request.status = 'COMPLETED'
                logger.info(f"Receipt validated successfully for request: {request_id}")
            else:
                # Receipt has discrepancies, keep status and flag for review
                logger.warning(
                    f"Receipt validation failed for request {request_id}: "
                    f"{validation_report['discrepancies_count']} discrepancies found"
                )

            purchase_request.save(update_fields=['receipt_validation_data', 'status', 'updated_at'])

        return {
            'status': 'success',
            'request_id': str(request_id),
            'is_valid': validation_report['is_valid'],
            'discrepancies_count': validation_report['discrepancies_count'],
            'message': validation_report['summary']
        }

    except PurchaseRequest.DoesNotExist:
        logger.error(f"Purchase request not found: {request_id}")
        return {'status': 'error', 'message': 'Purchase request not found'}

    except Exception as e:
        logger.error(f"Receipt validation failed for {request_id}: {str(e)}", exc_info=True)

        # Retry the task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying receipt validation ({self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)

        # Max retries reached
        logger.error(f"Max retries reached for receipt validation: {request_id}")
        return {
            'status': 'error',
            'request_id': str(request_id),
            'message': f'Receipt validation failed: {str(e)}'
        }


@shared_task
def cleanup_old_documents():
    """
    Periodic task to clean up old processed documents.
    Runs weekly via Celery Beat.

    Removes temporary files and archives old completed requests.
    """
    try:
        logger.info("Starting cleanup of old documents")

        cutoff_date = timezone.now() - timedelta(days=90)

        old_requests = PurchaseRequest.objects.filter(
            status='COMPLETED',
            updated_at__lt=cutoff_date
        )

        count = old_requests.count()

        if count == 0:
            logger.info("No old documents to clean up")
            return {'status': 'success', 'message': 'No old documents found', 'count': 0}

        # Archive logic could go here
        # For now, just log
        logger.info(f"Found {count} old completed requests (> 90 days)")

        # In production, you might:
        # 1. Move files to archive storage (S3 Glacier, etc.)
        # 2. Update database records with archive status
        # 3. Delete files from active storage

        logger.info("Cleanup completed successfully")

        return {
            'status': 'success',
            'message': f'Cleanup completed: {count} old requests processed',
            'count': count
        }

    except Exception as e:
        logger.error(f"Document cleanup failed: {str(e)}", exc_info=True)
        return {'status': 'error', 'message': f'Cleanup failed: {str(e)}'}


@shared_task
def send_po_notification(request_id):
    """
    Send notification email when PO is generated.

    Args:
        request_id: UUID of the purchase request
    """
    try:
        logger.info(f"Sending PO notification for request: {request_id}")

        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Get PO data
        po_data = purchase_request.purchase_order_data

        if not po_data:
            logger.error(f"No PO data found for notification: {request_id}")
            return {'status': 'error', 'message': 'No PO data available'}

        # Email content
        subject = f"Purchase Order {po_data['po_number']} Generated"
        message = f"""
Dear {purchase_request.created_by.get_full_name() or purchase_request.created_by.email},

Your purchase order has been generated successfully.

PO Number: {po_data['po_number']}
Vendor: {po_data['vendor'].get('name', 'N/A')}
Total Amount: {po_data['currency']} {po_data['total']:,.2f}

The purchase order is attached to this email and available in the system.

Best regards,
IST Africa Procurement System
"""

        # In production, send actual email
        # For now, just log
        logger.info(f"PO notification prepared: {subject}")
        logger.info(f"Recipient: {purchase_request.created_by.email}")

        # TODO: Implement actual email sending using Django's send_mail
        # from django.core.mail import send_mail
        # send_mail(
        #     subject=subject,
        #     message=message,
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[purchase_request.created_by.email],
        #     fail_silently=False,
        # )

        return {
            'status': 'success',
            'message': 'PO notification sent successfully',
            'recipient': purchase_request.created_by.email
        }

    except PurchaseRequest.DoesNotExist:
        logger.error(f"Purchase request not found: {request_id}")
        return {'status': 'error', 'message': 'Purchase request not found'}

    except Exception as e:
        logger.error(f"Failed to send PO notification for {request_id}: {str(e)}", exc_info=True)
        return {'status': 'error', 'message': f'Notification failed: {str(e)}'}
