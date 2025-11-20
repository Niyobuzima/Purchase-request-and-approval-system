"""
Root views for the API
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    API Root - Welcome endpoint with links to all available APIs.
    """
    return Response({
        'message': 'Welcome to Purchase Request & Approval System API',
        'version': 'v1',
        'endpoints': {
            'authentication': {
                'register': reverse('accounts:register', request=request, format=format),
                'login': reverse('accounts:login', request=request, format=format),
                'token_refresh': reverse('accounts:token_refresh', request=request, format=format),
                'profile': reverse('accounts:profile', request=request, format=format),
            },
            'documentation': {
                'swagger': request.build_absolute_uri('/api/docs/'),
                'redoc': request.build_absolute_uri('/api/redoc/'),
                'openapi_schema': request.build_absolute_uri('/api/schema/'),
            },
            'admin': request.build_absolute_uri('/admin/'),
        },
        'status': 'operational',
    })
