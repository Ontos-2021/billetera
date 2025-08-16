from rest_framework import serializers
from .models import Ingreso


class IngresoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingreso
        fields = ['id', 'descripcion', 'monto', 'fecha', 'moneda', 'categoria', 'usuario']
