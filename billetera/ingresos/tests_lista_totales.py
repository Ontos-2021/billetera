from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone

from ingresos.models import Ingreso, Moneda, CategoriaIngreso


class ListaIngresosTotalesPorMonedaTest(TestCase):
    """Tests para verificar que los totales de ingresos se calculan correctamente por moneda."""

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
        self.categoria = CategoriaIngreso.objects.create(nombre='Salario')

    def test_totales_separados_por_moneda(self):
        """Verifica que los totales se calculan separadamente por cada moneda."""
        # Crear ingresos en ARS
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('50000.00'),
            fecha=timezone.now(),
            descripcion='Sueldo',
            moneda=self.moneda_ars,
            categoria=self.categoria
        )
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('10000.00'),
            fecha=timezone.now(),
            descripcion='Bonus',
            moneda=self.moneda_ars,
            categoria=self.categoria
        )

        # Crear ingresos en USD
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('500.00'),
            fecha=timezone.now(),
            descripcion='Freelance USD',
            moneda=self.moneda_usd,
            categoria=self.categoria
        )

        response = self.client.get(reverse('ingresos:lista_ingresos'))
        self.assertEqual(response.status_code, 200)

        totales = response.context['totales_ingresos']
        self.assertEqual(len(totales), 2)

        # Convertir a dict para verificar
        totales_dict = {t['codigo']: t['total'] for t in totales}
        self.assertEqual(totales_dict['ARS'], Decimal('60000.00'))
        self.assertEqual(totales_dict['USD'], Decimal('500.00'))

    def test_default_moneda_es_ars_si_existe(self):
        """Verifica que la moneda por defecto es ARS si hay ingresos en ARS."""
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('100.00'),
            fecha=timezone.now(),
            descripcion='Ingreso USD',
            moneda=self.moneda_usd,
            categoria=self.categoria
        )
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('500.00'),
            fecha=timezone.now(),
            descripcion='Ingreso ARS',
            moneda=self.moneda_ars,
            categoria=self.categoria
        )

        response = self.client.get(reverse('ingresos:lista_ingresos'))
        self.assertEqual(response.context['totales_ingresos_default'], 'ARS')

    def test_default_moneda_primera_si_no_hay_ars(self):
        """Verifica que si no hay ARS, se usa la primera moneda disponible."""
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('100.00'),
            fecha=timezone.now(),
            descripcion='Ingreso USD',
            moneda=self.moneda_usd,
            categoria=self.categoria
        )

        response = self.client.get(reverse('ingresos:lista_ingresos'))
        self.assertEqual(response.context['totales_ingresos_default'], 'USD')

    def test_lista_vacia_sin_totales(self):
        """Verifica que sin ingresos, la lista de totales está vacía."""
        response = self.client.get(reverse('ingresos:lista_ingresos'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['totales_ingresos'], [])
        self.assertIsNone(response.context['totales_ingresos_default'])

    def test_totales_incluyen_simbolo_y_nombre(self):
        """Verifica que cada total incluye el símbolo y nombre de la moneda."""
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('1000.00'),
            fecha=timezone.now(),
            descripcion='Ingreso ARS',
            moneda=self.moneda_ars,
            categoria=self.categoria
        )

        response = self.client.get(reverse('ingresos:lista_ingresos'))
        totales = response.context['totales_ingresos']
        
        self.assertEqual(len(totales), 1)
        self.assertEqual(totales[0]['codigo'], 'ARS')
        self.assertEqual(totales[0]['simbolo'], '$')
        self.assertEqual(totales[0]['nombre'], 'Peso Argentino')
        self.assertEqual(totales[0]['total'], Decimal('1000.00'))

    def test_usuario_solo_ve_sus_ingresos(self):
        """Verifica que un usuario solo ve los totales de sus propios ingresos."""
        otro_usuario = User.objects.create_user(username='otro', password='password')
        
        # Ingreso del usuario actual
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal('1000.00'),
            fecha=timezone.now(),
            descripcion='Mi ingreso',
            moneda=self.moneda_ars,
            categoria=self.categoria
        )
        
        # Ingreso del otro usuario
        Ingreso.objects.create(
            usuario=otro_usuario,
            monto=Decimal('5000.00'),
            fecha=timezone.now(),
            descripcion='Ingreso de otro',
            moneda=self.moneda_ars,
            categoria=self.categoria
        )

        response = self.client.get(reverse('ingresos:lista_ingresos'))
        totales = response.context['totales_ingresos']
        
        # Solo debe ver su ingreso de 1000
        self.assertEqual(len(totales), 1)
        self.assertEqual(totales[0]['total'], Decimal('1000.00'))
