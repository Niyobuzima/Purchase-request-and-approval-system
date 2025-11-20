"""
Approval workflow views.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ApprovalLog
from .serializers import ApprovalLogSerializer


@swagger_auto_schema(tags=['Approval Logs'])
class ApprovalLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing approval logs.

    Provides read-only access to approval history.
    Users can view:
    - Their own approval actions
    - Approval logs for requests they have access to
    """
    serializer_class = ApprovalLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter approval logs based on user role.

        - STAFF: See logs for their own requests
        - APPROVER_L1/L2: See all logs for requests they can access
        - FINANCE: See all logs for approved/completed requests
        - ADMIN: See all logs
        """
        # Return base queryset for schema generation
        if getattr(self, 'swagger_fake_view', False):
            return ApprovalLog.objects.none()

        user = self.request.user
        queryset = ApprovalLog.objects.select_related('approver', 'request')

        if user.role == 'STAFF':
            # Staff can only see logs for their own requests
            queryset = queryset.filter(request__created_by=user)
        elif user.role == 'APPROVER_L1':
            # L1 approvers see logs for requests at their level
            queryset = queryset.filter(
                request__status='PENDING',
                request__current_approval_level__in=[1, 2]
            )
        elif user.role == 'APPROVER_L2':
            # L2 approvers see logs for requests at their level
            queryset = queryset.filter(
                request__status='PENDING',
                request__current_approval_level=2
            )
        elif user.role == 'FINANCE':
            # Finance sees logs for approved/completed requests
            queryset = queryset.filter(request__status__in=['APPROVED', 'COMPLETED'])
        elif user.role == 'ADMIN':
            # Admin sees everything
            pass
        else:
            # Unknown role - return empty queryset
            queryset = queryset.none()

        return queryset

    @swagger_auto_schema(
        tags=['Approval Logs'],
        operation_description="Get approval logs for a specific user",
        responses={200: ApprovalLogSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='my-actions')
    def my_actions(self, request):
        """
        Get all approval actions performed by the current user.

        GET /api/approval-logs/my-actions/

        Returns list of all approval/rejection actions the user has performed.
        """
        logs = ApprovalLog.objects.filter(approver=request.user).select_related('request', 'approver')
        serializer = self.get_serializer(logs, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data
        })
