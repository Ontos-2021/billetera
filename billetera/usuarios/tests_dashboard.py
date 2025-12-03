from django.test import TestCase, Client
from django.contrib.auth.models import User
from cuentas.models import Cuenta, TipoCuenta, TransferenciaCuenta
from gastos.models import Gasto, Moneda as MonedaGasto, Categoria
from ingresos.models import Ingreso, Moneda as MonedaIngreso, CategoriaIngreso
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

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

    def test_totales_por_moneda_includes_all_account_currencies(self):
        moneda_usd, _ = MonedaGasto.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dólar', 'simbolo': 'U$S'})
        Cuenta.objects.create(
            usuario=self.user,
            nombre='Cuenta USD',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('250.00'),
            moneda=moneda_usd
        )

        response = self.client.get(reverse('inicio_usuarios'))
        totals = response.context['totales_cuentas']
        self.assertEqual(len(totals), 2)
        totals_map = {item['codigo']: item['total'] for item in totals}
        self.assertEqual(totals_map['ARS'], Decimal('1000.00'))
        self.assertEqual(totals_map['USD'], Decimal('250.00'))
        self.assertEqual(response.context['totales_cuentas_default'], 'ARS')

    def test_rango_3d_filters_ingresos(self):
        """Test 3d filter uses 72-hour rolling window."""
        ahora = timezone.now()
        reciente = ahora - timedelta(hours=48)  # Dentro de las últimas 72h
        antiguo = ahora - timedelta(hours=80)   # Fuera de las últimas 72h

        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('200.00'),
            fecha=reciente,
            descripcion='Ingreso reciente',
            moneda=self.moneda_ingreso,
            cuenta=self.cuenta
        )
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('150.00'),
            fecha=antiguo,
            descripcion='Ingreso antiguo',
            moneda=self.moneda_ingreso,
            cuenta=self.cuenta
        )

        response = self.client.get(f"{reverse('inicio_usuarios')}?rango=3d")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_ingresos'], Decimal('200.00'))

    def test_dashboard_totals_ignore_transfers(self):
        moneda_usd_gasto, _ = MonedaGasto.objects.get_or_create(
            codigo='USD', defaults={'nombre': 'Dólar', 'simbolo': 'U$S'}
        )
        moneda_usd_ingreso, _ = MonedaIngreso.objects.get_or_create(
            codigo='USD', defaults={'nombre': 'Dólar', 'simbolo': 'U$S'}
        )
        cuenta_destino = Cuenta.objects.create(
            usuario=self.user,
            nombre='Cuenta USD',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('0.00'),
            moneda=moneda_usd_gasto
        )

        categoria_gasto, _ = Categoria.objects.get_or_create(nombre='Transferencia Saliente')
        categoria_ingreso, _ = CategoriaIngreso.objects.get_or_create(nombre='Transferencia Entrante')
        fecha_mov = timezone.now()

        gasto_transfer = Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('100.00'),
            fecha=fecha_mov,
            descripcion='Transferencia salida',
            moneda=self.moneda_gasto,
            cuenta=self.cuenta,
            categoria=categoria_gasto
        )
        ingreso_transfer = Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('50.00'),
            fecha=fecha_mov,
            descripcion='Transferencia entrada',
            moneda=moneda_usd_ingreso,
            cuenta=cuenta_destino,
            categoria=categoria_ingreso
        )

        TransferenciaCuenta.objects.create(
            usuario=self.user,
            cuenta_origen=self.cuenta,
            cuenta_destino=cuenta_destino,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('50.00'),
            tasa_manual=Decimal('0.500000'),
            gasto=gasto_transfer,
            ingreso=ingreso_transfer,
        )

        response = self.client.get(reverse('inicio_usuarios'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_gastos'], Decimal('0.00'))
        self.assertEqual(response.context['total_ingresos'], Decimal('0.00'))
