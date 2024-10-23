from django.shortcuts import render, redirect, get_object_or_404
from .models import Gasto
from .forms import GastoForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions
from .serializers import GastoSerializer
from .permissions import IsAdminOrReadOwnOnly


# Registro de usuario
def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('lista_gastos')
    else:
        form = UserCreationForm()
    return render(request, 'gastos/registro.html', {'form': form})


# Función para obtener los gastos filtrados por usuario o superusuario
def obtener_gastos(request):
    if request.user.is_superuser:
        return Gasto.objects.all().order_by('-fecha')
    return Gasto.objects.filter(usuario=request.user).order_by('-fecha')


# Lista de gastos
@login_required
def lista_gastos(request):
    gastos = obtener_gastos(request)
    return render(request, 'gastos/lista_gastos.html', {'gastos': gastos})


# Crear gasto
@login_required
def crear_gasto(request):
    if request.method == 'POST':
        form = GastoForm(request.POST)
        if form.is_valid():
            gasto = form.save(commit=False)
            gasto.usuario = request.user  # Asocia el gasto con el usuario autenticado
            gasto.save()
            return redirect('lista_gastos')
    else:
        form = GastoForm()
    return render(request, 'gastos/crear_gasto.html', {'form': form})


# Editar gasto
@login_required
def editar_gasto(request, id):
    gasto = get_object_or_404(Gasto, id=id, usuario=request.user if not request.user.is_superuser else None)
    if request.method == 'POST':
        form = GastoForm(request.POST, instance=gasto)
        if form.is_valid():
            form.save()
            return redirect('lista_gastos')
    else:
        form = GastoForm(instance=gasto)
    return render(request, 'gastos/editar_gasto.html', {'form': form})


# Eliminar gasto
@login_required
def eliminar_gasto(request, id):
    gasto = get_object_or_404(Gasto, id=id, usuario=request.user)
    if request.method == 'POST':
        gasto.delete()
        return redirect('lista_gastos')
    return render(request, 'gastos/eliminar_gasto.html', {'gasto': gasto})


# API REST para gestionar los gastos
class GastoViewSet(viewsets.ModelViewSet):
    queryset = Gasto.objects.all()  # Añade el queryset explícitamente aquí
    serializer_class = GastoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOwnOnly]

    def get_queryset(self):
        # Los superusuarios pueden ver todos los gastos
        if self.request.user.is_superuser:
            return Gasto.objects.all()

        # Filtrar gastos por usuario para usuarios normales
        queryset = Gasto.objects.filter(usuario=self.request.user)

        # Filtrar por fecha
        fecha = self.request.query_params.get('fecha', None)
        if fecha:
            queryset = queryset.filter(fecha=fecha)

        # Filtrar por categoría
        categoria = self.request.query_params.get('categoria', None)
        if categoria:
            queryset = queryset.filter(categoria=categoria)

        return queryset

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
