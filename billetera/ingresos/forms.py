from django import forms

from .models import Ingreso, Moneda
from cuentas.models import Cuenta


class IngresoForm(forms.ModelForm):
    class Meta:
        model = Ingreso
        fields = ['descripcion', 'monto', 'moneda', 'categoria', 'fecha', 'cuenta']
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
            'cuenta': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
        }
        labels = {
            'descripcion': 'Descripción del ingreso',
            'monto': 'Monto',
            'moneda': 'Moneda',
            'categoria': 'Categoría',
            'fecha': 'Fecha y Hora',
            'cuenta': 'Cuenta de Destino',
        }
        help_texts = {
            'descripcion': 'Breve descripción de tu fuente de ingreso',
            'monto': 'Ingresa el monto sin símbolos de moneda',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['cuenta'].queryset = Cuenta.objects.filter(usuario=self.user)

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is not None and monto < 0:
            raise forms.ValidationError("El monto no puede ser negativo.")
        return monto

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['cuenta'].queryset = Cuenta.objects.filter(usuario=user)

        if not self.instance.pk and not self.initial.get('moneda'):
            ars = Moneda.objects.filter(codigo='ARS').first()
            if ars:
                self.fields['moneda'].initial = ars.pk
