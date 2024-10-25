from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio_usuarios, name='inicio_usuarios'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
]
