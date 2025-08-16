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
+
-from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from gastos.models import Gasto
from ingresos.models import Ingreso

@login_required
def transactions_combined(request):
    # Combine ingresos and gastos for the authenticated user (or all if superuser)
    if request.user.is_superuser:
        gastos_qs = Gasto.objects.all()
        ingresos_qs = Ingreso.objects.all()
    else:
        gastos_qs = Gasto.objects.filter(usuario=request.user)
        ingresos_qs = Ingreso.objects.filter(usuario=request.user)

    gastos_list = [{
        'id': f'gasto-{g.id}',
        'tipo_registro': 'gasto',
        'descripcion': g.descripcion,
        'lugar': g.lugar,
        'monto': float(g.monto),
        'fecha': g.fecha.isoformat(),
        'categoria': g.categoria.nombre if g.categoria else None,
        'moneda': g.moneda.codigo if g.moneda else None,
    } for g in gastos_qs]

    ingresos_list = [{
        'id': f'ingreso-{i.id}',
        'tipo_registro': 'ingreso',
        'descripcion': i.descripcion,
        'monto': float(i.monto),
        'fecha': i.fecha.isoformat(),
        'categoria': i.categoria.nombre if i.categoria else None,
        'moneda': i.moneda.codigo if i.moneda else None,
    } for i in ingresos_qs]

    combined = gastos_list + ingresos_list
    # Sort descending by fecha
    combined.sort(key=lambda x: x['fecha'], reverse=True)
    return JsonResponse({'results': combined})
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

from usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('gastos/', include('gastos.urls')),  # Incluye las URLs de la app 'gastos' para las vistas HTML
    path('usuarios/', include('usuarios.urls')),
    path('ingresos/', include('ingresos.urls')),
    path('api/transactions/', transactions_combined, name='transactions_combined'),
    path('health/', lambda r: JsonResponse({'status': 'ok'})),
    path('', usuarios_views.inicio, name='inicio_usuarios'),  # Esta es la nueva línea para la página de inicio
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # También se puede servir en producción de esta manera cuando uses Railway Disk.
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]