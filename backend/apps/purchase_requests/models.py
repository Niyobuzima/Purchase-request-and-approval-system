import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()


class PurchaseRequest(models.Model):
    """
    Model representing a purchase request in the approval workflow.

    Status Flow:
        DRAFT -> PENDING -> APPROVED/REJECTED -> COMPLETED

    Approval Levels:
        0: Draft (not submitted)
        1: Pending Level 1 Approval
        2: Pending Level 2 Approval (final)

    Once APPROVED or REJECTED, status is immutable.
    """

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]

    # Primary key - UUID for security and uniqueness
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this purchase request"
    )

    # Basic Information
    title = models.CharField(
        max_length=255,
        help_text="Brief title describing the purchase request"
    )
    description = models.TextField(
        help_text="Detailed description of the purchase request"
    )

    # Status and Workflow
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True,
        help_text="Current status of the purchase request"
    )
    current_approval_level = models.IntegerField(
        default=0,
        help_text="Current approval level (0=draft, 1=L1, 2=L2)"
    )

    # Financial Information
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total amount of the purchase request"
    )

    # User Relationships
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='purchase_requests',
        help_text="User who created this request"
    )

    # Document Files
    proforma_file = models.FileField(
        upload_to='proforma/%Y/%m/',
        null=True,
        blank=True,
        help_text="Uploaded proforma invoice/quotation file"
    )
    purchase_order_file = models.FileField(
        upload_to='purchase_orders/%Y/%m/',
        null=True,
        blank=True,
        help_text="Generated purchase order file"
    )
    receipt_file = models.FileField(
        upload_to='receipts/%Y/%m/',
        null=True,
        blank=True,
        help_text="Uploaded receipt file after purchase completion"
    )

    # Extracted Data (JSON fields for AI-processed data)
    proforma_extracted_data = models.JSONField(
        null=True,
        blank=True,
        help_text="AI-extracted data from proforma invoice"
    )
    purchase_order_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Data used to generate the purchase order"
    )
    receipt_data = models.JSONField(
        null=True,
        blank=True,
        help_text="AI-extracted data from receipt"
    )
    receipt_validation = models.JSONField(
        null=True,
        blank=True,
        help_text="Receipt validation results comparing against PO"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when request was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when request was last updated"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Purchase Request'
        verbose_name_plural = 'Purchase Requests'
        indexes = [
            # Index for filtering by status and sorting by date
            models.Index(fields=['status', '-created_at']),
            # Index for filtering user's own requests
            models.Index(fields=['created_by', 'status']),
            # Index for approval workflow queries
            models.Index(fields=['status', 'current_approval_level']),
        ]
        constraints = [
            # Ensure total amount is positive if set
            models.CheckConstraint(
                check=models.Q(total_amount__gt=0) | models.Q(total_amount__isnull=True),
                name='total_amount_positive'
            ),
            # Ensure approval level is valid
            models.CheckConstraint(
                check=models.Q(current_approval_level__gte=0) & models.Q(current_approval_level__lte=2),
                name='valid_approval_level'
            ),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def can_be_edited(self):
        """Check if request can be edited (only DRAFT or PENDING can be edited)"""
        return self.status in ['DRAFT', 'PENDING']

    def can_be_submitted(self):
        """Check if request can be submitted for approval"""
        return self.status == 'DRAFT' and self.proforma_file

    def can_be_approved_by(self, user):
        """Check if user can approve this request at current level"""
        return (
            self.status == 'PENDING' and
            user.approval_level == self.current_approval_level and
            user.role in ['APPROVER_L1', 'APPROVER_L2']
        )

    def can_be_rejected_by(self, user):
        """Check if user can reject this request"""
        return self.can_be_approved_by(user)

    def is_finalized(self):
        """Check if request has been finalized (approved or rejected)"""
        return self.status in ['APPROVED', 'REJECTED']

    def get_approval_progress(self):
        """Get approval progress percentage"""
        if self.status == 'DRAFT':
            return 0
        elif self.status == 'PENDING':
            if self.current_approval_level == 1:
                return 33
            elif self.current_approval_level == 2:
                return 66
        elif self.status == 'APPROVED':
            return 100
        elif self.status == 'REJECTED':
            return 0
        return 0


class RequestItem(models.Model):
    """
    Model representing individual line items in a purchase request.

    Each purchase request can have multiple items with quantities and prices.
    """

    # Relationships
    request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='items',
        help_text="The purchase request this item belongs to"
    )

    # Item Details
    item_name = models.CharField(
        max_length=255,
        help_text="Name of the item being requested"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the item"
    )

    # Quantities and Pricing
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Quantity of items requested"
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per unit"
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total price (quantity * unit_price)"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when item was added"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when item was last updated"
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Request Item'
        verbose_name_plural = 'Request Items'
        constraints = [
            # Ensure all financial values are positive
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name='quantity_positive'
            ),
            models.CheckConstraint(
                check=models.Q(unit_price__gt=0),
                name='unit_price_positive'
            ),
            models.CheckConstraint(
                check=models.Q(total_price__gt=0),
                name='total_price_positive'
            ),
        ]

    def __str__(self):
        return f"{self.item_name} x{self.quantity} @ {self.unit_price}"

    def save(self, *args, **kwargs):
        """Override save to automatically calculate total_price"""
        # Calculate total price from quantity and unit price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

        # Update parent request's total amount
        self.update_request_total()

    def update_request_total(self):
        """Update the parent request's total amount based on all items"""
        from django.db.models import Sum

        # Calculate sum of all items' total prices
        total = self.request.items.aggregate(
            total=Sum('total_price')
        )['total'] or Decimal('0.00')

        # Update request's total amount
        if self.request.total_amount != total:
            self.request.total_amount = total
            self.request.save(update_fields=['total_amount', 'updated_at'])
