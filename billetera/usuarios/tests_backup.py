import os
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch


class BackupEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('admin_backup')

    def test_requires_auth_or_token(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)

    @patch('usuarios.views.run_database_backup')
    def test_with_token_allows(self, mock_backup):
        mock_backup.return_value = {
            'engine': 'django.db.backends.sqlite3',
            'object_key': 'backups/db/test/sqlite-123.enc',
            'r2_url': 's3://bucket/backups/db/test/sqlite-123.enc',
            'retention_kept': 3,
        }
        os.environ['BACKUP_WEBHOOK_TOKEN'] = 'secret'
        resp = self.client.get(self.url, {'token': 'secret'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get('status'), 'ok')

    @patch('usuarios.views.run_database_backup')
    def test_staff_user_allows(self, mock_backup):
        mock_backup.return_value = {
            'engine': 'django.db.backends.sqlite3',
            'object_key': 'backups/db/test/sqlite-123.enc',
            'r2_url': 's3://bucket/backups/db/test/sqlite-123.enc',
            'retention_kept': 3,
        }
        staff = User.objects.create_user('admin', password='pass', is_staff=True)
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get('status'), 'ok')
