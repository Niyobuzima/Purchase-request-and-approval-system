"""
Receipt validation modules.
Modular validation logic following KISS principle.
"""

from .vendor_comparison import compare_vendors
from .total_comparison import compare_totals
from .item_comparison import compare_items
from .discrepancy_builder import DiscrepancyBuilder
from .report_generator import generate_validation_report

__all__ = [
    'compare_vendors',
    'compare_totals',
    'compare_items',
    'DiscrepancyBuilder',
    'generate_validation_report',
]
