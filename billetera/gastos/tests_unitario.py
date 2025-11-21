from django.test import TestCase
from django.contrib.auth.models import User
from .models import Gasto, Moneda, Categoria
from decimal import Decimal

class GastoUnitarioTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        # Moneda 'ARS' is created by migration 0003, so we get it instead of creating it
        self.moneda, _ = Moneda.objects.get_or_create(nombre='Peso Argentino', codigo='ARS', defaults={'simbolo': '$'})
        self.categoria = Categoria.objects.create(nombre='Varios')

    def test_precio_unitario_single_item(self):
        """Test that precio_unitario equals monto when quantity is 1"""
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Single Item',
            monto=Decimal('100.00'),
            cantidad=1,
            moneda=self.moneda,
            categoria=self.categoria
        )
        self.assertEqual(gasto.precio_unitario, Decimal('100.00'))

    def test_precio_unitario_multiple_items(self):
        """Test that precio_unitario is calculated correctly for multiple items"""
        # Total amount 100, quantity 4 -> Unit price should be 25
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Multiple Items',
            monto=Decimal('100.00'),
            cantidad=4,
            moneda=self.moneda,
            categoria=self.categoria
        )
        self.assertEqual(gasto.precio_unitario, Decimal('25.00'))

    def test_precio_unitario_decimal_result(self):
        """Test that precio_unitario handles decimal results correctly"""
        # Total amount 100, quantity 3 -> Unit price should be 33.3333...
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Decimal Items',
            monto=Decimal('100.00'),
            cantidad=3,
            moneda=self.moneda,
            categoria=self.categoria
        )
        # We expect a Decimal result with high precision
        self.assertAlmostEqual(gasto.precio_unitario, Decimal('33.3333333333'), places=2)

    def test_precio_unitario_zero_quantity(self):
        """Test fallback when quantity is 0 (should not happen normally due to min=1)"""
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Zero Quantity',
            monto=Decimal('100.00'),
            cantidad=0,
            moneda=self.moneda,
            categoria=self.categoria
        )
        self.assertEqual(gasto.precio_unitario, Decimal('100.00'))
