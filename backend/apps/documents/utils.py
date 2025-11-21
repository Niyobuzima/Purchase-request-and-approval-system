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
    except (ValueError, TypeError):
        return None, Response({
            'status': 'error',
            'message': f'Invalid {param_name} format. Must be a valid UUID.'
        }, status=status.HTTP_400_BAD_REQUEST)
    else:
        return validated_uuid, None


def check_purchase_request_access(user, purchase_request, action='access'):
    """
    Check if user has access to a purchase request.
    STAFF can only access their own requests.
    Other roles (FINANCE, ADMIN) can access any request.
    
    Args:
        user: The user attempting to access the request
        purchase_request: The PurchaseRequest instance
        action: The action being performed (for error message customization)
    
    Returns:
        Response object with 403 status if access denied, None otherwise.
    """
    if user.role == 'STAFF' and purchase_request.created_by != user:
        return Response({
            'status': 'error',
            'message': f'You do not have permission to {action} this request'
        }, status=status.HTTP_403_FORBIDDEN)
    return None
