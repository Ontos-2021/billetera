from django import forms
from django.utils import timezone

from .models import Gasto, Moneda
from cuentas.models import Cuenta


class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['descripcion', 'lugar', 'categoria', 'cantidad', 'monto', 'moneda', 'fecha', 'cuenta']
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
            'cuenta': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
        }
        labels = {
            'descripcion': 'Descripción del gasto',
            'lugar': 'Lugar / Comercio',
            'categoria': 'Categoría',
            'cantidad': 'Cantidad',
            'monto': 'Precio Unitario',
            'moneda': 'Moneda',
            'fecha': 'Fecha y Hora',
            'cuenta': 'Cuenta de Origen',
        }
        help_texts = {
            'descripcion': 'Breve descripción de en qué gastaste',
            'lugar': 'Opcional: dónde se realizó la compra',
            'monto': 'Ingresa el precio por unidad',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['cuenta'].queryset = Cuenta.objects.filter(usuario=user)
        
        if not self.instance.pk:
            self._prefill_moneda_default()
        if self.instance and self.instance.pk:
            # If editing, show unit price instead of total amount
            self.initial['monto'] = self.instance.precio_unitario

    def _prefill_moneda_default(self):
        if self.fields['moneda'].initial:
            return
        ars = Moneda.objects.filter(codigo='ARS').first()
        if ars:
            self.fields['moneda'].initial = ars.pk

    def save(self, commit=True):
        gasto = super().save(commit=False)
        # Calculate total amount: Unit Price * Quantity
        # self.cleaned_data['monto'] contains the unit price input by user
        unit_price = self.cleaned_data.get('monto')
        quantity = self.cleaned_data.get('cantidad', 1)
        
        if unit_price is not None:
            gasto.monto = unit_price * quantity
            
        if commit:
            gasto.save()
        return gasto


class CompraGlobalHeaderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('fecha'):
            self.initial['fecha'] = timezone.localtime(timezone.now()).strftime('%Y-%m-%dT%H:%M')
        if not self.initial.get('moneda'):
            ars = Moneda.objects.filter(codigo='ARS').first()
            if ars:
                self.fields['moneda'].initial = ars.pk

    class Meta:
        model = Gasto
        fields = ['fecha', 'lugar', 'cuenta', 'moneda']
        widgets = {
            'fecha': forms.DateTimeInput(attrs={
                'class': 'form-control form-control-lg',
                'type': 'datetime-local'
            }),
            'lugar': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej: Supermercado, Shopping',
                'maxlength': '120'
            }),
            'cuenta': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
            'moneda': forms.Select(attrs={
                'class': 'form-select form-select-lg'
            }),
        }
        labels = {
            'fecha': 'Fecha y Hora',
            'lugar': 'Lugar / Comercio',
            'cuenta': 'Cuenta / Medio de Pago',
            'moneda': 'Moneda',
        }


class CompraGlobalItemForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = ['descripcion', 'categoria', 'cantidad', 'monto']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Producto/Servicio'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control text-center',
                'min': '1',
                'value': '1'
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control text-right',
                'placeholder': '0.00',
                'min': '0',
                'step': '0.01'
            }),
        }
