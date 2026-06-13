from django.test import TestCase
from django.urls import reverse

class HealthCheckTests(TestCase):
    def test_healthz_returns_200_and_json(self):
        url = reverse('health_check_healthz')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get('status'), 'healthy')
        self.assertEqual(resp.json().get('database'), 'healthy')
        self.assertIn('timestamp', resp.json())

    def test_health_slash_returns_200_and_json(self):
        url = reverse('health_check')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get('status'), 'healthy')
