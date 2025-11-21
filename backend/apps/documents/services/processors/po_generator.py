"""
Purchase Order PDF generation service.
Generates professional PDF documents from approved purchase requests.
"""

import logging
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from typing import Dict, Tuple

from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

logger = logging.getLogger(__name__)


class POGenerator:
    """
    Generates Purchase Orders from approved purchase requests.
    Creates professional PDF documents with auto-generated PO numbers.
    """

    def __init__(self):
        self.company_name = "IST Africa"
        self.company_address = "Kigali, Rwanda"
        self.company_contact = "+250788000000"
        self.company_email = "procurement@ist-africa.com"

    def generate(self, purchase_request) -> Tuple[ContentFile, Dict]:
        """
        Generate PO for a purchase request.

        Args:
            purchase_request: PurchaseRequest model instance

        Returns:
            Tuple of (PDF ContentFile, PO data dict)
        """
        logger.info(f"Generating PO for request: {purchase_request.id}")

        # Generate PO number
        po_number = self._generate_po_number(purchase_request)

        # Extract proforma data
        proforma_data = purchase_request.proforma_extracted_data or {}

        # Create PO data structure
        po_data = {
            'po_number': po_number,
            'date': datetime.now().isoformat(),
            'request_id': str(purchase_request.id),
            'vendor': proforma_data.get('vendor', {}),
            'buyer': {
                'name': self.company_name,
                'address': self.company_address,
                'contact': self.company_contact,
                'email': self.company_email
            },
            'items': proforma_data.get('items', []),
            'subtotal': proforma_data.get('subtotal', 0),
            'tax': proforma_data.get('tax', 0),
            'total': proforma_data.get('total', 0),
            'currency': proforma_data.get('currency', 'RWF'),
            'payment_terms': proforma_data.get('payment_terms', 'As per agreement'),
            'delivery_terms': 'FOB Kigali',
            'approved_by': self._get_approver_info(purchase_request),
            'notes': purchase_request.description or ''
        }

        # Normalize numeric fields to preserve precision (e.g., fractional quantities)
        po_data = self._normalize_po_data(po_data)

        # Generate PDF
        pdf_file = self._generate_pdf(po_data)

        logger.info(f"Successfully generated PO: {po_number}")
        return pdf_file, po_data

    def _generate_po_number(self, purchase_request) -> str:
        """Generate PO number in format: PO-YYYY-NNNNNN"""
        year = datetime.now().year
        # Use last 6 digits of UUID as unique identifier
        unique_id = str(purchase_request.id).replace('-', '')[-6:]
        return f"PO-{year}-{unique_id.upper()}"

    def _get_approver_info(self, purchase_request) -> Dict:
        """Get final approver information."""
        # Get the last APPROVED approval log
        from apps.approvals.models import ApprovalLog

        final_approval = ApprovalLog.objects.filter(
            request=purchase_request,
            action='APPROVED'
        ).order_by('-created_at').first()

        if final_approval:
            approver = final_approval.approver
            return {
                'name': approver.get_full_name() or approver.email,
                'email': approver.email,
                'role': approver.get_role_display(),
                'date': final_approval.created_at.isoformat()
            }

        return {
            'name': 'System',
            'email': '',
            'role': '',
            'date': datetime.now().isoformat()
        }

    def _generate_pdf(self, po_data: Dict) -> ContentFile:
        """Generate PDF document for PO."""
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Page margins
        left_margin = 50
        right_margin = width - 50
        top_margin = height - 50

        y_position = top_margin

        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin, y_position, "PURCHASE ORDER")

        c.setFont("Helvetica", 10)
        c.drawString(right_margin - 150, y_position, f"PO #: {po_data['po_number']}")
        y_position -= 15
        c.drawString(right_margin - 150, y_position, f"Date: {datetime.fromisoformat(po_data['date']).strftime('%Y-%m-%d')}")

        y_position -= 30

        # Buyer Information (left side)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_margin, y_position, "BUYER:")
        c.setFont("Helvetica", 10)
        y_position -= 15
        c.drawString(left_margin, y_position, po_data['buyer']['name'])
        y_position -= 12
        c.drawString(left_margin, y_position, po_data['buyer']['address'])
        y_position -= 12
        c.drawString(left_margin, y_position, po_data['buyer']['contact'])
        y_position -= 12
        c.drawString(left_margin, y_position, po_data['buyer']['email'])

        # Vendor Information (right side)
        vendor_x = width / 2 + 50
        vendor_y = top_margin - 95
        c.setFont("Helvetica-Bold", 11)
        c.drawString(vendor_x, vendor_y, "VENDOR:")
        c.setFont("Helvetica", 10)
        vendor_y -= 15
        c.drawString(vendor_x, vendor_y, po_data['vendor'].get('name', 'N/A'))
        vendor_y -= 12
        c.drawString(vendor_x, vendor_y, po_data['vendor'].get('address', 'N/A'))
        vendor_y -= 12
        c.drawString(vendor_x, vendor_y, po_data['vendor'].get('contact', 'N/A'))
        vendor_y -= 12
        c.drawString(vendor_x, vendor_y, po_data['vendor'].get('email', 'N/A'))

        y_position -= 60

        # Line Items Table
        c.setFont("Helvetica-Bold", 11)
        c.drawString(left_margin, y_position, "ITEMS:")
        y_position -= 20

        # Table headers
        table_data = [['#', 'Item Name', 'Description', 'Qty', 'Unit Price', 'Total']]

        # Table rows
        for idx, item in enumerate(po_data['items'], 1):
            item_name = item.get('name', '')
            quantity_value = self._safe_decimal(item.get('quantity', 0), 'item.quantity', context=item_name)
            unit_price_value = self._safe_decimal(item.get('unit_price', 0), 'item.unit_price', context=item_name)
            total_value = self._safe_decimal(item.get('total', 0), 'item.total', context=item_name)

            table_data.append([
                str(idx),
                item_name[:30],  # Truncate long names
                item.get('description', '')[:40],  # Truncate long descriptions
                self._format_quantity(quantity_value),
                self._format_currency(unit_price_value),
                self._format_currency(total_value)
            ])

        # Create table
        col_widths = [30, 120, 160, 50, 80, 80]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),  # Right-align numbers
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))

        # Draw table
        table_width, table_height = table.wrap(0, 0)
        table.drawOn(c, left_margin, y_position - table_height)

        y_position -= (table_height + 30)

        # Totals (right-aligned)
        totals_x = right_margin - 150
        c.setFont("Helvetica", 10)
        subtotal_value = self._safe_decimal(po_data.get('subtotal', 0), 'subtotal')
        c.drawString(totals_x, y_position, "Subtotal:")
        c.drawString(totals_x + 80, y_position, f"{po_data['currency']} {self._format_currency(subtotal_value)}")
        y_position -= 15

        tax_value = self._safe_decimal(po_data.get('tax', 0), 'tax')
        c.drawString(totals_x, y_position, "Tax:")
        c.drawString(totals_x + 80, y_position, f"{po_data['currency']} {self._format_currency(tax_value)}")
        y_position -= 15

        c.setFont("Helvetica-Bold", 11)
        total_value = self._safe_decimal(po_data.get('total', 0), 'total')
        c.drawString(totals_x, y_position, "TOTAL:")
        c.drawString(totals_x + 80, y_position, f"{po_data['currency']} {self._format_currency(total_value)}")

        y_position -= 30

        # Terms
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_margin, y_position, "Payment Terms:")
        c.setFont("Helvetica", 9)
        c.drawString(left_margin + 100, y_position, po_data['payment_terms'])
        y_position -= 15

        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_margin, y_position, "Delivery Terms:")
        c.setFont("Helvetica", 9)
        c.drawString(left_margin + 100, y_position, po_data['delivery_terms'])

        y_position -= 30

        # Notes
        if po_data.get('notes'):
            c.setFont("Helvetica-Bold", 10)
            c.drawString(left_margin, y_position, "Notes:")
            c.setFont("Helvetica", 9)
            y_position -= 15
            # Wrap notes text
            notes_text = po_data['notes'][:300]  # Limit length
            c.drawString(left_margin, y_position, notes_text)
            y_position -= 30

        # Approval signature
        c.setFont("Helvetica-Bold", 10)
        c.drawString(left_margin, y_position, "Approved By:")
        c.setFont("Helvetica", 9)
        y_position -= 15
        approver = po_data.get('approved_by', {})
        c.drawString(left_margin, y_position, f"{approver.get('name', 'N/A')} ({approver.get('role', 'N/A')})")
        y_position -= 12
        c.drawString(left_margin, y_position, f"Date: {datetime.fromisoformat(approver.get('date', datetime.now().isoformat())).strftime('%Y-%m-%d')}")

        # Footer
        c.setFont("Helvetica-Italic", 8)
        c.drawString(left_margin, 30, f"Purchase Order generated by {self.company_name} Procurement System")
        c.drawString(left_margin, 20, f"This is a computer-generated document and does not require a signature.")

        # Finalize PDF
        c.showPage()
        c.save()

        # Create ContentFile
        buffer.seek(0)
        pdf_content = ContentFile(buffer.read(), name=f"{po_data['po_number']}.pdf")

        return pdf_content

    def _normalize_po_data(self, po_data: Dict) -> Dict:
        """Sanitize and normalize numeric fields, preserving fractional quantities."""
        normalized = deepcopy(po_data)

        normalized_items = []
        for item in po_data.get('items', []):
            item_copy = dict(item)
            item_name = item_copy.get('name', 'Unknown Item')

            quantity_value = self._safe_decimal(item_copy.get('quantity', 0), 'item.quantity', context=item_name)
            unit_price_value = self._safe_decimal(item_copy.get('unit_price', 0), 'item.unit_price', context=item_name)
            total_value = self._safe_decimal(item_copy.get('total', 0), 'item.total', context=item_name)

            item_copy['quantity'] = self._decimal_to_serializable(quantity_value)
            item_copy['unit_price'] = self._decimal_to_serializable(unit_price_value, places=2)
            item_copy['total'] = self._decimal_to_serializable(total_value, places=2)
            normalized_items.append(item_copy)

        normalized['items'] = normalized_items
        normalized['subtotal'] = self._decimal_to_serializable(self._safe_decimal(po_data.get('subtotal', 0), 'subtotal'), places=2)
        normalized['tax'] = self._decimal_to_serializable(self._safe_decimal(po_data.get('tax', 0), 'tax'), places=2)
        normalized['total'] = self._decimal_to_serializable(self._safe_decimal(po_data.get('total', 0), 'total'), places=2)

        return normalized

    def _safe_decimal(self, value, field_name: str, context: str | None = None, default: Decimal = Decimal('0')) -> Decimal:
        """Convert a raw value to Decimal, logging issues and falling back to default."""
        if isinstance(value, Decimal):
            return value

        try:
            if isinstance(value, str):
                cleaned = value.strip().replace(',', '')
                if cleaned == '':
                    raise InvalidOperation('empty string')
                return Decimal(cleaned)

            if isinstance(value, (int, float)):
                return Decimal(str(value))

            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            logger.warning(
                "Failed to parse decimal for field '%s' (context=%s) raw_value='%s': %s",
                field_name,
                context,
                value,
                exc
            )
            return default

    def _decimal_to_serializable(self, value: Decimal, places: int | None = None) -> str:
        """Convert Decimal to a JSON-serializable string while preserving precision."""
        if places is not None:
            quant = Decimal(10) ** -places
            value = value.quantize(quant, rounding=ROUND_HALF_UP)
            return f"{value:.{places}f}"

        normalized = value.normalize()
        text = format(normalized, 'f')
        if '.' in text:
            text = text.rstrip('0').rstrip('.')
        return text or '0'

    def _format_quantity(self, value: Decimal) -> str:
        """Format quantity for PDF output without dropping fractional parts."""
        return self._decimal_to_serializable(value, places=None)

    def _format_currency(self, value: Decimal) -> str:
        """Format currency values with two decimal places and thousands separator."""
        quantized = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return f"{quantized:,.2f}"
