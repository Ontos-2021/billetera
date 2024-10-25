from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import PerfilUsuario
from .forms import PerfilUsuarioForm


def inicio_usuarios(request):
    return render(request, 'usuarios/inicio.html')


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
