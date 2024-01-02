from django.urls import path
from . import views

urlpatterns = [
    path('gastos/', views.lista_gastos, name='lista_gastos'),
    # Agrega aquí las URLs para las otras vistas (crear, editar, eliminar).
]
