"""
Shared utilities for document processing.
DRY principle - common functionality used across processors.
"""

from .ai_extraction import extract_with_vision_api
from .pdf_processing import extract_text_from_pdf, convert_pdf_to_image
from .converters import safe_decimal, safe_float
from .formatters import format_currency, format_percentage
from .comparisons import is_within_tolerance, calculate_percentage_difference

__all__ = [
    'extract_with_vision_api',
    'extract_text_from_pdf',
    'convert_pdf_to_image',
    'safe_decimal',
    'safe_float',
    'format_currency',
    'format_percentage',
    'is_within_tolerance',
    'calculate_percentage_difference',
]
