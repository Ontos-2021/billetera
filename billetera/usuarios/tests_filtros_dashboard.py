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

        # Fecha de referencia (usando Local Time para coincidir con la vista)
        self.ahora = timezone.localtime(timezone.now())

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

    def test_filtro_24h(self):
        """Test filtro 24h - ventana móvil de últimas 24 horas."""
        # Ingreso hace 12 horas (dentro de 24h)
        self.crear_ingreso(1000, self.ahora - timedelta(hours=12))
        # Ingreso hace 30 horas (fuera de 24h)
        self.crear_ingreso(500, self.ahora - timedelta(hours=30))

        response = self.client.get(reverse('inicio_usuarios'), {'rango': '24h'})
        self.assertEqual(response.status_code, 200)
        
        # Solo debe sumar el de las últimas 24h (1000)
        self.assertEqual(response.context['total_ingresos'], Decimal('1000.00'))

    def test_filtro_7d(self):
        """Test filtro 7d - ventana móvil de últimos 7 días."""
        # Ingreso hace 2 días (dentro de 7d)
        self.crear_ingreso(1000, self.ahora - timedelta(days=2))
        # Ingreso hace 5 días (dentro de 7d)
        self.crear_ingreso(500, self.ahora - timedelta(days=5))
        # Ingreso hace 8 días (fuera de 7d)
        self.crear_ingreso(200, self.ahora - timedelta(days=8))

        response = self.client.get(reverse('inicio_usuarios'), {'rango': '7d'})
        
        # Debe sumar los de últimos 7 días (1500)
        self.assertEqual(response.context['total_ingresos'], Decimal('1500.00'))

    def test_filtro_30d(self):
        """Test filtro 30d - ventana móvil de últimos 30 días."""
        # Ingreso hace 10 días (dentro de 30d)
        self.crear_ingreso(1000, self.ahora - timedelta(days=10))
        # Ingreso hace 25 días (dentro de 30d)
        self.crear_ingreso(500, self.ahora - timedelta(days=25))
        # Ingreso hace 35 días (fuera de 30d)
        self.crear_ingreso(200, self.ahora - timedelta(days=35))

        response = self.client.get(reverse('inicio_usuarios'), {'rango': '30d'})
        
        # Debe sumar los de últimos 30 días (1500)
        self.assertEqual(response.context['total_ingresos'], Decimal('1500.00'))

    def test_filtro_365d(self):
        """Test filtro 365d - ventana móvil de últimos 365 días."""
        # Ingreso hace 100 días (dentro de 365d)
        self.crear_ingreso(1000, self.ahora - timedelta(days=100))
        # Ingreso hace 300 días (dentro de 365d)
        self.crear_ingreso(500, self.ahora - timedelta(days=300))
        # Ingreso hace 400 días (fuera de 365d)
        self.crear_ingreso(200, self.ahora - timedelta(days=400))

        response = self.client.get(reverse('inicio_usuarios'), {'rango': '365d'})
        
        # Debe sumar los de últimos 365 días (1500)
        self.assertEqual(response.context['total_ingresos'], Decimal('1500.00'))

    @patch('django.utils.timezone.now')
    def test_filtro_24h_timezone_fix(self, mock_now):
        """
        Prueba crítica: Verifica que el filtro '24h' funcione correctamente
        cuando en Argentina es de noche (ej: 22:00) pero en UTC ya es el día siguiente (01:00).
        """
        # Simular: 21 de Noviembre a las 22:00 PM (Argentina, UTC-3)
        # En UTC esto es 22 de Noviembre a las 01:00 AM
        now_utc = datetime.datetime(2025, 11, 22, 1, 0, 0, tzinfo=datetime.timezone.utc)
        mock_now.return_value = now_utc
        
        # El usuario hizo un gasto hace 12 horas (dentro de 24h)
        # En UTC esto es 21 de Noviembre a las 13:00 PM
        gasto_date = datetime.datetime(2025, 11, 21, 13, 0, 0, tzinfo=datetime.timezone.utc)
        
        self.crear_gasto(1000, gasto_date)
        
        response = self.client.get(reverse('inicio_usuarios'), {'rango': '24h'})
        
        # El gasto DEBE aparecer
        self.assertEqual(response.context['total_gastos'], Decimal('1000.00'))

    def test_filtro_todo(self):
        """Test filtro todo - sin límite de tiempo."""
        # Ingreso reciente
        self.crear_ingreso(1000, self.ahora - timedelta(days=5))
        # Ingreso hace mucho tiempo
        self.crear_ingreso(500, self.ahora - timedelta(days=500))

        response = self.client.get(reverse('inicio_usuarios'), {'rango': 'todo'})
        
        # Debe sumar todo (1500)
        self.assertEqual(response.context['total_ingresos'], Decimal('1500.00'))

    def test_balance_neto_filtrado(self):
        """Test que el balance neto se calcula correctamente con filtros."""
        # Ingreso hace 6 horas: 1000 (dentro de 24h)
        self.crear_ingreso(1000, self.ahora - timedelta(hours=6))
        # Gasto hace 6 horas: 200 (dentro de 24h)
        self.crear_gasto(200, self.ahora - timedelta(hours=6))
        
        # Ingreso hace 30 horas: 500 (fuera de 24h)
        self.crear_ingreso(500, self.ahora - timedelta(hours=30))

        # Test Rango 24h
        response = self.client.get(reverse('inicio_usuarios'), {'rango': '24h'})
        # Balance = 1000 - 200 = 800
        self.assertEqual(response.context['balance_neto'], Decimal('800.00'))

        # Test Rango TODO
        response = self.client.get(reverse('inicio_usuarios'), {'rango': 'todo'})
        # Balance = (1000 + 500) - 200 = 1300
        self.assertEqual(response.context['balance_neto'], Decimal('1300.00'))
