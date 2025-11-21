"""
Receipt validation API views.
Handles receipt upload, validation, and report retrieval endpoints.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.purchase_requests.models import PurchaseRequest
from ..serializers import ReceiptValidationSerializer, ValidationReportSerializer
from ..tasks import validate_receipt
from ..utils import validate_uuid_param

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    tags=['Document Processing'],
    operation_summary='Validate receipt against PO',
    operation_description='Validate receipt using GPT-5 Vision and compare with PO. '
                         'This is an async operation that returns a task ID.',
    request_body=ReceiptValidationSerializer,
    responses={
        200: openapi.Response(
            description='Receipt validation started successfully',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, example='success'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING),
                    'task_id': openapi.Schema(type=openapi.TYPE_STRING),
                    'request_id': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        400: 'Bad Request',
        404: 'Purchase request not found'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_receipt_api(request):
    """Validate receipt against Purchase Order."""
    serializer = ReceiptValidationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'message': 'Invalid request data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    request_id = serializer.validated_data['request_id']

    try:
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check access
        if request.user.role == 'STAFF' and purchase_request.created_by != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to validate receipt for this request'
            }, status=status.HTTP_403_FORBIDDEN)

        # Validate receipt file exists
        if not purchase_request.receipt_file:
            return Response({
                'status': 'error',
                'message': 'No receipt file uploaded for this request'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate PO data exists
        if not purchase_request.purchase_order_data:
            return Response({
                'status': 'error',
                'message': 'No PO data available. Please generate the PO first.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Start async validation
        task = validate_receipt.delay(str(request_id))
        logger.info(f"Receipt validation started for request {request_id}, task {task.id}")

        return Response({
            'status': 'success',
            'message': 'Receipt validation started',
            'task_id': task.id,
            'request_id': str(request_id)
        }, status=status.HTTP_200_OK)

    except PurchaseRequest.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Purchase request not found'
        }, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='get',
    tags=['Document Processing'],
    operation_summary='Get receipt validation report',
    operation_description='Retrieve validation report for a receipt',
    manual_parameters=[
        openapi.Parameter(
            'request_id',
            openapi.IN_QUERY,
            description='UUID of the purchase request',
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description='Validation report retrieved successfully',
            schema=ValidationReportSerializer
        ),
        404: 'Not found'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_validation_report(request):
    """Get receipt validation report for a purchase request."""
    request_id_str = request.query_params.get('request_id')
    
    # Validate UUID format
    request_id, error_response = validate_uuid_param(request_id_str)
    if error_response:
        return error_response

    try:
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check access
        if request.user.role == 'STAFF' and purchase_request.created_by != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to view this data'
            }, status=status.HTTP_403_FORBIDDEN)

        if not purchase_request.receipt_validation:
            return Response({
                'status': 'error',
                'message': 'No validation data available. Please validate the receipt first.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ValidationReportSerializer(purchase_request.receipt_validation)

        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except PurchaseRequest.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Purchase request not found'
        }, status=status.HTTP_404_NOT_FOUND)
