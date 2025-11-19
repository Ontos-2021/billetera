from django.test import TestCase
from django.contrib.auth.models import User
from .models import Moneda, CategoriaIngreso, Ingreso
from django.urls import reverse
from django.utils import timezone


class IngresoModelTestCase(TestCase):
    def setUp(self):
        # Crear usuario para las pruebas
        self.usuario = User.objects.create_user(username='testuser', password='12345')

        # Crear algunas monedas si no existen
        self.moneda_usd, created = Moneda.objects.get_or_create(nombre='Dólar Estadounidense', codigo='USD',
                                                                simbolo='$')
        self.moneda_eur, created = Moneda.objects.get_or_create(nombre='Euro', codigo='EUR', simbolo='€')

        # Crear algunas categorías de ingresos si no existen
        self.categoria_salario, created = CategoriaIngreso.objects.get_or_create(nombre='Salario')
        self.categoria_freelance, created = CategoriaIngreso.objects.get_or_create(nombre='Freelance')

        # Crear ingreso de ejemplo
        self.ingreso = Ingreso.objects.create(
            usuario=self.usuario,
            descripcion='Pago por proyecto freelance',
            monto=500.00,
            moneda=self.moneda_usd,
            categoria=self.categoria_freelance,
            fecha=timezone.now()
        )

    def test_crear_ingreso(self):
        # Verificar que el ingreso se ha creado correctamente
        ingreso = Ingreso.objects.get(id=self.ingreso.id)
        self.assertEqual(ingreso.descripcion, 'Pago por proyecto freelance')
        self.assertEqual(ingreso.monto, 500.00)
        self.assertEqual(ingreso.moneda.codigo, 'USD')
        self.assertEqual(ingreso.categoria.nombre, 'Freelance')
        self.assertEqual(ingreso.usuario.username, 'testuser')

    def test_str_ingreso(self):
        # Verificar que el método __str__ devuelve el formato correcto
        self.assertEqual(str(self.ingreso), 'Pago por proyecto freelance - 500.0 $')

    def test_ingreso_sin_moneda(self):
        # Crear ingreso sin especificar moneda
        ingreso_sin_moneda = Ingreso.objects.create(
            usuario=self.usuario,
            descripcion='Ingreso sin moneda',
            monto=300.00,
            categoria=self.categoria_salario,
            fecha=timezone.now()
        )
        self.assertIsNone(ingreso_sin_moneda.moneda)

    def test_crear_categoria_ingreso(self):
        # Verificar que la categoría de ingreso se ha creado correctamente
        categoria = CategoriaIngreso.objects.get(nombre='Salario')
        self.assertEqual(categoria.nombre, 'Salario')

    def test_crear_moneda(self):
        # Verificar que la moneda se ha creado correctamente
        moneda = Moneda.objects.get(codigo='EUR')
        self.assertEqual(moneda.nombre, 'Euro')
        self.assertEqual(moneda.simbolo, '€')

    # Test para que no se pueda crear un ingreso negativo desde la vista
    def test_no_crear_ingreso_negativo(self):
        # Iniciar sesión como usuario
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('ingresos:crear_ingreso'), {
            'descripcion': 'Ingreso negativo',
            'monto': '-100.00',
            'moneda': self.moneda_usd.id,
            'categoria': self.categoria_salario.id,
            'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M')
        })

        # Verificar que el ingreso no fue creado
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ingreso.objects.filter(descripcion='Ingreso negativo').exists())

    # Test para que usuario pueda editar un ingreso desde la vista

    def test_usuario_puede_editar_ingreso(self):
        # Iniciar sesión como usuario
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('ingresos:editar_ingreso', kwargs={'ingreso_id': self.ingreso.id}), {
            'descripcion': 'Pago por proyecto freelance',
            'monto': '500.00',
            'moneda': self.moneda_usd.id,
            'categoria': self.categoria_freelance.id,
            'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M')
        })

        # Verificar que el ingreso ha sido editado
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Ingreso.objects.filter(descripcion='Pago por proyecto freelance', usuario=self.usuario).exists())

    # Test para que usuario pueda eliminar un ingreso desde la vista
    def test_usuario_puede_eliminar_ingreso(self):
        # Iniciar sesión como usuario
        login_successful = self.client.login(username='testuser', password='12345')
        self.assertTrue(login_successful, "No se pudo iniciar sesión con el usuario proporcionado.")

        # Asegurarse de que el ingreso existe antes de intentar eliminarlo
        self.assertTrue(Ingreso.objects.filter(id=self.ingreso.id).exists(),
                        "El ingreso no existe antes de intentar eliminarlo.")

        # Realizar la petición GET para acceder a la vista de confirmación de eliminación
        response_get = self.client.get(reverse('ingresos:eliminar_ingreso', kwargs={'ingreso_id': self.ingreso.id}))

        # Verificar si la solicitud GET fue exitosa (código de estado 200)
        if response_get.status_code == 302:
            # Si fue redirigido, mostrar mensaje para entender el motivo
            redirect_url = response_get.headers.get('Location')
            self.fail(
                f"La solicitud GET fue redirigida a {redirect_url}. Asegúrate de que el usuario tenga permisos adecuados.")

        self.assertEqual(response_get.status_code, 200, "La vista de confirmación no se pudo cargar correctamente.")

        # Realizar la petición POST para confirmar la eliminación del ingreso
        response_post = self.client.post(reverse('ingresos:eliminar_ingreso', kwargs={'ingreso_id': self.ingreso.id}))

        # Verificar que el ingreso ha sido eliminado
        self.assertEqual(response_post.status_code, 302,
                         "La solicitud POST no redirigió correctamente después de eliminar.")
        self.assertFalse(Ingreso.objects.filter(id=self.ingreso.id).exists(),
                         "El ingreso no fue eliminado correctamente.")

        # Verificar que la redirección es hacia la vista de lista de ingresos
        self.assertRedirects(response_post, reverse('ingresos:lista_ingresos'))

