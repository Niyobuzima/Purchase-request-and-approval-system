"""
URL Configuration for Approval Workflow API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApprovalLogViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'approval-logs', ApprovalLogViewSet, basename='approvallog')

app_name = 'approvals'

urlpatterns = [
    path('', include(router.urls)),
]
