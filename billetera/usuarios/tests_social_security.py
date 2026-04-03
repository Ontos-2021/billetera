import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import RequestFactory, SimpleTestCase, override_settings

from usuarios.social import GoogleLogin


class GoogleLoginSecurityTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @patch('usuarios.social.SocialAccount.objects.filter')
    @patch('usuarios.social.SocialLoginView.post')
    def test_rejects_unverified_google_email(self, mock_super_post, mock_filter):
        mock_super_post.return_value = SimpleNamespace(
            status_code=200,
            data={'user': {'email': 'user@example.com'}},
        )
        queryset = Mock()
        queryset.first.return_value = SimpleNamespace(extra_data={'email_verified': False})
        mock_filter.return_value = queryset

        response = GoogleLogin().post(self.factory.post('/auth/social/google/'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'detail': 'Google account email is not verified.'})

    @override_settings(GOOGLE_HOSTED_DOMAIN='company.com')
    @patch('usuarios.social.SocialAccount.objects.filter')
    @patch('usuarios.social.SocialLoginView.post')
    def test_rejects_hosted_domain_mismatch(self, mock_super_post, mock_filter):
        mock_super_post.return_value = SimpleNamespace(
            status_code=200,
            data={'user': {'email': 'user@example.com'}},
        )
        queryset = Mock()
        queryset.first.return_value = SimpleNamespace(extra_data={'email_verified': True, 'hd': 'other.com'})
        mock_filter.return_value = queryset

        response = GoogleLogin().post(self.factory.post('/auth/social/google/'))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.content), {'detail': 'Hosted domain (hd) mismatch.'})

    @patch('usuarios.social.SocialAccount.objects.filter')
    @patch('usuarios.social.SocialLoginView.post')
    def test_returns_original_response_when_google_claims_are_valid(self, mock_super_post, mock_filter):
        original_response = SimpleNamespace(
            status_code=200,
            data={'user': {'email': 'user@example.com'}},
        )
        mock_super_post.return_value = original_response
        queryset = Mock()
        queryset.first.return_value = SimpleNamespace(extra_data={'email_verified': True})
        mock_filter.return_value = queryset

        response = GoogleLogin().post(self.factory.post('/auth/social/google/'))

        self.assertIs(response, original_response)