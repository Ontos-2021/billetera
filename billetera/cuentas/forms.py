from django import forms
from .models import Cuenta

class CuentaForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = ['nombre', 'tipo', 'moneda', 'saldo_inicial']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej: Banco Galicia, MercadoPago',
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'moneda': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'saldo_inicial': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg number-input',
                'placeholder': '0.00',
                'step': '0.01',
            }),
        }
        labels = {
            'nombre': 'Nombre de la Cuenta',
            'tipo': 'Tipo de Cuenta',
            'moneda': 'Moneda',
            'saldo_inicial': 'Saldo Inicial',
        }
