from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from .models import Deuda, PagoDeuda
from .forms import DeudaForm, PagoDeudaForm
from gastos.models import Moneda, Gasto, Categoria
from ingresos.models import Ingreso, CategoriaIngreso

class DeudaTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='password')
        self.moneda, _ = Moneda.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dolar'})

    def test_crear_deuda(self):
        deuda = Deuda.objects.create(
            usuario=self.user,
            persona='Juan',
            tipo='POR_COBRAR',
            monto=100,
            moneda=self.moneda
        )
        self.assertEqual(deuda.estado, 'PENDIENTE')
        self.assertEqual(deuda.saldo_pendiente(), 100)

    def test_pago_parcial(self):
        deuda = Deuda.objects.create(
            usuario=self.user,
            persona='Juan',
            tipo='POR_COBRAR',
            monto=100,
            moneda=self.moneda
        )
        PagoDeuda.objects.create(deuda=deuda, monto=50)
        self.assertEqual(deuda.saldo_pendiente(), 50)
        self.assertEqual(deuda.estado, 'PENDIENTE')

    def test_pago_total(self):
        deuda = Deuda.objects.create(
            usuario=self.user,
            persona='Juan',
            tipo='POR_COBRAR',
            monto=100,
            moneda=self.moneda
        )
        PagoDeuda.objects.create(deuda=deuda, monto=100)
        deuda.refresh_from_db()
        self.assertEqual(deuda.saldo_pendiente(), 0)
        self.assertEqual(deuda.estado, 'PAGADA')

    def test_eliminar_pago(self):
        deuda = Deuda.objects.create(
            usuario=self.user,
            persona='Juan',
            tipo='POR_COBRAR',
            monto=100,
            moneda=self.moneda
        )
        pago = PagoDeuda.objects.create(deuda=deuda, monto=100)
        deuda.refresh_from_db()
        self.assertEqual(deuda.estado, 'PAGADA')
        
        pago.delete()
        deuda.refresh_from_db()
        self.assertEqual(deuda.estado, 'PENDIENTE')
        self.assertEqual(deuda.saldo_pendiente(), 100)

    def test_actualizar_estado_al_editar_deuda(self):
        """Verificar que el estado se actualiza si se cambia el monto de la deuda."""
        deuda = Deuda.objects.create(
            usuario=self.user,
            persona='Juan',
            tipo='POR_COBRAR',
            monto=100,
            moneda=self.moneda
        )
        PagoDeuda.objects.create(deuda=deuda, monto=100)
        deuda.refresh_from_db()
        self.assertEqual(deuda.estado, 'PAGADA')
        
        # Aumentar el monto de la deuda
        deuda.monto = 200
        deuda.save()
        deuda.refresh_from_db()
        self.assertEqual(deuda.estado, 'PENDIENTE')
        self.assertEqual(deuda.saldo_pendiente(), 100)


class FinanzasIntegrationTests(TestCase):
    """Tests para la integración con Gastos e Ingresos."""
    
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser_fin', password='password')
        self.moneda, _ = Moneda.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dolar'})
        self.client.login(username='testuser_fin', password='password')

    def test_crear_gasto_al_pagar_deuda(self):
        """Verificar que se crea un Gasto al pagar una deuda POR_PAGAR."""
        deuda = Deuda.objects.create(
            usuario=self.user,
            persona='Banco',
            tipo='POR_PAGAR',
            monto=1000,
            moneda=self.moneda
        )
        
        response = self.client.post(
            reverse('deudas:crear_pago', args=[deuda.pk]),
            {
                'monto': '500.00',
                'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
                'nota': 'Pago parcial',
                'incluir_en_finanzas': 'on'
            },
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se creó el pago
        pago = PagoDeuda.objects.first()
        self.assertIsNotNone(pago)
        self.assertEqual(pago.monto, 500)
        
        # Verificar que se creó el gasto relacionado
        self.assertIsNotNone(pago.gasto_relacionado)
        gasto = pago.gasto_relacionado
        self.assertEqual(gasto.monto, 500)
        self.assertEqual(gasto.categoria.nombre, 'Deudas')
        self.assertEqual(gasto.descripcion, f"Pago de deuda a {deuda.persona}")

    def test_crear_ingreso_al_cobrar_deuda(self):
        """Verificar que se crea un Ingreso al cobrar una deuda POR_COBRAR."""
        deuda = Deuda.objects.create(
            usuario=self.user,
            persona='Amigo',
            tipo='POR_COBRAR',
            monto=1000,
            moneda=self.moneda
        )
        
        response = self.client.post(
            reverse('deudas:crear_pago', args=[deuda.pk]),
            {
                'monto': '500.00',
                'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
                'nota': 'Cobro parcial',
                'incluir_en_finanzas': 'on'
            },
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se creó el pago
        pago = PagoDeuda.objects.first()
        self.assertIsNotNone(pago)
        
        # Verificar que se creó el ingreso relacionado
        self.assertIsNotNone(pago.ingreso_relacionado)
        ingreso = pago.ingreso_relacionado
        self.assertEqual(ingreso.monto, 500)
        self.assertEqual(ingreso.categoria.nombre, 'Deudas')
        self.assertEqual(ingreso.descripcion, f"Cobro de deuda a {deuda.persona}")

    def test_no_crear_finanzas_si_checkbox_desactivado(self):
        """Verificar que NO se crea Gasto/Ingreso si el checkbox no está marcado."""
        deuda = Deuda.objects.create(
            usuario=self.user,
            persona='Banco',
            tipo='POR_PAGAR',
            monto=1000,
            moneda=self.moneda
        )
        
        response = self.client.post(
            reverse('deudas:crear_pago', args=[deuda.pk]),
            {
                'monto': '500.00',
                'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'),
                'nota': 'Pago parcial'
                # incluir_en_finanzas no enviado
            },
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        
        pago = PagoDeuda.objects.first()
        self.assertIsNone(pago.gasto_relacionado)
        self.assertIsNone(pago.ingreso_relacionado)
        self.assertEqual(Gasto.objects.count(), 0)
        self.assertEqual(Ingreso.objects.count(), 0)


class DeudaProgresoTests(TestCase):
    """Tests para la funcionalidad de progreso de pago en la vista de detalle."""
    
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser2', password='password')
        self.moneda, _ = Moneda.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dolar'})
        self.deuda = Deuda.objects.create(
            usuario=self.user,
            persona='Maria',
            tipo='POR_COBRAR',
            monto=200,
            moneda=self.moneda
        )
        self.client.login(username='testuser2', password='password')

    def test_progreso_sin_pagos(self):
        """El progreso debe ser 0% cuando no hay pagos."""
        response = self.client.get(reverse('deudas:detalle_deuda', args=[self.deuda.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['monto_pagado'], 0)
        self.assertEqual(response.context['porcentaje_pagado'], 0)

    def test_progreso_pago_parcial(self):
        """El progreso debe reflejar el porcentaje pagado."""
        PagoDeuda.objects.create(deuda=self.deuda, monto=50)  # 50 de 200 = 25%
        response = self.client.get(reverse('deudas:detalle_deuda', args=[self.deuda.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['monto_pagado'], 50)
        self.assertEqual(response.context['porcentaje_pagado'], 25)

    def test_progreso_multiples_pagos(self):
        """El progreso debe sumar todos los pagos."""
        PagoDeuda.objects.create(deuda=self.deuda, monto=50)
        PagoDeuda.objects.create(deuda=self.deuda, monto=30)  # Total: 80 de 200 = 40%
        response = self.client.get(reverse('deudas:detalle_deuda', args=[self.deuda.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['monto_pagado'], 80)
        self.assertEqual(response.context['porcentaje_pagado'], 40)

    def test_progreso_pago_completo(self):
        """El progreso debe ser 100% cuando la deuda está completamente pagada."""
        PagoDeuda.objects.create(deuda=self.deuda, monto=200)
        response = self.client.get(reverse('deudas:detalle_deuda', args=[self.deuda.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['monto_pagado'], 200)
        self.assertEqual(response.context['porcentaje_pagado'], 100)

    def test_progreso_en_template(self):
        """El template debe mostrar el progreso correctamente."""
        PagoDeuda.objects.create(deuda=self.deuda, monto=100)  # 50%
        response = self.client.get(reverse('deudas:detalle_deuda', args=[self.deuda.pk]))
        self.assertContains(response, 'width: 50%')
        # Verificar que el monto pagado y total aparecen en la respuesta
        # El formato puede ser 100.00 o 100,00 dependiendo de la configuración regional
        content = response.content.decode('utf-8')
        self.assertTrue('100,00' in content or '100.00' in content)  # Monto pagado
        self.assertTrue('200,00' in content or '200.00' in content)  # Monto total


class MontosRapidosTests(TestCase):
    """Tests para verificar que los montos rápidos se muestran correctamente en el template."""
    
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser3', password='password')
        self.moneda, _ = Moneda.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dolar', 'simbolo': '$'})
        self.deuda = Deuda.objects.create(
            usuario=self.user,
            persona='Carlos',
            tipo='POR_COBRAR',
            monto=Decimal('400.00'),
            moneda=self.moneda
        )
        self.client.login(username='testuser3', password='password')

    def test_template_muestra_boton_total(self):
        """El template debe mostrar el botón de monto total."""
        response = self.client.get(reverse('deudas:crear_pago', args=[self.deuda.pk]))
        self.assertEqual(response.status_code, 200)
        # Verificar que el botón Total está presente
        self.assertContains(response, 'Total')
        self.assertContains(response, 'setAmount(400')

    def test_template_muestra_boton_50_porciento(self):
        """El template debe mostrar el botón de 50%."""
        response = self.client.get(reverse('deudas:crear_pago', args=[self.deuda.pk]))
        self.assertEqual(response.status_code, 200)
        # Verificar que el botón 50% está presente
        self.assertContains(response, '50%')
        # Verificar que el cálculo usa * 0.5
        self.assertContains(response, '* 0.5')

    def test_template_muestra_boton_25_porciento(self):
        """El template debe mostrar el botón de 25%."""
        response = self.client.get(reverse('deudas:crear_pago', args=[self.deuda.pk]))
        self.assertEqual(response.status_code, 200)
        # Verificar que el botón 25% está presente
        self.assertContains(response, '25%')
        # Verificar que el cálculo usa * 0.25
        self.assertContains(response, '* 0.25')

    def test_pago_25_porciento(self):
        """Verificar que se puede crear un pago del 25%."""
        monto_25_porciento = (self.deuda.saldo_pendiente() * Decimal('0.25')).quantize(Decimal('0.01'))
        response = self.client.post(
            reverse('deudas:crear_pago', args=[self.deuda.pk]),
            {'monto': str(monto_25_porciento), 'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'), 'nota': 'Pago 25%'},
        )
        # Si hay errores de formulario, mostrarlos
        if response.status_code == 200 and response.context.get('form'):
            self.fail(f"Form errors: {response.context['form'].errors}")
        self.assertEqual(response.status_code, 302)  # Redirect después de crear
        self.deuda.refresh_from_db()
        # Saldo debe ser 75% del original (400 - 100 = 300)
        self.assertEqual(self.deuda.saldo_pendiente(), Decimal('300.00'))

    def test_pago_50_porciento(self):
        """Verificar que se puede crear un pago del 50%."""
        monto_50_porciento = (self.deuda.saldo_pendiente() * Decimal('0.50')).quantize(Decimal('0.01'))
        response = self.client.post(
            reverse('deudas:crear_pago', args=[self.deuda.pk]),
            {'monto': str(monto_50_porciento), 'fecha': timezone.now().strftime('%Y-%m-%dT%H:%M'), 'nota': 'Pago 50%'},
        )
        # Si hay errores de formulario, mostrarlos
        if response.status_code == 200 and response.context.get('form'):
            self.fail(f"Form errors: {response.context['form'].errors}")
        self.assertEqual(response.status_code, 302)
        self.deuda.refresh_from_db()
        # Saldo debe ser 50% del original (400 - 200 = 200)
        self.assertEqual(self.deuda.saldo_pendiente(), Decimal('200.00'))


class FormularioFechaTests(TestCase):
    """Tests para verificar que los formularios manejan fechas correctamente."""
    
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser4', password='password')
        self.moneda, _ = Moneda.objects.get_or_create(codigo='USD', defaults={'nombre': 'Dolar', 'simbolo': '$'})

    def test_deuda_form_fecha_inicial(self):
        """El formulario de deuda debe tener la fecha y hora actual como inicial."""
        form = DeudaForm()
        # Verificar que el valor inicial es un datetime o string con formato correcto
        initial_fecha = form.initial.get('fecha')
        self.assertIsNotNone(initial_fecha)
        # Puede ser un objeto datetime o string dependiendo de cómo se inicialice
        # Si es datetime, comparamos fechas
        if hasattr(initial_fecha, 'date'):
            self.assertEqual(initial_fecha.date(), timezone.localdate())
        else:
            # Si es string, verificar formato
            self.assertTrue(len(str(initial_fecha)) > 10)

    def test_pago_form_fecha_inicial(self):
        """El formulario de pago debe tener la fecha y hora actual como inicial."""
        form = PagoDeudaForm()
        initial_fecha = form.initial.get('fecha')
        self.assertIsNotNone(initial_fecha)
        if hasattr(initial_fecha, 'date'):
            self.assertEqual(initial_fecha.date(), timezone.localdate())

    def test_deuda_form_acepta_fecha_valida(self):
        """El formulario de deuda debe aceptar una fecha y hora válida."""
        form_data = {
            'persona': 'Test Person',
            'tipo': 'POR_COBRAR',
            'monto': '100.00',
            'moneda': self.moneda.pk,
            'fecha': '2025-12-06T14:30',
            'descripcion': ''
        }
        form = DeudaForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_pago_form_acepta_fecha_valida(self):
        """El formulario de pago debe aceptar una fecha y hora válida."""
        form_data = {
            'monto': '50.00',
            'fecha': '2025-12-06T14:30',
            'nota': ''
        }
        form = PagoDeudaForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_deuda_form_widget_tipo_datetime(self):
        """El widget de fecha debe ser de tipo datetime-local."""
        form = DeudaForm()
        rendered_widget = str(form['fecha'])
        self.assertIn('type="datetime-local"', rendered_widget)

    def test_pago_form_widget_tipo_datetime(self):
        """El widget de fecha debe ser de tipo datetime-local."""
        form = PagoDeudaForm()
        rendered_widget = str(form['fecha'])
        self.assertIn('type="datetime-local"', rendered_widget)
