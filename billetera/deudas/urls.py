from django.urls import path
from . import views

app_name = 'deudas'

urlpatterns = [
    path('', views.DeudaListView.as_view(), name='lista_deudas'),
    path('nueva/', views.DeudaCreateView.as_view(), name='crear_deuda'),
    path('<int:pk>/', views.DeudaDetailView.as_view(), name='detalle_deuda'),
    path('<int:pk>/editar/', views.DeudaUpdateView.as_view(), name='editar_deuda'),
    path('<int:deuda_id>/pago/nuevo/', views.PagoDeudaCreateView.as_view(), name='crear_pago'),
]
