from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from gastos.models import Gasto, Categoria as CategoriaGasto
from ingresos.models import Ingreso, CategoriaIngreso, Moneda as IngresoMoneda

from .forms import AjusteSaldoForm, CuentaForm, TransferenciaForm
from .models import Cuenta, TransferenciaCuenta

@login_required
def lista_cuentas(request):
    cuentas = Cuenta.objects.filter(usuario=request.user)
    return render(request, 'cuentas/lista_cuentas.html', {'cuentas': cuentas})

@login_required
def crear_cuenta(request):
    if request.method == 'POST':
        form = CuentaForm(request.POST)
        if form.is_valid():
            cuenta = form.save(commit=False)
            cuenta.usuario = request.user
            cuenta.save()
            messages.success(request, 'Cuenta creada exitosamente.')
            return redirect('cuentas:lista_cuentas')
    else:
        form = CuentaForm()
    return render(request, 'cuentas/crear_cuenta.html', {'form': form})

@login_required
def editar_cuenta(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk, usuario=request.user)
    if request.method == 'POST':
        form = CuentaForm(request.POST, instance=cuenta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cuenta actualizada exitosamente.')
            return redirect('cuentas:lista_cuentas')
    else:
        form = CuentaForm(instance=cuenta)
    return render(request, 'cuentas/editar_cuenta.html', {'form': form, 'cuenta': cuenta})

@login_required
def eliminar_cuenta(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk, usuario=request.user)
    if request.method == 'POST':
        cuenta.delete()
        messages.success(request, 'Cuenta eliminada exitosamente.')
        return redirect('cuentas:lista_cuentas')
    return render(request, 'cuentas/eliminar_cuenta.html', {'cuenta': cuenta})

@login_required
def ajustar_saldo(request, pk):
    cuenta = get_object_or_404(Cuenta, pk=pk, usuario=request.user)
    
    # Calculate current system balance
    ingresos_cuenta = Ingreso.objects.filter(cuenta=cuenta).aggregate(Sum('monto'))['monto__sum'] or 0
    gastos_cuenta = Gasto.objects.filter(cuenta=cuenta).aggregate(Sum('monto'))['monto__sum'] or 0
    saldo_sistema = cuenta.saldo_inicial + ingresos_cuenta - gastos_cuenta
    
    if request.method == 'POST':
        form = AjusteSaldoForm(request.POST)
        if form.is_valid():
            saldo_real = form.cleaned_data['saldo_real']
            diferencia = saldo_real - saldo_sistema
            
            if diferencia > 0:
                # Need to add Income
                categoria, _ = CategoriaIngreso.objects.get_or_create(nombre='Ajuste de Saldo')
                
                # Find matching IngresoMoneda
                ingreso_moneda, _ = IngresoMoneda.objects.get_or_create(
                    codigo=cuenta.moneda.codigo,
                    defaults={'nombre': cuenta.moneda.nombre, 'simbolo': cuenta.moneda.simbolo}
                )

                Ingreso.objects.create(
                    usuario=request.user,
                    cuenta=cuenta,
                    monto=diferencia,
                    categoria=categoria,
                    descripcion='Ajuste manual de saldo (Positivo)',
                    moneda=ingreso_moneda,
                    fecha=timezone.now()
                )
                messages.success(request, f'Se registró un ingreso de ajuste por {diferencia}')
                
            elif diferencia < 0:
                # Need to add Expense
                categoria, _ = CategoriaGasto.objects.get_or_create(nombre='Ajuste de Saldo')
                Gasto.objects.create(
                    usuario=request.user,
                    cuenta=cuenta,
                    monto=abs(diferencia),
                    categoria=categoria,
                    descripcion='Ajuste manual de saldo (Negativo)',
                    moneda=cuenta.moneda,
                    fecha=timezone.now()
                )
                messages.success(request, f'Se registró un gasto de ajuste por {abs(diferencia)}')
            else:
                messages.info(request, 'El saldo real coincide con el del sistema. No se realizaron cambios.')
                
            return redirect('inicio_usuarios')
    else:
        form = AjusteSaldoForm(initial={'saldo_real': saldo_sistema})
        
    return render(request, 'cuentas/ajustar_saldo.html', {
        'form': form,
        'cuenta': cuenta,
        'saldo_sistema': saldo_sistema
    })


@login_required
def transferir_cuentas(request):
    if request.method == 'POST':
        form = TransferenciaForm(request.POST, usuario=request.user)
        if form.is_valid():
            datos = form.cleaned_data
            cuenta_origen = datos['cuenta_origen']
            cuenta_destino = datos['cuenta_destino']
            monto_origen = datos['monto_origen']
            monto_destino = datos['monto_destino']
            tasa = datos['tasa_manual']
            nota = datos.get('nota', '')

            try:
                with transaction.atomic():
                    categoria_gasto, _ = CategoriaGasto.objects.get_or_create(nombre='Transferencia Saliente')
                    categoria_ingreso, _ = CategoriaIngreso.objects.get_or_create(nombre='Transferencia Entrante')

                    fecha_mov = timezone.now()

                    gasto = Gasto.objects.create(
                        usuario=request.user,
                        descripcion=f'Transferencia a {cuenta_destino.nombre}',
                        monto=monto_origen,
                        categoria=categoria_gasto,
                        moneda=cuenta_origen.moneda,
                        cuenta=cuenta_origen,
                        fecha=fecha_mov,
                    )

                    ingreso_moneda, _ = IngresoMoneda.objects.get_or_create(
                        codigo=cuenta_destino.moneda.codigo,
                        defaults={'nombre': cuenta_destino.moneda.nombre, 'simbolo': cuenta_destino.moneda.simbolo}
                    )

                    ingreso = Ingreso.objects.create(
                        usuario=request.user,
                        descripcion=f'Transferencia desde {cuenta_origen.nombre}',
                        monto=monto_destino,
                        categoria=categoria_ingreso,
                        moneda=ingreso_moneda,
                        cuenta=cuenta_destino,
                        fecha=fecha_mov,
                    )

                    TransferenciaCuenta.objects.create(
                        usuario=request.user,
                        cuenta_origen=cuenta_origen,
                        cuenta_destino=cuenta_destino,
                        monto_origen=monto_origen,
                        monto_destino=monto_destino,
                        tasa_manual=tasa,
                        nota=nota,
                        fecha=fecha_mov,
                        gasto=gasto,
                        ingreso=ingreso,
                    )

                messages.success(request, 'Transferencia registrada exitosamente.')
                return redirect('inicio_usuarios')
            except Exception as exc:
                messages.error(request, f'No se pudo registrar la transferencia: {exc}')
    else:
        form = TransferenciaForm(usuario=request.user)

    return render(request, 'cuentas/transferir.html', {
        'form': form,
    })
