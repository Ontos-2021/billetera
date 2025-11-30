from decimal import Decimal, ROUND_HALF_UP

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

class AjusteSaldoForm(forms.Form):
    saldo_real = forms.DecimalField(
        max_digits=15, 
        decimal_places=2,
        label='Saldo Real Actual',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg number-input',
            'placeholder': '0.00',
            'step': '0.01'
        }),
        help_text='Ingresa la cantidad exacta de dinero que tienes en esta cuenta.',
    )


class TransferenciaForm(forms.Form):
    cuenta_origen = forms.ModelChoiceField(
        queryset=Cuenta.objects.none(),
        label='Cuenta de Origen',
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    cuenta_destino = forms.ModelChoiceField(
        queryset=Cuenta.objects.none(),
        label='Cuenta de Destino',
        widget=forms.Select(attrs={'class': 'form-select form-select-lg'})
    )
    monto_origen = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label='Monto a transferir',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg number-input',
            'step': '0.01',
            'min': '0'
        })
    )
    tasa_manual = forms.DecimalField(
        max_digits=18,
        decimal_places=6,
        label='Tasa manual',
        initial=Decimal('1.000000'),
        help_text='Indica cuántas unidades de la moneda destino equivale una unidad de la moneda origen (ej: 1 USD = 900 ARS).',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg number-input',
            'step': '0.000001',
            'min': '0'
        })
    )
    monto_destino = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label='Monto recibido',
        required=False,
        help_text='Si lo dejas vacío, calcularemos automáticamente según la tasa manual.',
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg number-input',
            'step': '0.01',
            'min': '0'
        })
    )
    nota = forms.CharField(
        required=False,
        label='Nota',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ej: extracción para efectivo'
        })
    )

    def __init__(self, *args, **kwargs):
        usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        if usuario:
            cuentas_qs = Cuenta.objects.filter(usuario=usuario)
            self.fields['cuenta_origen'].queryset = cuentas_qs
            self.fields['cuenta_destino'].queryset = cuentas_qs

    def clean(self):
        cleaned = super().clean()
        cuenta_origen = cleaned.get('cuenta_origen')
        cuenta_destino = cleaned.get('cuenta_destino')
        monto_origen = cleaned.get('monto_origen')
        tasa = cleaned.get('tasa_manual') or Decimal('1.0')
        monto_destino = cleaned.get('monto_destino')

        if cuenta_origen and cuenta_destino and cuenta_origen == cuenta_destino:
            self.add_error('cuenta_destino', 'Selecciona una cuenta diferente a la de origen.')

        if monto_origen is not None and monto_origen <= 0:
            self.add_error('monto_origen', 'El monto debe ser mayor a cero.')

        if tasa is not None and tasa <= 0:
            self.add_error('tasa_manual', 'La tasa debe ser mayor a cero.')

        if monto_destino is not None and monto_destino <= 0:
            self.add_error('monto_destino', 'El monto recibido debe ser mayor a cero.')

        if not self.errors and monto_destino in (None, Decimal('0')) and monto_origen is not None and tasa is not None:
            cleaned['monto_destino'] = (monto_origen * tasa).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return cleaned
