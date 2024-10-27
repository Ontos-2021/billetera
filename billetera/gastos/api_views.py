from rest_framework import viewsets, permissions
from .serializers import GastoSerializer
from .permissions import IsAdminOrReadOwnOnly, IsOwnerOrReadOnly
from .models import Gasto


# API REST para gestionar los gastos
class GastoViewSet(viewsets.ModelViewSet):
    queryset = Gasto.objects.all()  # Define el conjunto de datos inicial para la vista
    serializer_class = GastoSerializer  # Define el serializador a utilizar
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOwnOnly, IsOwnerOrReadOnly]  # Define los permisos para la vista

    def get_queryset(self):
        # Los superusuarios pueden ver todos los gastos
        if self.request.user.is_superuser:
            return Gasto.objects.all()

        # Filtrar gastos por usuario para usuarios normales
        queryset = Gasto.objects.filter(usuario=self.request.user)

        # Filtrar por fecha si se proporciona en los parámetros de la solicitud
        fecha = self.request.query_params.get('fecha', None)
        if fecha:
            queryset = queryset.filter(fecha=fecha)

        # Filtrar por categoría si se proporciona en los parámetros de la solicitud
        categoria = self.request.query_params.get('categoria', None)
        if categoria:
            queryset = queryset.filter(categoria=categoria)

        return queryset

    def perform_create(self, serializer):
        # Asocia automáticamente el usuario autenticado al crear un nuevo gasto
        serializer.save(usuario=self.request.user)
