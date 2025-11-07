import os
from django.db.models.signals import post_save, post_migrate
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.conf import settings
from .models import PerfilUsuario


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    # Evitar AttributeError si el perfil aún no existe (caso raro en condiciones de carrera)
    if hasattr(instance, 'perfilusuario'):
        instance.perfilusuario.save()


_socialapp_bootstrapped = False  # bandera para evitar múltiples ejecuciones


@receiver(post_migrate)
def bootstrap_google_socialapp_signal(sender, app_config, **kwargs):
    """Crear/actualizar Site + SocialApp de Google en despliegues donde el comando de bootstrap no corre.

    Idempotente: si ya existe la SocialApp enlazada al Site activo, se actualiza client_id/secret sólo si cambiaron.
    Ejecuta solo cuando:
      - allauth.socialaccount está instalado
      - Se migró el app 'socialaccount' (para asegurar tablas) o 'sites'
      - Hay GOOGLE_OAUTH_CLIENT_ID y GOOGLE_OAUTH_CLIENT_SECRET definidos
    """
    global _socialapp_bootstrapped
    if _socialapp_bootstrapped:
        return

    # Verificar que socialaccount esté instalado
    if 'allauth.socialaccount' not in settings.INSTALLED_APPS:
        return

    # Ejecutar únicamente tras migrar 'socialaccount' (o 'sites' si socialaccount vendrá luego)
    if app_config.label not in {'socialaccount', 'sites'}:
        return

    client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    secret = os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET')
    if not (client_id and secret):
        return  # sin credenciales no hacemos nada

    try:
        from django.contrib.sites.models import Site
        from allauth.socialaccount.models import SocialApp
    except Exception:
        return  # módulos no disponibles aún

    # Determinar dominio: SITE_DOMAIN override o primer host válido
    site_id = getattr(settings, 'SITE_ID', 1)
    domain = os.getenv('SITE_DOMAIN')
    if not domain:
        for h in getattr(settings, 'ALLOWED_HOSTS', []):
            if h and not h.startswith('.'):
                domain = h
                break
    domain = domain or 'localhost'
    name = domain

    site, created_site = Site.objects.get_or_create(id=site_id, defaults={'domain': domain, 'name': name})
    changed = False
    if site.domain != domain:
        site.domain = domain
        changed = True
    if site.name != name:
        site.name = name
        changed = True
    if changed:
        site.save()

    app, created_app = SocialApp.objects.get_or_create(
        provider='google',
        defaults={'name': 'Google', 'client_id': client_id, 'secret': secret}
    )
    updated = False
    if app.client_id != client_id:
        app.client_id = client_id
        updated = True
    if app.secret != secret:
        app.secret = secret
        updated = True
    if updated:
        app.save()

    # Asociar sólo el Site activo
    app.sites.set([site])

    _socialapp_bootstrapped = True  # marcar para evitar repetición
