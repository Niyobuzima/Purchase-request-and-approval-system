"""
URL configuration for Purchase Request & Approval System
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import api_root

# Swagger/OpenAPI documentation schema
schema_view = get_schema_view(
    openapi.Info(
        title="Purchase Request & Approval System API",
        default_version='v1',
        description="API for managing purchase requests and approvals",
        contact=openapi.Contact(email="admin@procure.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[],  # Disable authentication for schema view itself
)

urlpatterns = [
    # Root API endpoint
    path('', api_root, name='api-root'),
    path('api/', api_root, name='api-root-versioned'),

    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # API endpoints
    path('api/auth/', include('apps.accounts.urls')),
    path('api/', include('apps.purchase_requests.urls')),
    path('api/', include('apps.approvals.urls')),
    path('api/', include('apps.documents.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
