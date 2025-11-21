"""
Total amount comparison logic.
"""

import logging
from typing import Dict

from ..shared.converters import safe_float
from ..shared.comparisons import is_within_tolerance
from .discrepancy_builder import DiscrepancyBuilder

logger = logging.getLogger(__name__)


def compare_totals(
    receipt_data: Dict,
    po_data: Dict,
    builder: DiscrepancyBuilder,
    tolerance_percent: float = 5.0
) -> bool:
    """
    Compare total amounts between receipt and PO.

    Args:
        receipt_data: Extracted receipt data
        po_data: Purchase order data
        builder: Discrepancy builder to record issues
        tolerance_percent: Acceptable tolerance percentage

    Returns:
        True if totals match within tolerance, False otherwise
    """
    receipt_total = safe_float(receipt_data.get('total', 0), 'receipt_total')
    po_total = safe_float(po_data.get('total', 0), 'po_total')

    # Skip if either total is zero
    if receipt_total <= 0 or po_total <= 0:
        logger.warning("Total comparison skipped: zero total detected")
        return True

    # Check if within tolerance
    if is_within_tolerance(receipt_total, po_total, tolerance_percent):
        return True

    # Calculate difference and tolerance
    difference = abs(receipt_total - po_total)
    tolerance = abs(po_total) * (tolerance_percent / 100)

    builder.add_total_mismatch(
        expected=po_total,
        actual=receipt_total,
        difference=difference,
        tolerance=tolerance
    )
    return False
