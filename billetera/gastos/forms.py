from django import forms
from django.utils import timezone

from .models import Gasto, Moneda, Tienda
from cuentas.models import Cuenta


class GastoForm(forms.ModelForm):
    tienda_nombre = forms.CharField(
        required=False,
        label='Tienda / Comercio',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ej: Carrefour, Kiosco',
            'list': 'tiendas-list',
            'autocomplete': 'off'
        }),
        help_text='Selecciona una tienda existente o escribe una nueva.'
    )

    class Meta:
        model = Gasto
        fields = ['descripcion', 'tienda_nombre', 'categoria', 'cantidad', 'monto', 'descuento', 'moneda', 'fecha', 'cuenta']
        widgets = {
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej: Compra en supermercado',
                'maxlength': '255'
            }),
            # 'lugar' removed from widgets as it is replaced by tienda_nombre logic
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
            'descuento': forms.NumberInput(attrs={
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
            'monto': 'Precio Unitario',
            'descuento': 'Descuento Total',
            'moneda': 'Moneda',
            'fecha': 'Fecha y Hora',
            'cuenta': 'Cuenta de Origen',
        }
        help_texts = {
            'descripcion': 'Breve descripción de en qué gastaste',
            'monto': 'Ingresa el precio por unidad',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['cuenta'].queryset = Cuenta.objects.filter(usuario=self.user)
        
        if self.instance and self.instance.pk:
            if self.instance.tienda:
                self.fields['tienda_nombre'].initial = self.instance.tienda.nombre
            elif self.instance.lugar:
                self.fields['tienda_nombre'].initial = self.instance.lugar
            
            # If editing, show unit price instead of total amount
            self.initial['monto'] = self.instance.precio_unitario

        if not self.instance.pk:
            self._prefill_moneda_default()

    def _prefill_moneda_default(self):
        if self.fields['moneda'].initial:
            return
        ars = Moneda.objects.filter(codigo='ARS').first()
        if ars:
            self.fields['moneda'].initial = ars.pk

    def save(self, commit=True):
        gasto = super().save(commit=False)
        
        # 1. Handle Tienda logic
        tienda_nombre = self.cleaned_data.get('tienda_nombre')
        
        if tienda_nombre and self.user:
            tienda, created = Tienda.objects.get_or_create(
                nombre__iexact=tienda_nombre,
                usuario=self.user,
                defaults={'nombre': tienda_nombre}
            )
            gasto.tienda = tienda
            gasto.lugar = tienda.nombre  # Keep legacy field in sync
        else:
            gasto.tienda = None
            gasto.lugar = ""

        # 2. Handle Amount Calculation logic
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
