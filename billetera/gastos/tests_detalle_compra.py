"""
Tests para la vista de detalle de compra (modal partial).
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from gastos.models import Compra, Gasto, Moneda, Categoria
from cuentas.models import Cuenta, TipoCuenta


class DetalleCompraViewTest(TestCase):
    """Tests para la vista detalle_compra que retorna HTML partial."""
    
    def setUp(self):
        """Configuración inicial."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        self.client = Client()
        
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
        
        # Crear una compra con ítems
        self.compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Supermercado Test',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        self.gasto1 = Gasto.objects.create(
            usuario=self.user,
            descripcion='Leche',
            monto=Decimal('150.00'),
            cantidad=2,
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=self.compra
        )
        self.gasto2 = Gasto.objects.create(
            usuario=self.user,
            descripcion='Pan',
            monto=Decimal('80.00'),
            cantidad=1,
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=self.compra
        )
    
    def test_detalle_compra_returns_html(self):
        """Test: GET retorna status 200 y content-type text/html."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('gastos:detalle_compra', args=[self.compra.pk])
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])
    
    def test_detalle_compra_shows_items(self):
        """Test: Response contiene descripción de cada ítem."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('gastos:detalle_compra', args=[self.compra.pk])
        
        response = self.client.get(url)
        content = response.content.decode('utf-8')
        
        self.assertIn('Leche', content)
        self.assertIn('Pan', content)
    
    def test_detalle_compra_shows_total(self):
        """Test: Response contiene el total formateado."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('gastos:detalle_compra', args=[self.compra.pk])
        
        response = self.client.get(url)
        content = response.content.decode('utf-8')
        
        # El total es 150 + 80 = 230
        self.assertIn('230', content)
    
    def test_detalle_compra_shows_lugar(self):
        """Test: Response contiene el lugar de la compra."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('gastos:detalle_compra', args=[self.compra.pk])
        
        response = self.client.get(url)
        content = response.content.decode('utf-8')
        
        self.assertIn('Supermercado Test', content)
    
    def test_detalle_compra_requires_auth(self):
        """Test: Usuario no autenticado recibe redirect a login."""
        url = reverse('gastos:detalle_compra', args=[self.compra.pk])
        
        response = self.client.get(url)
        
        # Debe redirigir al login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_detalle_compra_only_owner(self):
        """Test: Usuario no puede ver compra de otro usuario (403)."""
        self.client.login(username='otheruser', password='testpass123')
        url = reverse('gastos:detalle_compra', args=[self.compra.pk])
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 403)
    
    def test_detalle_compra_superuser_can_view_any(self):
        """Test: Superusuario puede ver cualquier compra."""
        superuser = User.objects.create_superuser(
            username='admin',
            password='adminpass123'
        )
        self.client.login(username='admin', password='adminpass123')
        url = reverse('gastos:detalle_compra', args=[self.compra.pk])
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
    
    def test_detalle_compra_nonexistent_returns_404(self):
        """Test: Compra inexistente retorna 404."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('gastos:detalle_compra', args=[99999])
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_detalle_compra_shows_edit_links(self):
        """Test: El partial contiene links para editar ítems."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('gastos:detalle_compra', args=[self.compra.pk])
        
        response = self.client.get(url)
        content = response.content.decode('utf-8')
        
        # Debe contener links a editar gasto
        edit_url = reverse('gastos:editar_gasto', args=[self.gasto1.pk])
        self.assertIn(edit_url, content)
    
    def test_detalle_compra_shows_items_count(self):
        """Test: El partial muestra la cantidad de ítems."""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('gastos:detalle_compra', args=[self.compra.pk])
        
        response = self.client.get(url)
        content = response.content.decode('utf-8')
        
        # Debe mostrar "2 items"
        self.assertIn('2 items', content)
