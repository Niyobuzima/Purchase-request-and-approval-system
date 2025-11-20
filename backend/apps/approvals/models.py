"""
Approval workflow models.

Tracks the history of approval actions on purchase requests.
"""

from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class ApprovalLog(models.Model):
    """
    Records all approval-related actions on purchase requests.

    Provides a complete audit trail of:
    - When requests were submitted
    - Who approved/rejected at each level
    - Comments/reasons for decisions
    - Timestamps for all actions
    """

    ACTION_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('UPDATED', 'Updated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        'purchase_requests.PurchaseRequest',
        on_delete=models.CASCADE,
        related_name='approval_logs'
    )
    approver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='approval_actions'
    )
    approval_level = models.IntegerField(
        help_text="Approval level at which action was taken (0=submission, 1=L1, 2=L2)"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comments = models.TextField(blank=True, help_text="Approval/rejection reason or notes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['request', 'created_at']),
            models.Index(fields=['approver', '-created_at']),
            models.Index(fields=['action', '-created_at']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} by {self.approver.get_full_name()} on {self.request.title}"
