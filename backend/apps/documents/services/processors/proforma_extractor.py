"""
Proforma invoice extraction service using GPT-5 Vision.
Extracts structured data from proforma invoices (PDF and images).
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict

import fitz  # PyMuPDF
import pdfplumber

from .base import get_openai_client, encode_image, get_mime_type

logger = logging.getLogger(__name__)


class ProformaExtractor:
    """
    Extracts structured data from proforma invoices using GPT-5.
    Supports both PDF and image formats with OCR fallback.
    """

    def __init__(self):
        self.model = "gpt-5"  # Using GPT-5 with Response API
        self.max_output_tokens = 2000
        self.temperature = 0.2

    def extract(self, file_path: str) -> Dict:
        """
        Extract structured data from proforma invoice.

        Args:
            file_path: Path to the proforma file (PDF or image)

        Returns:
            Dict containing extracted invoice data

        Raises:
            ValueError: If file format is unsupported
            RuntimeError: If extraction fails
        """
        try:
            logger.info(f"Starting proforma extraction for: {file_path}")

            # Determine file type and extract
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.webp']:
                return self._extract_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

        except Exception as e:
            logger.error(f"Proforma extraction failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to extract proforma data: {str(e)}")

    def _extract_from_pdf(self, pdf_path: str) -> Dict:
        """Extract data from PDF proforma using PyMuPDF (cross-platform, no external dependencies)."""
        logger.info(f"Extracting from PDF: {pdf_path}")

        # Extract text using pdfplumber for context
        text_context = self._extract_text_from_pdf(pdf_path)

        # Convert first page to image using PyMuPDF
        temp_image_path = pdf_path.replace('.pdf', '_temp.png')

        try:
            # Open PDF with PyMuPDF using context manager
            with fitz.open(pdf_path) as pdf_document:
                if len(pdf_document) == 0:
                    raise RuntimeError("PDF has no pages")

                # Get first page
                first_page = pdf_document[0]

                # Render page to image (zoom factor 2.0 = 144 DPI, good quality)
                zoom = 2.0
                mat = fitz.Matrix(zoom, zoom)
                pix = first_page.get_pixmap(matrix=mat)

                # Save as PNG
                pix.save(temp_image_path)

            logger.info(f"Converted PDF to image: {temp_image_path}")

            # Extract using AI vision
            extracted_data = self._extract_with_ai(temp_image_path, text_context)
            return extracted_data

        finally:
            # Clean up temp image
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)

    def _extract_from_image(self, image_path: str) -> Dict:
        """Extract data from image proforma."""
        logger.info(f"Extracting from image: {image_path}")

        # For images, we don't have text context
        text_context = "No text extraction available for image files."

        # Extract using AI vision
        extracted_data = self._extract_with_ai(image_path, text_context)
        return extracted_data

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_parts = []
                for page in pdf.pages[:3]:  # First 3 pages max
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

                full_text = "\n\n".join(text_parts)
                return full_text[:4000]  # Limit to 4000 chars

        except Exception as e:
            logger.warning(f"Text extraction failed: {str(e)}")
            return ""

    def _extract_with_ai(self, image_path: str, text_context: str) -> Dict:
        """
        Use GPT-5 to extract structured data from invoice image.

        Args:
            image_path: Path to invoice image
            text_context: Extracted text for additional context

        Returns:
            Structured invoice data as dict
        """
        logger.info("Calling OpenAI GPT Vision API for extraction")

        # Encode image
        base64_image = encode_image(image_path)

        # Determine image format
        mime_type = get_mime_type(image_path)

        # Create extraction prompt
        prompt = self._create_extraction_prompt(text_context)

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
            # The Response API may expose JSON directly depending on SDK version
            raw_json = None
            if hasattr(response, "output_text") and response.output_text:
                raw_json = response.output_text
            elif hasattr(response, "output"):
                try:
                    # Common structure: response.output[0].content[0].text
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

            logger.info("Successfully received response from OpenAI Response API")

            # Parse JSON
            extracted_data = json.loads(raw_json)

            # Validate and normalize data
            validated_data = self._validate_extracted_data(extracted_data)

            logger.info("Successfully extracted and validated proforma data")
            return validated_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Raw response: {raw_json}")
            raise RuntimeError(f"Invalid JSON response from AI: {str(e)}") from e
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"AI extraction failed: {str(e)}") from e

    def _create_extraction_prompt(self, text_context: str) -> str:
        """Create the extraction prompt for GPT."""
        return f"""Analyze this proforma invoice or quotation document and extract the following information:

**Required Fields:**
1. Vendor Information:
   - name (company name)
   - contact (phone number)
   - email (email address)
   - address (full address)

2. Invoice Details:
   - invoice_number (invoice/quote/proforma number)
   - date (invoice/quote date in YYYY-MM-DD format)
   - currency (currency code, default to "RWF" if not specified)
   - payment_terms (e.g., "Net 30", "COD", etc.)

3. Line Items (array of items):
   - name (item/product name)
   - description (item description)
   - quantity (numeric quantity)
   - unit_price (numeric price per unit)
   - total (quantity x unit_price)

4. Totals:
   - subtotal (sum of all item totals before tax)
   - tax (tax amount, 0 if not specified)
   - total (final total including tax)

**Additional Context from Text Extraction:**
{text_context[:1000]}

**IMPORTANT INSTRUCTIONS:**
- Return ONLY a valid JSON object with these exact keys: vendor, invoice_number, date, items, subtotal, tax, total, currency, payment_terms
- All numeric values should be numbers, not strings
- Items must be an array of objects
- If a field is not found, use null for strings or 0 for numbers
- Ensure vendor is an object with name, contact, email, address keys
- Date must be in YYYY-MM-DD format
- Do not include any text before or after the JSON object
"""

    def _validate_extracted_data(self, data: Dict) -> Dict:
        """Validate and normalize extracted data."""

        def _safe_float(value, field_name: str = "unknown") -> float:
            """
            Safely convert any value to float with robust parsing.
            
            Handles:
            - None/empty values -> 0.0
            - Strings with thousands separators (1,000 -> 1000.0)
            - Currency symbols ($1,000 -> 1000.0)
            - Whitespace and non-numeric suffixes (e.g., "2 units" -> 2.0)
            
            Args:
                value: Input value to parse
                field_name: Name of field being parsed (for logging)
            
            Returns:
                Parsed float value or 0.0 on failure
            """
            # Handle None or empty
            if value is None or value == '':
                return 0.0
            
            # Already a number
            if isinstance(value, (int, float)):
                return float(value)
            
            # Try to parse string
            if isinstance(value, str):
                try:
                    # Strip whitespace
                    cleaned = value.strip()
                    
                    # Remove common currency symbols and thousands separators
                    cleaned = cleaned.replace(',', '')
                    cleaned = cleaned.replace('$', '')
                    cleaned = cleaned.replace('€', '')
                    cleaned = cleaned.replace('£', '')
                    cleaned = cleaned.replace('RWF', '')
                    cleaned = cleaned.replace('USD', '')
                    
                    # Strip any trailing non-numeric text (e.g., "2 units" -> "2")
                    # Find first sequence of digits with optional decimal point
                    match = re.search(r'[-+]?\d*\.?\d+', cleaned)
                    if match:
                        cleaned = match.group(0)
                    
                    # Convert to float
                    return float(cleaned)
                    
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse float for field '{field_name}' from value '{value}': {e}")
                    return 0.0
            
            # Fallback for unexpected types
            try:
                return float(value)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to convert '{type(value).__name__}' to float for field '{field_name}': {e}")
                return 0.0

        # Ensure required top-level keys exist
        required_keys = ['vendor', 'invoice_number', 'date', 'items', 'subtotal', 'tax', 'total', 'currency', 'payment_terms']
        for key in required_keys:
            if key not in data:
                logger.warning(f"Missing key in extracted data: {key}")
                if key == 'vendor':
                    data[key] = {'name': '', 'contact': '', 'email': '', 'address': ''}
                elif key == 'items':
                    data[key] = []
                elif key in ['subtotal', 'tax', 'total']:
                    data[key] = 0
                else:
                    data[key] = ''

        # Ensure vendor is properly structured
        if not isinstance(data['vendor'], dict):
            data['vendor'] = {'name': str(data['vendor']), 'contact': '', 'email': '', 'address': ''}

        vendor_keys = ['name', 'contact', 'email', 'address']
        for key in vendor_keys:
            if key not in data['vendor']:
                data['vendor'][key] = ''

        # Ensure items is a list
        if not isinstance(data['items'], list):
            data['items'] = []

        # Validate each item with robust parsing
        validated_items = []
        for item in data['items']:
            if isinstance(item, dict):
                # Parse numeric fields safely
                quantity = _safe_float(item.get('quantity', 0), 'item.quantity')
                unit_price = _safe_float(item.get('unit_price', 0), 'item.unit_price')
                item_total = _safe_float(item.get('total', 0), 'item.total')
                
                # Recalculate total to ensure accuracy; prefer computed value if parsing failed
                computed_total = quantity * unit_price
                if item_total == 0.0 and computed_total > 0.0:
                    item_total = computed_total
                elif abs(computed_total - item_total) > 0.01:  # Allow small rounding
                    logger.warning(
                        f"Item total mismatch for '{item.get('name', 'unknown')}': "
                        f"computed={computed_total:.2f}, extracted={item_total:.2f}. Using computed."
                    )
                    item_total = computed_total
                
                validated_item = {
                    'name': item.get('name', ''),
                    'description': item.get('description', ''),
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total': item_total
                }
                validated_items.append(validated_item)

        data['items'] = validated_items

        # Ensure numeric fields are numbers with safe parsing
        data['subtotal'] = _safe_float(data.get('subtotal', 0), 'subtotal')
        data['tax'] = _safe_float(data.get('tax', 0), 'tax')
        data['total'] = _safe_float(data.get('total', 0), 'total')

        # Recalculate totals to ensure accuracy
        calculated_subtotal = sum(item['total'] for item in data['items'])
        if abs(calculated_subtotal - data['subtotal']) > 1:  # Allow small rounding differences
            logger.warning(f"Subtotal mismatch: calculated={calculated_subtotal}, extracted={data['subtotal']}")
            data['subtotal'] = calculated_subtotal

        calculated_total = data['subtotal'] + data['tax']
        if abs(calculated_total - data['total']) > 1:
            logger.warning(f"Total mismatch: calculated={calculated_total}, extracted={data['total']}")
            data['total'] = calculated_total

        # Set default currency if not specified
        if not data.get('currency'):
            data['currency'] = 'RWF'

        return data
