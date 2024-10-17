from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Leer permisos está permitido para cualquier solicitud
        if request.method in permissions.SAFE_METHODS:
            return True

        # Los permisos de escritura solo se permiten al dueño del objeto.
        return obj.usuario == request.user
