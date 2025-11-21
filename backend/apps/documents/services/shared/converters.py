"""
Safe type converters for numeric values.
Handles decimal precision and float conversions with error handling.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Union, Optional

logger = logging.getLogger(__name__)


def safe_decimal(
    value: Union[str, int, float, Decimal],
    field_name: str = "value",
    context: Optional[str] = None,
    default: Decimal = Decimal('0')
) -> Decimal:
    """
    Safely convert value to Decimal with error handling.

    Args:
        value: Value to convert
        field_name: Field name for error messages
        context: Additional context for logging
        default: Default value if conversion fails

    Returns:
        Decimal value
    """
    try:
        if value is None or value == '':
            return default

        # Handle string values
        if isinstance(value, str):
            # Remove whitespace and commas
            cleaned = value.strip().replace(',', '')
            if not cleaned:
                return default
            return Decimal(cleaned)

        # Handle numeric values
        return Decimal(str(value))

    except (ValueError, InvalidOperation) as e:
        logger.warning(
            f"Failed to convert to Decimal: field='{field_name}', "
            f"context={context}, value='{value}', error={str(e)}"
        )
        return default


def safe_float(
    value: Union[str, int, float],
    field_name: str = "value",
    context: Optional[str] = None,
    default: float = 0.0
) -> float:
    """
    Safely convert value to float with error handling.

    Args:
        value: Value to convert
        field_name: Field name for error messages
        context: Additional context for logging
        default: Default value if conversion fails

    Returns:
        Float value
    """
    try:
        if value is None or value == '':
            return default

        # Handle string values
        if isinstance(value, str):
            cleaned = value.strip().replace(',', '')
            if not cleaned:
                return default
            return float(cleaned)

        return float(value)

    except (ValueError, TypeError) as e:
        logger.warning(
            f"Failed to convert to float: field='{field_name}', "
            f"context={context}, value='{value}', error={str(e)}"
        )
        return default
