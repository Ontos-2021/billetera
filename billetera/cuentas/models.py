from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_migrate
from django.dispatch import receiver

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

@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'cuentas':
        tipos = ['Efectivo', 'Banco', 'Billetera Virtual', 'Crypto']
        for tipo in tipos:
            if not TipoCuenta.objects.filter(nombre=tipo).exists():
                TipoCuenta.objects.create(nombre=tipo)
