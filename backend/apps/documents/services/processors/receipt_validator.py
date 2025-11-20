"""
Receipt validation service using GPT-5 Vision.
Validates receipts against purchase order data and generates discrepancy reports.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import fitz  # PyMuPDF
import pdfplumber

from .base import get_openai_client, encode_image, get_mime_type

logger = logging.getLogger(__name__)


class ReceiptValidator:
    """
    Validates receipts against purchase orders using GPT-5.
    Detects discrepancies and generates validation reports.
    """

    def __init__(self):
        self.model = "gpt-5"  # Using GPT-5 with Response API
        self.max_output_tokens = 2000
        self.temperature = 0.1  # Lower temperature for more consistent validation
        self.tolerance_percentage = 5.0  # 5% tolerance for price differences

    def validate(self, receipt_file_path: str, po_data: Dict) -> Dict:
        """
        Validate receipt against PO data.

        Args:
            receipt_file_path: Path to receipt file (PDF or image)
            po_data: Purchase order data dict

        Returns:
            Validation report dict with discrepancies
        """
        logger.info(f"Starting receipt validation for PO: {po_data.get('po_number')}")

        # Extract receipt data
        receipt_data = self._extract_receipt_data(receipt_file_path)

        # Compare and validate
        validation_report = self._compare_receipt_with_po(receipt_data, po_data)

        logger.info(f"Validation complete. Valid: {validation_report['is_valid']}")
        return validation_report

    def _extract_receipt_data(self, file_path: str) -> Dict:
        """Extract data from receipt using AI vision and PyMuPDF (cross-platform)."""
        logger.info(f"Extracting receipt data from: {file_path}")

        # Similar to proforma extraction
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.pdf':
            # Extract text
            text_context = self._extract_text_from_pdf(file_path)

            # Convert to image using PyMuPDF
            temp_image_path = file_path.replace('.pdf', '_temp.png')

            try:
                # Open PDF with PyMuPDF
                pdf_document = fitz.open(file_path)

                if len(pdf_document) == 0:
                    raise RuntimeError("Receipt PDF has no pages")

                # Get first page and convert to image
                first_page = pdf_document[0]
                zoom = 2.0
                mat = fitz.Matrix(zoom, zoom)
                pix = first_page.get_pixmap(matrix=mat)
                pix.save(temp_image_path)
                pdf_document.close()

                logger.info(f"Converted receipt PDF to image: {temp_image_path}")

                receipt_data = self._extract_receipt_with_ai(temp_image_path, text_context)
                return receipt_data

            finally:
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
        else:
            # Image file
            text_context = "No text extraction available for image files."
            return self._extract_receipt_with_ai(file_path, text_context)

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_parts = []
                for page in pdf.pages[:2]:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n\n".join(text_parts)[:3000]
        except Exception as e:
            logger.warning(f"Receipt text extraction failed: {str(e)}")
            return ""

    def _extract_receipt_with_ai(self, image_path: str, text_context: str) -> Dict:
        """Extract receipt data using GPT Vision."""
        logger.info("Calling OpenAI GPT Vision API for receipt extraction")

        base64_image = encode_image(image_path)
        mime_type = get_mime_type(image_path)

        prompt = f"""Analyze this receipt/invoice document and extract the following information:

1. Vendor name
2. Receipt/Invoice number
3. Date (in YYYY-MM-DD format)
4. Line items with:
   - Item name
   - Quantity
   - Unit price
   - Total price
5. Subtotal (before tax)
6. Tax amount
7. Total amount
8. Currency

**Text Context:**
{text_context[:1000]}

Return ONLY a valid JSON object with these keys: vendor_name, receipt_number, date, items (array), subtotal, tax, total, currency.
Each item should have: name, quantity, unit_price, total.
All numeric values must be numbers, not strings.
"""

        try:
            # Call OpenAI Response API with GPT-5 Vision
            response = get_openai_client().responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {"type": "input_image", "image_url": f"data:{mime_type};base64,{base64_image}"}
                        ]
                    }
                ],
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                response_format={"type": "json_object"}
            )

            # Extract JSON from Response API
            raw_json = None
            if hasattr(response, "output_text") and response.output_text:
                raw_json = response.output_text
            elif hasattr(response, "output"):
                try:
                    raw_json = response.output[0].content[0].text
                except Exception:
                    pass
            if raw_json is None and hasattr(response, "choices"):
                try:
                    raw_json = response.choices[0].message.content
                except Exception:
                    pass

            if not raw_json:
                raise RuntimeError("OpenAI Response API did not contain expected text output")

            receipt_data = json.loads(raw_json)
            logger.info("Successfully extracted receipt data")
            return receipt_data

        except Exception as e:
            logger.error(f"Receipt extraction failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to extract receipt data: {str(e)}")

    def _compare_receipt_with_po(self, receipt_data: Dict, po_data: Dict) -> Dict:
        """Compare receipt data with PO data and identify discrepancies."""
        discrepancies = []
        is_valid = True

        # Compare vendor
        receipt_vendor = receipt_data.get('vendor_name', '').lower()
        po_vendor = po_data.get('vendor', {}).get('name', '').lower()

        if receipt_vendor and po_vendor and receipt_vendor not in po_vendor and po_vendor not in receipt_vendor:
            discrepancies.append({
                'type': 'VENDOR_MISMATCH',
                'severity': 'HIGH',
                'field': 'vendor',
                'expected': po_data.get('vendor', {}).get('name'),
                'actual': receipt_data.get('vendor_name'),
                'message': 'Vendor name does not match'
            })
            is_valid = False

        # Compare total amount with tolerance
        receipt_total = float(receipt_data.get('total', 0))
        po_total = float(po_data.get('total', 0))

        if receipt_total > 0 and po_total > 0:
            difference = abs(receipt_total - po_total)
            tolerance = po_total * (self.tolerance_percentage / 100)

            if difference > tolerance:
                discrepancies.append({
                    'type': 'TOTAL_MISMATCH',
                    'severity': 'HIGH',
                    'field': 'total',
                    'expected': po_total,
                    'actual': receipt_total,
                    'difference': difference,
                    'tolerance': tolerance,
                    'message': f'Total amount differs by {difference:.2f} (tolerance: {tolerance:.2f})'
                })
                is_valid = False

        # Compare items
        po_items = {item['name'].lower(): item for item in po_data.get('items', [])}
        receipt_items = receipt_data.get('items', [])

        for receipt_item in receipt_items:
            item_name = receipt_item.get('name', '').lower()

            # Try to find matching PO item
            matched_po_item = None
            for po_item_name, po_item in po_items.items():
                if item_name in po_item_name or po_item_name in item_name:
                    matched_po_item = po_item
                    break

            if not matched_po_item:
                discrepancies.append({
                    'type': 'ITEM_NOT_IN_PO',
                    'severity': 'MEDIUM',
                    'field': 'items',
                    'item_name': receipt_item.get('name'),
                    'message': f"Item '{receipt_item.get('name')}' found in receipt but not in PO"
                })
                # Don't invalidate for extra items, just flag them
            else:
                # Compare quantities
                receipt_qty = float(receipt_item.get('quantity', 0))
                po_qty = float(matched_po_item.get('quantity', 0))

                if receipt_qty != po_qty:
                    discrepancies.append({
                        'type': 'QUANTITY_MISMATCH',
                        'severity': 'MEDIUM',
                        'field': 'quantity',
                        'item_name': receipt_item.get('name'),
                        'expected': po_qty,
                        'actual': receipt_qty,
                        'message': f"Quantity mismatch for '{receipt_item.get('name')}'"
                    })

                # Compare unit prices with tolerance
                receipt_price = float(receipt_item.get('unit_price', 0))
                po_price = float(matched_po_item.get('unit_price', 0))

                if receipt_price > 0 and po_price > 0:
                    price_diff = abs(receipt_price - po_price)
                    price_tolerance = po_price * (self.tolerance_percentage / 100)

                    if price_diff > price_tolerance:
                        discrepancies.append({
                            'type': 'PRICE_MISMATCH',
                            'severity': 'MEDIUM',
                            'field': 'unit_price',
                            'item_name': receipt_item.get('name'),
                            'expected': po_price,
                            'actual': receipt_price,
                            'difference': price_diff,
                            'tolerance': price_tolerance,
                            'message': f"Price mismatch for '{receipt_item.get('name')}'"
                        })

        # Check for missing items (items in PO but not in receipt)
        receipt_item_names = [item.get('name', '').lower() for item in receipt_items]
        for po_item in po_data.get('items', []):
            po_item_name = po_item['name'].lower()

            # Check if PO item is in receipt
            found = any(po_item_name in receipt_name or receipt_name in po_item_name
                       for receipt_name in receipt_item_names)

            if not found:
                discrepancies.append({
                    'type': 'ITEM_MISSING_FROM_RECEIPT',
                    'severity': 'HIGH',
                    'field': 'items',
                    'item_name': po_item['name'],
                    'message': f"Item '{po_item['name']}' in PO but not found in receipt"
                })
                is_valid = False

        # Build validation report
        report = {
            'is_valid': is_valid,
            'validation_date': datetime.now().isoformat(),
            'po_number': po_data.get('po_number'),
            'receipt_number': receipt_data.get('receipt_number'),
            'discrepancies_count': len(discrepancies),
            'discrepancies': discrepancies,
            'receipt_data': receipt_data,
            'summary': self._generate_summary(discrepancies, is_valid)
        }

        return report

    def _generate_summary(self, discrepancies: List[Dict], is_valid: bool) -> str:
        """Generate human-readable validation summary."""
        if is_valid:
            return "Receipt validation passed. All items and amounts match the purchase order within acceptable tolerance."

        high_severity = [d for d in discrepancies if d['severity'] == 'HIGH']
        medium_severity = [d for d in discrepancies if d['severity'] == 'MEDIUM']

        summary_parts = [
            f"Receipt validation failed with {len(discrepancies)} discrepancies:"
        ]

        if high_severity:
            summary_parts.append(f"- {len(high_severity)} high severity issues")
        if medium_severity:
            summary_parts.append(f"- {len(medium_severity)} medium severity issues")

        return " ".join(summary_parts)
