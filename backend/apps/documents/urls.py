"""
URL Configuration for Document Processing API.
"""

from django.urls import path
from .views import (
    process_proforma,
    get_proforma_data,
    generate_po,
    get_po_data,
    validate_receipt_api,
    get_validation_report,
    get_task_status
)

app_name = 'documents'

urlpatterns = [
    # Proforma processing
    path('documents/proforma/process/', process_proforma, name='process-proforma'),
    path('documents/proforma/data/', get_proforma_data, name='get-proforma-data'),

    # Purchase Order generation
    path('documents/po/generate/', generate_po, name='generate-po'),
    path('documents/po/data/', get_po_data, name='get-po-data'),

    # Receipt validation
    path('documents/receipt/validate/', validate_receipt_api, name='validate-receipt'),
    path('documents/receipt/validation-report/', get_validation_report, name='get-validation-report'),

    # Task status
    path('documents/task-status/', get_task_status, name='get-task-status'),
]
