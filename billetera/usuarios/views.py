from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import PerfilUsuario
from .forms import PerfilUsuarioForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from gastos.models import Gasto
from ingresos.models import Ingreso
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.views.decorators.csrf import csrf_exempt
import os
from django.utils import timezone
from datetime import timedelta

from usuarios.backup import run_database_backup
from cuentas.models import Cuenta


def inicio(request):
    context = {}

    if request.user.is_authenticated and not request.user.is_superuser:
        # --- Lógica de Filtrado por Rango de Tiempo ---
        rango = request.GET.get('rango', 'mes')  # Default: mes actual
        hoy = timezone.localtime(timezone.now())
        fecha_inicio = None

        if rango == 'hoy':
            fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
        elif rango == 'semana':
            fecha_inicio = hoy - timedelta(days=7)
        elif rango == 'mes':
            fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif rango == 'anio':
            fecha_inicio = hoy.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif rango == 'todo':
            fecha_inicio = None  # Sin filtro de fecha

        # Filtros base para totales (Usuario + Moneda ARS)
        filtros_ingresos = {'usuario': request.user, 'moneda__codigo': 'ARS'}
        filtros_gastos = {'usuario': request.user, 'moneda__codigo': 'ARS'}

        # Aplicar filtro de fecha si corresponde
        if fecha_inicio:
            filtros_ingresos['fecha__gte'] = fecha_inicio
            filtros_gastos['fecha__gte'] = fecha_inicio

        # Calcular Totales Filtrados
        total_ingresos = Ingreso.objects.filter(**filtros_ingresos).aggregate(Sum('monto'))['monto__sum'] or 0
        total_gastos = Gasto.objects.filter(**filtros_gastos).aggregate(Sum('monto'))['monto__sum'] or 0
        balance_neto = total_ingresos - total_gastos

        # --- Fin Lógica de Filtrado ---

        # Últimos 5 registros para la lista del inicio (Legacy, se puede mantener o quitar si no se usa)
        ultimos_ingresos = Ingreso.objects.filter(usuario=request.user).order_by('-fecha')[:5]
        ultimos_gastos = Gasto.objects.filter(usuario=request.user).order_by('-fecha')[:5]

        # Calcular saldos por cuenta
        cuentas = Cuenta.objects.filter(usuario=request.user)
        cuentas_con_saldo = []
        for cuenta in cuentas:
            ingresos_cuenta = Ingreso.objects.filter(cuenta=cuenta).aggregate(Sum('monto'))['monto__sum'] or 0
            gastos_cuenta = Gasto.objects.filter(cuenta=cuenta).aggregate(Sum('monto'))['monto__sum'] or 0
            saldo_actual = cuenta.saldo_inicial + ingresos_cuenta - gastos_cuenta
            cuentas_con_saldo.append({
                'id': cuenta.id,
                'nombre': cuenta.nombre,
                'tipo': cuenta.tipo.nombre if cuenta.tipo else 'Otro',
                'moneda_simbolo': cuenta.moneda.simbolo,
                'moneda_codigo': cuenta.moneda.codigo,
                'saldo': saldo_actual
            })

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
            'cuentas_saldo': cuentas_con_saldo,
            'rango_actual': rango, # Pasar el rango al template para resaltar el botón activo
        }

    return render(request, 'usuarios/inicio.html', context)


# Registro de usuario
def registro(request):
    # Maneja la lógica de registro de usuario
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guarda el nuevo usuario en la base de datos
            # Specify the backend to avoid multiple backends error
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('inicio_usuarios')  # Redirige a la lista de gastos
    else:
        form = UserCreationForm()  # Crea un formulario de registro vacío
    return render(request, 'usuarios/registro.html', {'form': form})


@login_required
def perfil_usuario(request):
    perfil = request.user.perfilusuario
    # Estadísticas de actividad financiera del usuario
    # Conteo de registros de ingresos y gastos y días activos (días distintos con al menos un movimiento)
    ingresos_qs = Ingreso.objects.filter(usuario=request.user)
    gastos_qs = Gasto.objects.filter(usuario=request.user)
    total_ingresos_registrados = ingresos_qs.count()
    total_gastos_registrados = gastos_qs.count()

    # Calcular días activos (número de días distintos con algún ingreso o gasto)
    from django.db.models.functions import TruncDate
    ingresos_dias = ingresos_qs.annotate(day=TruncDate('fecha')).values_list('day', flat=True).distinct()
    gastos_dias = gastos_qs.annotate(day=TruncDate('fecha')).values_list('day', flat=True).distinct()
    dias_activo = len(set(list(ingresos_dias) + list(gastos_dias)))

    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            return redirect('usuarios:perfil_usuario')
    else:
        form = PerfilUsuarioForm(instance=perfil)
    return render(request, 'usuarios/perfil_usuario.html', {
        'form': form,
        'total_ingresos': total_ingresos_registrados,
        'total_gastos': total_gastos_registrados,
        'dias_activo': dias_activo,
    })


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


# API: perfil /me protegido por JWT
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class ProfileMe(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({
            'id': u.id,
            'email': getattr(u, 'email', None),
            'first_name': getattr(u, 'first_name', ''),
            'last_name': getattr(u, 'last_name', ''),
        })


@csrf_exempt
def trigger_backup(request):
    """
    Endpoint protegido para disparar el backup.
    Seguridad:
      - Acepta GET/POST.
      - Si el header X-Backup-Token o ?token= coincide con BACKUP_WEBHOOK_TOKEN => permitido.
      - En caso contrario, requiere usuario autenticado STAFF.
    """
    if request.method not in ("GET", "POST"):
        return HttpResponseNotAllowed(["GET", "POST"])

    token_env = os.getenv('BACKUP_WEBHOOK_TOKEN')
    token_req = request.headers.get('X-Backup-Token') or request.GET.get('token') or request.POST.get('token')

    if not (token_env and token_req and token_req == token_env):
        # Fallback a staff
        user = getattr(request, 'user', None)
        if not (user and user.is_authenticated and user.is_staff):
            return HttpResponseForbidden('No autorizado')

    result = run_database_backup()
    return JsonResponse({'status': 'ok', **result})
