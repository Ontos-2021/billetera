from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Gasto, Categoria, Moneda
from decimal import Decimal


class GastosTestCase(TestCase):
    def setUp(self):
        # Crear un usuario normal y un superusuario
        self.usuario = User.objects.create_user(username='usuario', password='password123')
        self.superusuario = User.objects.create_superuser(username='admin', password='admin123')

        # Intentar obtener la moneda, si no existe, crearla
        self.moneda, _ = Moneda.objects.get_or_create(nombre='Peso Argentino', codigo='ARS', simbolo='$')

        # Intentar obtener la categoría, si no existe, crearla
        self.categoria, _ = Categoria.objects.get_or_create(nombre='Transporte')

        # Crear un gasto de ejemplo asociado al usuario normal
        self.gasto = Gasto.objects.create(
            usuario=self.usuario,
            descripcion='Taxi',
            monto=Decimal('500.00'),
            moneda=self.moneda,
            categoria=self.categoria
        )

        # Cliente para simular solicitudes
        self.client = Client()

    def test_admin_puede_editar_gasto(self):
        # Iniciar sesión como superusuario
        self.client.login(username='admin', password='admin123')
        response = self.client.post(reverse('gastos:editar_gasto', args=[self.gasto.id]), {
            'descripcion': 'Taxi Actualizado',
            'monto': '600.00',
            'moneda': self.moneda.id,
            'categoria': self.categoria.id
        })

        # Verificar redirección y cambios
        self.assertEqual(response.status_code, 302)
        self.gasto.refresh_from_db()
        self.assertEqual(self.gasto.descripcion, 'Taxi Actualizado')
        self.assertEqual(self.gasto.monto, Decimal('600.00'))

    def test_admin_puede_eliminar_gasto(self):
        # Iniciar sesión como superusuario
        self.client.login(username='admin', password='admin123')
        response = self.client.post(reverse('gastos:eliminar_gasto', args=[self.gasto.id]))

        # Verificar que el gasto ha sido eliminado
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Gasto.objects.filter(id=self.gasto.id).exists())

    def test_usuario_no_puede_gastar_si_no_tiene_fondos(self):
        # Crear un gasto mayor al saldo del usuario (en este ejemplo, asumimos que no tiene fondos disponibles)
        self.client.login(username='usuario', password='password123')
        response = self.client.post(reverse('gastos:crear_gasto'), {
            'descripcion': 'Compra sin fondos',
            'monto': '10000.00',  # Monto grande que el usuario no debería poder gastar
            'moneda': self.moneda.id,
            'categoria': self.categoria.id
        })

        # Verificar que el gasto no fue creado
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No tienes suficiente saldo para realizar este gasto')
        self.assertEqual(Gasto.objects.filter(descripcion='Compra sin fondos').count(), 0)

    def test_usuario_puede_crear_gasto(self):
        # Iniciar sesión como usuario
        self.client.login(username='usuario', password='password123')
        response = self.client.post(reverse('gastos:crear_gasto'), {
            'descripcion': 'Cine',
            'monto': '300.00',
            'moneda': self.moneda.id,
            'categoria': self.categoria.id
        })

        # Verificar que el gasto ha sido creado
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Gasto.objects.filter(descripcion='Cine', usuario=self.usuario).exists())

    def test_usuario_puede_eliminar_gasto(self):
        # Iniciar sesión como usuario
        self.client.login(username='usuario', password='password123')
        response = self.client.post(reverse('gastos:eliminar_gasto', kwargs={'id': self.gasto.id}))

        # Verificar que el gasto ha sido eliminado
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Gasto.objects.filter(id=self.gasto.id).exists())

    # Test para usuario que pueda editar un gasto desde la vista
    def test_usuario_puede_editar_gasto(self):
        # Iniciar sesión como usuario
        self.client.login(username='usuario', password='password123')
        response = self.client.post(reverse('gastos:editar_gasto', kwargs={'id': self.gasto.id}), {
            'descripcion': 'Cine',
            'monto': '300.00',
            'moneda': self.moneda.id,
            'categoria': self.categoria.id
        })

        # Verificar que el gasto ha sido editado
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Gasto.objects.filter(descripcion='Cine', usuario=self.usuario).exists())
