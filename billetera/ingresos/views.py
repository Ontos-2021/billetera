from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from .models import Ingreso
from .forms import IngresoForm


# Vista para crear un nuevo ingreso
@login_required
def crear_ingreso(request):
    if request.method == 'POST':
        form = IngresoForm(request.POST)
        if form.is_valid():
            ingreso = form.save(commit=False)
            ingreso.usuario = request.user  # Asignar el usuario actual
            ingreso.save()
            return redirect('ingresos:lista_ingresos')  # Redirigir a la lista de ingresos
    else:
        form = IngresoForm()
    return render(request, 'ingresos/crear_ingreso.html', {'form': form})


# Vista para editar un ingreso existente
@login_required
def editar_ingreso(request, ingreso_id):
    ingreso = get_object_or_404(Ingreso, id=ingreso_id, usuario=request.user)
    if request.method == 'POST':
        form = IngresoForm(request.POST, instance=ingreso)
        if form.is_valid():
            form.save()
            return redirect('ingresos/lista_ingresos.html')
    else:
        form = IngresoForm(instance=ingreso)
    return render(request, 'ingresos/editar_ingreso.html', {'form': form, 'ingreso': ingreso})


# Vista para eliminar (o cancelar) un ingreso existente
@login_required
def eliminar_ingreso(request, ingreso_id):
    ingreso = get_object_or_404(Ingreso, id=ingreso_id, usuario=request.user)
    if request.method == 'POST':
        ingreso.delete()
        return redirect('ingresos:lista_ingresos')
    return render(request, 'ingresos/eliminar_ingreso.html', {'ingreso': ingreso})


# Vista para listar los ingresos de un usuario
@login_required
def lista_ingresos(request):
    ingresos = Ingreso.objects.filter(usuario=request.user).order_by('-fecha')
    return render(request, 'ingresos/lista_ingresos.html', {'ingresos': ingresos})
