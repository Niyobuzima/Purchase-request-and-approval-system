"""
Celery task status API views.
Handles async task status checking endpoints.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from celery.result import AsyncResult

from ..serializers import TaskStatusSerializer

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='get',
    tags=['Document Processing'],
    operation_summary='Get task status',
    operation_description='Check status of async document processing task',
    manual_parameters=[
        openapi.Parameter(
            'task_id',
            openapi.IN_QUERY,
            description='Celery task ID',
            type=openapi.TYPE_STRING,
            required=True
        )
    ],
    responses={
        200: openapi.Response(
            description='Task status retrieved successfully',
            schema=TaskStatusSerializer
        ),
        400: 'Bad Request'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_status(request):
    """Get status of an async document processing task."""
    task_id = request.query_params.get('task_id')

    if not task_id:
        return Response({
            'status': 'error',
            'message': 'task_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        task_result = AsyncResult(task_id)

        response_data = {
            'task_id': task_id,
            'status': task_result.state,
        }

        if task_result.state == 'SUCCESS':
            response_data['result'] = task_result.result
        elif task_result.state == 'FAILURE':
            response_data['error'] = str(task_result.result)

        serializer = TaskStatusSerializer(response_data)

        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception(f"Failed to get task status for {task_id}")
        return Response({
            'status': 'error',
            'message': f'Failed to get task status: {e}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
