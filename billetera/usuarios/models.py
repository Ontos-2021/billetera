from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def perfil_imagen_upload_path(instance, filename):
    user_id = instance.usuario_id or 'anonymous'
    return f"imagenes_perfil/user_{user_id}/{filename}"


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    # Datos de identidad y estadísticos
    fecha_nacimiento = models.DateField(null=True, blank=True)
    pais = models.CharField(max_length=100, null=True, blank=True)
    ciudad = models.CharField(max_length=100, null=True, blank=True)
    
    # Campos legacy (se pueden mantener opcionales o eliminar en el futuro)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    imagen_perfil = models.ImageField(upload_to=perfil_imagen_upload_path, null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


class Plan(models.Model):
    FREE = 'FREE'
    PRO = 'PRO'
    PREMIUM = 'PREMIUM'
    
    PLAN_CHOICES = [
        (FREE, 'Gratuito'),
        (PRO, 'Pro'),
        (PREMIUM, 'Premium'),
    ]
    
    nombre = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    descripcion = models.TextField(blank=True)
    
    def __str__(self):
        return self.get_nombre_display()


class Suscripcion(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='suscripcion')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    external_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID de suscripción en Mercado Pago")

    def __str__(self):
        return f"{self.usuario.username} - {self.plan}"

    @property
    def es_valida(self):
        if not self.activo:
            return False
        if self.fecha_fin and self.fecha_fin < timezone.now():
            return False
        return True
