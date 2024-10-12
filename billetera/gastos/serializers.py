from rest_framework import serializers
from .models import Gasto


class GastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gasto
        fields = ['id', 'descripcion', 'monto', 'fecha', 'moneda', 'categoria', 'usuario']
