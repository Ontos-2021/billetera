from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Gasto, Categoria, Moneda
from cuentas.models import Cuenta, TipoCuenta
from decimal import Decimal
from django.utils import timezone

class CompraGlobalTestCase(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        
        self.moneda, _ = Moneda.objects.get_or_create(codigo='ARS', defaults={'nombre': 'Peso', 'simbolo': '$'})
        self.categoria, _ = Categoria.objects.get_or_create(nombre='Comida')
        self.tipo_cuenta, _ = TipoCuenta.objects.get_or_create(nombre='Efectivo')
        self.cuenta = Cuenta.objects.create(
            usuario=self.usuario,
            nombre='Billetera',
            tipo=self.tipo_cuenta,
            moneda=self.moneda,
            saldo_inicial=10000
        )

    def test_compra_global_calculates_total_correctly(self):
        """Test that the total amount is calculated as unit_price * quantity"""
        url = reverse('gastos:compra_global')
        
        data = {
            # Header fields
            'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'lugar': 'Supermercado Test',
            'cuenta': self.cuenta.id,
            'moneda': self.moneda.id,
            
            # Management form
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            
            # Item 0
            'form-0-descripcion': 'Item 1',
            'form-0-categoria': self.categoria.id,
            'form-0-cantidad': '2',
            'form-0-monto': '1000.00', # Unit price
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 302)
        
        gasto = Gasto.objects.first()
        self.assertIsNotNone(gasto)
        self.assertEqual(gasto.descripcion, 'Item 1')
        self.assertEqual(gasto.cantidad, 2)
        self.assertEqual(gasto.monto, Decimal('2000.00'))

    def test_compra_global_multiple_items(self):
        """Test creating multiple items in one global purchase"""
        url = reverse('gastos:compra_global')
        
        data = {
            'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'lugar': 'Shopping',
            'cuenta': self.cuenta.id,
            'moneda': self.moneda.id,
            
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            
            # Item 0
            'form-0-descripcion': 'Zapatos',
            'form-0-categoria': self.categoria.id,
            'form-0-cantidad': '1',
            'form-0-monto': '5000.00',
            
            # Item 1
            'form-1-descripcion': 'Medias',
            'form-1-categoria': self.categoria.id,
            'form-1-cantidad': '3',
            'form-1-monto': '500.00',
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        self.assertEqual(Gasto.objects.count(), 2)
        
        zapatos = Gasto.objects.get(descripcion='Zapatos')
        self.assertEqual(zapatos.monto, Decimal('5000.00'))
        self.assertEqual(zapatos.cantidad, 1)
        
        medias = Gasto.objects.get(descripcion='Medias')
        self.assertEqual(medias.monto, Decimal('1500.00')) # 3 * 500
        self.assertEqual(medias.cantidad, 3)
