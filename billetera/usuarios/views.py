from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import PerfilUsuario
from .forms import PerfilUsuarioForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login


def inicio(request):
    return render(request, 'usuarios/inicio.html')


def inicio_usuarios(request):
    return render(request, 'usuarios/inicio.html')


# Registro de usuario
def registro(request):
    # Maneja la lógica de registro de usuario
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Guarda el nuevo usuario en la base de datos
            login(request, user)  # Inicia sesión automáticamente con el nuevo usuario
            return redirect('gastos:    lista_gastos')  # Redirige a la lista de gastos
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
            return redirect('perfil_usuario')
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
