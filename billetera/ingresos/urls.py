from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import IngresoViewSet

router = DefaultRouter()
router.register(r'', IngresoViewSet, basename='ingreso')

app_name = 'ingresos'

urlpatterns = [
    path('api/', include(router.urls)),
    path('', views.lista_ingresos, name='lista_ingresos'),
    path('crear/', views.crear_ingreso, name='crear_ingreso'),
    path('editar/<int:ingreso_id>/', views.editar_ingreso, name='editar_ingreso'),
    path('eliminar/<int:ingreso_id>/', views.eliminar_ingreso, name='eliminar_ingreso'),
]
