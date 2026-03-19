from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class ApiSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='api-user',
            email='api@example.com',
            password='s3cure-pass-123',
        )

    def test_token_obtain_pair_is_public(self):
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'username': self.user.username, 'password': 's3cure-pass-123'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())

    def test_me_endpoint_requires_authentication(self):
        response = self.client.get(reverse('me'))

        self.assertIn(response.status_code, (401, 403))

    def test_gastos_api_requires_authentication(self):
        response = self.client.get('/gastos/api/')

        self.assertIn(response.status_code, (401, 403))