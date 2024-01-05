from django.db import models
from django.utils import timezone  # Importa timezone para configurar la zona horaria.
from django.db.models.signals import post_migrate # Para crear información automática en la base de datos
from django.dispatch import receiver

class Moneda(models.Model):
    nombre = models.CharField(max_length=30)
    codigo = models.CharField(max_length=3, unique=True)
    simbolo = models.CharField(max_length=5)

    def __str__(self):
        return self.nombre

# Para crear información automática a la base de datos
@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'gastos':
        # Crea instancias de Moneda si no existen
        if not Moneda.objects.filter(codigo='USD').exists():
            Moneda.objects.create(codigo='USD', nombre='Dólar Estadounidense', simbolo='$')
        if not Moneda.objects.filter(codigo='EUR').exists():
            Moneda.objects.create(codigo='EUR', nombre='Euro', simbolo='€')
        if not Moneda.objects.filter(codigo='ARS').exists():
            Moneda.objects.create(codigo='ARS', nombre='Peso Argentino', simbolo='$')
        if not Moneda.objects.filter(codigo='CLP').exists():
            Moneda.objects.create(codigo='CLP', nombre='Peso Chileno', simbolo='$')
    
class Categoria(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.nombre

class Gasto(models.Model):
    descripcion = models.CharField(max_length=255)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)  # Agrega este campo para la fecha de creación.
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, null=True, blank=True, related_name='gastos')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=True, blank=True, related_name='gastos')

    def __str__(self):
        return self.descripcion
