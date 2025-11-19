from django import forms
from .models import Gasto


class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['descripcion', 'lugar', 'categoria', 'cantidad', 'monto', 'moneda', 'fecha']
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
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg number-input text-center',
                'min': '1',
                'step': '1'
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
            'fecha': forms.DateTimeInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'datetime-local'
            }),
        }
        labels = {
            'descripcion': 'Descripción del gasto',
            'lugar': 'Lugar / Comercio',
            'categoria': 'Categoría',
            'cantidad': 'Cantidad',
            'monto': 'Monto Total',
            'moneda': 'Moneda',
            'fecha': 'Fecha y Hora',
        }
        help_texts = {
            'descripcion': 'Breve descripción de en qué gastaste',
            'lugar': 'Opcional: dónde se realizó la compra',
            'monto': 'Ingresa el monto total sin símbolos de moneda',
        }
