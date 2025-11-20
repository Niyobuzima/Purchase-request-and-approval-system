"""
Django admin configuration for approval workflow.
"""

from django.contrib import admin
from .models import ApprovalLog


@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    """
    Admin interface for viewing approval logs.
    """
    list_display = ('id', 'request', 'approver', 'approval_level', 'action', 'created_at')
    list_filter = ('action', 'approval_level', 'created_at')
    search_fields = ('request__title', 'approver__email', 'comments')
    readonly_fields = ('id', 'request', 'approver', 'approval_level', 'action', 'comments', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        """Prevent manual creation of approval logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of approval logs for audit trail integrity"""
        return False
