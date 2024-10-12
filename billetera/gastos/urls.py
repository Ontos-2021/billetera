from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.lista_gastos, name='lista_gastos'),
    path('crear/', views.crear_gasto, name='crear_gasto'),
    path('editar/<int:id>/', views.editar_gasto, name='editar_gasto'),
    path('eliminar/<int:id>/', views.eliminar_gasto, name='eliminar_gasto'),

    # Rutas para autenticación
    path('login/', auth_views.LoginView.as_view(template_name='gastos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', views.registro, name='registro'),  # Vamos a crear esta vista
]
