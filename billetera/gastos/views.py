from django.shortcuts import render, redirect, get_object_or_404
from .models import Gasto
from .forms import GastoForm
from django.contrib.auth.decorators import login_required
from django.db.models import Sum


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
    
    # Calcular total de gastos
    total_gastos = gastos.aggregate(total=Sum('monto'))['total'] or 0
    
    return render(request, 'gastos/lista_gastos.html', {
        'gastos': gastos,
        'total_gastos': total_gastos
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
    return render(request, 'gastos/editar_gasto.html', {'form': form})


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

