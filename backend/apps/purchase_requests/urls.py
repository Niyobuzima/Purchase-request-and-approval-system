"""
URL Configuration for Purchase Request API.

Routes all purchase request endpoints according to the API design specification.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PurchaseRequestViewSet, RequestItemViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'requests', PurchaseRequestViewSet, basename='purchaserequest')
router.register(r'items', RequestItemViewSet, basename='requestitem')

app_name = 'purchase_requests'

urlpatterns = [
    path('', include(router.urls)),
]
