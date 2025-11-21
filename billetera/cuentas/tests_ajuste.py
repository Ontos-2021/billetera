from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from cuentas.models import Cuenta, TipoCuenta
from gastos.models import Moneda, Gasto, Categoria as CategoriaGasto
from ingresos.models import Ingreso, CategoriaIngreso
from decimal import Decimal

class AjusteSaldoTest(TestCase):
    def setUp(self):
        # Create User
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        
        # Create Dependencies
        self.moneda, _ = Moneda.objects.get_or_create(codigo='ARS', defaults={'nombre': 'Peso Argentino', 'simbolo': '$'})
        self.tipo_cuenta = TipoCuenta.objects.create(nombre='Efectivo')
        
        # Create Account with Initial Balance 1000
        self.cuenta = Cuenta.objects.create(
            usuario=self.user,
            nombre='Billetera',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda
        )
        
        self.url = reverse('cuentas:ajustar_saldo', args=[self.cuenta.id])

    def test_ajuste_positivo_crea_ingreso(self):
        """Test that adjusting balance upwards creates an Income"""
        # System Balance: 1000. User says: 1500. Diff: +500
        response = self.client.post(self.url, {'saldo_real': '1500.00'})
        
        self.assertRedirects(response, reverse('inicio_usuarios'))
        
        # Check Income created
        ingreso = Ingreso.objects.last()
        self.assertIsNotNone(ingreso)
        self.assertEqual(ingreso.monto, Decimal('500.00'))
        self.assertEqual(ingreso.cuenta, self.cuenta)
        self.assertEqual(ingreso.categoria.nombre, 'Ajuste de Saldo')
        self.assertEqual(ingreso.descripcion, 'Ajuste manual de saldo (Positivo)')

    def test_ajuste_negativo_crea_gasto(self):
        """Test that adjusting balance downwards creates an Expense"""
        # System Balance: 1000. User says: 800. Diff: -200
        response = self.client.post(self.url, {'saldo_real': '800.00'})
        
        self.assertRedirects(response, reverse('inicio_usuarios'))
        
        # Check Expense created
        gasto = Gasto.objects.last()
        self.assertIsNotNone(gasto)
        self.assertEqual(gasto.monto, Decimal('200.00'))
        self.assertEqual(gasto.cuenta, self.cuenta)
        self.assertEqual(gasto.categoria.nombre, 'Ajuste de Saldo')
        self.assertEqual(gasto.descripcion, 'Ajuste manual de saldo (Negativo)')

    def test_ajuste_neutro_no_hace_nada(self):
        """Test that if balance matches, no record is created"""
        # System Balance: 1000. User says: 1000.
        response = self.client.post(self.url, {'saldo_real': '1000.00'})
        
        self.assertRedirects(response, reverse('inicio_usuarios'))
        self.assertEqual(Ingreso.objects.count(), 0)
        self.assertEqual(Gasto.objects.count(), 0)

    def test_permisos_usuario(self):
        """Test that user cannot adjust another user's account"""
        other_user = User.objects.create_user(username='other', password='password')
        other_account = Cuenta.objects.create(
            usuario=other_user,
            nombre='Other Wallet',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda
        )
        
        url = reverse('cuentas:ajustar_saldo', args=[other_account.id])
        response = self.client.get(url)
        
        # Should return 404 because get_object_or_404 filters by request.user
        self.assertEqual(response.status_code, 404)
