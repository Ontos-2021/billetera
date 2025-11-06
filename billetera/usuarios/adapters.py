import os
from django.conf import settings
from django.core.exceptions import PermissionDenied
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Extra validation when logging in via Google through the server-side (templates) flow.
    Blocks login if email is not verified or if hosted domain is restricted and doesn't match.
    """

    def pre_social_login(self, request, sociallogin):
        # extra_data comes from Google's userinfo and id_token
        data = (sociallogin.account.extra_data or {})
        email_verified = data.get('email_verified', True)
        if not email_verified:
            raise PermissionDenied('Tu email de Google no está verificado.')

        # Optional hosted domain restriction
        hosted_domain = getattr(settings, 'GOOGLE_HOSTED_DOMAIN', None) or os.getenv('GOOGLE_HOSTED_DOMAIN')
        if hosted_domain:
            hd_claim = data.get('hd')
            if not hd_claim or hd_claim.lower() != hosted_domain.lower():
                raise PermissionDenied('Tu cuenta de Google no pertenece al dominio permitido.')
