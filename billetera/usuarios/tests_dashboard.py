from django.test import TestCase, Client
from django.contrib.auth.models import User
from cuentas.models import Cuenta, TipoCuenta, TransferenciaCuenta
from gastos.models import Gasto, Moneda as MonedaGasto, Categoria, Compra
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


class DashboardMovimientosAgrupados(TestCase):
    """Tests para verificar que las compras aparecen agrupadas en últimos movimientos."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        
        self.moneda, _ = MonedaGasto.objects.get_or_create(
            codigo='ARS', defaults={'nombre': 'Peso', 'simbolo': '$'}
        )
        self.categoria = Categoria.objects.create(nombre='Alimentación')
        self.tipo_cuenta, _ = TipoCuenta.objects.get_or_create(nombre='Efectivo')
        self.cuenta = Cuenta.objects.create(
            usuario=self.user,
            nombre='Billetera',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('10000.00'),
            moneda=self.moneda
        )
    
    def test_movimientos_agrupa_compra(self):
        """Test: Compra con 3 gastos aparece como 1 solo movimiento."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Supermercado',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        for i in range(3):
            Gasto.objects.create(
                usuario=self.user,
                descripcion=f'Item {i+1}',
                monto=Decimal('100.00'),
                categoria=self.categoria,
                moneda=self.moneda,
                cuenta=self.cuenta,
                compra=compra
            )
        
        response = self.client.get(reverse('inicio_usuarios'))
        movimientos = response.context['movimientos']
        
        # Debe haber 1 movimiento tipo 'compra', no 3 gastos individuales
        tipos = [m['tipo'] for m in movimientos]
        self.assertEqual(tipos.count('compra'), 1)
        self.assertEqual(tipos.count('gasto'), 0)

    def test_movimientos_compra_muestra_cantidad_item_unico(self):
        """Si una compra tiene 1 ítem con cantidad > 1, debe verse xN en la descripción."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Kiosco',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Galletitas',
            cantidad=2,
            monto=Decimal('200.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )

        response = self.client.get(reverse('inicio_usuarios'))
        movimientos = response.context['movimientos']
        mov_compra = [m for m in movimientos if m['tipo'] == 'compra'][0]
        self.assertIn('x2', mov_compra['descripcion'])

    def test_movimientos_compra_muestra_cantidades_en_compra_multiple(self):
        """Si una compra tiene varios ítems, mostrar xN para los que tengan cantidad > 1."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Super',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Coca',
            cantidad=3,
            monto=Decimal('300.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Pan',
            cantidad=1,
            monto=Decimal('100.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )

        response = self.client.get(reverse('inicio_usuarios'))
        movimientos = response.context['movimientos']
        mov_compra = [m for m in movimientos if m['tipo'] == 'compra'][0]
        self.assertIn('Coca x3', mov_compra['descripcion'])
    
    def test_movimientos_compra_muestra_total(self):
        """Test: Movimiento tipo compra muestra suma de ítems."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Tienda',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Item 1',
            monto=Decimal('150.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Item 2',
            monto=Decimal('350.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        
        response = self.client.get(reverse('inicio_usuarios'))
        movimientos = response.context['movimientos']
        
        mov_compra = [m for m in movimientos if m['tipo'] == 'compra'][0]
        self.assertEqual(mov_compra['monto'], Decimal('500.00'))
    
    def test_movimientos_compra_tiene_icono_correcto(self):
        """Test: HTML contiene emoji 🛒 para movimientos tipo compra."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Mercado',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Producto',
            monto=Decimal('100.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        
        response = self.client.get(reverse('inicio_usuarios'))
        content = response.content.decode('utf-8')
        
        self.assertIn('🛒', content)
    
    def test_movimientos_gasto_individual_sin_cambios(self):
        """Test: Gasto sin compra asociada sigue apareciendo normal."""
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Gasto suelto',
            monto=Decimal('200.00'),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=None  # Sin compra
        )
        
        response = self.client.get(reverse('inicio_usuarios'))
        movimientos = response.context['movimientos']
        
        tipos = [m['tipo'] for m in movimientos]
        self.assertEqual(tipos.count('gasto'), 1)
        self.assertEqual(tipos.count('compra'), 0)
    
    def test_movimientos_mezcla_compras_y_gastos(self):
        """Test: Lista ordenada correctamente mezclando compras y gastos individuales."""
        ahora = timezone.now()
        
        # Gasto individual reciente
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Gasto reciente',
            monto=Decimal('50.00'),
            fecha=ahora,
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=None
        )
        
        # Compra antigua
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=ahora - timedelta(hours=2),
            lugar='Tienda antigua',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        Gasto.objects.create(
            usuario=self.user,
            descripcion='Item compra',
            monto=Decimal('100.00'),
            fecha=ahora - timedelta(hours=2),
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta,
            compra=compra
        )
        
        response = self.client.get(reverse('inicio_usuarios'))
        movimientos = response.context['movimientos']
        
        # El gasto reciente debe aparecer primero
        self.assertEqual(movimientos[0]['tipo'], 'gasto')
        self.assertEqual(movimientos[0]['descripcion'], 'Gasto reciente')
        
        # La compra debe aparecer después
        self.assertEqual(movimientos[1]['tipo'], 'compra')
    
    def test_movimientos_compra_tiene_items_count(self):
        """Test: Movimiento tipo compra incluye items_count."""
        compra = Compra.objects.create(
            usuario=self.user,
            fecha=timezone.now(),
            lugar='Super',
            cuenta=self.cuenta,
            moneda=self.moneda
        )
        for i in range(4):
            Gasto.objects.create(
                usuario=self.user,
                descripcion=f'Item {i}',
                monto=Decimal('25.00'),
                categoria=self.categoria,
                moneda=self.moneda,
                cuenta=self.cuenta,
                compra=compra
            )
        
        response = self.client.get(reverse('inicio_usuarios'))
        movimientos = response.context['movimientos']
        
        mov_compra = [m for m in movimientos if m['tipo'] == 'compra'][0]
        self.assertEqual(mov_compra['items_count'], 4)
