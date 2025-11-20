"""
API Views for Document Processing.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from celery.result import AsyncResult

from apps.purchase_requests.models import PurchaseRequest
from .serializers import (
    ProformaProcessingSerializer,
    ProformaDataSerializer,
    POGenerationSerializer,
    PODataSerializer,
    ReceiptValidationSerializer,
    ValidationReportSerializer,
    TaskStatusSerializer
)
from .tasks import (
    process_proforma_document,
    generate_purchase_order,
    validate_receipt
)

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    tags=['Document Processing'],
    operation_summary='Process proforma invoice with AI',
    operation_description='Extract structured data from proforma invoice using GPT-5 Vision. '
                         'This is an async operation that returns a task ID.',
    request_body=ProformaProcessingSerializer,
    responses={
        200: openapi.Response(
            description='Processing started successfully',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'task_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'request_id': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        400: 'Bad Request',
        404: 'Purchase request not found'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_proforma(request):
    """
    Process proforma invoice document using AI extraction.

    Initiates async task to extract structured data from uploaded proforma file.
    """
    serializer = ProformaProcessingSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'message': 'Invalid request data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    request_id = serializer.validated_data['request_id']

    try:
        # Verify purchase request exists
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check if user has access to this request
        if request.user.role == 'STAFF' and purchase_request.created_by != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to process this request'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if proforma file is uploaded
        if not purchase_request.proforma_file:
            return Response({
                'status': 'error',
                'message': 'No proforma file uploaded for this request'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Start async processing task
        task = process_proforma_document.delay(str(request_id))

        logger.info(f"Proforma processing started for request {request_id}, task {task.id}")

        return Response({
            'status': 'success',
            'message': 'Proforma processing started',
            'task_id': task.id,
            'request_id': str(request_id)
        }, status=status.HTTP_200_OK)

    except PurchaseRequest.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Purchase request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='get',
    tags=['Document Processing'],
    operation_summary='Get extracted proforma data',
    operation_description='Retrieve extracted proforma data for a purchase request',
    manual_parameters=[
        openapi.Parameter(
            'request_id',
            openapi.IN_QUERY,
            description='UUID of the purchase request',
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description='Proforma data retrieved successfully',
            schema=ProformaDataSerializer
        ),
        404: 'Not found'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_proforma_data(request):
    """Get extracted proforma data for a purchase request."""
    request_id = request.query_params.get('request_id')

    if not request_id:
        return Response({
            'status': 'error',
            'message': 'request_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check access
        if request.user.role == 'STAFF' and purchase_request.created_by != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to view this data'
            }, status=status.HTTP_403_FORBIDDEN)

        if not purchase_request.proforma_extracted_data:
            return Response({
                'status': 'error',
                'message': 'No proforma data available. Please process the proforma file first.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ProformaDataSerializer(purchase_request.proforma_extracted_data)

        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except PurchaseRequest.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Purchase request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='post',
    tags=['Document Processing'],
    operation_summary='Generate Purchase Order',
    operation_description='Generate PO PDF for approved purchase request. '
                         'This is an async operation that returns a task ID.',
    request_body=POGenerationSerializer,
    responses={
        200: openapi.Response(
            description='PO generation started successfully',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'task_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'request_id': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        400: 'Bad Request',
        404: 'Purchase request not found'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_po(request):
    """
    Generate Purchase Order PDF for approved request.

    Initiates async task to create PO PDF document.
    """
    serializer = POGenerationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'message': 'Invalid request data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    request_id = serializer.validated_data['request_id']

    try:
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check access
        if request.user.role == 'STAFF' and purchase_request.created_by != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to generate PO for this request'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if request is approved
        if purchase_request.status != 'APPROVED':
            return Response({
                'status': 'error',
                'message': f'Request must be approved before generating PO (current status: {purchase_request.status})'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if proforma data exists
        if not purchase_request.proforma_extracted_data:
            return Response({
                'status': 'error',
                'message': 'No proforma data available. Please process the proforma file first.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Start async PO generation task
        task = generate_purchase_order.delay(str(request_id))

        logger.info(f"PO generation started for request {request_id}, task {task.id}")

        return Response({
            'status': 'success',
            'message': 'Purchase Order generation started',
            'task_id': task.id,
            'request_id': str(request_id)
        }, status=status.HTTP_200_OK)

    except PurchaseRequest.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Purchase request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='get',
    tags=['Document Processing'],
    operation_summary='Get Purchase Order data',
    operation_description='Retrieve PO data for a purchase request',
    manual_parameters=[
        openapi.Parameter(
            'request_id',
            openapi.IN_QUERY,
            description='UUID of the purchase request',
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description='PO data retrieved successfully',
            schema=PODataSerializer
        ),
        404: 'Not found'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_po_data(request):
    """Get PO data for a purchase request."""
    request_id = request.query_params.get('request_id')

    if not request_id:
        return Response({
            'status': 'error',
            'message': 'request_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check access
        if request.user.role == 'STAFF' and purchase_request.created_by != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to view this data'
            }, status=status.HTTP_403_FORBIDDEN)

        if not purchase_request.purchase_order_data:
            return Response({
                'status': 'error',
                'message': 'No PO data available. Please generate the PO first.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PODataSerializer(purchase_request.purchase_order_data)

        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except PurchaseRequest.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Purchase request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='post',
    tags=['Document Processing'],
    operation_summary='Validate receipt against PO',
    operation_description='Validate receipt using GPT-5 Vision and compare with PO. '
                         'This is an async operation that returns a task ID.',
    request_body=ReceiptValidationSerializer,
    responses={
        200: openapi.Response(
            description='Receipt validation started successfully',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'task_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'request_id': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        400: 'Bad Request',
        404: 'Purchase request not found'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_receipt_api(request):
    """
    Validate receipt against Purchase Order.

    Initiates async task to extract receipt data and compare with PO.
    """
    serializer = ReceiptValidationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'message': 'Invalid request data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    request_id = serializer.validated_data['request_id']

    try:
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check access
        if request.user.role == 'STAFF' and purchase_request.created_by != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to validate receipt for this request'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if receipt file is uploaded
        if not purchase_request.receipt_file:
            return Response({
                'status': 'error',
                'message': 'No receipt file uploaded for this request'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if PO data exists
        if not purchase_request.purchase_order_data:
            return Response({
                'status': 'error',
                'message': 'No PO data available. Please generate the PO first.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Start async validation task
        task = validate_receipt.delay(str(request_id))

        logger.info(f"Receipt validation started for request {request_id}, task {task.id}")

        return Response({
            'status': 'success',
            'message': 'Receipt validation started',
            'task_id': task.id,
            'request_id': str(request_id)
        }, status=status.HTTP_200_OK)

    except PurchaseRequest.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Purchase request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='get',
    tags=['Document Processing'],
    operation_summary='Get receipt validation report',
    operation_description='Retrieve validation report for a receipt',
    manual_parameters=[
        openapi.Parameter(
            'request_id',
            openapi.IN_QUERY,
            description='UUID of the purchase request',
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description='Validation report retrieved successfully',
            schema=ValidationReportSerializer
        ),
        404: 'Not found'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_validation_report(request):
    """Get receipt validation report for a purchase request."""
    request_id = request.query_params.get('request_id')

    if not request_id:
        return Response({
            'status': 'error',
            'message': 'request_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check access
        if request.user.role == 'STAFF' and purchase_request.created_by != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to view this data'
            }, status=status.HTTP_403_FORBIDDEN)

        if not purchase_request.receipt_validation:
            return Response({
                'status': 'error',
                'message': 'No validation data available. Please validate the receipt first.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ValidationReportSerializer(purchase_request.receipt_validation)

        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except PurchaseRequest.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Purchase request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='get',
    tags=['Document Processing'],
    operation_summary='Get task status',
    operation_description='Check status of async document processing task',
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_QUERY,
            description='Celery task ID',
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description='Task status retrieved successfully',
            schema=TaskStatusSerializer
        ),
        400: 'Bad Request'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_status(request):
    """Get status of an async document processing task."""
    task_id = request.query_params.get('task_id')

    if not task_id:
        return Response({
            'status': 'error',
            'message': 'task_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        task_result = AsyncResult(task_id)

        response_data = {
            'task_id': task_id,
            'status': task_result.state,
        }

        if task_result.state == 'SUCCESS':
            response_data['result'] = task_result.result
        elif task_result.state == 'FAILURE':
            response_data['error'] = str(task_result.result)

        serializer = TaskStatusSerializer(response_data)

        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to get task status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
