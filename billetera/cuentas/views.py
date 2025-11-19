from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cuenta
from .forms import CuentaForm
from django.contrib import messages

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
