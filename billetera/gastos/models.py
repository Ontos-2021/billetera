from django.db import models
from django.utils import timezone  # Importa timezone para configurar la zona horaria.

class Moneda(models.Model):
    nombre = models.CharField(max_length=50)
    codigo = models.CharField(max_length=3)
    simbolo = models.CharField(max_length=5)

    def __str__(self):
        return self.nombre

class Gasto(models.Model):
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)  # Agrega este campo para la fecha de creación.
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, null=True, blank=True, related_name='gastos')

    def __str__(self):
        return self.descripcion
