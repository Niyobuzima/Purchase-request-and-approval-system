"""
Purchase Order PDF generation service.
Generates professional PDF documents from approved purchase requests.
"""

import logging
from datetime import datetime
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
            table_data.append([
                str(idx),
                item['name'][:30],  # Truncate long names
                item.get('description', '')[:40],  # Truncate long descriptions
                str(int(item['quantity'])),
                f"{item['unit_price']:,.2f}",
                f"{item['total']:,.2f}"
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
        c.drawString(totals_x, y_position, "Subtotal:")
        c.drawString(totals_x + 80, y_position, f"{po_data['currency']} {po_data['subtotal']:,.2f}")
        y_position -= 15

        c.drawString(totals_x, y_position, "Tax:")
        c.drawString(totals_x + 80, y_position, f"{po_data['currency']} {po_data['tax']:,.2f}")
        y_position -= 15

        c.setFont("Helvetica-Bold", 11)
        c.drawString(totals_x, y_position, "TOTAL:")
        c.drawString(totals_x + 80, y_position, f"{po_data['currency']} {po_data['total']:,.2f}")

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
