from django import forms
from .models import Ingreso


class IngresoForm(forms.ModelForm):
    class Meta:
        model = Ingreso
        fields = ['descripcion', 'monto', 'moneda', 'categoria', 'fecha']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej: Salario mensual',
                'maxlength': '255'
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
            'categoria': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'fecha': forms.DateTimeInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'datetime-local'
            }),
        }
        labels = {
            'descripcion': 'Descripción del ingreso',
            'monto': 'Monto',
            'moneda': 'Moneda',
            'categoria': 'Categoría',
            'fecha': 'Fecha y Hora',
        }
        help_texts = {
            'descripcion': 'Breve descripción de tu fuente de ingreso',
            'monto': 'Ingresa el monto sin símbolos de moneda',
        }
