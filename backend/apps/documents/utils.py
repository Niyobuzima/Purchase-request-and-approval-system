"""
Utility functions for document processing views.
"""

from uuid import UUID
from rest_framework import status
from rest_framework.response import Response


def validate_uuid_param(param_value, param_name='request_id'):
    """
    Validate that a parameter is a valid UUID.
    
    Args:
        param_value: The value to validate as UUID
        param_name: The name of the parameter (for error messages)
    
    Returns:
        tuple: (validated_uuid, error_response)
            - If valid: (UUID object, None)
            - If invalid: (None, Response object with 400 status)
    """
    if not param_value:
        return None, Response({
            'status': 'error',
            'message': f'{param_name} parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        validated_uuid = UUID(param_value)
        return validated_uuid, None
    except (ValueError, TypeError):
        return None, Response({
            'status': 'error',
            'message': f'Invalid {param_name} format. Must be a valid UUID.'
        }, status=status.HTTP_400_BAD_REQUEST)
