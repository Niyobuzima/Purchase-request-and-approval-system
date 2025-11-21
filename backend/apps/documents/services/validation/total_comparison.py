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
        True if totals match within tolerance, False otherwise.
        Returns False if either total is missing, invalid, or zero,
        and records an appropriate discrepancy.
    """
    receipt_total = safe_float(receipt_data.get('total', 0), 'receipt_total')
    po_total = safe_float(po_data.get('total', 0), 'po_total')

    # Check for missing or invalid totals
    if receipt_total <= 0 and po_total <= 0:
        logger.warning("Both totals are zero or missing")
        builder.add_missing_data(
            field='total',
            expected=po_total,
            actual=receipt_total,
            message='Both receipt and PO totals are missing or invalid'
        )
        return False
    
    if receipt_total <= 0:
        logger.warning("Receipt total is zero or missing")
        builder.add_missing_data(
            field='total',
            expected=po_total,
            actual=receipt_total,
            message='Receipt total is missing or invalid'
        )
        return False
    
    if po_total <= 0:
        logger.warning("PO total is zero or missing")
        builder.add_missing_data(
            field='total',
            expected=po_total,
            actual=receipt_total,
            message='PO total is missing or invalid'
        )
        return False

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
