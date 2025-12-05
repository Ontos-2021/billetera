from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Sum
from .models import Ingreso
from .forms import IngresoForm


# Vista para crear un nuevo ingreso
@login_required
def crear_ingreso(request):
    if request.method == 'POST':
        form = IngresoForm(request.POST, user=request.user)
        if form.is_valid():
            ingreso = form.save(commit=False)
            ingreso.usuario = request.user  # Asignar el usuario actual
            ingreso.save()
            return redirect('ingresos:lista_ingresos')  # Redirigir a la lista de ingresos
    else:
        form = IngresoForm(user=request.user)
    return render(request, 'ingresos/crear_ingreso.html', {'form': form})


# Vista para editar un ingreso existente
@login_required
def editar_ingreso(request, ingreso_id):
    ingreso = get_object_or_404(Ingreso, id=ingreso_id, usuario=request.user)
    if request.method == 'POST':
        form = IngresoForm(request.POST, instance=ingreso, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('ingresos:lista_ingresos')  # Redireccionar a la lista de ingresos
    else:
        form = IngresoForm(instance=ingreso, user=request.user)
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
    from decimal import Decimal
    ingresos = Ingreso.objects.filter(usuario=request.user).order_by('-fecha')
    
    # Calcular totales por moneda (excluyendo transferencias)
    totales_por_moneda = {}
    for ingreso in ingresos:
        # Excluir ingresos que son transferencias
        if hasattr(ingreso, 'transferencias_generadas') and ingreso.transferencias_generadas.exists():
            continue
        codigo = ingreso.moneda.codigo
        if codigo not in totales_por_moneda:
            totales_por_moneda[codigo] = {
                'codigo': codigo,
                'simbolo': ingreso.moneda.simbolo,
                'nombre': ingreso.moneda.nombre,
                'total': Decimal('0.00'),
            }
        totales_por_moneda[codigo]['total'] += ingreso.monto
    
    totales_list = sorted(totales_por_moneda.values(), key=lambda x: x['codigo'])
    moneda_default = 'ARS' if 'ARS' in totales_por_moneda else (totales_list[0]['codigo'] if totales_list else None)
    
    return render(request, 'ingresos/lista_ingresos.html', {
        'ingresos': ingresos,
        'totales_ingresos': totales_list,
        'totales_ingresos_default': moneda_default,
    })
