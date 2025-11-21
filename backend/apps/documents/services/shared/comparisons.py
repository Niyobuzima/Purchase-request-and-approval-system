"""
Numeric comparison utilities.
Functions for tolerance-based comparisons.
"""

from typing import Union
from decimal import Decimal


def calculate_percentage_difference(
    value1: Union[Decimal, float],
    value2: Union[Decimal, float]
) -> float:
    """
    Calculate percentage difference between two values.

    Args:
        value1: First value
        value2: Second value

    Returns:
        Percentage difference (0-100)
    """
    if value2 == 0:
        return 100.0 if value1 != 0 else 0.0

    diff = abs(float(value1) - float(value2))
    percentage = (diff / abs(float(value2))) * 100
    return percentage


def is_within_tolerance(
    actual: Union[Decimal, float],
    expected: Union[Decimal, float],
    tolerance_percent: float = 5.0
) -> bool:
    """
    Check if actual value is within tolerance of expected value.

    Args:
        actual: Actual value
        expected: Expected value
        tolerance_percent: Tolerance percentage (e.g., 5.0 for 5%)

    Returns:
        True if within tolerance, False otherwise
    """
    if expected == 0:
        return actual == 0

    diff = abs(float(actual) - float(expected))
    tolerance = abs(float(expected)) * (tolerance_percent / 100)

    return diff <= tolerance


def calculate_absolute_difference(
    value1: Union[Decimal, float],
    value2: Union[Decimal, float]
) -> float:
    """
    Calculate absolute difference between two values.

    Args:
        value1: First value
        value2: Second value

    Returns:
        Absolute difference
    """
    return abs(float(value1) - float(value2))
