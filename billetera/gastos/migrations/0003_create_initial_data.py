from django.db import migrations


def create_initial(apps, schema_editor):
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


def reverse_initial(apps, schema_editor):
    # Do not delete user data on rollback; keep this no-op to be safe
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('gastos', '0002_categoria_moneda_gasto_lugar_gasto_usuario_and_more'),
    ]

    operations = [
        migrations.RunPython(create_initial, reverse_initial),
    ]
