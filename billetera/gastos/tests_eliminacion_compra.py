"""
Tests para eliminación de ítems de compra y eliminación del último ítem.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from gastos.models import Compra, Gasto, Moneda, Categoria
from cuentas.models import Cuenta, TipoCuenta


class EliminarItemCompraTest(TestCase):
    """Tests para la eliminación de ítems de una compra."""
    
    def setUp(self):
        """Configuración inicial."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        self.moneda, _ = Moneda.objects.get_or_create(
            codigo='ARS',
            defaults={'nombre': 'Peso Argentino', 'simbolo': '$'}
        )
        self.categoria, _ = Categoria.objects.get_or_create(nombre='Alimentación')
        self.tipo_cuenta, _ = TipoCuenta.objects.get_or_create(nombre='Efectivo')
        self.cuenta = Cuenta.objects.create(
            usuario=self.user,
            nombre='Billetera',
            tipo=self.tipo_cuenta,
            moneda=self.moneda,
            saldo_inicial=Decimal('1000.00')
        )
    
    def test_eliminar_item_de_compra(self):
        """Test: Eliminar 1 gasto de compra con 3 ítems: compra sigue existiendo con 2."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Supermercado',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        gasto1 = Gasto.objects.create(
            usuario=self.user,
            descripcion='Item 1',
            monto=Decimal('100.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        gasto2 = Gasto.objects.create(
            usuario=self.user,
            descripcion='Item 2',
            monto=Decimal('200.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        gasto3 = Gasto.objects.create(
            usuario=self.user,
            descripcion='Item 3',
            monto=Decimal('300.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        
        # Verificar estado inicial
        self.assertEqual(compra.items.count(), 3)
        self.assertEqual(Compra.objects.count(), 1)
        
        # Eliminar el primer ítem
        url = reverse('gastos:eliminar_gasto', args=[gasto1.id])
        response = self.client.post(url)
        
        # Verificar redirect
        self.assertEqual(response.status_code, 302)
        
        # Verificar que la compra sigue existiendo con 2 ítems
        compra.refresh_from_db()
        self.assertEqual(Compra.objects.count(), 1)
        self.assertEqual(compra.items.count(), 2)
        
        # Verificar que el gasto fue eliminado
        self.assertFalse(Gasto.objects.filter(id=gasto1.id).exists())
        
        # Verificar que los otros gastos siguen
        self.assertTrue(Gasto.objects.filter(id=gasto2.id).exists())
        self.assertTrue(Gasto.objects.filter(id=gasto3.id).exists())
    
    def test_eliminar_ultimo_item_elimina_compra(self):
        """Test: Eliminar único ítem restante también elimina la Compra."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Tienda',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Único Item',
            monto=Decimal('500.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        
        compra_id = compra.id
        
        # Verificar estado inicial
        self.assertEqual(Compra.objects.count(), 1)
        self.assertEqual(compra.items.count(), 1)
        
        # Eliminar el único ítem
        url = reverse('gastos:eliminar_gasto', args=[gasto.id])
        response = self.client.post(url)
        
        # Verificar redirect
        self.assertEqual(response.status_code, 302)
        
        # Verificar que tanto el gasto como la compra fueron eliminados
        self.assertFalse(Gasto.objects.filter(id=gasto.id).exists())
        self.assertFalse(Compra.objects.filter(id=compra_id).exists())
    
    def test_eliminar_gasto_sin_compra(self):
        """Test: Eliminar gasto individual (sin compra) funciona normal."""
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Gasto Individual',
            monto=Decimal('250.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=None  # Sin compra
        )
        
        gasto_id = gasto.id
        
        # Eliminar
        url = reverse('gastos:eliminar_gasto', args=[gasto.id])
        response = self.client.post(url)
        
        # Verificar redirect
        self.assertEqual(response.status_code, 302)
        
        # Verificar que fue eliminado
        self.assertFalse(Gasto.objects.filter(id=gasto_id).exists())
    
    def test_eliminar_item_recalcula_total_compra(self):
        """Test: El total de la compra se actualiza después de eliminar un ítem."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Mercado',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        gasto1 = Gasto.objects.create(
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
        
        # Total inicial: 300
        self.assertEqual(compra.total, Decimal('300.00'))
        
        # Eliminar item 1 (100)
        url = reverse('gastos:eliminar_gasto', args=[gasto1.id])
        self.client.post(url)
        
        # Refrescar y verificar nuevo total: 200
        compra.refresh_from_db()
        self.assertEqual(compra.total, Decimal('200.00'))

    def test_eliminar_gasto_get_request(self):
        """
        Verifica que la vista de eliminar gasto responda correctamente a una petición GET.
        El bug reportado es que retorna None (ValueError).
        """
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Gasto para borrar',
            monto=Decimal('100.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta
        )
        url = reverse('gastos:eliminar_gasto', args=[gasto.id])
        try:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'gastos/eliminar_gasto.html')
        except ValueError as e:
            self.fail(f"La vista lanzó ValueError: {e}")


class EditarItemCompraTest(TestCase):
    """Tests para la edición de ítems de una compra."""
    
    def setUp(self):
        """Configuración inicial."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
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
    
    def test_editar_item_mantiene_compra(self):
        """Test: Editar gasto de una compra no afecta la relación con Compra."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Tienda',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Item Original',
            monto=Decimal('100.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        
        # Editar el gasto
        url = reverse('gastos:editar_gasto', args=[gasto.id])
        response = self.client.post(url, {
            'descripcion': 'Item Editado',
            'monto': '150.00',
            'cantidad': 1,
            'categoria': self.categoria2.id,
            'moneda': self.moneda.id,
            'cuenta': self.cuenta.id,
            'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        })
        
        # Refrescar y verificar
        gasto.refresh_from_db()
        self.assertEqual(gasto.descripcion, 'Item Editado')
        self.assertEqual(gasto.monto, Decimal('150.00'))
        self.assertEqual(gasto.compra, compra)  # Sigue perteneciendo a la compra
    
    def test_editar_item_recalcula_total(self):
        """Test: Cambiar monto de ítem se refleja en compra.total."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Super',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion='Item',
            monto=Decimal('100.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        
        # Total inicial: 100
        self.assertEqual(compra.total, Decimal('100.00'))
        
        # Editar monto a 250
        url = reverse('gastos:editar_gasto', args=[gasto.id])
        self.client.post(url, {
            'descripcion': 'Item',
            'monto': '250.00',
            'cantidad': 1,
            'categoria': self.categoria.id,
            'moneda': self.moneda.id,
            'cuenta': self.cuenta.id,
            'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        })
        
        # Verificar nuevo total
        compra.refresh_from_db()
        self.assertEqual(compra.total, Decimal('250.00'))
