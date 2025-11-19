from django.db import models
from django.utils import timezone
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import User


class Moneda(models.Model):
    nombre = models.CharField(max_length=30)
    codigo = models.CharField(max_length=3, unique=True)
    simbolo = models.CharField(max_length=5)

    def __str__(self):
        return self.nombre


# Para crear información automática a la base de datos
@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'ingresos':
        # Crea instancias de Moneda si no existen
        if not Moneda.objects.filter(codigo='USD').exists():
            Moneda.objects.create(codigo='USD', nombre='Dólar Estadounidense', simbolo='$')
        if not Moneda.objects.filter(codigo='EUR').exists():
            Moneda.objects.create(codigo='EUR', nombre='Euro', simbolo='€')
        if not Moneda.objects.filter(codigo='ARS').exists():
            Moneda.objects.create(codigo='ARS', nombre='Peso Argentino', simbolo='$')
        if not Moneda.objects.filter(codigo='CLP').exists():
            Moneda.objects.create(codigo='CLP', nombre='Peso Chileno', simbolo='$')
        # Crea instancias de Categoría si no existen
        categorias = ['Salario',
                      'Regalos',
                      'Inversiones',
                      'Freelance',
                      'Ventas',
                      'Alquiler',
                      'Intereses',
                      'Dividendos']
        for categoria_nombre in categorias:
            if not CategoriaIngreso.objects.filter(nombre=categoria_nombre).exists():
                CategoriaIngreso.objects.create(nombre=categoria_nombre)


class CategoriaIngreso(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.nombre


class Ingreso(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ingresos')
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, null=True, blank=True, related_name='ingresos')
    categoria = models.ForeignKey(CategoriaIngreso, on_delete=models.CASCADE, null=True, blank=True, related_name='ingresos')
    cuenta = models.ForeignKey('cuentas.Cuenta', on_delete=models.SET_NULL, null=True, blank=True, related_name='ingresos')

    def __str__(self):
        return f"{self.descripcion} - {self.monto} {self.moneda.simbolo}"
