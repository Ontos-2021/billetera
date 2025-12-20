from django.urls import path

import usuarios.views
from . import views
from django.contrib.auth import views as auth_views
from usuarios.views import registro

app_name = 'usuarios'

urlpatterns = [
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('perfil/editar', views.editar_perfil, name='editar_perfil'),

    # Rutas para autenticación
    path('login/', auth_views.LoginView.as_view(template_name='usuarios/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', usuarios.views.registro,  name='registro'),
    path('reporte/pdf/', usuarios.views.exportar_reporte_pdf, name='exportar_reporte_pdf'),
    path('planes/', views.lista_planes, name='lista_planes'),
    path('procesar_pago/<int:plan_id>/', views.procesar_pago, name='procesar_pago'),
    path('pago_exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('pago_fallido/', views.pago_fallido, name='pago_fallido'),
    path('webhook/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
]
