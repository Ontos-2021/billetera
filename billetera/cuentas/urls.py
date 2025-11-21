from django.urls import path
from . import views

app_name = 'cuentas'

urlpatterns = [
    path('', views.lista_cuentas, name='lista_cuentas'),
    path('crear/', views.crear_cuenta, name='crear_cuenta'),
    path('editar/<int:pk>/', views.editar_cuenta, name='editar_cuenta'),
    path('eliminar/<int:pk>/', views.eliminar_cuenta, name='eliminar_cuenta'),
    path('ajustar/<int:pk>/', views.ajustar_saldo, name='ajustar_saldo'),
]