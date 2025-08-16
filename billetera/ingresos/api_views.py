from rest_framework import viewsets, permissions
from .serializers import IngresoSerializer
from .models import Ingreso


class IngresoViewSet(viewsets.ModelViewSet):
    queryset = Ingreso.objects.all()
    serializer_class = IngresoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Ingreso.objects.all()
        queryset = Ingreso.objects.filter(usuario=self.request.user)
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
