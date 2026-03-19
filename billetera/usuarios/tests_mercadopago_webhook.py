import hashlib
import hmac
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import Plan, Suscripcion


class MercadoPagoWebhookTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mp-user',
            email='mp@example.com',
            password='safe-pass-123',
        )
        self.plan = Plan.objects.create(nombre=Plan.PRO, precio='9.99')
        self.url = reverse('usuarios:webhook_mercadopago')
        self.secret = 'webhook-secret'
        self.request_id = 'req-123'
        self.payment_id = '987654321'

    def _signature(self):
        ts = '1704908010'
        manifest = f'id:{self.payment_id.lower()};request-id:{self.request_id};ts:{ts};'
        digest = hmac.new(
            self.secret.encode('utf-8'),
            manifest.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        return f'ts={ts},v1={digest}'

    def _headers(self, signature=None):
        return {
            'HTTP_X_SIGNATURE': signature or self._signature(),
            'HTTP_X_REQUEST_ID': self.request_id,
        }

    @patch.dict('os.environ', {'MERCADOPAGO_WEBHOOK_SECRET': 'webhook-secret', 'MERCADOPAGO_ACCESS_TOKEN': 'token'}, clear=False)
    def test_rejects_invalid_signature(self):
        response = self.client.post(
            f'{self.url}?topic=payment&data.id={self.payment_id}',
            data=json.dumps({'type': 'payment', 'data': {'id': self.payment_id}}),
            content_type='application/json',
            **self._headers(signature='ts=1704908010,v1=bad-signature')
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Suscripcion.objects.exists())

    @patch.dict('os.environ', {'MERCADOPAGO_WEBHOOK_SECRET': 'webhook-secret', 'MERCADOPAGO_ACCESS_TOKEN': 'token'}, clear=False)
    @patch('usuarios.views.mercadopago')
    def test_approved_payment_creates_subscription(self, mock_mercadopago):
        payment_client = Mock()
        payment_client.get.return_value = {
            'response': {
                'status': 'approved',
                'external_reference': f'{self.user.id}_{self.plan.id}',
            }
        }
        sdk = Mock()
        sdk.payment.return_value = payment_client
        mock_mercadopago.SDK.return_value = sdk

        response = self.client.post(
            f'{self.url}?topic=payment&data.id={self.payment_id}',
            data=json.dumps({'type': 'payment', 'data': {'id': self.payment_id}}),
            content_type='application/json',
            **self._headers()
        )

        self.assertEqual(response.status_code, 200)
        subscription = Suscripcion.objects.get(usuario=self.user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.external_id, self.payment_id)
        self.assertTrue(subscription.activo)

    @patch.dict('os.environ', {'MERCADOPAGO_WEBHOOK_SECRET': 'webhook-secret', 'MERCADOPAGO_ACCESS_TOKEN': 'token'}, clear=False)
    @patch('usuarios.views.mercadopago')
    @patch('usuarios.views.timezone.now')
    def test_replayed_payment_does_not_extend_subscription(self, mock_now, mock_mercadopago):
        first_now = timezone.make_aware(datetime(2026, 3, 19, 10, 0, 0))
        second_now = first_now + timedelta(days=3)
        mock_now.side_effect = [first_now, second_now]

        payment_client = Mock()
        payment_client.get.return_value = {
            'response': {
                'status': 'approved',
                'external_reference': f'{self.user.id}_{self.plan.id}',
            }
        }
        sdk = Mock()
        sdk.payment.return_value = payment_client
        mock_mercadopago.SDK.return_value = sdk

        for _ in range(2):
            response = self.client.post(
                f'{self.url}?topic=payment&data.id={self.payment_id}',
                data=json.dumps({'type': 'payment', 'data': {'id': self.payment_id}}),
                content_type='application/json',
                **self._headers()
            )
            self.assertEqual(response.status_code, 200)

        subscription = Suscripcion.objects.get(usuario=self.user)
        self.assertEqual(subscription.fecha_inicio, first_now)
        self.assertEqual(subscription.fecha_fin, first_now + timedelta(days=30))
        self.assertEqual(Suscripcion.objects.count(), 1)