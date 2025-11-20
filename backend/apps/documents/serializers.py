"""
Serializers for document processing APIs.
"""

from rest_framework import serializers


class ProformaProcessingSerializer(serializers.Serializer):
    """Serializer for initiating proforma document processing."""

    request_id = serializers.UUIDField(
        help_text="UUID of the purchase request with uploaded proforma file"
    )


class ProformaDataSerializer(serializers.Serializer):
    """Serializer for displaying extracted proforma data."""

    vendor = serializers.DictField(help_text="Vendor information")
    invoice_number = serializers.CharField(help_text="Invoice/proforma number")
    date = serializers.CharField(help_text="Invoice date")
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of invoice items"
    )
    subtotal = serializers.FloatField(help_text="Subtotal amount")
    tax = serializers.FloatField(help_text="Tax amount")
    total = serializers.FloatField(help_text="Total amount")
    currency = serializers.CharField(help_text="Currency code")
    payment_terms = serializers.CharField(help_text="Payment terms")


class POGenerationSerializer(serializers.Serializer):
    """Serializer for initiating PO generation."""

    request_id = serializers.UUIDField(
        help_text="UUID of the approved purchase request"
    )


class PODataSerializer(serializers.Serializer):
    """Serializer for displaying PO data."""

    po_number = serializers.CharField(help_text="Purchase Order number")
    date = serializers.CharField(help_text="PO generation date")
    request_id = serializers.UUIDField(help_text="Related purchase request ID")
    vendor = serializers.DictField(help_text="Vendor information")
    buyer = serializers.DictField(help_text="Buyer information")
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of PO items"
    )
    subtotal = serializers.FloatField(help_text="Subtotal amount")
    tax = serializers.FloatField(help_text="Tax amount")
    total = serializers.FloatField(help_text="Total amount")
    currency = serializers.CharField(help_text="Currency code")
    payment_terms = serializers.CharField(help_text="Payment terms")
    delivery_terms = serializers.CharField(help_text="Delivery terms")
    approved_by = serializers.DictField(help_text="Approver information")


class ReceiptValidationSerializer(serializers.Serializer):
    """Serializer for initiating receipt validation."""

    request_id = serializers.UUIDField(
        help_text="UUID of the purchase request with uploaded receipt"
    )


class DiscrepancySerializer(serializers.Serializer):
    """Serializer for validation discrepancy."""

    type = serializers.CharField(help_text="Discrepancy type")
    severity = serializers.CharField(help_text="Severity level (HIGH, MEDIUM, LOW)")
    field = serializers.CharField(help_text="Field with discrepancy")
    message = serializers.CharField(help_text="Human-readable description")
    expected = serializers.Field(required=False, help_text="Expected value")
    actual = serializers.Field(required=False, help_text="Actual value")
    difference = serializers.FloatField(required=False, help_text="Numeric difference")
    tolerance = serializers.FloatField(required=False, help_text="Allowed tolerance")
    item_name = serializers.CharField(required=False, help_text="Item name (for item-level discrepancies)")


class ValidationReportSerializer(serializers.Serializer):
    """Serializer for receipt validation report."""

    is_valid = serializers.BooleanField(help_text="Overall validation status")
    validation_date = serializers.CharField(help_text="When validation was performed")
    po_number = serializers.CharField(help_text="Related PO number")
    receipt_number = serializers.CharField(help_text="Receipt/invoice number")
    discrepancies_count = serializers.IntegerField(help_text="Number of discrepancies found")
    discrepancies = DiscrepancySerializer(many=True, help_text="List of discrepancies")
    receipt_data = serializers.DictField(help_text="Extracted receipt data")
    summary = serializers.CharField(help_text="Human-readable summary")


class TaskStatusSerializer(serializers.Serializer):
    """Serializer for Celery task status."""

    task_id = serializers.CharField(help_text="Celery task ID")
    status = serializers.CharField(help_text="Task status (PENDING, STARTED, SUCCESS, FAILURE)")
    result = serializers.Field(required=False, help_text="Task result if completed")
    error = serializers.CharField(required=False, help_text="Error message if failed")
