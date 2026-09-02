from rest_framework import permissions


class StaffPermission(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        return super(permissions.IsAuthenticated) and request.user.is_staff


class ClientPermission(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        return super(permissions.IsAuthenticated) and not request.user.is_staff


def CustomPermissionFactory(permissions_codename):
    class CustomPermission(permissions.BasePermission):

        def has_permission(self, request, view):
            for permission_codename in permissions_codename:
                if request.user.has_perm(permission_codename):
                    return True
            return False

    return CustomPermission


class ReadOnlyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
