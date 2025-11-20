"""
Serializers for Purchase Request API.

Implements data validation, transformation, and nested serialization
according to the feature guide and API design specifications.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PurchaseRequest, RequestItem
from decimal import Decimal

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for nested representations.
    Only exposes safe, non-sensitive user information.
    """
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role']
        read_only_fields = fields

    def get_name(self, obj):
        """Return full name of the user"""
        return obj.get_full_name() or obj.email


class RequestItemSerializer(serializers.ModelSerializer):
    """
    Serializer for individual request line items.
    Handles automatic total_price calculation.
    """

    class Meta:
        model = RequestItem
        fields = [
            'id',
            'item_name',
            'description',
            'quantity',
            'unit_price',
            'total_price',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']

    def validate_quantity(self, value):
        """Ensure quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero")
        return value

    def validate_unit_price(self, value):
        """Ensure unit price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Unit price must be greater than zero")
        return value


class PurchaseRequestListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list views.
    Minimizes data transfer for performance.
    """
    created_by = UserMinimalSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_progress = serializers.IntegerField(source='get_approval_progress', read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            'id',
            'title',
            'status',
            'status_display',
            'total_amount',
            'current_approval_level',
            'approval_progress',
            'created_by',
            'created_at',
            'updated_at'
        ]
        read_only_fields = fields


class PurchaseRequestDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for detail views.
    Includes all fields and nested relationships.
    """
    created_by = UserMinimalSerializer(read_only=True)
    items = RequestItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approval_progress = serializers.IntegerField(source='get_approval_progress', read_only=True)
    can_be_edited = serializers.SerializerMethodField()
    can_be_submitted = serializers.SerializerMethodField()
    is_finalized = serializers.SerializerMethodField()

    # Override file fields to handle empty files
    proforma_file = serializers.SerializerMethodField()
    purchase_order_file = serializers.SerializerMethodField()
    receipt_file = serializers.SerializerMethodField()

    def get_can_be_edited(self, obj):
        """Check if request can be edited"""
        return obj.can_be_edited()

    def get_can_be_submitted(self, obj):
        """Check if request can be submitted"""
        return obj.can_be_submitted()

    def get_is_finalized(self, obj):
        """Check if request is finalized"""
        return obj.is_finalized()

    def get_proforma_file(self, obj):
        """Get proforma file URL or None"""
        if obj.proforma_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.proforma_file.url)
            return obj.proforma_file.url
        return None

    def get_purchase_order_file(self, obj):
        """Get purchase order file URL or None"""
        if obj.purchase_order_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.purchase_order_file.url)
            return obj.purchase_order_file.url
        return None

    def get_receipt_file(self, obj):
        """Get receipt file URL or None"""
        if obj.receipt_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.receipt_file.url)
            return obj.receipt_file.url
        return None

    class Meta:
        model = PurchaseRequest
        exclude = []  # Use all fields
        fields = [
            'id',
            'title',
            'description',
            'status',
            'status_display',
            'current_approval_level',
            'total_amount',
            'created_by',
            'proforma_file',
            'proforma_extracted_data',
            'purchase_order_file',
            'purchase_order_data',
            'receipt_file',
            'receipt_data',
            'receipt_validation',
            'items',
            'approval_progress',
            'can_be_edited',
            'can_be_submitted',
            'is_finalized',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'status',
            'current_approval_level',
            'total_amount',
            'created_by',
            'proforma_extracted_data',
            'proforma_file',  # Read-only because we use SerializerMethodField
            'purchase_order_file',  # Read-only because we use SerializerMethodField
            'purchase_order_data',
            'receipt_file',  # Read-only because we use SerializerMethodField
            'receipt_data',
            'receipt_validation',
            'created_at',
            'updated_at'
        ]


class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating purchase requests.
    Handles file upload and initial data validation.
    """
    items = RequestItemSerializer(many=True, required=False)

    class Meta:
        model = PurchaseRequest
        fields = [
            'title',
            'description',
            'proforma_file',
            'items'
        ]

    def validate_title(self, value):
        """Ensure title is not empty and reasonable length"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        if len(value) > 255:
            raise serializers.ValidationError("Title is too long (max 255 characters)")
        return value.strip()

    def validate_description(self, value):
        """Ensure description is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Description cannot be empty")
        return value.strip()

    def validate_proforma_file(self, value):
        """Validate proforma file upload"""
        if value:
            # Check file size (max 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if value.size > max_size:
                raise serializers.ValidationError(
                    f"File size exceeds maximum limit of 10MB (got {value.size / 1024 / 1024:.2f}MB)"
                )

            # Check file extension
            allowed_extensions = ['pdf', 'png', 'jpg', 'jpeg']
            file_extension = value.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise serializers.ValidationError(
                    f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
                )

        return value

    def create(self, validated_data):
        """Create purchase request with items"""
        items_data = validated_data.pop('items', [])
        request = self.context.get('request')

        # Create the purchase request
        purchase_request = PurchaseRequest.objects.create(
            created_by=request.user,
            **validated_data
        )

        # Create items if provided
        for item_data in items_data:
            RequestItem.objects.create(
                request=purchase_request,
                **item_data
            )

        return purchase_request


class PurchaseRequestUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating purchase requests.
    Only allows updating specific fields based on status.
    """
    items = RequestItemSerializer(many=True, required=False)

    class Meta:
        model = PurchaseRequest
        fields = [
            'title',
            'description',
            'proforma_file',
            'items'
        ]

    def validate(self, attrs):
        """Ensure request can be edited"""
        instance = self.instance
        if instance and not instance.can_be_edited():
            raise serializers.ValidationError(
                "Cannot edit request in current status. Only DRAFT and PENDING requests can be edited."
            )
        return attrs

    def update(self, instance, validated_data):
        """Update purchase request and items"""
        items_data = validated_data.pop('items', None)

        # Update request fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update items if provided (replace all items)
        if items_data is not None:
            # Delete existing items
            instance.items.all().delete()

            # Create new items
            for item_data in items_data:
                RequestItem.objects.create(
                    request=instance,
                    **item_data
                )

        return instance


class PurchaseRequestSubmitSerializer(serializers.Serializer):
    """
    Serializer for submitting a request for approval.
    """
    pass  # No additional fields needed


class PurchaseRequestApproveSerializer(serializers.Serializer):
    """
    Serializer for approving a request.
    """
    comments = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=5000,
        help_text="Optional comments about the approval"
    )


class PurchaseRequestRejectSerializer(serializers.Serializer):
    """
    Serializer for rejecting a request.
    """
    comments = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=5000,
        help_text="Required reason for rejection"
    )

    def validate_comments(self, value):
        """Ensure rejection reason is provided"""
        if not value or not value.strip():
            raise serializers.ValidationError("Rejection reason is required")
        return value.strip()


class ReceiptUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading receipt files.
    """
    receipt_file = serializers.FileField(
        required=True,
        help_text="Receipt file (PDF, PNG, JPG)"
    )

    def validate_receipt_file(self, value):
        """Validate receipt file upload"""
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size exceeds maximum limit of 10MB (got {value.size / 1024 / 1024:.2f}MB)"
            )

        # Check file extension
        allowed_extensions = ['pdf', 'png', 'jpg', 'jpeg']
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(
                f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
            )

        return value
