from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Deuda, PagoDeuda
from .forms import DeudaForm, PagoDeudaForm
from gastos.models import Gasto, Categoria
from ingresos.models import Ingreso, CategoriaIngreso, Moneda as MonedaIngreso

class DeudaListView(LoginRequiredMixin, ListView):
    model = Deuda
    template_name = 'deudas/lista_deudas.html'
    context_object_name = 'deudas'

    def get_queryset(self):
        return Deuda.objects.filter(usuario=self.request.user).order_by('-fecha')

class DeudaCreateView(LoginRequiredMixin, CreateView):
    model = Deuda
    form_class = DeudaForm
    template_name = 'deudas/form_deuda.html'
    success_url = reverse_lazy('deudas:lista_deudas')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)

class DeudaUpdateView(LoginRequiredMixin, UpdateView):
    model = Deuda
    form_class = DeudaForm
    template_name = 'deudas/form_deuda.html'
    success_url = reverse_lazy('deudas:lista_deudas')

    def get_queryset(self):
        return Deuda.objects.filter(usuario=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Forzar actualización de estado por si cambió el monto
        self.object.actualizar_estado()
        return response

class DeudaDetailView(LoginRequiredMixin, DetailView):
    model = Deuda
    template_name = 'deudas/detalle_deuda.html'
    context_object_name = 'deuda'

    def get_queryset(self):
        return Deuda.objects.filter(usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pagos'] = self.object.pagos.all().order_by('-fecha')
        # Calcular progreso de pago
        monto_total = self.object.monto
        saldo_pendiente = self.object.saldo_pendiente()
        monto_pagado = monto_total - saldo_pendiente
        if monto_total > 0:
            porcentaje_pagado = int((monto_pagado / monto_total) * 100)
        else:
            porcentaje_pagado = 0
        context['monto_pagado'] = monto_pagado
        context['porcentaje_pagado'] = porcentaje_pagado
        return context

class PagoDeudaCreateView(LoginRequiredMixin, CreateView):
    model = PagoDeuda
    form_class = PagoDeudaForm
    template_name = 'deudas/form_pago.html'

    def dispatch(self, request, *args, **kwargs):
        self.deuda = get_object_or_404(Deuda, pk=kwargs['deuda_id'], usuario=request.user)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.deuda = self.deuda
        response = super().form_valid(form)
        
        # Verificar si se debe incluir en finanzas
        if form.cleaned_data.get('incluir_en_finanzas'):
            pago = self.object
            deuda = self.deuda
            
            if deuda.tipo == 'POR_PAGAR':
                # Crear Gasto
                categoria, _ = Categoria.objects.get_or_create(nombre='Deudas')
                gasto = Gasto.objects.create(
                    usuario=self.request.user,
                    descripcion=f"Pago de deuda a {deuda.persona}",
                    monto=pago.monto,
                    fecha=pago.fecha,
                    moneda=deuda.moneda,
                    categoria=categoria,
                    # Si hay nota, agregarla a la descripción o usarla
                )
                pago.gasto_relacionado = gasto
                pago.save()
                
            elif deuda.tipo == 'POR_COBRAR':
                # Crear Ingreso
                categoria, _ = CategoriaIngreso.objects.get_or_create(nombre='Deudas')
                # Buscar la moneda correspondiente en Ingresos
                moneda_ingreso, _ = MonedaIngreso.objects.get_or_create(
                    codigo=deuda.moneda.codigo,
                    defaults={
                        'nombre': deuda.moneda.nombre,
                        'simbolo': deuda.moneda.simbolo
                    }
                )
                
                ingreso = Ingreso.objects.create(
                    usuario=self.request.user,
                    descripcion=f"Cobro de deuda a {deuda.persona}",
                    monto=pago.monto,
                    fecha=pago.fecha,
                    moneda=moneda_ingreso,
                    categoria=categoria
                )
                pago.ingreso_relacionado = ingreso
                pago.save()
                
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['deuda'] = self.deuda
        return kwargs

    def get_success_url(self):
        return reverse_lazy('deudas:detalle_deuda', kwargs={'pk': self.deuda.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['deuda'] = self.deuda
        return context


class PagoDeudaUpdateView(LoginRequiredMixin, UpdateView):
    model = PagoDeuda
    form_class = PagoDeudaForm
    template_name = 'deudas/form_pago.html'

    def get_queryset(self):
        # Asegurar que el pago pertenece a una deuda del usuario
        return PagoDeuda.objects.filter(deuda__usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['deuda'] = self.object.deuda
        return context

    def get_success_url(self):
        return reverse_lazy('deudas:detalle_deuda', kwargs={'pk': self.object.deuda.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        pago = self.object
        deuda = pago.deuda
        
        # Actualizar estado de la deuda
        deuda.actualizar_estado()
        
        # Manejo de integración financiera
        incluir = form.cleaned_data.get('incluir_en_finanzas')
        
        if incluir:
            if deuda.tipo == 'POR_PAGAR':
                if pago.gasto_relacionado:
                    # Actualizar gasto existente
                    gasto = pago.gasto_relacionado
                    gasto.monto = pago.monto
                    gasto.fecha = pago.fecha
                    gasto.save()
                else:
                    # Crear nuevo gasto
                    categoria, _ = Categoria.objects.get_or_create(nombre='Deudas')
                    gasto = Gasto.objects.create(
                        usuario=self.request.user,
                        descripcion=f"Pago de deuda a {deuda.persona}",
                        monto=pago.monto,
                        fecha=pago.fecha,
                        moneda=deuda.moneda,
                        categoria=categoria,
                    )
                    pago.gasto_relacionado = gasto
                    pago.save()
            
            elif deuda.tipo == 'POR_COBRAR':
                if pago.ingreso_relacionado:
                    # Actualizar ingreso existente
                    ingreso = pago.ingreso_relacionado
                    ingreso.monto = pago.monto
                    ingreso.fecha = pago.fecha
                    ingreso.save()
                else:
                    # Crear nuevo ingreso
                    categoria, _ = CategoriaIngreso.objects.get_or_create(nombre='Deudas')
                    moneda_ingreso, _ = MonedaIngreso.objects.get_or_create(
                        codigo=deuda.moneda.codigo,
                        defaults={
                            'nombre': deuda.moneda.nombre,
                            'simbolo': deuda.moneda.simbolo
                        }
                    )
                    ingreso = Ingreso.objects.create(
                        usuario=self.request.user,
                        descripcion=f"Cobro de deuda a {deuda.persona}",
                        monto=pago.monto,
                        fecha=pago.fecha,
                        moneda=moneda_ingreso,
                        categoria=categoria
                    )
                    pago.ingreso_relacionado = ingreso
                    pago.save()
        else:
            # Si se desmarca, eliminar los relacionados si existen
            if pago.gasto_relacionado:
                pago.gasto_relacionado.delete()
                pago.gasto_relacionado = None
                pago.save()
            if pago.ingreso_relacionado:
                pago.ingreso_relacionado.delete()
                pago.ingreso_relacionado = None
                pago.save()
                
        return response

