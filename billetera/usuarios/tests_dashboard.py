from django.test import TestCase, Client
from django.contrib.auth.models import User
from cuentas.models import Cuenta, TipoCuenta
from gastos.models import Gasto, Moneda as MonedaGasto, Categoria
from ingresos.models import Ingreso, Moneda as MonedaIngreso
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone

class DashboardCuentasTest(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

        # Create Moneda Gasto
        self.moneda_gasto, _ = MonedaGasto.objects.get_or_create(nombre='Peso Argentino', codigo='ARS', defaults={'simbolo': '$'})
        
        # Create Moneda Ingreso (needs to match for consistency in test, though models are different)
        self.moneda_ingreso, _ = MonedaIngreso.objects.get_or_create(nombre='Peso Argentino', codigo='ARS', defaults={'simbolo': '$'})

        # Create TipoCuenta
        self.tipo_cuenta, _ = TipoCuenta.objects.get_or_create(nombre='Banco')

        # Create Cuenta
        self.cuenta = Cuenta.objects.create(
            usuario=self.user,
            nombre='Banco Galicia',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda_gasto
        )

        # Create Categoria (needed for Gasto/Ingreso)
        self.categoria = Categoria.objects.create(nombre='General')

    def test_dashboard_balance_calculation(self):
        # Initial state: Balance should be 1000
        response = self.client.get(reverse('inicio_usuarios'))
        self.assertEqual(response.status_code, 200)
        cuentas_saldo = response.context['cuentas_saldo']
        self.assertEqual(len(cuentas_saldo), 1)
        self.assertEqual(cuentas_saldo[0]['saldo'], Decimal('1000.00'))

        # Add Income: +500
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('500.00'),
            fecha=timezone.now(),
            descripcion='Sueldo',
            moneda=self.moneda_ingreso,
            cuenta=self.cuenta
        )

        # Check balance: 1500
        response = self.client.get(reverse('inicio_usuarios'))
        cuentas_saldo = response.context['cuentas_saldo']
        self.assertEqual(cuentas_saldo[0]['saldo'], Decimal('1500.00'))

        # Add Expense: -200
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('200.00'),
            fecha=timezone.now(),
            descripcion='Compra',
            moneda=self.moneda_gasto,
            cuenta=self.cuenta,
            categoria=self.categoria
        )

        # Check balance: 1300
        response = self.client.get(reverse('inicio_usuarios'))
        cuentas_saldo = response.context['cuentas_saldo']
        self.assertEqual(cuentas_saldo[0]['saldo'], Decimal('1300.00'))
