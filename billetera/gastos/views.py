from django.shortcuts import render, redirect, get_object_or_404
from .models import Gasto
from .forms import GastoForm

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect


def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guarda el usuario en la base de datos
            login(request, user)  # Inicia sesión automáticamente después del registro
            return redirect('lista_gastos')  # Redirige al usuario a la lista de gastos
    else:
        form = UserCreationForm()
    return render(request, 'gastos/registro.html', {'form': form})


from django.contrib.auth.decorators import login_required


@login_required
def lista_gastos(request):
    if request.user.is_superuser:
        gastos = Gasto.objects.all().order_by('-fecha')
    else:
        gastos = Gasto.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'gastos/lista_gastos.html', {'gastos': gastos})


from datetime import datetime

from rest_framework import viewsets
from .models import Gasto
from .serializers import GastoSerializer
from rest_framework.permissions import IsAuthenticated

from .permissions import *
from rest_framework import permissions


class GastoViewSet(viewsets.ModelViewSet):
    queryset = Gasto.objects.all()
    serializer_class = GastoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOwnOnly]

    def get_queryset(self):
        # Los superusuarios pueden ver todos los gastos
        if self.request.user.is_superuser:
            return Gasto.objects.all()

        # Los usuarios normales solo pueden ver sus propios gastos
        return Gasto.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        # Cuando se crea un gasto, asigna automáticamente el usuario que lo crea
        serializer.save(usuario=self.request.user)


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


@login_required
def editar_gasto(request, id):
    if request.user.is_superuser:
        gasto = get_object_or_404(Gasto, id=id)
    else:
        gasto = get_object_or_404(Gasto, id=id, usuario=request.user)  # Verifica que el gasto pertenezca al usuario
    if request.method == 'POST':
        form = GastoForm(request.POST, instance=gasto)
        if form.is_valid():
            form.save()
            return redirect('lista_gastos')
    else:
        form = GastoForm(instance=gasto)
    return render(request, 'gastos/editar_gasto.html', {'form': form})


@login_required
def eliminar_gasto(request, id):
    gasto = get_object_or_404(Gasto, id=id, usuario=request.user)  # Verifica que el gasto pertenezca al usuario
    if request.method == 'POST':
        gasto.delete()
        return redirect('lista_gastos')
    return render(request, 'gastos/eliminar_gasto.html', {'gasto': gasto})
