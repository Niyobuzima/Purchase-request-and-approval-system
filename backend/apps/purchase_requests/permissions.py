"""
Custom permissions for purchase request operations.

Implements role-based access control according to the feature guide:
- STAFF: Can create and manage their own requests
- APPROVER_L1/L2: Can view and approve/reject requests at their level
- FINANCE: Can view all approved requests and access POs
- ADMIN: Full access to all operations
"""

from rest_framework import permissions


class IsStaffUser(permissions.BasePermission):
    """
    Permission for STAFF role users.
    Staff can create requests and manage their own requests.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'STAFF'
        )


class IsApprover(permissions.BasePermission):
    """
    Permission for APPROVER_L1 or APPROVER_L2 roles.
    Approvers can view requests at their approval level and approve/reject them.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ['APPROVER_L1', 'APPROVER_L2']
        )


class IsApproverL1(permissions.BasePermission):
    """
    Permission specifically for Level 1 approvers.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'APPROVER_L1' and
            request.user.approval_level == 1
        )


class IsApproverL2(permissions.BasePermission):
    """
    Permission specifically for Level 2 approvers.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'APPROVER_L2' and
            request.user.approval_level == 2
        )


class IsFinance(permissions.BasePermission):
    """
    Permission for FINANCE role users.
    Finance can view all approved requests, access POs, and review receipts.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'FINANCE'
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners to edit their requests.
    Read-only access is allowed for others based on their role.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed based on role
        if request.method in permissions.SAFE_METHODS:
            # Staff can only see their own requests
            if request.user.role == 'STAFF':
                return obj.created_by == request.user

            # Approvers can see pending requests at their level
            if request.user.role in ['APPROVER_L1', 'APPROVER_L2']:
                return True  # Filtered in queryset

            # Finance can see all approved requests
            if request.user.role == 'FINANCE':
                return obj.status in ['APPROVED', 'COMPLETED']

            # Admin can see everything
            if request.user.role == 'ADMIN':
                return True

        # Write permissions only for the owner (and only for DRAFT/PENDING)
        return obj.created_by == request.user and obj.can_be_edited()


class CanApproveRequest(permissions.BasePermission):
    """
    Permission to approve/reject requests.
    Only approvers at the correct level can approve/reject.
    """

    def has_object_permission(self, request, view, obj):
        return obj.can_be_approved_by(request.user)


class CanSubmitRequest(permissions.BasePermission):
    """
    Permission to submit a request for approval.
    Only the owner can submit their DRAFT requests.
    """

    def has_object_permission(self, request, view, obj):
        return (
            obj.created_by == request.user and
            obj.can_be_submitted()
        )


class CanUploadReceipt(permissions.BasePermission):
    """
    Permission to upload receipts.
    Only the owner can upload receipts for APPROVED requests.
    """

    def has_object_permission(self, request, view, obj):
        return (
            obj.created_by == request.user and
            obj.status == 'APPROVED'
        )


class CanAccessPO(permissions.BasePermission):
    """
    Permission to access purchase orders.
    Staff (owner), Finance, and Admin can access POs.
    """

    def has_object_permission(self, request, view, obj):
        return (
            obj.created_by == request.user or
            request.user.role in ['FINANCE', 'ADMIN']
        ) and obj.status in ['APPROVED', 'COMPLETED']
