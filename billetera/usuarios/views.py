from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import PerfilUsuario
from .forms import PerfilUsuarioForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from gastos.models import Gasto
from ingresos.models import Ingreso


def inicio(request):
    context = {}

    if request.user.is_authenticated and not request.user.is_superuser:
        # Últimos 5 registros para la lista del inicio
        ultimos_ingresos = Ingreso.objects.filter(usuario=request.user).order_by('-fecha')[:5]
        ultimos_gastos = Gasto.objects.filter(usuario=request.user).order_by('-fecha')[:5]

        # Total de todos los ingresos y registros solo con moneda de id 3 (Peso Argentino)

        total_ingresos = Ingreso.objects.filter(usuario=request.user, moneda=3).aggregate(Sum('monto'))['monto__sum'] or 0
        total_gastos = Gasto.objects.filter(usuario=request.user, moneda=3).aggregate(Sum('monto'))['monto__sum'] or 0
        
        # Calcular el balance neto (ingresos - gastos)
        balance_neto = total_ingresos - total_gastos

        # Construir lista combinada de últimos movimientos (ingresos y gastos mezclados cronológicamente)
        # Tomamos más elementos de cada lado para que al mezclarlos haya suficiente para los 10 finales
        ingresos_para_mezcla = Ingreso.objects.filter(usuario=request.user).order_by('-fecha')[:10]
        gastos_para_mezcla = Gasto.objects.filter(usuario=request.user).order_by('-fecha')[:10]

        movimientos = []
        for ing in ingresos_para_mezcla:
            movimientos.append({
                'tipo': 'ingreso',
                'descripcion': ing.descripcion,
                'categoria': getattr(ing, 'categoria', ''),
                'monto': ing.monto,
                'fecha': ing.fecha,
                'obj': ing,
            })
        for gas in gastos_para_mezcla:
            movimientos.append({
                'tipo': 'gasto',
                'descripcion': gas.descripcion,
                'categoria': getattr(gas, 'categoria', ''),
                'monto': gas.monto,
                'fecha': gas.fecha,
                'obj': gas,
            })

        # Orden descendente por fecha y limitar a 10
        movimientos = sorted(movimientos, key=lambda x: x['fecha'], reverse=True)[:10]

        context = {
            'ingresos': ultimos_ingresos,  # Para mantener compatibilidad con el template
            'gastos': ultimos_gastos,  # Para mantener compatibilidad con el template
            'total_ingresos': total_ingresos,
            'total_gastos': total_gastos,
            'balance_neto': balance_neto,
            'movimientos': movimientos,
        }

    return render(request, 'usuarios/inicio.html', context)


# Registro de usuario
def registro(request):
    # Maneja la lógica de registro de usuario
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guarda el nuevo usuario en la base de datos
            login(request, user)  # Inicia sesión automáticamente con el nuevo usuario
            return redirect('inicio_usuarios')  # Redirige a la lista de gastos
    else:
        form = UserCreationForm()  # Crea un formulario de registro vacío
    return render(request, 'usuarios/registro.html', {'form': form})


@login_required
def perfil_usuario(request):
    perfil = request.user.perfilusuario
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            return redirect('usuarios:perfil_usuario')
    else:
        form = PerfilUsuarioForm(instance=perfil)
    return render(request, 'usuarios/perfil_usuario.html', {'form': form})


@login_required
def editar_perfil(request):
    perfil = get_object_or_404(PerfilUsuario, usuario=request.user)
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            return redirect('perfil_usuario')
    else:
        form = PerfilUsuarioForm(instance=perfil)

    return render(request, 'usuarios/editar_perfil.html', {'form': form, 'perfil': perfil})
