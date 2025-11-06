import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = "Create or update Google SocialApp from env vars."

    def handle(self, *args, **opts):
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        if not client_id or not secret:
            self.stderr.write('Missing GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET')
            return

        site, _ = Site.objects.get_or_create(id=1, defaults={'domain': 'localhost', 'name': 'localhost'})
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={'name': 'Google', 'client_id': client_id, 'secret': secret}
        )
        if not created:
            app.client_id = client_id
            app.secret = secret
        app.save()
        app.sites.add(site)
        self.stdout.write(self.style.SUCCESS('Google SocialApp ready.'))
