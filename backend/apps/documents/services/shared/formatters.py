"""
Formatting utilities for numeric values.
Currency formatting and display functions.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union


def format_currency(value: Union[Decimal, float], decimals: int = 2) -> str:
    """
    Format number as currency with thousand separators.

    Args:
        value: Numeric value to format
        decimals: Number of decimal places

    Returns:
        Formatted currency string (e.g., "1,234.56")
    """
    if isinstance(value, float):
        value = Decimal(str(value))

    quantized = value.quantize(
        Decimal(10) ** -decimals,
        rounding=ROUND_HALF_UP
    )
    return f"{quantized:,.{decimals}f}"


def format_percentage(value: Union[Decimal, float], decimals: int = 2) -> str:
    """
    Format number as percentage.

    Args:
        value: Numeric value (e.g., 0.05 for 5%)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string (e.g., "5.00%")
    """
    percentage = float(value) * 100
    return f"{percentage:.{decimals}f}%"
