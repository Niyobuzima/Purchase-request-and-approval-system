"""
Line item comparison logic.
"""

import logging
from typing import Dict, List, Optional

from ..shared.converters import safe_float
from ..shared.comparisons import is_within_tolerance
from .discrepancy_builder import DiscrepancyBuilder

logger = logging.getLogger(__name__)


def compare_items(
    receipt_data: Dict,
    po_data: Dict,
    builder: DiscrepancyBuilder,
    tolerance_percent: float = 5.0
) -> bool:
    """
    Compare line items between receipt and PO.

    Args:
        receipt_data: Extracted receipt data
        po_data: Purchase order data
        builder: Discrepancy builder to record issues
        tolerance_percent: Acceptable tolerance percentage for prices

    Returns:
        True if all items match, False otherwise
    """
    all_items_valid = True

    # Build normalized item dictionaries
    po_items = _normalize_items(po_data.get('items', []))
    receipt_items = _normalize_items(receipt_data.get('items', []))

    # Compare each receipt item against PO
    for receipt_item in receipt_items.values():
        matched_po_item = _find_matching_item(receipt_item, po_items)

        if not matched_po_item:
            # Extra item in receipt
            builder.add_extra_item(receipt_item['name'])
            continue

        # Compare quantity
        if not _compare_quantity(receipt_item, matched_po_item, builder):
            all_items_valid = False

        # Compare price
        if not _compare_price(receipt_item, matched_po_item, builder, tolerance_percent):
            all_items_valid = False

    # Check for missing items (in PO but not in receipt)
    for po_item in po_items.values():
        if not _find_matching_item(po_item, receipt_items):
            builder.add_missing_item(po_item['name'])
            all_items_valid = False

    return all_items_valid


def _normalize_items(items: List[Dict]) -> Dict[str, Dict]:
    """Normalize items list into dictionary keyed by lowercase name."""
    normalized = {}

    if not isinstance(items, list):
        return normalized

    for item in items:
        if not isinstance(item, dict):
            continue

        name = item.get('name', '')
        if not isinstance(name, str) or not name.strip():
            continue

        normalized[name.lower().strip()] = {
            'name': name,
            'quantity': safe_float(item.get('quantity', 0), 'quantity'),
            'unit_price': safe_float(item.get('unit_price', 0), 'unit_price'),
        }

    return normalized


def _find_matching_item(item: Dict, items_dict: Dict[str, Dict]) -> Optional[Dict]:
    """Find matching item using fuzzy name matching."""
    item_name = item['name'].lower().strip()

    # Exact match
    if item_name in items_dict:
        return items_dict[item_name]

    # Fuzzy match - check if one contains the other
    for candidate_name, candidate_item in items_dict.items():
        if item_name in candidate_name or candidate_name in item_name:
            return candidate_item

    return None


def _compare_quantity(
    receipt_item: Dict,
    po_item: Dict,
    builder: DiscrepancyBuilder
) -> bool:
    """Compare quantities between receipt and PO items."""
    receipt_qty = receipt_item['quantity']
    po_qty = po_item['quantity']

    if receipt_qty == po_qty:
        return True

    builder.add_quantity_mismatch(
        item_name=receipt_item['name'],
        expected=po_qty,
        actual=receipt_qty
    )
    return False


def _compare_price(
    receipt_item: Dict,
    po_item: Dict,
    builder: DiscrepancyBuilder,
    tolerance_percent: float
) -> bool:
    """Compare unit prices with tolerance."""
    receipt_price = receipt_item['unit_price']
    po_price = po_item['unit_price']

    # Skip if either price is zero
    if receipt_price <= 0 or po_price <= 0:
        return True

    if is_within_tolerance(receipt_price, po_price, tolerance_percent):
        return True

    difference = abs(receipt_price - po_price)
    tolerance = abs(po_price) * (tolerance_percent / 100)

    builder.add_price_mismatch(
        item_name=receipt_item['name'],
        expected=po_price,
        actual=receipt_price,
        difference=difference,
        tolerance=tolerance
    )
    return False
