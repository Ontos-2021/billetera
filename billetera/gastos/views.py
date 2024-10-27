from django.shortcuts import render, redirect, get_object_or_404
from .models import Gasto
from .forms import GastoForm
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions
from .serializers import GastoSerializer
from .permissions import IsAdminOrReadOwnOnly


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
    return render(request, 'gastos/lista_gastos.html', {'gastos': gastos})


# Crear gasto
@login_required  # Requiere que el usuario esté autenticado
def crear_gasto(request):
    if request.method == 'POST':
        form = GastoForm(request.POST)
        if form.is_valid():
            gasto = form.save(commit=False)  # Crea un objeto Gasto sin guardarlo aún
            gasto.usuario = request.user  # Asocia el gasto con el usuario autenticado
            gasto.save()  # Guarda el gasto en la base de datos
            return redirect('lista_gastos')  # Redirige a la lista de gastos
    else:
        form = GastoForm()  # Crea un formulario de gasto vacío
    return render(request, 'gastos/crear_gasto.html', {'form': form})


# Editar gasto
@login_required  # Requiere que el usuario esté autenticado
def editar_gasto(request, id):
    # Obtiene el gasto por id, asegurándose de que pertenezca al usuario (excepto si es superusuario)
    gasto = get_object_or_404(Gasto, id=id, usuario=request.user if not request.user.is_superuser else None)
    if request.method == 'POST':
        form = GastoForm(request.POST, instance=gasto)  # Crea un formulario con los datos del gasto existente
        if form.is_valid():
            form.save()  # Guarda los cambios realizados en el gasto
            return redirect('lista_gastos')  # Redirige a la lista de gastos
    else:
        form = GastoForm(instance=gasto)  # Crea un formulario con los datos del gasto para editar
    return render(request, 'gastos/editar_gasto.html', {'form': form})


# Eliminar gasto
@login_required  # Requiere que el usuario esté autenticado
def eliminar_gasto(request, id):
    # Obtiene el gasto por id, asegurándose de que pertenezca al usuario
    gasto = get_object_or_404(Gasto, id=id, usuario=request.user)
    if request.method == 'POST':
        gasto.delete()  # Elimina el gasto de la base de datos
        return redirect('lista_gastos')  # Redirige a la lista de gastos
    return render(request, 'gastos/eliminar_gasto.html', {'gasto': gasto})


# API REST para gestionar los gastos
class GastoViewSet(viewsets.ModelViewSet):
    queryset = Gasto.objects.all()  # Define el conjunto de datos inicial para la vista
    serializer_class = GastoSerializer  # Define el serializador a utilizar
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOwnOnly]  # Define los permisos para la vista

    def get_queryset(self):
        # Los superusuarios pueden ver todos los gastos
        if self.request.user.is_superuser:
            return Gasto.objects.all()

        # Filtrar gastos por usuario para usuarios normales
        queryset = Gasto.objects.filter(usuario=self.request.user)

        # Filtrar por fecha si se proporciona en los parámetros de la solicitud
        fecha = self.request.query_params.get('fecha', None)
        if fecha:
            queryset = queryset.filter(fecha=fecha)

        # Filtrar por categoría si se proporciona en los parámetros de la solicitud
        categoria = self.request.query_params.get('categoria', None)
        if categoria:
            queryset = queryset.filter(categoria=categoria)

        return queryset

    def perform_create(self, serializer):
        # Asocia automáticamente el usuario autenticado al crear un nuevo gasto
        serializer.save(usuario=self.request.user)
