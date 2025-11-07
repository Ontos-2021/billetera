import os
from urllib.parse import urlparse
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = "Ensure Site and Google SocialApp exist and are linked (idempotent)."

    def _pick_domain(self) -> str:
        """
        Decide the Site.domain to use:
        1) SITE_DOMAIN env (host or URL)
        2) RENDER_EXTERNAL_URL / EXTERNAL_URL / KOYEB_APP_URL (URL)
        3) First host from ALLOWED_HOSTS
        4) Fallback: 'localhost'
        Returns host without scheme.
        """
        # 1) Explicit site domain
        site_domain = os.environ.get('SITE_DOMAIN')
        if site_domain:
            site_domain = site_domain.strip()
            if site_domain.startswith('http://') or site_domain.startswith('https://'):
                return urlparse(site_domain).netloc
            return site_domain

        # 2) Provider specific external URL envs
        ext = os.environ.get('RENDER_EXTERNAL_URL') or os.environ.get('EXTERNAL_URL') or os.environ.get('KOYEB_APP_URL')
        if ext:
            parsed = urlparse(ext)
            if parsed.netloc:
                return parsed.netloc

        # 3) ALLOWED_HOSTS
        ah = os.environ.get('ALLOWED_HOSTS', '')
        if ah:
            first = [x.strip() for x in ah.split(',') if x.strip()][0]
            if first.startswith('http://') or first.startswith('https://'):
                return urlparse(first).netloc or first
            return first

        # 4) default
        return 'localhost'

    def handle(self, *args, **opts):
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
        if not client_id or not secret:
            self.stderr.write('Missing GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET; skipping SocialApp bootstrap')
            return

        site_id = int(os.environ.get('SITE_ID', 1))
        domain = self._pick_domain()
        name = os.environ.get('SITE_NAME', domain)

        # Ensure Site exists and has correct domain/name
        site, created_site = Site.objects.get_or_create(id=site_id, defaults={'domain': domain, 'name': name})
        if not created_site:
            changed = False
            if site.domain != domain:
                site.domain = domain
                changed = True
            if site.name != name:
                site.name = name
                changed = True
            if changed:
                site.save()

        # Ensure SocialApp exists and linked to this Site
        app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={'name': 'Google', 'client_id': client_id, 'secret': secret}
        )
        if not created:
            # Update secrets idempotently
            updated = False
            if app.client_id != client_id:
                app.client_id = client_id
                updated = True
            if app.secret != secret:
                app.secret = secret
                updated = True
            if updated:
                app.save()
        else:
            app.save()

        # Link only the current site (avoid orphaned links)
        app.sites.set([site])

        self.stdout.write(self.style.SUCCESS(f'Bootstrap complete: Site(id={site.id}, domain={site.domain}) linked to Google SocialApp.'))
