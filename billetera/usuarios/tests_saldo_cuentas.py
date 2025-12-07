from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from gastos.models import Gasto, Moneda as MonedaGasto, Categoria
from ingresos.models import Ingreso, Moneda as MonedaIngreso, CategoriaIngreso
from cuentas.models import Cuenta, TipoCuenta, TransferenciaCuenta

class SaldoCuentasTest(TestCase):
    """
    Tests exhaustivos para verificar el cálculo de saldos de cuentas en el dashboard.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

        # Monedas
        self.moneda_ars, _ = MonedaGasto.objects.get_or_create(
            codigo='ARS', defaults={'nombre': 'Peso Argentino', 'simbolo': '$'}
        )
        self.moneda_usd, _ = MonedaGasto.objects.get_or_create(
            codigo='USD', defaults={'nombre': 'Dólar', 'simbolo': 'U$S'}
        )
        
        # Asegurar que existan las monedas en Ingresos también (por si acaso)
        self.moneda_ingreso_ars, _ = MonedaIngreso.objects.get_or_create(
            codigo='ARS', defaults={'nombre': 'Peso Argentino', 'simbolo': '$'}
        )
        self.moneda_ingreso_usd, _ = MonedaIngreso.objects.get_or_create(
            codigo='USD', defaults={'nombre': 'Dólar', 'simbolo': 'U$S'}
        )

        # Categorías
        self.categoria_gasto = Categoria.objects.create(nombre='General')
        self.categoria_ingreso = CategoriaIngreso.objects.create(nombre='Salario')
        self.categoria_transf_sal = Categoria.objects.create(nombre='Transferencia Saliente')
        self.categoria_transf_ent = CategoriaIngreso.objects.create(nombre='Transferencia Entrante')

        # Tipo de cuenta
        self.tipo_cuenta, _ = TipoCuenta.objects.get_or_create(nombre='Banco')

    def test_saldo_inicial(self):
        """Verifica que el saldo inicial se refleje correctamente."""
        Cuenta.objects.create(
            usuario=self.user,
            nombre='Cuenta Base',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda_ars
        )
        
        response = self.client.get(reverse('inicio_usuarios'))
        cuentas_ctx = response.context['cuentas_saldo']
        
        self.assertEqual(len(cuentas_ctx), 1)
        self.assertEqual(cuentas_ctx[0]['saldo'], Decimal('1000.00'))

    def test_ingresos_suman_al_saldo(self):
        """Verifica que los ingresos aumenten el saldo."""
        cuenta = Cuenta.objects.create(
            usuario=self.user,
            nombre='Cuenta Ingresos',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda_ars
        )
        
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('500.00'),
            fecha=timezone.now(),
            descripcion='Ingreso Test',
            moneda=self.moneda_ingreso_ars,
            categoria=self.categoria_ingreso,
            cuenta=cuenta
        )
        
        response = self.client.get(reverse('inicio_usuarios'))
        cuentas_ctx = response.context['cuentas_saldo']
        
        # 1000 + 500 = 1500
        self.assertEqual(cuentas_ctx[0]['saldo'], Decimal('1500.00'))

    def test_gastos_restan_al_saldo(self):
        """Verifica que los gastos disminuyan el saldo."""
        cuenta = Cuenta.objects.create(
            usuario=self.user,
            nombre='Cuenta Gastos',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda_ars
        )
        
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('200.00'),
            fecha=timezone.now(),
            descripcion='Gasto Test',
            moneda=self.moneda_ars,
            categoria=self.categoria_gasto,
            cuenta=cuenta
        )
        
        response = self.client.get(reverse('inicio_usuarios'))
        cuentas_ctx = response.context['cuentas_saldo']
        
        # 1000 - 200 = 800
        self.assertEqual(cuentas_ctx[0]['saldo'], Decimal('800.00'))

    def test_transferencia_entre_cuentas(self):
        """Verifica que una transferencia descuente de origen y sume a destino."""
        origen = Cuenta.objects.create(
            usuario=self.user,
            nombre='Origen',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda_ars
        )
        destino = Cuenta.objects.create(
            usuario=self.user,
            nombre='Destino',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('0.00'),
            moneda=self.moneda_ars
        )
        
        # Simular transferencia (creando Gasto e Ingreso como lo hace la vista de transferencia)
        monto = Decimal('300.00')
        
        gasto = Gasto.objects.create(
            usuario=self.user,
            descripcion=f'Transferencia a {destino.nombre}',
            monto=monto,
            categoria=self.categoria_transf_sal,
            moneda=origen.moneda,
            cuenta=origen,
            fecha=timezone.now(),
        )

        ingreso = Ingreso.objects.create(
            usuario=self.user,
            descripcion=f'Transferencia desde {origen.nombre}',
            monto=monto,
            categoria=self.categoria_transf_ent,
            moneda=self.moneda_ingreso_ars,
            cuenta=destino,
            fecha=timezone.now(),
        )
        
        # No necesitamos crear el objeto TransferenciaCuenta para que el cálculo funcione,
        # ya que el cálculo se basa en Gasto e Ingreso. Pero lo creamos por completitud.
        TransferenciaCuenta.objects.create(
            usuario=self.user,
            cuenta_origen=origen,
            cuenta_destino=destino,
            monto_origen=monto,
            monto_destino=monto,
            gasto=gasto,
            ingreso=ingreso
        )
        
        response = self.client.get(reverse('inicio_usuarios'))
        cuentas_ctx = response.context['cuentas_saldo']
        
        saldo_origen = next(c['saldo'] for c in cuentas_ctx if c['nombre'] == 'Origen')
        saldo_destino = next(c['saldo'] for c in cuentas_ctx if c['nombre'] == 'Destino')
        
        # Origen: 1000 - 300 = 700
        self.assertEqual(saldo_origen, Decimal('700.00'))
        # Destino: 0 + 300 = 300
        self.assertEqual(saldo_destino, Decimal('300.00'))

    def test_multiples_monedas(self):
        """Verifica que los saldos no se mezclen entre monedas diferentes."""
        cuenta_ars = Cuenta.objects.create(
            usuario=self.user,
            nombre='Caja ARS',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda_ars
        )
        cuenta_usd = Cuenta.objects.create(
            usuario=self.user,
            nombre='Caja USD',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('100.00'),
            moneda=self.moneda_usd
        )
        
        # Gasto en ARS
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('200.00'),
            fecha=timezone.now(),
            moneda=self.moneda_ars,
            categoria=self.categoria_gasto,
            cuenta=cuenta_ars
        )
        
        # Ingreso en USD
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('50.00'),
            fecha=timezone.now(),
            moneda=self.moneda_ingreso_usd,
            categoria=self.categoria_ingreso,
            cuenta=cuenta_usd
        )
        
        response = self.client.get(reverse('inicio_usuarios'))
        cuentas_ctx = response.context['cuentas_saldo']
        
        saldo_ars = next(c['saldo'] for c in cuentas_ctx if c['nombre'] == 'Caja ARS')
        saldo_usd = next(c['saldo'] for c in cuentas_ctx if c['nombre'] == 'Caja USD')
        
        # ARS: 1000 - 200 = 800
        self.assertEqual(saldo_ars, Decimal('800.00'))
        # USD: 100 + 50 = 150
        self.assertEqual(saldo_usd, Decimal('150.00'))

    def test_totales_por_moneda(self):
        """Verifica que el total de cuentas por moneda se calcule correctamente."""
        # Cuenta 1 ARS: 1000
        Cuenta.objects.create(
            usuario=self.user,
            nombre='ARS 1',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda_ars
        )
        # Cuenta 2 ARS: 500
        Cuenta.objects.create(
            usuario=self.user,
            nombre='ARS 2',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('500.00'),
            moneda=self.moneda_ars
        )
        # Cuenta USD: 100
        Cuenta.objects.create(
            usuario=self.user,
            nombre='USD 1',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('100.00'),
            moneda=self.moneda_usd
        )
        
        response = self.client.get(reverse('inicio_usuarios'))
        totales_cuentas = response.context['totales_cuentas']
        
        total_ars = next(t['total'] for t in totales_cuentas if t['codigo'] == 'ARS')
        total_usd = next(t['total'] for t in totales_cuentas if t['codigo'] == 'USD')
        
        self.assertEqual(total_ars, Decimal('1500.00'))
        self.assertEqual(total_usd, Decimal('100.00'))

    def test_eliminar_movimiento_actualiza_saldo(self):
        """Verifica que al eliminar un gasto o ingreso, el saldo se recalcule correctamente."""
        cuenta = Cuenta.objects.create(
            usuario=self.user,
            nombre='Cuenta Borrado',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda_ars
        )
        
        gasto = Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('200.00'),
            fecha=timezone.now(),
            descripcion='Gasto a borrar',
            moneda=self.moneda_ars,
            categoria=self.categoria_gasto,
            cuenta=cuenta
        )
        
        # Saldo inicial: 800
        response = self.client.get(reverse('inicio_usuarios'))
        cuentas_ctx = response.context['cuentas_saldo']
        self.assertEqual(cuentas_ctx[0]['saldo'], Decimal('800.00'))
        
        # Eliminar gasto
        gasto.delete()
        
        # Saldo debe volver a 1000
        response = self.client.get(reverse('inicio_usuarios'))
        cuentas_ctx = response.context['cuentas_saldo']
        self.assertEqual(cuentas_ctx[0]['saldo'], Decimal('1000.00'))
