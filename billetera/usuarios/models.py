from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    imagen_perfil = models.ImageField(upload_to='imagenes_perfil/', null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"
