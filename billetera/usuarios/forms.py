from django import forms
from .models import PerfilUsuario


class PerfilUsuarioForm(forms.ModelForm):
    # Campo extra para editar el nombre del usuario (User.first_name)
    nombre_pila = forms.CharField(
        max_length=30, 
        required=False, 
        label="Nombre / Apodo",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre o apodo'})
    )

    class Meta:
        model = PerfilUsuario
        fields = ['imagen_perfil', 'fecha_nacimiento', 'pais', 'ciudad', 'direccion', 'telefono']
        widgets = {
            'imagen_perfil': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'pais': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Argentina'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Buenos Aires'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Calle Falsa 123'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+54 9 11 1234 5678'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializar el campo nombre_pila con el valor actual del usuario
        if self.instance and self.instance.usuario:
            self.fields['nombre_pila'].initial = self.instance.usuario.first_name

    def save(self, commit=True):
        perfil = super().save(commit=False)
        # Guardar el nombre_pila en el modelo User
        if commit:
            user = perfil.usuario
            user.first_name = self.cleaned_data['nombre_pila']
            user.save()
            perfil.save()
        return perfil
