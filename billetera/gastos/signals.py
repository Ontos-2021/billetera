from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import connection
from django.apps import apps
import logging

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    # Only run for this app
    if getattr(sender, 'name', None) != 'gastos':
        return

    try:
        existing_tables = connection.introspection.table_names()
        if 'gastos_moneda' not in existing_tables:
            return

        Moneda = apps.get_model('gastos', 'Moneda')
        Categoria = apps.get_model('gastos', 'Categoria')

        monedas = [
            ('USD', 'Dólar Estadounidense', '$'),
            ('EUR', 'Euro', '€'),
            ('ARS', 'Peso Argentino', '$'),
            ('CLP', 'Peso Chileno', '$'),
        ]
        for codigo, nombre, simbolo in monedas:
            Moneda.objects.get_or_create(codigo=codigo, defaults={'nombre': nombre, 'simbolo': simbolo})

        categorias = [
            'Alimentación', 'Transporte', 'Entretenimiento', 'Salud', 'Vivienda',
            'Educación', 'Ropa', 'Viajes', 'Tecnología', 'Ahorros e Inversiones', 'Vicio'
        ]
        for nombre in categorias:
            Categoria.objects.get_or_create(nombre=nombre)

    except Exception as e:
        logger.exception('Error creating initial data (post_migrate): %s', e)
