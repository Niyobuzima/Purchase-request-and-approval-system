"""
Purchase Order generation API views.
Handles PO creation and retrieval endpoints.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.purchase_requests.models import PurchaseRequest
from ..serializers import POGenerationSerializer, PODataSerializer
from ..tasks import generate_purchase_order
from ..utils import validate_uuid_param, check_purchase_request_access

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    tags=['Document Processing'],
    operation_summary='Generate Purchase Order',
    operation_description='Generate PO PDF for approved purchase request. '
                         'This is an async operation that returns a task ID.',
    request_body=POGenerationSerializer,
    responses={
        200: openapi.Response(
            description='PO generation started successfully',
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
def generate_po(request):
    """Generate Purchase Order PDF for approved request."""
    serializer = POGenerationSerializer(data=request.data)

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
        error_response = check_purchase_request_access(
            request.user, purchase_request, 'generate PO for'
        )
        if error_response:
            return error_response

        # Validate request status
        if purchase_request.status != 'APPROVED':
            return Response({
                'status': 'error',
                'message': f'Request must be approved before generating PO (current status: {purchase_request.status})'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate proforma data exists
        if not purchase_request.proforma_extracted_data:
            return Response({
                'status': 'error',
                'message': 'No proforma data available. Please process the proforma file first.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Start async PO generation
        task = generate_purchase_order.delay(str(request_id))
        logger.info(f"PO generation started for request {request_id}, task {task.id}")

        return Response({
            'status': 'success',
            'message': 'Purchase Order generation started',
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
    operation_summary='Get Purchase Order data',
    operation_description='Retrieve PO data for a purchase request',
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
            description='PO data retrieved successfully',
            schema=PODataSerializer
        ),
        404: 'Not found'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_po_data(request):
    """Get PO data for a purchase request."""
    request_id_str = request.query_params.get('request_id')
    
    # Validate UUID format
    request_id, error_response = validate_uuid_param(request_id_str)
    if error_response:
        return error_response

    try:
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check access
        error_response = check_purchase_request_access(
            request.user, purchase_request, 'view'
        )
        if error_response:
            return error_response

        if not purchase_request.purchase_order_data:
            return Response({
                'status': 'error',
                'message': 'No PO data available. Please generate the PO first.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PODataSerializer(purchase_request.purchase_order_data)

        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except PurchaseRequest.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Purchase request not found'
        }, status=status.HTTP_404_NOT_FOUND)
