from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_delete
from django.dispatch import receiver
from gastos.models import Moneda

class Deuda(models.Model):
    TIPO_CHOICES = [
        ('POR_COBRAR', 'Por Cobrar'),
        ('POR_PAGAR', 'Por Pagar'),
    ]
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADA', 'Pagada'),
    ]

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deudas')
    persona = models.CharField(max_length=100, help_text="Nombre de la persona externa")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    moneda = models.ForeignKey(Moneda, on_delete=models.PROTECT)
    fecha = models.DateTimeField(default=timezone.now)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    descripcion = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.persona} - {self.monto} {self.moneda.codigo}"

    def saldo_pendiente(self):
        pagado = self.pagos.aggregate(total=models.Sum('monto'))['total'] or 0
        return self.monto - pagado

    def actualizar_estado(self):
        saldo = self.saldo_pendiente()
        if saldo <= 0:
            self.estado = 'PAGADA'
        else:
            self.estado = 'PENDIENTE'
        # Evitar recursión infinita si se llama desde save()
        super(Deuda, self).save(update_fields=['estado'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar estado después de guardar por si cambió el monto
        self.actualizar_estado()

class PagoDeuda(models.Model):
    deuda = models.ForeignKey(Deuda, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(default=timezone.now)
    nota = models.TextField(blank=True)
    gasto_relacionado = models.OneToOneField('gastos.Gasto', on_delete=models.SET_NULL, null=True, blank=True, related_name='pago_deuda')
    ingreso_relacionado = models.OneToOneField('ingresos.Ingreso', on_delete=models.SET_NULL, null=True, blank=True, related_name='pago_deuda')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago de {self.monto} a {self.deuda}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.deuda.actualizar_estado()

@receiver(post_delete, sender=PagoDeuda)
def actualizar_deuda_post_delete(sender, instance, **kwargs):
    instance.deuda.actualizar_estado()
