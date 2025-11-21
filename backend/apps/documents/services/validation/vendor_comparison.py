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
        True if vendors match, False otherwise.
        Returns False and records discrepancy if vendor data is missing or empty.
    """
    # Defensively extract vendor data
    receipt_vendor_raw = receipt_data.get('vendor_name') or ''
    receipt_vendor = receipt_vendor_raw.lower().strip() if isinstance(receipt_vendor_raw, str) else ''
    
    # Guard against po_data['vendor'] being None
    vendor_dict = po_data.get('vendor') or {}
    po_vendor_raw = vendor_dict.get('name') or ''
    po_vendor = po_vendor_raw.lower().strip() if isinstance(po_vendor_raw, str) else ''

    # Check for missing vendor data
    if not receipt_vendor and not po_vendor:
        logger.warning("Both vendors are missing or empty")
        builder.add_vendor_missing(
            expected=po_vendor_raw or None,
            actual=receipt_vendor_raw or None,
            message='Both receipt and PO vendor information are missing or empty'
        )
        return False
    
    if not receipt_vendor:
        logger.warning("Receipt vendor is missing or empty")
        builder.add_vendor_missing(
            expected=po_vendor_raw or None,
            actual=receipt_vendor_raw or None,
            message='Receipt vendor information is missing or empty'
        )
        return False
    
    if not po_vendor:
        logger.warning("PO vendor is missing or empty")
        builder.add_vendor_missing(
            expected=po_vendor_raw or None,
            actual=receipt_vendor_raw or None,
            message='PO vendor information is missing or empty'
        )
        return False

    # Fuzzy match - check if one contains the other
    if receipt_vendor in po_vendor or po_vendor in receipt_vendor:
        return True

    # No match - record discrepancy with original values
    builder.add_vendor_mismatch(
        expected=po_vendor_raw,
        actual=receipt_vendor_raw
    )
    return False
