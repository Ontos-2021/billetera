from django.test import TestCase
from django.contrib.auth.models import User
from .models import Moneda, CategoriaIngreso, Ingreso


class IngresoModelTestCase(TestCase):
    def setUp(self):
        # Crear usuario para las pruebas
        self.usuario = User.objects.create_user(username='testuser', password='12345')

        # Crear algunas monedas si no existen
        self.moneda_usd, created = Moneda.objects.get_or_create(nombre='Dólar Estadounidense', codigo='USD',
                                                                simbolo='$')
        self.moneda_eur, created = Moneda.objects.get_or_create(nombre='Euro', codigo='EUR', simbolo='€')

        # Crear algunas categorías de ingresos si no existen
        self.categoria_salario, created = CategoriaIngreso.objects.get_or_create(nombre='Salario')
        self.categoria_freelance, created = CategoriaIngreso.objects.get_or_create(nombre='Freelance')

        # Crear ingreso de ejemplo
        self.ingreso = Ingreso.objects.create(
            usuario=self.usuario,
            descripcion='Pago por proyecto freelance',
            monto=500.00,
            moneda=self.moneda_usd,
            categoria=self.categoria_freelance
        )

    def test_crear_ingreso(self):
        # Verificar que el ingreso se ha creado correctamente
        ingreso = Ingreso.objects.get(id=self.ingreso.id)
        self.assertEqual(ingreso.descripcion, 'Pago por proyecto freelance')
        self.assertEqual(ingreso.monto, 500.00)
        self.assertEqual(ingreso.moneda.codigo, 'USD')
        self.assertEqual(ingreso.categoria.nombre, 'Freelance')
        self.assertEqual(ingreso.usuario.username, 'testuser')

    def test_str_ingreso(self):
        # Verificar que el método __str__ devuelve el formato correcto
        self.assertEqual(str(self.ingreso), 'Pago por proyecto freelance - 500.0 $')

    def test_ingreso_sin_moneda(self):
        # Crear ingreso sin especificar moneda
        ingreso_sin_moneda = Ingreso.objects.create(
            usuario=self.usuario,
            descripcion='Ingreso sin moneda',
            monto=300.00,
            categoria=self.categoria_salario
        )
        self.assertIsNone(ingreso_sin_moneda.moneda)

    def test_crear_categoria_ingreso(self):
        # Verificar que la categoría de ingreso se ha creado correctamente
        categoria = CategoriaIngreso.objects.get(nombre='Salario')
        self.assertEqual(categoria.nombre, 'Salario')

    def test_crear_moneda(self):
        # Verificar que la moneda se ha creado correctamente
        moneda = Moneda.objects.get(codigo='EUR')
        self.assertEqual(moneda.nombre, 'Euro')
        self.assertEqual(moneda.simbolo, '€')

    # Test para que no se pueda crear un ingreso negativo
