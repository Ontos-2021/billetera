from django.shortcuts import render, redirect, get_object_or_404
from .models import Gasto, Compra, Tienda
from .forms import GastoForm, CompraGlobalHeaderForm, CompraGlobalItemForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.forms import formset_factory
from django.db import transaction
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
# import weasyprint  -- Moved inside the view to avoid dependency issues on dev
from .filters import GastoFilter


# Función para obtener los gastos filtrados por usuario o superusuario
def obtener_gastos(request):
    # Los superusuarios pueden ver todos los gastos
    if request.user.is_superuser:
        queryset = Gasto.objects.all().order_by('-fecha')
    else:
        # Los usuarios normales solo pueden ver sus propios gastos
        queryset = Gasto.objects.filter(usuario=request.user).order_by('-fecha')
    
    # Aplicar filtros
    filter_set = GastoFilter(request.GET, queryset=queryset)
    return filter_set


# Lista de gastos
@login_required  # Requiere que el usuario esté autenticado
def lista_gastos(request):
    gastos_filter = obtener_gastos(request)  # Obtiene el objeto FilterSet
    gastos = gastos_filter.qs # Obtiene el queryset filtrado
    
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
        'filter': gastos_filter, # Pasar el filtro al template
        'totales_gastos': totales_list,
        'totales_gastos_default': moneda_default,
    })


# Crear gasto
@login_required  # Requiere que el usuario esté autenticado
def crear_gasto(request):
    if request.method == 'POST':
        form = GastoForm(request.POST, user=request.user)
        if form.is_valid():
            gasto = form.save(commit=False)  # Crea un objeto Gasto sin guardarlo aún
            gasto.usuario = request.user  # Asocia el gasto con el usuario autenticado
            gasto.save()  # Guarda el gasto en la base de datos
            return redirect('gastos:lista_gastos')  # Redirige a la lista de gastos
    else:
        form = GastoForm(user=request.user)  # Crea un formulario de gasto vacío
    
    tiendas = Tienda.objects.filter(usuario=request.user)
    return render(request, 'gastos/crear_gasto.html', {'form': form, 'tiendas': tiendas})


# Editar gasto
@login_required  # Requiere que el usuario esté autenticado
def editar_gasto(request, id):
    # Obtiene el gasto por id, permitiendo al superusuario editar cualquier gasto
    gasto = get_object_or_404(Gasto, id=id)
    if not request.user.is_superuser and gasto.usuario != request.user:
        return redirect('gastos:lista_gastos')  # Redirige si el usuario no tiene permisos

    if request.method == 'POST':
        form = GastoForm(request.POST, instance=gasto, user=request.user)  # Crea un formulario con los datos del gasto existente
        if form.is_valid():
            form.save()  # Guarda los cambios realizados en el gasto
            return redirect('gastos:lista_gastos')  # Redirige a la lista de gastos
    else:
        form = GastoForm(instance=gasto, user=request.user)  # Crea un formulario con los datos del gasto para editar
    
    tiendas = Tienda.objects.filter(usuario=request.user)
    return render(request, 'gastos/editar_gasto.html', {'form': form, 'gasto': gasto, 'tiendas': tiendas})


# Eliminar gasto
@login_required  # Requiere que el usuario esté autenticado
def eliminar_gasto(request, id):
    # Obtiene el gasto por id, permitiendo al superusuario eliminar cualquier gasto
    gasto = get_object_or_404(Gasto, id=id)
    if not request.user.is_superuser and gasto.usuario != request.user:
        return redirect('gastos:lista_gastos')  # Redirige si el usuario no tiene permisos

    if request.method == 'POST':
        compra = gasto.compra  # Guardar referencia a la compra antes de eliminar
        gasto.delete()  # Elimina el gasto de la base de datos
        
        # Si el gasto pertenecía a una compra y era el último ítem, eliminar la compra
        if compra and compra.items.count() == 0:
            compra.delete()
        
        return redirect('gastos:lista_gastos')  # Redirige a la lista de gastos


@login_required
def exportar_gastos_pdf(request):
    import weasyprint
    gastos_filter = obtener_gastos(request)
    gastos = gastos_filter.qs
    total_general = gastos.aggregate(Sum('monto'))['monto__sum'] or 0
    
    html_string = render_to_string('gastos/reporte_pdf.html', {
        'gastos': gastos,
        'total_general': total_general,
        'user': request.user,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_gastos.pdf"'

    weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response
    return render(request, 'gastos/eliminar_gasto.html', {'gasto': gasto})


# Crear gasto global
@login_required
def compra_global(request):
    ItemFormSet = formset_factory(CompraGlobalItemForm, extra=1)
    
    if request.method == 'POST':
        header_form = CompraGlobalHeaderForm(request.POST, user=request.user)
        item_formset = ItemFormSet(request.POST)
        
        if header_form.is_valid() and item_formset.is_valid():
            try:
                with transaction.atomic():
                    header_data = header_form.cleaned_data
                    
                    # Crear objeto Compra para agrupar los gastos
                    compra = Compra.objects.create(
                        usuario=request.user,
                        fecha=header_data['fecha'],
                        lugar=header_data['lugar'] or '',
                        cuenta=header_data['cuenta'],
                        moneda=header_data['moneda'],
                    )
                    
                    items_created = 0
                    for form in item_formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            gasto = form.save(commit=False)
                            gasto.usuario = request.user
                            # Assign header fields
                            gasto.fecha = header_data['fecha']
                            gasto.lugar = header_data['lugar']
                            gasto.cuenta = header_data['cuenta']
                            gasto.moneda = header_data['moneda']
                            # Asociar a la compra
                            gasto.compra = compra

                            # Calculate total amount (Unit Price * Quantity)
                            unit_price = form.cleaned_data.get('monto')
                            quantity = form.cleaned_data.get('cantidad', 1)
                            if unit_price is not None and quantity:
                                gasto.monto = unit_price * quantity

                            gasto.save()
                            items_created += 1
                    
                    # Si no se creó ningún item, eliminar la compra vacía
                    if items_created == 0:
                        compra.delete()
                            
                    return redirect('gastos:lista_gastos')
            except Exception as e:
                # Handle errors if needed
                pass
    else:
        header_form = CompraGlobalHeaderForm(user=request.user)
        ItemFormSet = formset_factory(CompraGlobalItemForm, extra=1)
        item_formset = ItemFormSet()
        
    return render(request, 'gastos/compra_global.html', {
        'header_form': header_form,
        'item_formset': item_formset
    })


# Detalle de compra (retorna HTML partial para modal)
@login_required
def detalle_compra(request, pk):
    """
    Retorna un HTML partial con el detalle de una compra para ser
    cargado en un modal vía fetch.
    """
    compra = get_object_or_404(Compra, pk=pk)
    
    # Verificar que el usuario sea el dueño o superusuario
    if not request.user.is_superuser and compra.usuario != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permiso para ver esta compra.")
    
    return render(request, 'gastos/_detalle_compra_partial.html', {
        'compra': compra,
    })
