from django.shortcuts import render, redirect, get_object_or_404
from .models import Gasto
from .forms import GastoForm, CompraGlobalHeaderForm, CompraGlobalItemForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.forms import formset_factory
from django.db import transaction


# Función para obtener los gastos filtrados por usuario o superusuario
def obtener_gastos(request):
    # Los superusuarios pueden ver todos los gastos
    if request.user.is_superuser:
        return Gasto.objects.all().order_by('-fecha')
    # Los usuarios normales solo pueden ver sus propios gastos
    return Gasto.objects.filter(usuario=request.user).order_by('-fecha')


# Lista de gastos
@login_required  # Requiere que el usuario esté autenticado
def lista_gastos(request):
    gastos = obtener_gastos(request)  # Obtiene los gastos correspondientes al usuario
    
    # Calcular totales por moneda (excluyendo transferencias)
    from decimal import Decimal
    totales_por_moneda = {}
    for gasto in gastos:
        # Excluir gastos que son transferencias
        if hasattr(gasto, 'transferencias_generadas') and gasto.transferencias_generadas.exists():
            continue
        codigo = gasto.moneda.codigo
        if codigo not in totales_por_moneda:
            totales_por_moneda[codigo] = {
                'codigo': codigo,
                'simbolo': gasto.moneda.simbolo,
                'nombre': gasto.moneda.nombre,
                'total': Decimal('0.00'),
            }
        totales_por_moneda[codigo]['total'] += gasto.monto
    
    totales_list = sorted(totales_por_moneda.values(), key=lambda x: x['codigo'])
    moneda_default = 'ARS' if 'ARS' in totales_por_moneda else (totales_list[0]['codigo'] if totales_list else None)
    
    return render(request, 'gastos/lista_gastos.html', {
        'gastos': gastos,
        'totales_gastos': totales_list,
        'totales_gastos_default': moneda_default,
    })


# Crear gasto
@login_required  # Requiere que el usuario esté autenticado
def crear_gasto(request):
    if request.method == 'POST':
        form = GastoForm(request.POST)
        if form.is_valid():
            gasto = form.save(commit=False)  # Crea un objeto Gasto sin guardarlo aún
            gasto.usuario = request.user  # Asocia el gasto con el usuario autenticado
            gasto.save()  # Guarda el gasto en la base de datos
            return redirect('gastos:lista_gastos')  # Redirige a la lista de gastos
    else:
        form = GastoForm()  # Crea un formulario de gasto vacío
    return render(request, 'gastos/crear_gasto.html', {'form': form})


# Editar gasto
@login_required  # Requiere que el usuario esté autenticado
def editar_gasto(request, id):
    # Obtiene el gasto por id, permitiendo al superusuario editar cualquier gasto
    gasto = get_object_or_404(Gasto, id=id)
    if not request.user.is_superuser and gasto.usuario != request.user:
        return redirect('gastos:lista_gastos')  # Redirige si el usuario no tiene permisos

    if request.method == 'POST':
        form = GastoForm(request.POST, instance=gasto)  # Crea un formulario con los datos del gasto existente
        if form.is_valid():
            form.save()  # Guarda los cambios realizados en el gasto
            return redirect('gastos:lista_gastos')  # Redirige a la lista de gastos
    else:
        form = GastoForm(instance=gasto)  # Crea un formulario con los datos del gasto para editar
    return render(request, 'gastos/editar_gasto.html', {'form': form, 'gasto': gasto})


# Eliminar gasto
@login_required  # Requiere que el usuario esté autenticado
def eliminar_gasto(request, id):
    # Obtiene el gasto por id, permitiendo al superusuario eliminar cualquier gasto
    gasto = get_object_or_404(Gasto, id=id)
    if not request.user.is_superuser and gasto.usuario != request.user:
        return redirect('gastos:lista_gastos')  # Redirige si el usuario no tiene permisos

    if request.method == 'POST':
        gasto.delete()  # Elimina el gasto de la base de datos
        return redirect('gastos:lista_gastos')  # Redirige a la lista de gastos
    return render(request, 'gastos/eliminar_gasto.html', {'gasto': gasto})


# Crear gasto global
@login_required
def compra_global(request):
    ItemFormSet = formset_factory(CompraGlobalItemForm, extra=1)
    
    if request.method == 'POST':
        header_form = CompraGlobalHeaderForm(request.POST)
        item_formset = ItemFormSet(request.POST)
        
        if header_form.is_valid() and item_formset.is_valid():
            try:
                with transaction.atomic():
                    # Get header data but don't save yet (it's not a model instance we want to save directly as is)
                    # Actually header_form is a ModelForm for Gasto, but we want to use its cleaned_data 
                    # to populate multiple Gasto instances.
                    
                    header_data = header_form.cleaned_data
                    
                    for form in item_formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            gasto = form.save(commit=False)
                            gasto.usuario = request.user
                            # Assign header fields
                            gasto.fecha = header_data['fecha']
                            gasto.lugar = header_data['lugar']
                            gasto.cuenta = header_data['cuenta']
                            gasto.moneda = header_data['moneda']

                            # Calculate total amount (Unit Price * Quantity)
                            unit_price = form.cleaned_data.get('monto')
                            quantity = form.cleaned_data.get('cantidad', 1)
                            if unit_price is not None and quantity:
                                gasto.monto = unit_price * quantity

                            gasto.save()
                            
                    return redirect('gastos:lista_gastos')
            except Exception as e:
                # Handle errors if needed
                pass
    else:
        header_form = CompraGlobalHeaderForm()
        ItemFormSet = formset_factory(CompraGlobalItemForm, extra=1)
        item_formset = ItemFormSet()
        
    return render(request, 'gastos/compra_global.html', {
        'header_form': header_form,
        'item_formset': item_formset
    })

