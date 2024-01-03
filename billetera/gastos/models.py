from django.db import models
from django.utils import timezone  # Importa timezone para configurar la zona horaria.

class Gasto(models.Model):
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)  # Agrega este campo para la fecha de creación.
    moneda = models.CharField(max_length=10, default='pesos')

    def __str__(self):
        return self.descripcion
