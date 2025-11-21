from django.test import TestCase
from django.contrib.auth.models import User
from .models import Gasto, Moneda, Categoria
from .forms import GastoForm
from decimal import Decimal

class GastoFormUnitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.moneda, _ = Moneda.objects.get_or_create(nombre='Peso Argentino', codigo='ARS', defaults={'simbolo': '$'})
        self.categoria = Categoria.objects.create(nombre='Varios')

    def test_form_calculates_total_amount(self):
        """Test that the form calculates total amount = unit price * quantity"""
        form_data = {
            'descripcion': 'Test Item',
            'cantidad': 4,
            'monto': 1000,  # Unit Price
            'moneda': self.moneda.id,
            'categoria': self.categoria.id,
            'fecha': '2025-11-21 12:00:00',
            'lugar': 'Test Place'
        }
        form = GastoForm(data=form_data)
        self.assertTrue(form.is_valid())
        gasto = form.save(commit=False)
        gasto.usuario = self.user
        gasto.save()
        
        # Check that saved amount is 4000 (4 * 1000)
        self.assertEqual(gasto.monto, Decimal('4000.00'))
        self.assertEqual(gasto.cantidad, 4)
        # Check unit price property
        self.assertEqual(gasto.precio_unitario, Decimal('1000.00'))

    def test_form_initial_value_is_unit_price(self):
        """Test that when editing, the form shows unit price, not total"""
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Existing Item',
            monto=Decimal('4000.00'), # Total
            cantidad=4,
            moneda=self.moneda,
            categoria=self.categoria
        )
        
        form = GastoForm(instance=gasto)
        # The initial value for 'monto' field should be 1000 (4000/4)
        self.assertEqual(form.initial['monto'], Decimal('1000.00'))
