from django.db import models
from django.contrib.auth.models import User  # Importar el modelo de usuario
from django.utils import timezone  # Importar timezone


class Moneda(models.Model):
    nombre = models.CharField(max_length=30)
    codigo = models.CharField(max_length=3, unique=True)
    simbolo = models.CharField(max_length=5)

    def __str__(self):
        return self.nombre


# Initial data logic moved to gastos/signals.py to ensure it runs after migrations


class Categoria(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.nombre


class Gasto(models.Model):
    usuario = models.ForeignKey(User,
                                on_delete=models.CASCADE,
                                related_name='gastos',  # Relación con usuario
                                null=True,
                                blank=True)
    descripcion = models.CharField(max_length=255)
    lugar = models.CharField(max_length=120, null=True, blank=True, help_text='Lugar o comercio donde se realizó la compra (ej: Carrefour, Kiosco, etc.)')
    cantidad = models.PositiveIntegerField(default=1)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, null=True, blank=True, related_name='gastos')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=True, blank=True, related_name='gastos')
    cuenta = models.ForeignKey('cuentas.Cuenta', on_delete=models.SET_NULL, null=True, blank=True, related_name='gastos')

    def __str__(self):
        if self.moneda:
            return f"{self.descripcion} ({self.cantidad}) - {self.monto} {self.moneda.simbolo}"
        else:
            return f"{self.descripcion} ({self.cantidad}) - {self.monto}"
