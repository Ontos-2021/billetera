from django.test import TestCase
from django.contrib.auth.models import User
from .models import PerfilUsuario


class PerfilUsuarioModelTest(TestCase):

    def setUp(self):
        # Crea un usuario y automáticamente se crea un perfil asociado
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.perfil = PerfilUsuario.objects.get(usuario=self.user)

    def test_crear_perfil_usuario(self):
        # En lugar de crear un nuevo perfil, simplemente verifica o modifica el existente
        self.perfil.direccion = 'Calle Falsa 123'
        self.perfil.telefono = '123456789'
        self.perfil.save()
        self.assertEqual(self.perfil.direccion, 'Calle Falsa 123')
        self.assertEqual(self.perfil.telefono, '123456789')

    def test_relacion_usuario_perfil(self):
        # Comprueba la relación entre el usuario y el perfil ya existente
        self.assertEqual(self.perfil.usuario.username, 'testuser')


from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario


class VistasUsuariosTest(TestCase):
    def setUp(self):
        # Configuración inicial antes de cada prueba
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.perfil = PerfilUsuario.objects.get(usuario=self.user)

        # URLs a probar
        self.editar_perfil_url = reverse('editar_perfil')
        self.registro_url = reverse('registro')
        self.login_url = reverse('login')

    def test_editar_perfil_view_GET(self):
        # Autenticar al usuario para poder acceder a la vista de editar perfil
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.editar_perfil_url)

        # Verificar que la respuesta sea exitosa (código 200)
        self.assertEqual(response.status_code, 200)
        # Verificar que se utiliza el template correcto
        self.assertTemplateUsed(response, 'usuarios/editar_perfil.html')
        # Verificar que el contexto contiene el perfil del usuario
        self.assertContains(response, 'Editar Perfil')

    def test_registro_view_GET(self):
        # Prueba para la vista de registro de usuario
        response = self.client.get(self.registro_url)

        # Verificar que la respuesta sea exitosa (código 200)
        self.assertEqual(response.status_code, 200)
        # Verificar que se utiliza el template correcto
        self.assertTemplateUsed(response, 'usuarios/registro.html')
        # Verificar que el contexto contiene el formulario de registro
        self.assertContains(response, 'Registrarse')

    def test_login_view_GET(self):
        # Prueba para la vista de registro de usuario
        response = self.client.get(self.login_url)

        # Verificar que la respuesta sea exitosa (código 200)
        self.assertEqual(response.status_code, 200)
        # Verificar que se utiliza el template correcto
        self.assertTemplateUsed(response, 'usuarios/login.html')
        # Verificar que el contexto contiene el formulario de registro
        self.assertContains(response, 'Registrarse')

    def test_editar_perfil_view_POST(self):
        # Autenticar al usuario para poder acceder a la vista de editar perfil
        self.client.login(username='testuser', password='password123')

        # Datos nuevos para actualizar el perfil
        data = {
            # Se podría chequear si guarda las imágenes
            'direccion': 'Nueva Direccion 456',
            'telefono': '987654321'
        }
        response = self.client.post(self.editar_perfil_url, data)

        # Verificar redirección después de actualizar el perfil
        self.assertEqual(response.status_code, 302)

        # Recargar el perfil desde la base de datos
        self.perfil.refresh_from_db()

        # Verificar que los datos se actualizaron correctamente
        self.assertEqual(self.perfil.direccion, 'Nueva Direccion 456')
        self.assertEqual(self.perfil.telefono, '987654321')

    def test_registro_view_POST(self):
        # Prueba para crear un usuario nuevo mediante la vista de registro
        data = {
            'username': 'newuser',
            'password1': 'newpassword123',
            'password2': 'newpassword123'
        }
        response = self.client.post(self.registro_url, data)

        # Verificar que el usuario se haya creado correctamente y se redirige
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
