"""
API Views for Purchase Request Management.

Implements CRUD operations, approval workflow, and document handling
according to the feature guide and implementation plan.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.db import transaction
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import PurchaseRequest, RequestItem
from .serializers import (
    PurchaseRequestListSerializer,
    PurchaseRequestDetailSerializer,
    PurchaseRequestCreateSerializer,
    PurchaseRequestUpdateSerializer,
    PurchaseRequestSubmitSerializer,
    PurchaseRequestApproveSerializer,
    PurchaseRequestRejectSerializer,
    ReceiptUploadSerializer,
    RequestItemSerializer,
)
from .permissions import (
    IsOwnerOrReadOnly,
    CanApproveRequest,
    CanSubmitRequest,
    CanUploadReceipt,
    CanAccessPO,
)
from apps.approvals.models import ApprovalLog
from apps.approvals.serializers import ApprovalLogSerializer


@swagger_auto_schema(
    tags=['Purchase Requests'],
)
class PurchaseRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Purchase Request CRUD operations and workflow actions.

    Provides endpoints for:
    - List: GET /api/requests/
    - Create: POST /api/requests/
    - Retrieve: GET /api/requests/{id}/
    - Update: PUT/PATCH /api/requests/{id}/
    - Delete: DELETE /api/requests/{id}/
    - Submit: PATCH /api/requests/{id}/submit/
    - Approve: PATCH /api/requests/{id}/approve/
    - Reject: PATCH /api/requests/{id}/reject/
    - Upload Receipt: POST /api/requests/{id}/upload-receipt/
    - Download PO: GET /api/requests/{id}/download-po/
    """

    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'current_approval_level']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'total_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Filter queryset based on user role.

        - STAFF: Only their own requests
        - APPROVER_L1: Pending requests at level 1
        - APPROVER_L2: Pending requests at level 2
        - FINANCE: All approved and completed requests
        - ADMIN: All requests
        """
        # Return base queryset for schema generation
        if getattr(self, 'swagger_fake_view', False):
            return PurchaseRequest.objects.none()

        user = self.request.user
        queryset = PurchaseRequest.objects.select_related('created_by').prefetch_related('items')

        if user.role == 'STAFF':
            # Staff can only see their own requests
            queryset = queryset.filter(created_by=user)

        elif user.role == 'APPROVER_L1':
            # L1 approvers see pending requests at level 1
            queryset = queryset.filter(
                status='PENDING',
                current_approval_level=1
            )

        elif user.role == 'APPROVER_L2':
            # L2 approvers see pending requests at level 2
            queryset = queryset.filter(
                status='PENDING',
                current_approval_level=2
            )

        elif user.role == 'FINANCE':
            # Finance sees all approved and completed requests
            queryset = queryset.filter(
                status__in=['APPROVED', 'COMPLETED']
            )

        elif user.role == 'ADMIN':
            # Admin sees everything
            pass

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return PurchaseRequestListSerializer
        elif self.action == 'create':
            return PurchaseRequestCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PurchaseRequestUpdateSerializer
        elif self.action == 'submit':
            return PurchaseRequestSubmitSerializer
        elif self.action == 'approve':
            return PurchaseRequestApproveSerializer
        elif self.action == 'reject':
            return PurchaseRequestRejectSerializer
        elif self.action == 'upload_receipt':
            return ReceiptUploadSerializer
        else:
            return PurchaseRequestDetailSerializer

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        elif self.action == 'submit':
            permission_classes = [IsAuthenticated, CanSubmitRequest]
        elif self.action in ['approve', 'reject']:
            permission_classes = [IsAuthenticated, CanApproveRequest]
        elif self.action == 'upload_receipt':
            permission_classes = [IsAuthenticated, CanUploadReceipt]
        elif self.action == 'download_po':
            permission_classes = [IsAuthenticated, CanAccessPO]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        """
        Create a new purchase request.

        POST /api/requests/
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return detailed representation
        detail_serializer = PurchaseRequestDetailSerializer(instance, context={'request': request})
        return Response({
            'status': 'success',
            'message': 'Purchase request created successfully',
            'data': detail_serializer.data
        }, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a purchase request.

        GET /api/requests/{id}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    def update(self, request, *args, **kwargs):
        """
        Update a purchase request.

        PUT/PATCH /api/requests/{id}/
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Check permission
        self.check_object_permissions(request, instance)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Return detailed representation
        detail_serializer = PurchaseRequestDetailSerializer(instance, context={'request': request})
        return Response({
            'status': 'success',
            'message': 'Purchase request updated successfully',
            'data': detail_serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """
        Delete a purchase request (only DRAFT).

        DELETE /api/requests/{id}/
        """
        instance = self.get_object()

        # Only allow deleting DRAFT requests
        if instance.status != 'DRAFT':
            return Response({
                'status': 'error',
                'message': 'Only DRAFT requests can be deleted'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check permission
        self.check_object_permissions(request, instance)

        instance.delete()
        return Response({
            'status': 'success',
            'message': 'Purchase request deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        """
        List purchase requests (filtered by role).

        GET /api/requests/
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({
                'status': 'success',
                'data': serializer.data
            })

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    @swagger_auto_schema(
        tags=['Purchase Requests - Workflow'],
        operation_description="Submit a draft request for approval",
        responses={
            200: openapi.Response('Request submitted successfully', PurchaseRequestDetailSerializer),
            400: 'Bad Request - Request cannot be submitted',
            403: 'Forbidden - Not the owner',
            404: 'Not Found'
        }
    )
    @action(detail=True, methods=['patch'], url_path='submit')
    def submit(self, request, pk=None):
        """
        Submit a request for approval.

        PATCH /api/requests/{id}/submit/

        Changes status from DRAFT to PENDING and sets approval level to 1.
        """
        instance = self.get_object()

        # Check permission
        self.check_object_permissions(request, instance)

        # Validate submission
        if not instance.can_be_submitted():
            return Response({
                'status': 'error',
                'message': 'Request cannot be submitted. Ensure it is in DRAFT status and has a proforma file.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Submit the request
        with transaction.atomic():
            instance.status = 'PENDING'
            instance.current_approval_level = 1
            instance.save(update_fields=['status', 'current_approval_level', 'updated_at'])

            # Create approval log entry for submission
            ApprovalLog.objects.create(
                request=instance,
                approver=request.user,
                approval_level=0,  # 0 indicates submission
                action='SUBMITTED',
                comments=''
            )

        # Return updated representation
        serializer = PurchaseRequestDetailSerializer(instance, context={'request': request})
        return Response({
            'status': 'success',
            'message': 'Purchase request submitted successfully. Awaiting Level 1 approval.',
            'data': serializer.data
        })

    @swagger_auto_schema(
        tags=['Purchase Requests - Workflow'],
        operation_description="Approve a request at current approval level",
        request_body=PurchaseRequestApproveSerializer,
        responses={
            200: openapi.Response('Request approved', PurchaseRequestDetailSerializer),
            403: 'Forbidden - Not authorized to approve',
            404: 'Not Found'
        }
    )
    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Approve a request at current approval level.

        PATCH /api/requests/{id}/approve/

        L1 approval: Advances to level 2
        L2 approval: Changes status to APPROVED and triggers PO generation
        """
        instance = self.get_object()

        # Check permission
        self.check_object_permissions(request, instance)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comments = serializer.validated_data.get('comments', '')

        # Validate approval
        if not instance.can_be_approved_by(request.user):
            return Response({
                'status': 'error',
                'message': f'You cannot approve this request. Current approval level: {instance.current_approval_level}, Your level: {request.user.approval_level}'
            }, status=status.HTTP_403_FORBIDDEN)

        # Process approval
        with transaction.atomic():
            if instance.current_approval_level == 1:
                # L1 approval - advance to L2
                instance.current_approval_level = 2
                instance.save(update_fields=['current_approval_level', 'updated_at'])
                message = 'Request approved at Level 1. Now awaiting Level 2 approval.'

            elif instance.current_approval_level == 2:
                # L2 approval - finalize as APPROVED
                instance.status = 'APPROVED'
                instance.save(update_fields=['status', 'updated_at'])
                message = 'Request approved at Level 2. Purchase order will be generated.'

                # TODO: Trigger PO generation task
                # from apps.documents.tasks import generate_purchase_order
                # generate_purchase_order.delay(str(instance.id))

            # Create approval log entry
            ApprovalLog.objects.create(
                request=instance,
                approver=request.user,
                approval_level=request.user.approval_level,
                action='APPROVED',
                comments=comments
            )

        # Return updated representation
        detail_serializer = PurchaseRequestDetailSerializer(instance, context={'request': request})
        return Response({
            'status': 'success',
            'message': message,
            'data': detail_serializer.data
        })

    @swagger_auto_schema(
        tags=['Purchase Requests - Workflow'],
        operation_description="Reject a request at current approval level",
        request_body=PurchaseRequestRejectSerializer,
        responses={
            200: openapi.Response('Request rejected', PurchaseRequestDetailSerializer),
            403: 'Forbidden - Not authorized to reject',
            404: 'Not Found'
        }
    )
    @action(detail=True, methods=['patch'], url_path='reject')
    def reject(self, request, pk=None):
        """
        Reject a request at current approval level.

        PATCH /api/requests/{id}/reject/

        Changes status to REJECTED (immutable).
        """
        instance = self.get_object()

        # Check permission
        self.check_object_permissions(request, instance)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comments = serializer.validated_data['comments']

        # Validate rejection
        if not instance.can_be_rejected_by(request.user):
            return Response({
                'status': 'error',
                'message': f'You cannot reject this request. Current approval level: {instance.current_approval_level}, Your level: {request.user.approval_level}'
            }, status=status.HTTP_403_FORBIDDEN)

        # Process rejection
        with transaction.atomic():
            instance.status = 'REJECTED'
            instance.save(update_fields=['status', 'updated_at'])

            # Create approval log entry
            ApprovalLog.objects.create(
                request=instance,
                approver=request.user,
                approval_level=request.user.approval_level,
                action='REJECTED',
                comments=comments
            )

        # Return updated representation
        detail_serializer = PurchaseRequestDetailSerializer(instance, context={'request': request})
        return Response({
            'status': 'success',
            'message': f'Request rejected. Reason: {comments}',
            'data': detail_serializer.data
        })

    @swagger_auto_schema(
        tags=['Purchase Requests - Documents'],
        operation_description="Upload receipt for an approved request",
        request_body=ReceiptUploadSerializer,
        responses={
            200: openapi.Response('Receipt uploaded successfully', PurchaseRequestDetailSerializer),
            400: 'Bad Request - Invalid file',
            403: 'Forbidden - Not authorized',
            404: 'Not Found'
        }
    )
    @action(detail=True, methods=['post'], url_path='upload-receipt')
    def upload_receipt(self, request, pk=None):
        """
        Upload receipt for an approved request.

        POST /api/requests/{id}/upload-receipt/

        Triggers receipt validation against PO.
        """
        instance = self.get_object()

        # Check permission
        self.check_object_permissions(request, instance)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        receipt_file = serializer.validated_data['receipt_file']

        # Save receipt
        with transaction.atomic():
            instance.receipt_file = receipt_file
            instance.save(update_fields=['receipt_file', 'updated_at'])

            # TODO: Trigger receipt validation task
            # from apps.documents.tasks import validate_receipt
            # validate_receipt.delay(str(instance.id))

        # Return updated representation
        detail_serializer = PurchaseRequestDetailSerializer(instance, context={'request': request})
        return Response({
            'status': 'success',
            'message': 'Receipt uploaded successfully. Validation in progress.',
            'data': detail_serializer.data
        })

    @swagger_auto_schema(
        tags=['Purchase Requests - Documents'],
        operation_description="Download purchase order file",
        responses={
            200: openapi.Response(
                'Purchase order details',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'po_number': openapi.Schema(type=openapi.TYPE_STRING),
                                'file_url': openapi.Schema(type=openapi.TYPE_STRING),
                                'generated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                            }
                        )
                    }
                )
            ),
            404: 'Not Found - PO not generated yet'
        }
    )
    @action(detail=True, methods=['get'], url_path='download-po')
    def download_po(self, request, pk=None):
        """
        Download purchase order file.

        GET /api/requests/{id}/download-po/

        Returns purchase order file or error if not available.
        """
        instance = self.get_object()

        # Check permission
        self.check_object_permissions(request, instance)

        if not instance.purchase_order_file:
            return Response({
                'status': 'error',
                'message': 'Purchase order not yet generated for this request'
            }, status=status.HTTP_404_NOT_FOUND)

        # Return file URL
        return Response({
            'status': 'success',
            'data': {
                'po_number': instance.purchase_order_data.get('po_number') if instance.purchase_order_data else None,
                'file_url': request.build_absolute_uri(instance.purchase_order_file.url),
                'generated_at': instance.updated_at
            }
        })

    @swagger_auto_schema(
        tags=['Purchase Requests - Workflow'],
        operation_description="Get approval history for a request",
        responses={
            200: openapi.Response(
                'Approval history',
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT))
                    }
                )
            )
        }
    )
    @action(detail=True, methods=['get'], url_path='approval-history')
    def approval_history(self, request, pk=None):
        """
        Get approval history for a request.

        GET /api/requests/{id}/approval-history/

        Returns list of approval log entries.
        """
        instance = self.get_object()

        # Get approval logs for this request
        logs = ApprovalLog.objects.filter(request=instance).select_related('approver')
        serializer = ApprovalLogSerializer(logs, many=True)

        return Response({
            'status': 'success',
            'data': serializer.data
        })


@swagger_auto_schema(
    tags=['Request Items'],
)
class RequestItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing individual request items.

    Only accessible for editing items on DRAFT requests.
    """
    serializer_class = RequestItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter items based on user access to parent request"""
        # Return base queryset for schema generation
        if getattr(self, 'swagger_fake_view', False):
            return RequestItem.objects.none()

        user = self.request.user
        if user.role == 'STAFF':
            # Staff can only see items from their own requests
            return RequestItem.objects.filter(request__created_by=user)
        elif user.role == 'ADMIN':
            return RequestItem.objects.all()
        else:
            # Approvers and Finance see items from visible requests
            return RequestItem.objects.none()

    def create(self, request, *args, **kwargs):
        """Add item to a request (only DRAFT)"""
        # TODO: Implement with proper validation
        return Response({
            'status': 'error',
            'message': 'Use request update endpoint to manage items'
        }, status=status.HTTP_400_BAD_REQUEST)
