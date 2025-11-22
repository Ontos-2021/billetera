from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import datetime
from unittest.mock import patch
from gastos.models import Gasto, Moneda as MonedaGasto, Categoria
from ingresos.models import Ingreso, Moneda as MonedaIngreso, CategoriaIngreso

class DashboardFiltrosTest(TestCase):
    def setUp(self):
        # Crear usuario
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

        # Crear Monedas (ARS)
        self.moneda_gasto, _ = MonedaGasto.objects.get_or_create(nombre='Peso Argentino', codigo='ARS', defaults={'simbolo': '$'})
        self.moneda_ingreso, _ = MonedaIngreso.objects.get_or_create(nombre='Peso Argentino', codigo='ARS', defaults={'simbolo': '$'})

        # Crear Categorías
        self.categoria_gasto = Categoria.objects.create(nombre='General')
        self.categoria_ingreso = CategoriaIngreso.objects.create(nombre='Salario')

        # Fechas de referencia (usando Local Time para coincidir con la vista)
        self.ahora = timezone.localtime(timezone.now())
        self.inicio_mes = self.ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        self.inicio_anio = self.ahora.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    def crear_ingreso(self, monto, fecha):
        Ingreso.objects.create(
            usuario=self.user,
            monto=Decimal(monto),
            fecha=fecha,
            descripcion='Ingreso Test',
            moneda=self.moneda_ingreso,
            categoria=self.categoria_ingreso
        )

    def crear_gasto(self, monto, fecha):
        Gasto.objects.create(
            usuario=self.user,
            monto=Decimal(monto),
            fecha=fecha,
            descripcion='Gasto Test',
            moneda=self.moneda_gasto,
            categoria=self.categoria_gasto
        )

    def test_filtro_hoy(self):
        # Ingreso HOY
        self.crear_ingreso(1000, self.ahora)
        # Ingreso AYER (fuera de hoy)
        self.crear_ingreso(500, self.ahora - timedelta(days=1))

        response = self.client.get(reverse('inicio_usuarios'), {'rango': 'hoy'})
        self.assertEqual(response.status_code, 200)
        
        # Solo debe sumar el de hoy (1000)
        self.assertEqual(response.context['total_ingresos'], Decimal('1000.00'))

    def test_filtro_semana(self):
        # Ingreso HOY (dentro de semana)
        self.crear_ingreso(1000, self.ahora)
        # Ingreso hace 5 días (dentro de semana)
        self.crear_ingreso(500, self.ahora - timedelta(days=5))
        # Ingreso hace 8 días (fuera de semana)
        self.crear_ingreso(200, self.ahora - timedelta(days=8))

        response = self.client.get(reverse('inicio_usuarios'), {'rango': 'semana'})
        
        # Debe sumar hoy + hace 5 días (1500)
        self.assertEqual(response.context['total_ingresos'], Decimal('1500.00'))

    def test_filtro_mes(self):
        # Ingreso HOY (dentro del mes)
        self.crear_ingreso(1000, self.ahora)
        
        # Ingreso el día 1 del mes (dentro del mes)
        # Nota: Si hoy es día 1, esto es lo mismo que hoy, pero sirve igual.
        self.crear_ingreso(500, self.inicio_mes + timedelta(hours=1))

        # Ingreso el mes pasado (fuera del mes)
        fecha_mes_pasado = self.inicio_mes - timedelta(days=1)
        self.crear_ingreso(200, fecha_mes_pasado)

        response = self.client.get(reverse('inicio_usuarios'), {'rango': 'mes'})
        
        # Debe sumar hoy + inicio mes (1500)
        self.assertEqual(response.context['total_ingresos'], Decimal('1500.00'))

    def test_filtro_anio(self):
        # Ingreso HOY (dentro del año)
        self.crear_ingreso(1000, self.ahora)
        
        # Ingreso el 1 de Enero (dentro del año)
        self.crear_ingreso(500, self.inicio_anio + timedelta(hours=1))

        # Ingreso el año pasado (fuera del año)
        fecha_anio_pasado = self.inicio_anio - timedelta(days=1)
        self.crear_ingreso(200, fecha_anio_pasado)

        response = self.client.get(reverse('inicio_usuarios'), {'rango': 'anio'})
        
        # Debe sumar hoy + inicio año (1500)
        self.assertEqual(response.context['total_ingresos'], Decimal('1500.00'))

    @patch('django.utils.timezone.now')
    def test_filtro_hoy_timezone_fix(self, mock_now):
        """
        Prueba crítica: Verifica que el filtro 'hoy' funcione correctamente
        cuando en Argentina es de noche (ej: 22:00) pero en UTC ya es el día siguiente (01:00).
        """
        # Simular: 21 de Noviembre a las 22:00 PM (Argentina, UTC-3)
        # En UTC esto es 22 de Noviembre a las 01:00 AM
        now_utc = datetime.datetime(2025, 11, 22, 1, 0, 0, tzinfo=datetime.timezone.utc)
        mock_now.return_value = now_utc
        
        # El usuario hizo un gasto "hoy" (21 de Noviembre) a las 10:00 AM Local
        # En UTC esto es 21 de Noviembre a las 13:00 PM
        gasto_date = datetime.datetime(2025, 11, 21, 13, 0, 0, tzinfo=datetime.timezone.utc)
        
        self.crear_gasto(1000, gasto_date)
        
        response = self.client.get(reverse('inicio_usuarios'), {'rango': 'hoy'})
        
        # El gasto DEBE aparecer (antes del fix daba 0)
        self.assertEqual(response.context['total_gastos'], Decimal('1000.00'))

    def test_filtro_todo(self):
        # Ingreso HOY
        self.crear_ingreso(1000, self.ahora)
        # Ingreso Año Pasado
        fecha_anio_pasado = self.inicio_anio - timedelta(days=1)
        self.crear_ingreso(500, fecha_anio_pasado)

        response = self.client.get(reverse('inicio_usuarios'), {'rango': 'todo'})
        
        # Debe sumar todo (1500)
        self.assertEqual(response.context['total_ingresos'], Decimal('1500.00'))

    def test_balance_neto_filtrado(self):
        # Ingreso HOY: 1000
        self.crear_ingreso(1000, self.ahora)
        # Gasto HOY: 200
        self.crear_gasto(200, self.ahora)
        
        # Ingreso AYER: 500
        self.crear_ingreso(500, self.ahora - timedelta(days=1))

        # Test Rango HOY
        response = self.client.get(reverse('inicio_usuarios'), {'rango': 'hoy'})
        # Balance = 1000 - 200 = 800
        self.assertEqual(response.context['balance_neto'], Decimal('800.00'))

        # Test Rango TODO
        response = self.client.get(reverse('inicio_usuarios'), {'rango': 'todo'})
        # Balance = (1000 + 500) - 200 = 1300
        self.assertEqual(response.context['balance_neto'], Decimal('1300.00'))
