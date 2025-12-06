from django.test import TestCase
from django.contrib.auth.models import User
from cuentas.models import Cuenta, TipoCuenta
from gastos.models import Moneda
from gastos.forms import CompraGlobalHeaderForm

class CompraGlobalPrivacyTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        
        # Use get_or_create instead of create to avoid UNIQUE constraint errors
        self.moneda, _ = Moneda.objects.get_or_create(codigo='ARS', defaults={'nombre': 'Peso', 'simbolo': '$'})
        self.tipo = TipoCuenta.objects.create(nombre='Efectivo')
        
        self.cuenta1 = Cuenta.objects.create(usuario=self.user1, nombre='Cuenta 1', tipo=self.tipo, moneda=self.moneda)
        self.cuenta2 = Cuenta.objects.create(usuario=self.user2, nombre='Cuenta 2', tipo=self.tipo, moneda=self.moneda)

    def test_compra_global_form_privacy(self):
        # Form for user1 should only show cuenta1
        form = CompraGlobalHeaderForm(user=self.user1)
        self.assertIn(self.cuenta1, form.fields['cuenta'].queryset)
        self.assertNotIn(self.cuenta2, form.fields['cuenta'].queryset)
        
        # Form for user2 should only show cuenta2
        form = CompraGlobalHeaderForm(user=self.user2)
        self.assertIn(self.cuenta2, form.fields['cuenta'].queryset)
        self.assertNotIn(self.cuenta1, form.fields['cuenta'].queryset)
