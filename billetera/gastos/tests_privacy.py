from django.test import TestCase
from django.contrib.auth.models import User
from cuentas.models import Cuenta, TipoCuenta
from gastos.models import Moneda
from gastos.forms import GastoForm
from ingresos.forms import IngresoForm

class PrivacyFormTest(TestCase):
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')

        # Create currency and account type
        self.moneda, _ = Moneda.objects.get_or_create(codigo='ARS', defaults={'nombre': 'Peso Argentino', 'simbolo': '$'})
        self.tipo_cuenta = TipoCuenta.objects.create(nombre='Billetera Virtual')

        # Create accounts
        self.cuenta_user1 = Cuenta.objects.create(
            usuario=self.user1,
            nombre='Cuenta User 1',
            tipo=self.tipo_cuenta,
            moneda=self.moneda
        )
        self.cuenta_user2 = Cuenta.objects.create(
            usuario=self.user2,
            nombre='Cuenta User 2',
            tipo=self.tipo_cuenta,
            moneda=self.moneda
        )

    def test_gasto_form_privacy(self):
        # Initialize form with user1
        form = GastoForm(user=self.user1)
        
        # Check that only user1's account is in the queryset
        self.assertIn(self.cuenta_user1, form.fields['cuenta'].queryset)
        self.assertNotIn(self.cuenta_user2, form.fields['cuenta'].queryset)

    def test_ingreso_form_privacy(self):
        # Initialize form with user1
        form = IngresoForm(user=self.user1)
        
        # Check that only user1's account is in the queryset
        self.assertIn(self.cuenta_user1, form.fields['cuenta'].queryset)
        self.assertNotIn(self.cuenta_user2, form.fields['cuenta'].queryset)

    def test_gasto_form_privacy_user2(self):
        # Initialize form with user2
        form = GastoForm(user=self.user2)
        
        # Check that only user2's account is in the queryset
        self.assertIn(self.cuenta_user2, form.fields['cuenta'].queryset)
        self.assertNotIn(self.cuenta_user1, form.fields['cuenta'].queryset)
