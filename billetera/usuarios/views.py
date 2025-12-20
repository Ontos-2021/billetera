from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import PerfilUsuario
from .forms import PerfilUsuarioForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from gastos.models import Gasto, Compra
from ingresos.models import Ingreso
from deudas.models import Deuda
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import os
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.template.loader import render_to_string
# import weasyprint  <-- Moved inside function to avoid crash on Windows dev env
from django.db.models.functions import TruncDate

from usuarios.backup import run_database_backup
from cuentas.models import Cuenta


def inicio(request):
    context = {}

    if request.user.is_authenticated and not request.user.is_superuser:
        # --- Lógica de Filtrado por Rango de Tiempo (Rolling Windows) ---
        rango = request.GET.get('rango', '30d')  # Default: últimos 30 días
        ahora = timezone.localtime(timezone.now())
        fecha_inicio = None

        if rango == '24h':
            fecha_inicio = ahora - timedelta(hours=24)
        elif rango == '3d':
            fecha_inicio = ahora - timedelta(hours=72)
        elif rango == '7d':
            fecha_inicio = ahora - timedelta(days=7)
        elif rango == '30d':
            fecha_inicio = ahora - timedelta(days=30)
        elif rango == '365d':
            fecha_inicio = ahora - timedelta(days=365)
        elif rango == 'todo':
            fecha_inicio = None  # Sin filtro de fecha
        else:
            # Fallback para parámetros legacy o inválidos
            fecha_inicio = ahora - timedelta(days=30)

        # Filtros base para totales (Usuario + Moneda ARS)
        filtros_ingresos = {
            'usuario': request.user,
            'moneda__codigo': 'ARS',
            'transferencias_generadas__isnull': True,
        }
        filtros_gastos = {
            'usuario': request.user,
            'moneda__codigo': 'ARS',
            'transferencias_generadas__isnull': True,
        }

        # Aplicar filtro de fecha si corresponde
        if fecha_inicio:
            filtros_ingresos['fecha__gte'] = fecha_inicio
            filtros_gastos['fecha__gte'] = fecha_inicio

        # Calcular Totales Filtrados
        total_ingresos = Ingreso.objects.filter(**filtros_ingresos).aggregate(Sum('monto'))['monto__sum'] or 0
        total_gastos = Gasto.objects.filter(**filtros_gastos).aggregate(Sum('monto'))['monto__sum'] or 0
        balance_neto = total_ingresos - total_gastos

        # --- Datos para el Gráfico (Últimos 6 meses) ---
        chart_labels = []
        chart_ingresos = []
        chart_gastos = []
        
        # Iterar sobre los últimos 6 meses
        for i in range(5, -1, -1):
            mes_inicio = (ahora.replace(day=1) - timedelta(days=i*30)).replace(day=1)
            # Calcular fin de mes (inicio del siguiente mes - 1 segundo)
            if mes_inicio.month == 12:
                mes_fin = mes_inicio.replace(year=mes_inicio.year + 1, month=1)
            else:
                mes_fin = mes_inicio.replace(month=mes_inicio.month + 1)
            
            # Nombre del mes para el label
            chart_labels.append(mes_inicio.strftime('%b'))
            
            # Filtros para el mes
            filtros_mes_ingresos = {
                'usuario': request.user,
                'moneda__codigo': 'ARS',
                'transferencias_generadas__isnull': True,
                'fecha__gte': mes_inicio,
                'fecha__lt': mes_fin,
            }
            filtros_mes_gastos = {
                'usuario': request.user,
                'moneda__codigo': 'ARS',
                'transferencias_generadas__isnull': True,
                'fecha__gte': mes_inicio,
                'fecha__lt': mes_fin,
            }
            
            ingresos_mes = Ingreso.objects.filter(**filtros_mes_ingresos).aggregate(Sum('monto'))['monto__sum'] or 0
            gastos_mes = Gasto.objects.filter(**filtros_mes_gastos).aggregate(Sum('monto'))['monto__sum'] or 0
            
            chart_ingresos.append(float(ingresos_mes))
            chart_gastos.append(float(gastos_mes))

        # --- Fin Lógica de Filtrado ---

        # --- Suite de gráficos (rango variable) ---
        # Nota: mantenemos coherencia con el dashboard: ARS + sin transferencias.
        chart_start = fecha_inicio
        if chart_start is None:
            # Evitar rangos enormes en "todo" para gráficos diarios.
            chart_start = ahora - timedelta(days=365)
        start_date = timezone.localtime(chart_start).date()
        end_date = timezone.localtime(ahora).date()
        if (end_date - start_date).days > 365:
            start_date = end_date - timedelta(days=365)

        ingresos_qs = Ingreso.objects.filter(**filtros_ingresos)
        gastos_qs = Gasto.objects.filter(**filtros_gastos)

        ingresos_diarios = (
            ingresos_qs
            .annotate(dia=TruncDate('fecha'))
            .values('dia')
            .annotate(total=Sum('monto'))
            .order_by('dia')
        )
        gastos_diarios = (
            gastos_qs
            .annotate(dia=TruncDate('fecha'))
            .values('dia')
            .annotate(total=Sum('monto'))
            .order_by('dia')
        )

        ingresos_map = {row['dia']: float(row['total'] or 0) for row in ingresos_diarios}
        gastos_map = {row['dia']: float(row['total'] or 0) for row in gastos_diarios}

        daily_labels = []
        daily_ingresos = []
        daily_gastos = []
        for i in range((end_date - start_date).days + 1):
            d = start_date + timedelta(days=i)
            daily_labels.append(d.strftime('%d/%m'))
            daily_ingresos.append(ingresos_map.get(d, 0))
            daily_gastos.append(gastos_map.get(d, 0))

        categorias_qs = (
            gastos_qs
            .values('categoria__nombre')
            .annotate(total=Sum('monto'))
            .order_by('-total')
        )
        pie_labels = []
        pie_values = []
        otros_total = 0.0
        max_slices = 8
        for idx, row in enumerate(categorias_qs):
            label = row['categoria__nombre'] or 'Sin categoría'
            value = float(row['total'] or 0)
            if idx < max_slices:
                pie_labels.append(label)
                pie_values.append(value)
            else:
                otros_total += value
        if otros_total > 0:
            pie_labels.append('Otros')
            pie_values.append(otros_total)

        daily_flow_chart = {
            'labels': daily_labels,
            'ingresos': daily_ingresos,
            'gastos': daily_gastos,
            'range': rango,
        }
        category_pie_chart = {
            'labels': pie_labels,
            'values': pie_values,
            'range': rango,
        }

        # Últimos 5 registros para la lista del inicio (Legacy, se puede mantener o quitar si no se usa)
        ultimos_ingresos = Ingreso.objects.filter(usuario=request.user).order_by('-fecha')[:5]
        ultimos_gastos = Gasto.objects.filter(usuario=request.user).order_by('-fecha')[:5]

        # Calcular saldos por cuenta
        cuentas = Cuenta.objects.filter(usuario=request.user)
        cuentas_con_saldo = []
        totales_por_moneda = {}
        for cuenta in cuentas:
            ingresos_cuenta = Ingreso.objects.filter(cuenta=cuenta).aggregate(Sum('monto'))['monto__sum'] or Decimal('0.00')
            gastos_cuenta = Gasto.objects.filter(cuenta=cuenta).aggregate(Sum('monto'))['monto__sum'] or Decimal('0.00')
            saldo_actual = cuenta.saldo_inicial + Decimal(ingresos_cuenta) - Decimal(gastos_cuenta)
            cuentas_con_saldo.append({
                'id': cuenta.id,
                'nombre': cuenta.nombre,
                'tipo': cuenta.tipo.nombre if cuenta.tipo else 'Otro',
                'moneda_simbolo': cuenta.moneda.simbolo,
                'moneda_codigo': cuenta.moneda.codigo,
                'saldo': saldo_actual
            })
            codigo = cuenta.moneda.codigo
            if codigo not in totales_por_moneda:
                totales_por_moneda[codigo] = {
                    'codigo': codigo,
                    'simbolo': cuenta.moneda.simbolo,
                    'nombre': cuenta.moneda.nombre,
                    'total': Decimal('0.00'),
                }
            totales_por_moneda[codigo]['total'] += saldo_actual

        totals_list = sorted(totales_por_moneda.values(), key=lambda item: item['codigo'])
        moneda_default = 'ARS' if 'ARS' in totales_por_moneda else (totals_list[0]['codigo'] if totals_list else None)

        # Construir lista combinada de últimos movimientos (ingresos, gastos individuales y compras agrupadas)
        # Tomamos más elementos de cada lado para que al mezclarlos haya suficiente para los 10 finales
        ingresos_para_mezcla = Ingreso.objects.filter(usuario=request.user).order_by('-fecha')[:10]
        # Gastos individuales (sin compra asociada)
        gastos_individuales = Gasto.objects.filter(usuario=request.user, compra__isnull=True).order_by('-fecha')[:10]
        # Compras (agrupan gastos)
        compras_para_mezcla = Compra.objects.filter(usuario=request.user).prefetch_related('items').order_by('-fecha')[:10]

        movimientos = []
        for ing in ingresos_para_mezcla:
            movimientos.append({
                'tipo': 'ingreso',
                'descripcion': ing.descripcion,
                'categoria': getattr(ing, 'categoria', ''),
                'monto': ing.monto,
                'fecha': ing.fecha,
                'obj': ing,
                'cuenta_nombre': ing.cuenta.nombre if ing.cuenta else None,
                'moneda_codigo': ing.moneda.codigo if ing.moneda else 'ARS',
                'moneda_simbolo': ing.moneda.simbolo if ing.moneda else '$',
                'url': reverse('ingresos:editar_ingreso', args=[ing.id]),
            })
        for gas in gastos_individuales:
            descripcion = gas.descripcion
            if gas.cantidad > 1:
                descripcion += f" x{gas.cantidad}"
            movimientos.append({
                'tipo': 'gasto',
                'descripcion': descripcion,
                'categoria': getattr(gas, 'categoria', ''),
                'monto': gas.monto,
                'fecha': gas.fecha,
                'obj': gas,
                'cuenta_nombre': gas.cuenta.nombre if gas.cuenta else None,
                'moneda_codigo': gas.moneda.codigo if gas.moneda else 'ARS',
                'moneda_simbolo': gas.moneda.simbolo if gas.moneda else '$',
                'url': reverse('gastos:editar_gasto', args=[gas.id]),
            })
        for compra in compras_para_mezcla:
            items = list(compra.items.all())
            total_compra = sum(item.monto for item in items)
            items_count = len(items)

            if items_count == 1:
                item = items[0]
                descripcion = item.descripcion
                if item.cantidad > 1:
                    descripcion += f" x{item.cantidad}"
            else:
                descripcion = f"Compra en {compra.lugar}" if compra.lugar else "Compra"
                items_con_cantidad = [f"{item.descripcion} x{item.cantidad}" for item in items if item.cantidad > 1]
                if items_con_cantidad:
                    descripcion += f" ({', '.join(items_con_cantidad)})"

            movimientos.append({
                'tipo': 'compra',
                'descripcion': descripcion,
                'categoria': '',  # Las compras agrupan varias categorías
                'monto': total_compra,
                'fecha': compra.fecha,
                'obj': compra,
                'cuenta_nombre': compra.cuenta.nombre if compra.cuenta else None,
                'moneda_codigo': compra.moneda.codigo if compra.moneda else 'ARS',
                'moneda_simbolo': compra.moneda.simbolo if compra.moneda else '$',
                'items_count': items_count,
                'compra_id': compra.id,
                'url': '#',  # No navega directamente, abre modal
            })

        # Orden descendente por fecha y limitar a 10
        movimientos = sorted(movimientos, key=lambda x: x['fecha'], reverse=True)[:10]

        # Calcular totales de deudas
        deudas = Deuda.objects.filter(usuario=request.user)
        totales_deudas = {
            'POR_COBRAR': {},
            'POR_PAGAR': {}
        }
        
        for deuda in deudas:
            saldo = deuda.saldo_pendiente()
            if saldo > 0:
                codigo = deuda.moneda.codigo
                tipo = deuda.tipo
                if codigo not in totales_deudas[tipo]:
                    totales_deudas[tipo][codigo] = {
                        'codigo': codigo,
                        'simbolo': deuda.moneda.simbolo,
                        'total': Decimal('0.00')
                    }
                totales_deudas[tipo][codigo]['total'] += saldo
        
        deudas_por_cobrar_list = sorted(totales_deudas['POR_COBRAR'].values(), key=lambda x: x['codigo'])
        deudas_por_pagar_list = sorted(totales_deudas['POR_PAGAR'].values(), key=lambda x: x['codigo'])

        context = {
            'ingresos': ultimos_ingresos,  # Para mantener compatibilidad con el template
            'gastos': ultimos_gastos,  # Para mantener compatibilidad con el template
            'total_ingresos': total_ingresos,
            'total_gastos': total_gastos,
            'balance_neto': balance_neto,
            'movimientos': movimientos,
            'cuentas_saldo': cuentas_con_saldo,
            'rango_actual': rango, # Pasar el rango al template para resaltar el botón activo
            'totales_cuentas': totals_list,
            'totales_cuentas_default': moneda_default,
            'chart_labels': chart_labels,
            'chart_ingresos': chart_ingresos,
            'chart_gastos': chart_gastos,
            'daily_flow_chart': daily_flow_chart,
            'category_pie_chart': category_pie_chart,
            'deudas_por_cobrar': deudas_por_cobrar_list,
            'deudas_por_pagar': deudas_por_pagar_list,
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


@login_required
def exportar_reporte_pdf(request):
    rango = request.GET.get('rango', '30d')
    ahora = timezone.localtime(timezone.now())
    fecha_inicio = None
    rango_label = "Últimos 30 días"

    if rango == '24h':
        fecha_inicio = ahora - timedelta(hours=24)
        rango_label = "Últimas 24 horas"
    elif rango == '3d':
        fecha_inicio = ahora - timedelta(hours=72)
        rango_label = "Últimos 3 días"
    elif rango == '7d':
        fecha_inicio = ahora - timedelta(days=7)
        rango_label = "Últimos 7 días"
    elif rango == '30d':
        fecha_inicio = ahora - timedelta(days=30)
        rango_label = "Últimos 30 días"
    elif rango == '365d':
        fecha_inicio = ahora - timedelta(days=365)
        rango_label = "Último año"
    elif rango == 'todo':
        fecha_inicio = None
        rango_label = "Histórico Completo"
    else:
        fecha_inicio = ahora - timedelta(days=30)

    filtros_ingresos = {'usuario': request.user}
    filtros_gastos = {'usuario': request.user}
    filtros_compras = {'usuario': request.user}

    if fecha_inicio:
        filtros_ingresos['fecha__gte'] = fecha_inicio
        filtros_gastos['fecha__gte'] = fecha_inicio
        filtros_compras['fecha__gte'] = fecha_inicio

    # Totales
    total_ingresos = Ingreso.objects.filter(**filtros_ingresos).aggregate(Sum('monto'))['monto__sum'] or 0
    total_gastos = Gasto.objects.filter(**filtros_gastos).aggregate(Sum('monto'))['monto__sum'] or 0
    balance_neto = total_ingresos - total_gastos

    # Movimientos
    ingresos = Ingreso.objects.filter(**filtros_ingresos).order_by('-fecha')
    gastos_individuales = Gasto.objects.filter(**filtros_gastos, compra__isnull=True).order_by('-fecha')
    compras = Compra.objects.filter(**filtros_compras).prefetch_related('items').order_by('-fecha')

    movimientos = []
    for ing in ingresos:
        movimientos.append({
            'tipo': 'ingreso',
            'descripcion': ing.descripcion,
            'categoria': getattr(ing, 'categoria', ''),
            'monto': ing.monto,
            'fecha': ing.fecha,
            'cuenta_nombre': ing.cuenta.nombre if ing.cuenta else None,
            'moneda_simbolo': ing.moneda.simbolo if ing.moneda else '$',
        })
    for gas in gastos_individuales:
        descripcion = gas.descripcion
        if gas.cantidad > 1:
            descripcion += f" x{gas.cantidad}"
        movimientos.append({
            'tipo': 'gasto',
            'descripcion': descripcion,
            'categoria': getattr(gas, 'categoria', ''),
            'monto': gas.monto,
            'fecha': gas.fecha,
            'cuenta_nombre': gas.cuenta.nombre if gas.cuenta else None,
            'moneda_simbolo': gas.moneda.simbolo if gas.moneda else '$',
        })
    for compra in compras:
        items = list(compra.items.all())
        total_compra = sum(item.monto for item in items)
        items_count = len(items)

        if items_count == 1:
            item = items[0]
            descripcion = item.descripcion
            if item.cantidad > 1:
                descripcion += f" x{item.cantidad}"
        else:
            descripcion = f"Compra en {compra.lugar}" if compra.lugar else "Compra"
            items_con_cantidad = [f"{item.descripcion} x{item.cantidad}" for item in items if item.cantidad > 1]
            if items_con_cantidad:
                descripcion += f" ({', '.join(items_con_cantidad)})"

        movimientos.append({
            'tipo': 'compra',
            'descripcion': descripcion,
            'categoria': '',
            'monto': total_compra,
            'fecha': compra.fecha,
            'cuenta_nombre': compra.cuenta.nombre if compra.cuenta else None,
            'moneda_simbolo': compra.moneda.simbolo if compra.moneda else '$',
            'items_count': items_count,
        })

    # Ordenar y limitar (opcional, para PDF quizás queremos todos o un límite razonable)
    movimientos = sorted(movimientos, key=lambda x: x['fecha'], reverse=True)
    
    # Si son muchos, limitamos a 100 para no explotar el PDF
    if len(movimientos) > 100:
        movimientos = movimientos[:100]

    context = {
        'user': request.user,
        'rango_label': rango_label,
        'total_ingresos': total_ingresos,
        'total_gastos': total_gastos,
        'balance_neto': balance_neto,
        'movimientos': movimientos,
    }

    import weasyprint
    html_string = render_to_string('usuarios/reporte_pdf.html', context)
    html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
    result = html.write_pdf()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="reporte_{rango}.pdf"'
    response.write(result)
    return response
