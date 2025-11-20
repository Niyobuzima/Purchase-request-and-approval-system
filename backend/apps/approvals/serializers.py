"""
Serializers for approval workflow.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ApprovalLog

User = get_user_model()


class ApproverMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for approval logs.
    """
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'role']
        read_only_fields = fields

    def get_name(self, obj):
        """Return full name of the approver"""
        return obj.get_full_name() or obj.email


class ApprovalLogSerializer(serializers.ModelSerializer):
    """
    Serializer for approval log entries.
    Provides full audit trail information.
    """
    approver = ApproverMinimalSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = ApprovalLog
        fields = [
            'id',
            'approver',
            'approval_level',
            'action',
            'action_display',
            'comments',
            'created_at'
        ]
        read_only_fields = fields
