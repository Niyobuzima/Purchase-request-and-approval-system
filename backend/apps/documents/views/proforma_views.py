"""
Proforma invoice processing API views.
Handles proforma document upload and extraction endpoints.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.purchase_requests.models import PurchaseRequest
from ..serializers import ProformaProcessingSerializer, ProformaDataSerializer
from ..tasks import process_proforma_document

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    tags=['Document Processing'],
    operation_summary='Process proforma invoice with AI',
    operation_description='Extract structured data from proforma invoice using GPT-5. '
                         'This is an async operation that returns a task ID.',
    request_body=ProformaProcessingSerializer,
    responses={
        200: openapi.Response(
            description='Processing started successfully',
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
def process_proforma(request):
    """Process proforma invoice document using AI extraction."""
    serializer = ProformaProcessingSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'status': 'error',
            'message': 'Invalid request data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    request_id = serializer.validated_data['request_id']

    try:
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check access permission
        if request.user.role == 'STAFF' and purchase_request.created_by != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to process this request'
            }, status=status.HTTP_403_FORBIDDEN)

        # Validate proforma file exists
        if not purchase_request.proforma_file:
            return Response({
                'status': 'error',
                'message': 'No proforma file uploaded for this request'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Start async processing
        task = process_proforma_document.delay(str(request_id))
        logger.info(f"Proforma processing started for request {request_id}, task {task.id}")

        return Response({
            'status': 'success',
            'message': 'Proforma processing started',
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
    operation_summary='Get extracted proforma data',
    operation_description='Retrieve extracted proforma data for a purchase request',
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
            description='Proforma data retrieved successfully',
            schema=ProformaDataSerializer
        ),
        404: 'Not found'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_proforma_data(request):
    """Get extracted proforma data for a purchase request."""
    request_id = request.query_params.get('request_id')

    if not request_id:
        return Response({
            'status': 'error',
            'message': 'request_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        purchase_request = PurchaseRequest.objects.get(id=request_id)

        # Check access
        if request.user.role == 'STAFF' and purchase_request.created_by != request.user:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to view this data'
            }, status=status.HTTP_403_FORBIDDEN)

        if not purchase_request.proforma_extracted_data:
            return Response({
                'status': 'error',
                'message': 'No proforma data available. Please process the proforma file first.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ProformaDataSerializer(purchase_request.proforma_extracted_data)

        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except PurchaseRequest.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Purchase request not found'
        }, status=status.HTTP_404_NOT_FOUND)
