from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone

from gastos.models import Gasto, Moneda, Categoria


class ListaGastosTotalesPorMonedaTest(TestCase):
    """Tests para verificar que los totales de gastos se calculan correctamente por moneda."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

        # Crear monedas (get_or_create porque las migraciones pueden crearlas)
        self.moneda_ars, _ = Moneda.objects.get_or_create(
            codigo='ARS', defaults={'nombre': 'Peso Argentino', 'simbolo': '$'}
        )
        self.moneda_usd, _ = Moneda.objects.get_or_create(
            codigo='USD', defaults={'nombre': 'Dólar', 'simbolo': 'U$S'}
        )

        # Crear categoría
        self.categoria = Categoria.objects.create(nombre='General')

    def test_totales_separados_por_moneda(self):
        """Verifica que los totales se calculan separadamente por cada moneda."""
        # Crear gastos en ARS
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('1000.00'),
            fecha=timezone.now(),
            descripcion='Gasto ARS 1',
            moneda=self.moneda_ars,
            categoria=self.categoria
        )
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('500.00'),
            fecha=timezone.now(),
            descripcion='Gasto ARS 2',
            moneda=self.moneda_ars,
            categoria=self.categoria
        )

        # Crear gastos en USD
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('100.00'),
            fecha=timezone.now(),
            descripcion='Gasto USD 1',
            moneda=self.moneda_usd,
            categoria=self.categoria
        )

        response = self.client.get(reverse('gastos:lista_gastos'))
        self.assertEqual(response.status_code, 200)

        totales = response.context['totales_gastos']
        self.assertEqual(len(totales), 2)

        # Convertir a dict para verificar
        totales_dict = {t['codigo']: t['total'] for t in totales}
        self.assertEqual(totales_dict['ARS'], Decimal('1500.00'))
        self.assertEqual(totales_dict['USD'], Decimal('100.00'))

    def test_default_moneda_es_ars_si_existe(self):
        """Verifica que la moneda por defecto es ARS si hay gastos en ARS."""
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('100.00'),
            fecha=timezone.now(),
            descripcion='Gasto USD',
            moneda=self.moneda_usd,
            categoria=self.categoria
        )
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('500.00'),
            fecha=timezone.now(),
            descripcion='Gasto ARS',
            moneda=self.moneda_ars,
            categoria=self.categoria
        )

        response = self.client.get(reverse('gastos:lista_gastos'))
        self.assertEqual(response.context['totales_gastos_default'], 'ARS')

    def test_default_moneda_primera_si_no_hay_ars(self):
        """Verifica que si no hay ARS, se usa la primera moneda disponible."""
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('100.00'),
            fecha=timezone.now(),
            descripcion='Gasto USD',
            moneda=self.moneda_usd,
            categoria=self.categoria
        )

        response = self.client.get(reverse('gastos:lista_gastos'))
        self.assertEqual(response.context['totales_gastos_default'], 'USD')

    def test_lista_vacia_sin_totales(self):
        """Verifica que sin gastos, la lista de totales está vacía."""
        response = self.client.get(reverse('gastos:lista_gastos'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['totales_gastos'], [])
        self.assertIsNone(response.context['totales_gastos_default'])

    def test_totales_incluyen_simbolo_y_nombre(self):
        """Verifica que cada total incluye el símbolo y nombre de la moneda."""
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal('100.00'),
            fecha=timezone.now(),
            descripcion='Gasto ARS',
            moneda=self.moneda_ars,
            categoria=self.categoria
        )

        response = self.client.get(reverse('gastos:lista_gastos'))
        totales = response.context['totales_gastos']
        
        self.assertEqual(len(totales), 1)
        self.assertEqual(totales[0]['codigo'], 'ARS')
        self.assertEqual(totales[0]['simbolo'], '$')
        self.assertEqual(totales[0]['nombre'], 'Peso Argentino')
        self.assertEqual(totales[0]['total'], Decimal('100.00'))
