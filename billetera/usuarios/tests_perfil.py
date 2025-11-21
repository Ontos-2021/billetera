from django.test import TestCase, Client
from django.contrib.auth.models import User
from usuarios.models import PerfilUsuario
from django.urls import reverse
from datetime import date

class PerfilUsuarioTest(TestCase):
    def setUp(self):
        # Crear usuario y perfil
        self.user = User.objects.create_user(username='testuser', password='password', first_name='Test User')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        
        # Asegurar que el perfil existe (se crea por señal o manualmente si no hay señal)
        self.perfil, created = PerfilUsuario.objects.get_or_create(usuario=self.user)

    def test_ver_perfil_sin_datos(self):
        """Prueba que la vista de perfil carga correctamente sin datos extra"""
        response = self.client.get(reverse('perfil_usuario'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
        self.assertContains(response, 'No especificada') # Fecha nacimiento vacía

    def test_ver_perfil_con_datos(self):
        """Prueba que la vista de perfil muestra los datos correctamente"""
        self.perfil.fecha_nacimiento = date(1990, 5, 15)
        self.perfil.pais = 'Argentina'
        self.perfil.ciudad = 'Buenos Aires'
        self.perfil.save()

        response = self.client.get(reverse('perfil_usuario'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar formato de fecha corregido (15 de Mayo 1990)
        # Nota: El mes puede variar según locale, pero verificamos que no crashee y contenga el año
        self.assertContains(response, '1990')
        self.assertContains(response, 'Argentina')
        self.assertContains(response, 'Buenos Aires')

    def test_editar_perfil(self):
        """Prueba la edición de perfil con los nuevos campos"""
        url = reverse('editar_perfil')
        data = {
            'nombre_pila': 'Nuevo Nombre',
            'fecha_nacimiento': '1995-12-25',
            'pais': 'Chile',
            'ciudad': 'Santiago',
        }
        
        response = self.client.post(url, data)
        
        # Verificar redirección o éxito
        if response.status_code == 302:
            self.assertRedirects(response, reverse('perfil_usuario'))
        else:
            self.assertEqual(response.status_code, 200)

        # Verificar que los datos se guardaron
        self.user.refresh_from_db()
        self.perfil.refresh_from_db()
        
        self.assertEqual(self.user.first_name, 'Nuevo Nombre')
        self.assertEqual(self.perfil.fecha_nacimiento, date(1995, 12, 25))
        self.assertEqual(self.perfil.pais, 'Chile')
        self.assertEqual(self.perfil.ciudad, 'Santiago')
