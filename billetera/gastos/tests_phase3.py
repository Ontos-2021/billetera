from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from gastos.models import Gasto, Moneda, Tienda, Categoria
from cuentas.models import Cuenta, TipoCuenta
from django.utils import timezone

class Phase3Tests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(self.user)
        
        self.moneda, _ = Moneda.objects.get_or_create(codigo='ARS', defaults={'nombre': 'Peso', 'simbolo': '$'})
        self.tipo_cuenta = TipoCuenta.objects.create(nombre='Efectivo')
        self.cuenta = Cuenta.objects.create(usuario=self.user, nombre='Cartera', tipo=self.tipo_cuenta, moneda=self.moneda)
        self.categoria = Categoria.objects.create(nombre='Comida')

    def test_create_gasto_creates_tienda(self):
        data = {
            'descripcion': 'Compra en Tienda Nueva',
            'tienda_nombre': 'Tienda Nueva',
            'categoria': self.categoria.id,
            'cantidad': 1,
            'monto': 100,
            'moneda': self.moneda.id,
            'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'cuenta': self.cuenta.id
        }
        response = self.client.post(reverse('gastos:crear_gasto'), data)
        if response.status_code == 200:
            print(response.context['form'].errors)
        self.assertEqual(response.status_code, 302) # Redirects on success
        
        # Check if Tienda was created
        tienda = Tienda.objects.filter(nombre='Tienda Nueva', usuario=self.user).first()
        self.assertIsNotNone(tienda)
        
        # Check if Gasto is linked to Tienda
        gasto = Gasto.objects.filter(descripcion='Compra en Tienda Nueva').first()
        self.assertEqual(gasto.tienda, tienda)
        self.assertEqual(gasto.lugar, 'Tienda Nueva')

    def test_create_gasto_reuses_tienda(self):
        # Create existing tienda
        tienda_existente = Tienda.objects.create(nombre='Tienda Existente', usuario=self.user)
        
        data = {
            'descripcion': 'Compra en Tienda Existente',
            'tienda_nombre': 'Tienda Existente',
            'categoria': self.categoria.id,
            'cantidad': 1,
            'monto': 100,
            'moneda': self.moneda.id,
            'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'cuenta': self.cuenta.id
        }
        response = self.client.post(reverse('gastos:crear_gasto'), data)
        self.assertEqual(response.status_code, 302)
        
        # Check if Gasto is linked to existing Tienda
        gasto = Gasto.objects.filter(descripcion='Compra en Tienda Existente').first()
        self.assertEqual(gasto.tienda, tienda_existente)
        
        # Ensure no duplicate tienda was created
        self.assertEqual(Tienda.objects.filter(nombre='Tienda Existente', usuario=self.user).count(), 1)
