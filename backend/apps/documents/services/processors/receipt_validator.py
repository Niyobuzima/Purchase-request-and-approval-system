"""
Receipt validation service using GPT-5 Vision.
Refactored to follow KISS and DRY principles with shared modules.
"""

import logging
from pathlib import Path
from typing import Dict

from ..shared.pdf_processing import extract_text_from_pdf, convert_pdf_to_image
from ..shared.ai_extraction import extract_with_vision_api
from ..validation import compare_vendors, compare_totals, compare_items
from ..validation import DiscrepancyBuilder, generate_validation_report

logger = logging.getLogger(__name__)


class ReceiptValidator:
    """
    Validates receipts against purchase orders using GPT-5.
    Detects discrepancies and generates validation reports.
    """

    def __init__(self):
        self.model = "gpt-5"
        self.max_output_tokens = 2000
        self.temperature = 0.1
        self.tolerance_percentage = 5.0

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

        # Extract receipt data using AI
        receipt_data = self._extract_receipt_data(receipt_file_path)

        # Compare and validate
        validation_report = self._compare_receipt_with_po(receipt_data, po_data)

        logger.info(f"Validation complete. Valid: {validation_report['is_valid']}")
        return validation_report

    def _extract_receipt_data(self, file_path: str) -> Dict:
        """Extract data from receipt using AI vision."""
        logger.info(f"Extracting receipt data from: {file_path}")

        file_path_obj = Path(file_path)
        file_ext = file_path_obj.suffix.lower()

        if file_ext == '.pdf':
            # Extract text context
            text_context = extract_text_from_pdf(file_path, max_pages=2, max_chars=3000)

            # Convert to image
            temp_image_path = str(file_path_obj.parent / f"{file_path_obj.stem}_temp.png")

            try:
                convert_pdf_to_image(file_path, temp_image_path, page_number=0, zoom=2.0)
                receipt_data = self._extract_with_ai(temp_image_path, text_context)
                return receipt_data

            finally:
                # Cleanup temp image
                temp_image_obj = Path(temp_image_path)
                if temp_image_obj.exists():
                    temp_image_obj.unlink()
        else:
            # Image file - no text context
            text_context = "Image file - no text extraction available."
            return self._extract_with_ai(file_path, text_context)

    def _extract_with_ai(self, image_path: str, text_context: str) -> Dict:
        """Extract receipt data using GPT Vision API."""
        prompt = """Analyze this receipt/invoice document and extract the following information:

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

Return ONLY a valid JSON object with these keys: vendor_name, receipt_number, date, items (array), subtotal, tax, total, currency.
Each item should have: name, quantity, unit_price, total.
All numeric values must be numbers, not strings."""

        return extract_with_vision_api(
            image_path=image_path,
            prompt=prompt,
            text_context=text_context,
            model=self.model,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens
        )

    def _compare_receipt_with_po(self, receipt_data: Dict, po_data: Dict) -> Dict:
        """Compare receipt data with PO data and identify discrepancies."""
        builder = DiscrepancyBuilder()
        is_valid = True

        # Compare vendor
        if not compare_vendors(receipt_data, po_data, builder):
            is_valid = False

        # Compare total amounts
        if not compare_totals(receipt_data, po_data, builder, self.tolerance_percentage):
            is_valid = False

        # Compare line items
        if not compare_items(receipt_data, po_data, builder, self.tolerance_percentage):
            is_valid = False

        # Generate comprehensive report
        return generate_validation_report(
            is_valid=is_valid,
            discrepancies=builder.get_discrepancies(),
            receipt_data=receipt_data,
            po_data=po_data
        )
