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


class IsAdminOrReadOwnOnly(permissions.BasePermission):
    """
    Permiso personalizado que permite a los administradores ver todo
    y a los usuarios normales ver solo sus propios datos.
    """

    def has_object_permission(self, request, view, obj):
        # Permitir a los administradores acceso completo
        if request.user.is_superuser:
            return True

        # Permitir solo a los dueños del objeto leer y modificar sus propios datos
        return obj.usuario == request.user

