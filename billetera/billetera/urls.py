"""
URL configuration for billetera project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

from usuarios import views as usuarios_views
from django.urls import include, path as dj_path
from usuarios.views import ProfileMe
from usuarios.social import GoogleLogin
from usuarios.jwt_views import WalletTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

urlpatterns = [
    # Backup manual (token o staff)
    path('admin/tools/backup', usuarios_views.trigger_backup, name='admin_backup'),
    path('admin/', admin.site.urls),
    # Allauth (server-side templates based login flow)
    path('accounts/', include('allauth.urls')),
    # Auth endpoints (dj-rest-auth + allauth)
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    # Note: dj-rest-auth may not provide a social_urls module in all versions; we expose
    # specific social endpoints below (e.g. Google) instead.
    # Social code exchange for Google (PKCE code flow)
    path('auth/social/google/', GoogleLogin.as_view(), name='google_login'),
    path('gastos/', include('gastos.urls')),  # Incluye las URLs de la app 'gastos' para las vistas HTML
    path('usuarios/', include('usuarios.urls')),
    path('ingresos/', include('ingresos.urls')),
    path('cuentas/', include('cuentas.urls')),
    path('deudas/', include('deudas.urls')),
    path('', usuarios_views.inicio, name='inicio_usuarios'),  # Esta es la nueva línea para la página de inicio
    path('api/me/', ProfileMe.as_view(), name='me'),
    # JWT token endpoints (SimpleJWT custom view)
    dj_path('api/token/', WalletTokenObtainPairView.as_view(), name='token_obtain_pair'),
    dj_path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    dj_path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # También se puede servir en producción de esta manera cuando uses Railway Disk.
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]