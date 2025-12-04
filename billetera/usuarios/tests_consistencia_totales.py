from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone

from gastos.models import Gasto, Moneda as MonedaGasto, Categoria
from ingresos.models import Ingreso, Moneda as MonedaIngreso, CategoriaIngreso
from cuentas.models import Cuenta, TipoCuenta, TransferenciaCuenta


class ConsistenciaTotalesTest(TestCase):
    """
    Tests para verificar que los totales del dashboard (filtro 'todo') 
    coinciden con los totales de las listas de gastos e ingresos.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

        # Crear monedas
        self.moneda_gasto_ars, _ = MonedaGasto.objects.get_or_create(
            codigo='ARS', defaults={'nombre': 'Peso Argentino', 'simbolo': '$'}
        )
        self.moneda_gasto_usd, _ = MonedaGasto.objects.get_or_create(
            codigo='USD', defaults={'nombre': 'Dólar', 'simbolo': 'U$S'}
        )
        self.moneda_ingreso_ars, _ = MonedaIngreso.objects.get_or_create(
            codigo='ARS', defaults={'nombre': 'Peso Argentino', 'simbolo': '$'}
        )
        self.moneda_ingreso_usd, _ = MonedaIngreso.objects.get_or_create(
            codigo='USD', defaults={'nombre': 'Dólar', 'simbolo': 'U$S'}
        )

        # Crear categorías
        self.categoria_gasto = Categoria.objects.create(nombre='General')
        self.categoria_ingreso = CategoriaIngreso.objects.create(nombre='Salario')

        # Crear tipo de cuenta y cuentas
        self.tipo_cuenta, _ = TipoCuenta.objects.get_or_create(nombre='Banco')
        self.cuenta_ars = Cuenta.objects.create(
            usuario=self.user,
            nombre='Cuenta ARS',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('0.00'),
            moneda=self.moneda_gasto_ars
        )
        self.cuenta_usd = Cuenta.objects.create(
            usuario=self.user,
            nombre='Cuenta USD',
            tipo=self.tipo_cuenta,
            saldo_inicial=Decimal('0.00'),
            moneda=self.moneda_gasto_usd
        )

    def test_total_ingresos_ars_dashboard_coincide_con_lista(self):
        """
        Verifica que el total de ingresos ARS en el dashboard (filtro 'todo')
        coincide con el total ARS en la lista de ingresos.
        """
        # Crear ingresos en ARS
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('50000.00'),
            fecha=timezone.now(),
            descripcion='Sueldo',
            moneda=self.moneda_ingreso_ars,
            categoria=self.categoria_ingreso,
            cuenta=self.cuenta_ars
        )
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('10000.00'),
            fecha=timezone.now(),
            descripcion='Bonus',
            moneda=self.moneda_ingreso_ars,
            categoria=self.categoria_ingreso,
            cuenta=self.cuenta_ars
        )

        # Obtener total del dashboard con filtro 'todo'
        response_dashboard = self.client.get(reverse('inicio_usuarios'), {'rango': 'todo'})
        total_dashboard = response_dashboard.context['total_ingresos']

        # Obtener total de la lista de ingresos
        response_lista = self.client.get(reverse('ingresos:lista_ingresos'))
        totales_lista = response_lista.context['totales_ingresos']
        total_lista_ars = next((t['total'] for t in totales_lista if t['codigo'] == 'ARS'), Decimal('0.00'))

        self.assertEqual(total_dashboard, total_lista_ars)

    def test_total_gastos_ars_dashboard_coincide_con_lista(self):
        """
        Verifica que el total de gastos ARS en el dashboard (filtro 'todo')
        coincide con el total ARS en la lista de gastos.
        """
        # Crear gastos en ARS
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('5000.00'),
            fecha=timezone.now(),
            descripcion='Supermercado',
            moneda=self.moneda_gasto_ars,
            categoria=self.categoria_gasto,
            cuenta=self.cuenta_ars
        )
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('2000.00'),
            fecha=timezone.now(),
            descripcion='Nafta',
            moneda=self.moneda_gasto_ars,
            categoria=self.categoria_gasto,
            cuenta=self.cuenta_ars
        )

        # Obtener total del dashboard con filtro 'todo'
        response_dashboard = self.client.get(reverse('inicio_usuarios'), {'rango': 'todo'})
        total_dashboard = response_dashboard.context['total_gastos']

        # Obtener total de la lista de gastos
        response_lista = self.client.get(reverse('gastos:lista_gastos'))
        totales_lista = response_lista.context['totales_gastos']
        total_lista_ars = next((t['total'] for t in totales_lista if t['codigo'] == 'ARS'), Decimal('0.00'))

        self.assertEqual(total_dashboard, total_lista_ars)

    def test_totales_excluyen_transferencias_consistentemente(self):
        """
        Verifica que tanto el dashboard como las listas excluyen transferencias
        del cálculo de totales de manera consistente.
        """
        # Crear ingresos y gastos normales
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('100000.00'),
            fecha=timezone.now(),
            descripcion='Sueldo real',
            moneda=self.moneda_ingreso_ars,
            categoria=self.categoria_ingreso,
            cuenta=self.cuenta_ars
        )
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('5000.00'),
            fecha=timezone.now(),
            descripcion='Compra real',
            moneda=self.moneda_gasto_ars,
            categoria=self.categoria_gasto,
            cuenta=self.cuenta_ars
        )

        # Crear una transferencia (gasto + ingreso vinculados)
        gasto_transfer = Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('50000.00'),
            fecha=timezone.now(),
            descripcion='Transferencia a USD',
            moneda=self.moneda_gasto_ars,
            categoria=self.categoria_gasto,
            cuenta=self.cuenta_ars
        )
        ingreso_transfer = Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('50.00'),
            fecha=timezone.now(),
            descripcion='Transferencia desde ARS',
            moneda=self.moneda_ingreso_usd,
            categoria=self.categoria_ingreso,
            cuenta=self.cuenta_usd
        )
        TransferenciaCuenta.objects.create(
            usuario=self.user,
            cuenta_origen=self.cuenta_ars,
            cuenta_destino=self.cuenta_usd,
            monto_origen=Decimal('50000.00'),
            monto_destino=Decimal('50.00'),
            tasa_manual=Decimal('0.001'),
            gasto=gasto_transfer,
            ingreso=ingreso_transfer
        )

        # Dashboard - solo debe contar los movimientos reales
        response_dashboard = self.client.get(reverse('inicio_usuarios'), {'rango': 'todo'})
        total_ingresos_dashboard = response_dashboard.context['total_ingresos']
        total_gastos_dashboard = response_dashboard.context['total_gastos']

        # Listas - deben coincidir
        response_lista_ingresos = self.client.get(reverse('ingresos:lista_ingresos'))
        totales_ingresos = response_lista_ingresos.context['totales_ingresos']
        total_ingresos_lista_ars = next((t['total'] for t in totales_ingresos if t['codigo'] == 'ARS'), Decimal('0.00'))

        response_lista_gastos = self.client.get(reverse('gastos:lista_gastos'))
        totales_gastos = response_lista_gastos.context['totales_gastos']
        total_gastos_lista_ars = next((t['total'] for t in totales_gastos if t['codigo'] == 'ARS'), Decimal('0.00'))

        # Verificar que los totales son correctos (excluyendo transferencias)
        self.assertEqual(total_ingresos_dashboard, Decimal('100000.00'))  # Solo el sueldo real
        self.assertEqual(total_gastos_dashboard, Decimal('5000.00'))  # Solo la compra real

        # Verificar consistencia entre dashboard y listas
        self.assertEqual(total_ingresos_dashboard, total_ingresos_lista_ars)
        self.assertEqual(total_gastos_dashboard, total_gastos_lista_ars)

    def test_balance_neto_dashboard_consistente_con_listas(self):
        """
        Verifica que el balance neto del dashboard coincide con 
        la diferencia entre totales de listas.
        """
        # Crear movimientos
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('80000.00'),
            fecha=timezone.now(),
            descripcion='Ingreso',
            moneda=self.moneda_ingreso_ars,
            categoria=self.categoria_ingreso,
            cuenta=self.cuenta_ars
        )
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('30000.00'),
            fecha=timezone.now(),
            descripcion='Gasto',
            moneda=self.moneda_gasto_ars,
            categoria=self.categoria_gasto,
            cuenta=self.cuenta_ars
        )

        # Dashboard
        response_dashboard = self.client.get(reverse('inicio_usuarios'), {'rango': 'todo'})
        balance_dashboard = response_dashboard.context['balance_neto']
        total_ingresos_dashboard = response_dashboard.context['total_ingresos']
        total_gastos_dashboard = response_dashboard.context['total_gastos']

        # Listas
        response_lista_ingresos = self.client.get(reverse('ingresos:lista_ingresos'))
        totales_ingresos = response_lista_ingresos.context['totales_ingresos']
        total_ingresos_lista = next((t['total'] for t in totales_ingresos if t['codigo'] == 'ARS'), Decimal('0.00'))

        response_lista_gastos = self.client.get(reverse('gastos:lista_gastos'))
        totales_gastos = response_lista_gastos.context['totales_gastos']
        total_gastos_lista = next((t['total'] for t in totales_gastos if t['codigo'] == 'ARS'), Decimal('0.00'))

        # Verificar consistencia
        self.assertEqual(balance_dashboard, total_ingresos_lista - total_gastos_lista)
        self.assertEqual(balance_dashboard, Decimal('50000.00'))

    def test_multiples_monedas_totales_independientes(self):
        """
        Verifica que los totales en diferentes monedas se calculan 
        independientemente y de forma consistente.
        """
        # Ingresos en ARS y USD
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('50000.00'),
            fecha=timezone.now(),
            descripcion='Sueldo ARS',
            moneda=self.moneda_ingreso_ars,
            categoria=self.categoria_ingreso,
            cuenta=self.cuenta_ars
        )
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('500.00'),
            fecha=timezone.now(),
            descripcion='Freelance USD',
            moneda=self.moneda_ingreso_usd,
            categoria=self.categoria_ingreso,
            cuenta=self.cuenta_usd
        )

        # Dashboard solo muestra ARS
        response_dashboard = self.client.get(reverse('inicio_usuarios'), {'rango': 'todo'})
        total_dashboard = response_dashboard.context['total_ingresos']

        # Lista muestra ambas monedas
        response_lista = self.client.get(reverse('ingresos:lista_ingresos'))
        totales_lista = response_lista.context['totales_ingresos']

        total_lista_ars = next((t['total'] for t in totales_lista if t['codigo'] == 'ARS'), Decimal('0.00'))
        total_lista_usd = next((t['total'] for t in totales_lista if t['codigo'] == 'USD'), Decimal('0.00'))

        # Dashboard debe coincidir solo con ARS
        self.assertEqual(total_dashboard, total_lista_ars)
        self.assertEqual(total_dashboard, Decimal('50000.00'))

        # USD debe tener su propio total en la lista
        self.assertEqual(total_lista_usd, Decimal('500.00'))
