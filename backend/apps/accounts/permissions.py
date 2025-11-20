from rest_framework import permissions


class IsStaff(permissions.BasePermission):
    """
    Permission class for regular staff members.
    Allows users with STAFF role.
    """

    message = 'You must be a staff member to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'STAFF'
        )


class IsApproverL1(permissions.BasePermission):
    """
    Permission class for Level 1 Approvers.
    Allows users with APPROVER_L1 role.
    """

    message = 'You must be a Level 1 Approver to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'APPROVER_L1'
        )


class IsApproverL2(permissions.BasePermission):
    """
    Permission class for Level 2 Approvers.
    Allows users with APPROVER_L2 role.
    """

    message = 'You must be a Level 2 Approver to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'APPROVER_L2'
        )


class IsApprover(permissions.BasePermission):
    """
    Permission class for any Approver (L1 or L2).
    Allows users with APPROVER_L1 or APPROVER_L2 role.
    """

    message = 'You must be an Approver to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ['APPROVER_L1', 'APPROVER_L2']
        )


class IsFinance(permissions.BasePermission):
    """
    Permission class for Finance team members.
    Allows users with FINANCE role.
    """

    message = 'You must be a Finance team member to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'FINANCE'
        )


class IsAdmin(permissions.BasePermission):
    """
    Permission class for System Administrators.
    Allows users with ADMIN role.
    """

    message = 'You must be an Administrator to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'ADMIN'
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows owners to edit objects.
    Read-only for everyone else.
    """

    message = 'You can only edit your own objects.'

    def has_object_permission(self, request, view, obj):
        # Read permissions for safe methods
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only to owner
        # Assumes the object has a 'created_by' or 'user' field
        return obj.created_by == request.user if hasattr(obj, 'created_by') else obj.user == request.user


class CanApproveAtLevel(permissions.BasePermission):
    """
    Permission class that checks if user can approve at a specific level.
    The level should be passed via view context.
    """

    message = 'You do not have permission to approve at this level.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Get the required approval level from view
        required_level = getattr(view, 'approval_level', None)

        if required_level is None:
            return False

        return request.user.can_approve_at_level(required_level)


class IsStaffOrApprover(permissions.BasePermission):
    """
    Permission class for Staff or Approvers.
    Useful for views that should be accessible to both roles.
    """

    message = 'You must be a Staff member or Approver to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ['STAFF', 'APPROVER_L1', 'APPROVER_L2']
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows admins full access.
    Read-only for everyone else.
    """

    message = 'Only administrators can modify this resource.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Read permissions for safe methods
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for admins
        return request.user.role == 'ADMIN'
