from django.conf import settings
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.models import SocialAccount
from django.http import JsonResponse


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    callback_url = getattr(settings, 'GOOGLE_REDIRECT_URI', None)

    def post(self, request, *args, **kwargs):
        """
        After dj-rest-auth / allauth completes the social login exchange, perform
        a lightweight validation on the returned social account extra_data to
        ensure email_verified is True and (optionally) the hosted domain matches.
        """
        resp = super().post(request, *args, **kwargs)

        try:
            if resp.status_code == 200 and hasattr(resp, 'data'):
                user_data = resp.data.get('user') or {}
                email = user_data.get('email')
                if email:
                    # try to get social account for this user and provider
                    sa = SocialAccount.objects.filter(provider='google', user__email=email).first()
                    if sa:
                        extra = sa.extra_data or {}
                        # email_verified
                        if extra.get('email_verified') is not True:
                            return JsonResponse({'detail': 'Google account email is not verified.'}, status=400)
                        # optional hosted domain check
                        hd_allowed = getattr(settings, 'GOOGLE_HOSTED_DOMAIN', None)
                        if hd_allowed:
                            hd = extra.get('hd')
                            if hd != hd_allowed:
                                return JsonResponse({'detail': 'Hosted domain (hd) mismatch.'}, status=400)
        except Exception:
            # don't fail the whole flow on our check; just return original resp
            return resp

        return resp
