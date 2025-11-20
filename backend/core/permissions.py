"""
Custom permission classes for role-based access control
"""
from rest_framework import permissions


class IsStaff(permissions.BasePermission):
    """
    Permission check for Staff role
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'STAFF'


class IsApproverL1(permissions.BasePermission):
    """
    Permission check for Level 1 Approver role
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'APPROVER_L1'


class IsApproverL2(permissions.BasePermission):
    """
    Permission check for Level 2 Approver role
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'APPROVER_L2'


class IsAnyApprover(permissions.BasePermission):
    """
    Permission check for any Approver role (L1 or L2)
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and
                request.user.role in ['APPROVER_L1', 'APPROVER_L2'])


class IsFinance(permissions.BasePermission):
    """
    Permission check for Finance role
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'FINANCE'


class IsAdmin(permissions.BasePermission):
    """
    Permission check for Admin role
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ADMIN'


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it
    """
    def has_object_permission(self, request, view, obj):
        # Check if object has created_by field
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False


class CanApproveRequest(permissions.BasePermission):
    """
    Permission to check if user can approve a specific request
    """
    def has_object_permission(self, request, view, obj):
        # User must be an approver
        if not request.user.role in ['APPROVER_L1', 'APPROVER_L2']:
            return False

        # User's approval level must match request's current level
        if not hasattr(request.user, 'approval_level'):
            return False

        # Request must be in PENDING status
        if obj.status != 'PENDING':
            return False

        return request.user.approval_level == obj.current_approval_level
