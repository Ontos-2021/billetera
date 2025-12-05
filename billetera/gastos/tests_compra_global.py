from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Gasto, Categoria, Moneda, Compra
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

    def test_compra_global_creates_compra_object(self):
        """Test: POST válido crea 1 Compra + N Gasto asociados."""
        url = reverse('gastos:compra_global')
        
        data = {
            'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'lugar': 'Supermercado Día',
            'cuenta': self.cuenta.id,
            'moneda': self.moneda.id,
            
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            
            'form-0-descripcion': 'Leche',
            'form-0-categoria': self.categoria.id,
            'form-0-cantidad': '2',
            'form-0-monto': '150.00',
            
            'form-1-descripcion': 'Pan',
            'form-1-categoria': self.categoria.id,
            'form-1-cantidad': '1',
            'form-1-monto': '80.00',
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se creó 1 Compra
        self.assertEqual(Compra.objects.count(), 1)
        compra = Compra.objects.first()
        
        # Verificar que se crearon 2 Gasto asociados
        self.assertEqual(Gasto.objects.count(), 2)
        self.assertEqual(compra.items.count(), 2)

    def test_compra_global_items_share_compra(self):
        """Test: Todos los gastos creados tienen mismo compra_id."""
        url = reverse('gastos:compra_global')
        
        data = {
            'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'lugar': 'Farmacia',
            'cuenta': self.cuenta.id,
            'moneda': self.moneda.id,
            
            'form-TOTAL_FORMS': '3',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            
            'form-0-descripcion': 'Ibuprofeno',
            'form-0-categoria': self.categoria.id,
            'form-0-cantidad': '1',
            'form-0-monto': '500.00',
            
            'form-1-descripcion': 'Vitaminas',
            'form-1-categoria': self.categoria.id,
            'form-1-cantidad': '1',
            'form-1-monto': '800.00',
            
            'form-2-descripcion': 'Curitas',
            'form-2-categoria': self.categoria.id,
            'form-2-cantidad': '2',
            'form-2-monto': '200.00',
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        gastos = Gasto.objects.all()
        compra_ids = set(g.compra_id for g in gastos)
        
        # Todos deben tener el mismo compra_id
        self.assertEqual(len(compra_ids), 1)
        self.assertIsNotNone(list(compra_ids)[0])

    def test_compra_global_compra_has_correct_metadata(self):
        """Test: La Compra tiene lugar, fecha, cuenta, moneda del header."""
        url = reverse('gastos:compra_global')
        fecha_str = '2025-12-05T14:30'
        
        data = {
            'fecha': fecha_str,
            'lugar': 'Tienda Especial',
            'cuenta': self.cuenta.id,
            'moneda': self.moneda.id,
            
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            
            'form-0-descripcion': 'Producto',
            'form-0-categoria': self.categoria.id,
            'form-0-cantidad': '1',
            'form-0-monto': '100.00',
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        compra = Compra.objects.first()
        self.assertEqual(compra.lugar, 'Tienda Especial')
        self.assertEqual(compra.cuenta, self.cuenta)
        self.assertEqual(compra.moneda, self.moneda)
        self.assertEqual(compra.usuario, self.usuario)

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
        
        # Verificar que ambos pertenecen a la misma compra
        self.assertEqual(zapatos.compra, medias.compra)
        self.assertIsNotNone(zapatos.compra)
