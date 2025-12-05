import django_filters
from django import forms
from .models import Ingreso

class IngresoFilter(django_filters.FilterSet):
    descripcion = django_filters.CharFilter(lookup_expr='icontains', label='Descripción', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar...'}))
    categoria = django_filters.CharFilter(field_name='categoria', lookup_expr='icontains', label='Categoría', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Categoría'}))
    fecha_inicio = django_filters.DateFilter(field_name='fecha', lookup_expr='gte', label='Desde', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    fecha_fin = django_filters.DateFilter(field_name='fecha', lookup_expr='lte', label='Hasta', widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = Ingreso
        fields = ['descripcion', 'categoria', 'fecha_inicio', 'fecha_fin']
