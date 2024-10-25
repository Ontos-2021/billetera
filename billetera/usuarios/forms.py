from django import forms
from .models import PerfilUsuario


class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['direccion', 'telefono', 'imagen_perfil']
