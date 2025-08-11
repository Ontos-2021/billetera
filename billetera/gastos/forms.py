from django import forms
from .models import Gasto


class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['descripcion', 'lugar', 'categoria', 'monto', 'moneda']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej: Compra en supermercado',
                'maxlength': '255'
            }),
            'lugar': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej: Carrefour, Kiosco Don Pepe',
                'maxlength': '120'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg number-input',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'moneda': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
        }
        labels = {
            'descripcion': 'Descripción del gasto',
            'lugar': 'Lugar / Comercio',
            'categoria': 'Categoría',
            'monto': 'Monto',
            'moneda': 'Moneda',
        }
        help_texts = {
            'descripcion': 'Breve descripción de en qué gastaste',
            'lugar': 'Opcional: dónde se realizó la compra',
            'monto': 'Ingresa el monto sin símbolos de moneda',
        }
