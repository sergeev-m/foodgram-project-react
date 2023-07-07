from rest_framework import permissions


class IsAuthenticatedOrOwnerOrReadOnly(permissions.BasePermission):
    """ + для автора, админа или только чтение. """

    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return bool(
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )