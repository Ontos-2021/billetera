"""
Tests para el modelo Compra y su relación con Gasto.
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from gastos.models import Compra, Gasto, Moneda, Categoria
from cuentas.models import Cuenta, TipoCuenta


class CompraModelTest(TestCase):
    """Tests para el modelo Compra."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.moneda, _ = Moneda.objects.get_or_create(
            codigo='ARS',
            defaults={'nombre': 'Peso Argentino', 'simbolo': '$'}
        )
        self.categoria, _ = Categoria.objects.get_or_create(nombre='Alimentación')
        self.categoria2, _ = Categoria.objects.get_or_create(nombre='Limpieza')
        
        self.tipo_cuenta, _ = TipoCuenta.objects.get_or_create(nombre='Efectivo')
        self.cuenta = Cuenta.objects.create(
            usuario=self.user,
            nombre='Billetera',
            tipo=self.tipo_cuenta,
            moneda=self.moneda,
            saldo_inicial=Decimal('1000.00')
        )
    
    def test_compra_creation(self):
        """Test: Crear una compra con campos requeridos."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Supermercado Día',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        
        self.assertEqual(compra.usuario, self.user)
        self.assertEqual(compra.lugar, 'Supermercado Día')
        self.assertEqual(compra.cuenta, self.cuenta)
        self.assertEqual(compra.moneda, self.moneda)
        self.assertIsNotNone(compra.created_at)
    
    def test_compra_str_representation(self):
        """Test: Representación string de una compra."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Carrefour',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        
        self.assertIn('Carrefour', str(compra))
        self.assertIn('0 items', str(compra))
    
    def test_compra_total_property_with_items(self):
        """Test: La propiedad total retorna la suma de los gastos asociados."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Supermercado',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        
        # Crear 3 gastos asociados a la compra
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Leche',
            monto=Decimal('150.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Pan',
            monto=Decimal('80.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Detergente',
            monto=Decimal('320.00'),
            categoria=self.categoria2,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        
        self.assertEqual(compra.total, Decimal('550.00'))
    
    def test_compra_total_empty(self):
        """Test: Compra sin ítems retorna total 0."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Tienda Vacía',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        
        self.assertEqual(compra.total, 0)
    
    def test_compra_items_count(self):
        """Test: La propiedad items_count retorna cantidad correcta."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Supermercado',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        
        # Sin ítems
        self.assertEqual(compra.items_count, 0)
        
        # Agregar ítems
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Item 1',
            monto=Decimal('100.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Item 2',
            monto=Decimal('200.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        
        self.assertEqual(compra.items_count, 2)
    
    def test_gasto_compra_nullable(self):
        """Test: Un gasto puede existir sin compra asociada (backwards compatible)."""
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Gasto individual',
            monto=Decimal('500.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=None  # Sin compra
        )
        
        self.assertIsNone(gasto.compra)
        self.assertEqual(gasto.descripcion, 'Gasto individual')
    
    def test_compra_ordering(self):
        """Test: Las compras se ordenan por fecha descendente."""
        fecha_antigua = timezone.now() - timezone.timedelta(days=5)
        fecha_reciente = timezone.now()
        
        compra_antigua = Compra.objects.create(
            usuario=self.user,
            fecha=fecha_antigua,
            lugar='Compra Antigua',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        compra_reciente = Compra.objects.create(
            usuario=self.user,
            fecha=fecha_reciente,
            lugar='Compra Reciente',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        
        compras = list(Compra.objects.all())
        self.assertEqual(compras[0], compra_reciente)
        self.assertEqual(compras[1], compra_antigua)
    
    def test_compra_cascade_delete_removes_gastos(self):
        """Test: Eliminar una compra elimina sus gastos asociados."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Supermercado',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Item a eliminar',
            monto=Decimal('100.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        
        self.assertEqual(Gasto.objects.filter(compra=compra).count(), 1)
        
        compra.delete()
        
        # Los gastos asociados deben ser eliminados (CASCADE)
        self.assertEqual(Gasto.objects.filter(descripcion='Item a eliminar').count(), 0)
