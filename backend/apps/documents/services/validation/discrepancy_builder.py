"""
Discrepancy builder for validation reports.
Follows builder pattern for clean discrepancy creation.
"""

from typing import Dict, List, Optional, Union
from decimal import Decimal


class DiscrepancyBuilder:
    """
    Builder for creating validation discrepancy records.
    Ensures consistent discrepancy structure.
    """

    def __init__(self):
        self.discrepancies: List[Dict] = []

    def add_vendor_mismatch(
        self,
        expected: str,
        actual: str,
        message: Optional[str] = None
    ) -> 'DiscrepancyBuilder':
        """Add vendor name mismatch discrepancy."""
        self.discrepancies.append({
            'type': 'VENDOR_MISMATCH',
            'severity': 'HIGH',
            'field': 'vendor',
            'expected': expected,
            'actual': actual,
            'message': message or 'Vendor name does not match'
        })
        return self

    def add_total_mismatch(
        self,
        expected: Union[Decimal, float],
        actual: Union[Decimal, float],
        difference: Union[Decimal, float],
        tolerance: Union[Decimal, float],
        message: Optional[str] = None
    ) -> 'DiscrepancyBuilder':
        """Add total amount mismatch discrepancy."""
        self.discrepancies.append({
            'type': 'TOTAL_MISMATCH',
            'severity': 'HIGH',
            'field': 'total',
            'expected': float(expected),
            'actual': float(actual),
            'difference': float(difference),
            'tolerance': float(tolerance),
            'message': message or f'Total differs by {float(difference):.2f}'
        })
        return self

    def add_quantity_mismatch(
        self,
        item_name: str,
        expected: Union[int, float],
        actual: Union[int, float],
        message: Optional[str] = None
    ) -> 'DiscrepancyBuilder':
        """Add quantity mismatch discrepancy."""
        self.discrepancies.append({
            'type': 'QUANTITY_MISMATCH',
            'severity': 'MEDIUM',
            'field': 'quantity',
            'item_name': item_name,
            'expected': float(expected),
            'actual': float(actual),
            'message': message or f"Quantity mismatch for '{item_name}'"
        })
        return self

    def add_price_mismatch(
        self,
        item_name: str,
        expected: Union[Decimal, float],
        actual: Union[Decimal, float],
        difference: Union[Decimal, float],
        tolerance: Union[Decimal, float],
        message: Optional[str] = None
    ) -> 'DiscrepancyBuilder':
        """Add price mismatch discrepancy."""
        self.discrepancies.append({
            'type': 'PRICE_MISMATCH',
            'severity': 'MEDIUM',
            'field': 'unit_price',
            'item_name': item_name,
            'expected': float(expected),
            'actual': float(actual),
            'difference': float(difference),
            'tolerance': float(tolerance),
            'message': message or f"Price mismatch for '{item_name}'"
        })
        return self

    def add_missing_item(
        self,
        item_name: str,
        message: Optional[str] = None
    ) -> 'DiscrepancyBuilder':
        """Add missing item discrepancy (in PO but not in receipt)."""
        self.discrepancies.append({
            'type': 'ITEM_MISSING_FROM_RECEIPT',
            'severity': 'HIGH',
            'field': 'items',
            'item_name': item_name,
            'message': message or f"'{item_name}' in PO but not in receipt"
        })
        return self

    def add_extra_item(
        self,
        item_name: str,
        message: Optional[str] = None
    ) -> 'DiscrepancyBuilder':
        """Add extra item discrepancy (in receipt but not in PO)."""
        self.discrepancies.append({
            'type': 'ITEM_NOT_IN_PO',
            'severity': 'MEDIUM',
            'field': 'items',
            'item_name': item_name,
            'message': message or f"'{item_name}' in receipt but not in PO"
        })
        return self

    def get_discrepancies(self) -> List[Dict]:
        """Get all discrepancies."""
        return self.discrepancies

    def has_discrepancies(self) -> bool:
        """Check if any discrepancies were added."""
        return len(self.discrepancies) > 0

    def count(self) -> int:
        """Get count of discrepancies."""
        return len(self.discrepancies)
