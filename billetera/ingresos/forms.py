from django import forms
from .models import Ingreso


class IngresoForm(forms.ModelForm):
    class Meta:
        model = Ingreso
        fields = ['descripcion', 'monto', 'moneda', 'categoria']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción del ingreso'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monto'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
        }
