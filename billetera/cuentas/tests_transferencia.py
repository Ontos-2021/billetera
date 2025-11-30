from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from cuentas.models import Cuenta, TipoCuenta, TransferenciaCuenta
from gastos.models import Moneda as GastoMoneda


class TransferenciaCuentaViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='transfer_tester', password='secret123')
        self.client = Client()
        self.client.login(username='transfer_tester', password='secret123')

        self.moneda_ars, _ = GastoMoneda.objects.get_or_create(
            codigo='ARS', defaults={'nombre': 'Peso Argentino', 'simbolo': '$'}
        )
        self.moneda_usd, _ = GastoMoneda.objects.get_or_create(
            codigo='USD', defaults={'nombre': 'Dólar', 'simbolo': 'U$S'}
        )

        self.tipo, _ = TipoCuenta.objects.get_or_create(nombre='Banco')

        self.cuenta_pesos = Cuenta.objects.create(
            usuario=self.user,
            nombre='Cuenta ARS',
            tipo=self.tipo,
            saldo_inicial=Decimal('1000.00'),
            moneda=self.moneda_ars,
        )
        self.cuenta_dolares = Cuenta.objects.create(
            usuario=self.user,
            nombre='Cuenta USD',
            tipo=self.tipo,
            saldo_inicial=Decimal('0.00'),
            moneda=self.moneda_usd,
        )

        self.url = reverse('cuentas:transferir_cuentas')

    def test_transfer_creates_records_and_converts_amount(self):
        response = self.client.post(self.url, {
            'cuenta_origen': self.cuenta_pesos.id,
            'cuenta_destino': self.cuenta_dolares.id,
            'monto_origen': '100.00',
            'tasa_manual': '0.50',
            'monto_destino': '',
            'nota': 'Extracción a efectivo',
        })

        self.assertRedirects(response, reverse('inicio_usuarios'))
        self.assertEqual(TransferenciaCuenta.objects.count(), 1)
        transferencia = TransferenciaCuenta.objects.first()
        self.assertEqual(transferencia.cuenta_origen, self.cuenta_pesos)
        self.assertEqual(transferencia.cuenta_destino, self.cuenta_dolares)
        self.assertEqual(transferencia.monto_origen, Decimal('100.00'))
        self.assertEqual(transferencia.monto_destino, Decimal('50.00'))
        self.assertEqual(transferencia.tasa_manual, Decimal('0.500000'))
        self.assertEqual(transferencia.nota, 'Extracción a efectivo')
        self.assertIsNotNone(transferencia.gasto)
        self.assertIsNotNone(transferencia.ingreso)
        self.assertEqual(transferencia.gasto.monto, Decimal('100.00'))
        self.assertEqual(transferencia.ingreso.monto, Decimal('50.00'))

    def test_transfer_same_account_is_invalid(self):
        response = self.client.post(self.url, {
            'cuenta_origen': self.cuenta_pesos.id,
            'cuenta_destino': self.cuenta_pesos.id,
            'monto_origen': '10.00',
            'tasa_manual': '1.00',
            'monto_destino': '10.00',
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('cuenta_destino', form.errors)
        self.assertIn('Selecciona una cuenta diferente', form.errors['cuenta_destino'][0])
        self.assertEqual(TransferenciaCuenta.objects.count(), 0)
