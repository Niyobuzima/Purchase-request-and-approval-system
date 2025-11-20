"""
Reusable mixins for views and models
"""
from rest_framework import status
from rest_framework.response import Response


class StandardResponseMixin:
    """
    Mixin to provide standard API response format
    """
    def success_response(self, data=None, message="Operation successful", status_code=status.HTTP_200_OK):
        """Return standardized success response"""
        return Response({
            'status': 'success',
            'data': data,
            'message': message
        }, status=status_code)

    def error_response(self, errors=None, message="Operation failed", status_code=status.HTTP_400_BAD_REQUEST):
        """Return standardized error response"""
        return Response({
            'status': 'error',
            'errors': errors,
            'message': message
        }, status=status_code)


class TimestampMixin:
    """
    Mixin to add created_at and updated_at fields to models
    This is for reference - Django models will use auto_now/auto_now_add
    """
    pass
