from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from decimal import Decimal

from gastos.models import Compra, Gasto, Moneda, Categoria
from cuentas.models import Cuenta, TipoCuenta


class EditarCompraGlobalTestCase(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')

        self.moneda, _ = Moneda.objects.get_or_create(codigo='ARS', defaults={'nombre': 'Peso', 'simbolo': '$'})
        self.categoria, _ = Categoria.objects.get_or_create(nombre='Comida')
        self.tipo_cuenta, _ = TipoCuenta.objects.get_or_create(nombre='Efectivo')
        self.cuenta1 = Cuenta.objects.create(
            usuario=self.usuario,
            nombre='Billetera',
            tipo=self.tipo_cuenta,
            moneda=self.moneda,
            saldo_inicial=Decimal('10000.00')
        )
        self.cuenta2 = Cuenta.objects.create(
            usuario=self.usuario,
            nombre='Tarjeta',
            tipo=self.tipo_cuenta,
            moneda=self.moneda,
            saldo_inicial=Decimal('0.00')
        )

        self.compra = Compra.objects.create(
            usuario=self.usuario,
            fecha=timezone.now(),
            lugar='Supermercado Test',
            cuenta=self.cuenta1,
            moneda=self.moneda,
        )
        self.gasto1 = Gasto.objects.create(
            usuario=self.usuario,
            descripcion='Leche',
            monto=Decimal('150.00'),
            cantidad=1,
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta1,
            lugar=self.compra.lugar,
            fecha=self.compra.fecha,
            compra=self.compra,
        )
        self.gasto2 = Gasto.objects.create(
            usuario=self.usuario,
            descripcion='Pan',
            monto=Decimal('80.00'),
            cantidad=1,
            categoria=self.categoria,
            moneda=self.moneda,
            cuenta=self.cuenta1,
            lugar=self.compra.lugar,
            fecha=self.compra.fecha,
            compra=self.compra,
        )

    def test_editar_compra_updates_all_items(self):
        url = reverse('gastos:editar_compra', args=[self.compra.pk])
        new_fecha_str = '2025-12-06T09:15'
        data = {
            'fecha': new_fecha_str,
            'lugar': 'Nuevo Comercio',
            'cuenta': self.cuenta2.id,
            'moneda': self.moneda.id,
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        self.compra.refresh_from_db()
        self.assertEqual(self.compra.lugar, 'Nuevo Comercio')
        self.assertEqual(self.compra.cuenta, self.cuenta2)

        self.gasto1.refresh_from_db()
        self.gasto2.refresh_from_db()
        self.assertEqual(self.gasto1.lugar, 'Nuevo Comercio')
        self.assertEqual(self.gasto2.lugar, 'Nuevo Comercio')
        self.assertEqual(self.gasto1.cuenta, self.cuenta2)
        self.assertEqual(self.gasto2.cuenta, self.cuenta2)

        # Ensure date propagated (compare formatted local datetime)
        self.assertEqual(timezone.localtime(self.gasto1.fecha).strftime('%Y-%m-%dT%H:%M'), new_fecha_str)
        self.assertEqual(timezone.localtime(self.gasto2.fecha).strftime('%Y-%m-%dT%H:%M'), new_fecha_str)
