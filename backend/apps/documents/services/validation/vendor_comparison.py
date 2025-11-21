"""
Vendor comparison logic.
"""

import logging
from typing import Dict

from .discrepancy_builder import DiscrepancyBuilder

logger = logging.getLogger(__name__)


def compare_vendors(
    receipt_data: Dict,
    po_data: Dict,
    builder: DiscrepancyBuilder
) -> bool:
    """
    Compare vendor information between receipt and PO.

    Args:
        receipt_data: Extracted receipt data
        po_data: Purchase order data
        builder: Discrepancy builder to record issues

    Returns:
        True if vendors match, False otherwise
    """
    receipt_vendor = receipt_data.get('vendor_name', '').lower().strip()
    po_vendor = po_data.get('vendor', {}).get('name', '').lower().strip()

    # Skip if either vendor is empty
    if not receipt_vendor or not po_vendor:
        logger.warning("Vendor comparison skipped: empty vendor name")
        return True

    # Fuzzy match - check if one contains the other
    if receipt_vendor in po_vendor or po_vendor in receipt_vendor:
        return True

    # No match - record discrepancy
    builder.add_vendor_mismatch(
        expected=po_data.get('vendor', {}).get('name'),
        actual=receipt_data.get('vendor_name')
    )
    return False
