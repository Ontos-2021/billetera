from django.shortcuts import render
from .models import Gasto

def lista_gastos(request):
    gastos = Gasto.objects.all()
    return render(request, 'gastos/lista_gastos.html', {'gastos': gastos})
