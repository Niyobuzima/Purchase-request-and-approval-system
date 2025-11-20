"""
Custom exceptions for the application
"""
from rest_framework.exceptions import APIException
from rest_framework import status


class ConcurrentModificationError(APIException):
    """Raised when concurrent modification is detected"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'The resource was modified by another user. Please refresh and try again.'
    default_code = 'concurrent_modification'


class InvalidStateTransitionError(APIException):
    """Raised when an invalid state transition is attempted"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Invalid state transition attempted.'
    default_code = 'invalid_state_transition'


class DocumentProcessingError(APIException):
    """Raised when document processing fails"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Document processing failed. Please try again or contact support.'
    default_code = 'document_processing_error'


class InsufficientPermissionsError(APIException):
    """Raised when user doesn't have required permissions"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'insufficient_permissions'
