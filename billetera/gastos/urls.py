from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_gastos, name='lista_gastos'),
    path('crear/', views.crear_gasto, name='crear_gasto'),
    path('editar/<int:id>/', views.editar_gasto, name='editar_gasto'),
    path('eliminar/<int:id>/', views.eliminar_gasto, name='eliminar_gasto'),
]
