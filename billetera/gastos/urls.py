from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from . import views
from .views import GastoViewSet

# Router para las rutas de la API REST
router = DefaultRouter()
router.register(r'gastos', GastoViewSet)

# Lista de URLS combinada
urlpatterns = [
    # Rutas de la API REST
    path('api/', include(router.urls)),  # Prefijo 'api/' para las rutas del router

    # Rutas para las vistas tradicionales
    path('', views.lista_gastos, name='lista_gastos'),
    path('crear/', views.crear_gasto, name='crear_gasto'),
    path('editar/<int:id>/', views.editar_gasto, name='editar_gasto'),
    path('eliminar/<int:id>/', views.eliminar_gasto, name='eliminar_gasto'),

    # Rutas para autenticación
    path('login/', auth_views.LoginView.as_view(template_name='gastos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', views.registro, name='registro'),
]
