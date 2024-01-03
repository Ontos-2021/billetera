from django.shortcuts import render, redirect, get_object_or_404
from .models import Gasto
from .forms import GastoForm

def lista_gastos(request):
    gastos = Gasto.objects.all().order_by('-fecha')
    return render(request, 'gastos/lista_gastos.html', {'gastos': gastos})

from datetime import datetime
def crear_gasto(request):
    if request.method == 'POST':
        form = GastoForm(request.POST)
        if form.is_valid():
            gasto = form.save(commit=False)
            # Asegúrate de que la fecha esté en el formato correcto (por ejemplo, "2024-01-02").
            gasto.save()
            return redirect('lista_gastos')
    else:
        form = GastoForm()
    return render(request, 'gastos/crear_gasto.html', {'form': form})

def editar_gasto(request, id):
    gasto = get_object_or_404(Gasto, id=id)
    if request.method == 'POST':
        form = GastoForm(request.POST, instance=gasto)
        if form.is_valid():
            form.save()
            return redirect('lista_gastos')
    else:
        form = GastoForm(instance=gasto)
    return render(request, 'gastos/editar_gasto.html', {'form': form})

def eliminar_gasto(request, id):
    gasto = get_object_or_404(Gasto, id=id)
    if request.method == 'POST':
        gasto.delete()
        return redirect('lista_gastos')
    return render(request, 'gastos/eliminar_gasto.html', {'gasto': gasto})
