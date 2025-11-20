"""
Utility functions used across the application
"""
import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename using UUID

    Args:
        original_filename: Original file name

    Returns:
        Unique filename with original extension
    """
    ext = original_filename.split('.')[-1] if '.' in original_filename else ''
    unique_name = f"{uuid.uuid4()}"
    return f"{unique_name}.{ext}" if ext else unique_name


def calculate_file_hash(file_content: bytes) -> str:
    """
    Calculate MD5 hash of file content

    Args:
        file_content: File content as bytes

    Returns:
        MD5 hash string
    """
    return hashlib.md5(file_content).hexdigest()


def format_currency(amount: float, currency: str = "RWF") -> str:
    """
    Format currency amount

    Args:
        amount: Amount to format
        currency: Currency code

    Returns:
        Formatted currency string
    """
    return f"{currency} {amount:,.2f}"


def generate_po_number(request_id: int) -> str:
    """
    Generate Purchase Order number

    Args:
        request_id: Purchase request ID

    Returns:
        PO number in format PO-YYYY-NNNNNN
    """
    year = datetime.now().year
    return f"PO-{year}-{request_id:06d}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing dangerous characters

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    import re
    # Remove any character that's not alphanumeric, dash, underscore, or dot
    sanitized = re.sub(r'[^\w\-.]', '_', filename)
    return sanitized
