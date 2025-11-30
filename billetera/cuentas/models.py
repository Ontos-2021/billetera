from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone

class TipoCuenta(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class Cuenta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cuentas')
    nombre = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoCuenta, on_delete=models.SET_NULL, null=True)
    saldo_inicial = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    moneda = models.ForeignKey('gastos.Moneda', on_delete=models.PROTECT)
    
    def __str__(self):
        # Use a safe access to moneda.codigo in case it's not loaded yet or something
        return f"{self.nombre}"


class TransferenciaCuenta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transferencias_cuentas')
    cuenta_origen = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name='transferencias_salientes')
    cuenta_destino = models.ForeignKey(Cuenta, on_delete=models.PROTECT, related_name='transferencias_entrantes')
    monto_origen = models.DecimalField(max_digits=15, decimal_places=2)
    monto_destino = models.DecimalField(max_digits=15, decimal_places=2)
    tasa_manual = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal('1.000000'))
    nota = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(default=timezone.now)
    gasto = models.ForeignKey('gastos.Gasto', on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_generadas')
    ingreso = models.ForeignKey('ingresos.Ingreso', on_delete=models.SET_NULL, null=True, blank=True, related_name='transferencias_generadas')

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Transferencia {self.cuenta_origen} → {self.cuenta_destino} ({self.fecha:%Y-%m-%d})"

@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'cuentas':
        tipos = ['Efectivo', 'Banco', 'Billetera Virtual', 'Crypto']
        for tipo in tipos:
            if not TipoCuenta.objects.filter(nombre=tipo).exists():
                TipoCuenta.objects.create(nombre=tipo)
