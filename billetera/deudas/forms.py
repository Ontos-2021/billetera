from django import forms
from django.utils import timezone
from .models import Deuda, PagoDeuda
from gastos.models import Moneda

class DeudaForm(forms.ModelForm):
    class Meta:
        model = Deuda
        fields = ['persona', 'tipo', 'monto', 'moneda', 'fecha', 'fecha_vencimiento', 'descripcion']
        widgets = {
            'fecha': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-warning focus:border-warning transition-colors duration-200'
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-warning focus:border-warning transition-colors duration-200'
            }),
            'persona': forms.TextInput(attrs={'placeholder': 'Ej: Juan Pérez'}),
            'tipo': forms.Select(),
            'monto': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'moneda': forms.Select(),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Detalles adicionales sobre la deuda...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial['fecha'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
            # Set default currency to ARS
            try:
                ars = Moneda.objects.get(codigo='ARS')
                self.initial['moneda'] = ars.pk
            except Moneda.DoesNotExist:
                pass

class PagoDeudaForm(forms.ModelForm):
    incluir_en_finanzas = forms.BooleanField(
        required=False,
        initial=False,
        label="Incluir en movimientos financieros",
        help_text="Si se marca, se creará un Gasto o Ingreso correspondiente.",
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-success border-gray-300 rounded focus:ring-success transition-colors duration-200'
        })
    )

    class Meta:
        model = PagoDeuda
        fields = ['monto', 'fecha', 'nota']
        widgets = {
            'fecha': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-200 focus:ring-2 focus:ring-success focus:border-success transition-colors duration-200'
            }),
            'monto': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'nota': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Nota sobre el pago...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.initial['fecha'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
