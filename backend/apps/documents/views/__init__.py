"""
Document processing API views.
Exports all view functions for easy importing.
"""

from .proforma_views import process_proforma, get_proforma_data
from .po_views import generate_po, get_po_data
from .receipt_views import validate_receipt_api, get_validation_report
from .task_views import get_task_status

__all__ = [
    # Proforma views
    'process_proforma',
    'get_proforma_data',

    # PO views
    'generate_po',
    'get_po_data',

    # Receipt views
    'validate_receipt_api',
    'get_validation_report',

    # Task views
    'get_task_status',
]
