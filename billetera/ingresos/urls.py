from django.urls import path
from . import views

app_name = 'ingresos'

urlpatterns = [
    path('', views.lista_ingresos, name='lista_ingresos'),
    path('crear/', views.crear_ingreso, name='crear_ingreso'),
    path('editar/<int:ingreso_id>/', views.editar_ingreso, name='editar_ingreso'),
    path('eliminar/<int:ingreso_id>/', views.eliminar_ingreso, name='eliminar_ingreso'),
]
