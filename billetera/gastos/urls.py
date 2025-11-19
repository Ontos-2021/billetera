from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import GastoViewSet

# Router para las rutas de la API REST
router = DefaultRouter()
router.register(r'', GastoViewSet, basename='gasto')

app_name = 'gastos'

# Lista de URLS combinada
urlpatterns = [
    # Rutas de la API REST
    path('api/', include(router.urls)),  # Prefijo 'api/' para las rutas del router

    # Rutas para las vistas tradicionales
    path('', views.lista_gastos, name='lista_gastos'),
    path('crear/', views.crear_gasto, name='crear_gasto'),
    path('compra-global/', views.compra_global, name='compra_global'),
    path('editar/<int:id>/', views.editar_gasto, name='editar_gasto'),
    path('eliminar/<int:id>/', views.eliminar_gasto, name='eliminar_gasto'),
]
