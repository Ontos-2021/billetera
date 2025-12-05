from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from gastos.models import Gasto, Moneda, Categoria
from cuentas.models import Cuenta, TipoCuenta
from django.utils import timezone
from datetime import timedelta
from unittest.mock import MagicMock, patch
import sys

class Phase2Tests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.force_login(self.user)
        
        self.moneda, _ = Moneda.objects.get_or_create(codigo='ARS', defaults={'nombre': 'Peso', 'simbolo': '$'})
        self.tipo_cuenta = TipoCuenta.objects.create(nombre='Efectivo')
        self.cuenta = Cuenta.objects.create(usuario=self.user, nombre='Cartera', tipo=self.tipo_cuenta, moneda=self.moneda)
        
        self.categoria_comida = Categoria.objects.create(nombre='Comida')
        self.categoria_transporte = Categoria.objects.create(nombre='Transporte')

        # Create some expenses
        self.gasto1 = Gasto.objects.create(
            usuario=self.user,
            descripcion='Gasto 1',
            monto=100,
            moneda=self.moneda,
            cuenta=self.cuenta,
            fecha=timezone.now(),
            categoria=self.categoria_comida
        )
        self.gasto2 = Gasto.objects.create(
            usuario=self.user,
            descripcion='Gasto 2',
            monto=200,
            moneda=self.moneda,
            cuenta=self.cuenta,
            fecha=timezone.now() - timedelta(days=10),
            categoria=self.categoria_transporte
        )

    def test_pdf_export(self):
        # Mock weasyprint module
        mock_weasyprint = MagicMock()
        mock_weasyprint.HTML.return_value.write_pdf.side_effect = lambda response: response.write(b'%PDF-1.4 mock')
        
        with patch.dict(sys.modules, {'weasyprint': mock_weasyprint}):
            response = self.client.get(reverse('gastos:exportar_gastos_pdf'))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'application/pdf')
            self.assertTrue(response.content.startswith(b'%PDF'))

    def test_gasto_filter_description(self):
        response = self.client.get(reverse('gastos:lista_gastos'), {'descripcion': 'Gasto 1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gasto 1')
        self.assertNotContains(response, 'Gasto 2')

    def test_gasto_filter_category(self):
        response = self.client.get(reverse('gastos:lista_gastos'), {'categoria': 'Transporte'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gasto 2')
        self.assertNotContains(response, 'Gasto 1')
