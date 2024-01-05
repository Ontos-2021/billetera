Para agregar información inicial a tu base de datos en Django, puedes utilizar las **"fixtures"** o los **"señales"**. Aquí te explico ambas opciones:

**1. Fixtures:**

Las fixtures son archivos que contienen datos iniciales que se pueden cargar en la base de datos. Puedes crear un archivo JSON, YAML o XML que contenga los datos iniciales para tus modelos y luego cargarlo en la base de datos.

1. Crea un archivo JSON (por ejemplo, `initial_data.json`) con los datos iniciales para tus modelos. Aquí tienes un ejemplo para el modelo `Moneda`:

```json
[
    {
        "model": "gastos.moneda",
        "pk": 1,
        "fields": {
            "codigo": "USD",
            "nombre": "Dólar Estadounidense",
            "simbolo": "$"
        }
    },
    {
        "model": "gastos.moneda",
        "pk": 2,
        "fields": {
            "codigo": "EUR",
            "nombre": "Euro",
            "simbolo": "€"
        }
    }
]
```

2. Guarda este archivo JSON en una ubicación adecuada en tu proyecto.

3. Para cargar los datos en la base de datos, utiliza el siguiente comando de Django:

```bash
python manage.py loaddata initial_data.json
```

Esto cargará los datos iniciales en la base de datos y los hará disponibles cuando alguien clone el proyecto y ejecute las migraciones.

**2. Señales (Signals):**

Puedes utilizar señales para crear datos iniciales automáticamente cuando se crea una nueva instancia de tu modelo. Aquí tienes un ejemplo para el modelo `Moneda`:

```python
from django.db import models
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class Moneda(models.Model):
    codigo = models.CharField(max_length=3, unique=True)
    nombre = models.CharField(max_length=255)
    simbolo = models.CharField(max_length=10)

    def __str__(self):
        return self.nombre

@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'gastos':
        # Crea instancias de Moneda si no existen
        if not Moneda.objects.filter(codigo='USD').exists():
            Moneda.objects.create(codigo='USD', nombre='Dólar Estadounidense', simbolo='$')
        if not Moneda.objects.filter(codigo='EUR').exists():
            Moneda.objects.create(codigo='EUR', nombre='Euro', simbolo='€')
```

El código anterior utiliza una señal `post_migrate` que se dispara después de que se ejecutan las migraciones. Verifica si las instancias de `Moneda` con códigos 'USD' y 'EUR' existen en la base de datos y las crea si no existen.

Puedes adaptar este enfoque para otros modelos y datos iniciales que necesites agregar automáticamente a tu base de datos.

Ambos métodos tienen sus ventajas y desventajas, así que elige el que mejor se adapte a tus necesidades y preferencias.

---

Me alegra que el código funcione. Es cierto que `sender.name` hace referencia al nombre de la aplicación en lugar del nombre del modelo en este contexto. Esto puede parecer confuso, pero funciona porque la mayoría de las aplicaciones en Django tienen un nombre que coincide con el nombre del modelo principal en esa aplicación.

En tu caso, si el nombre de tu aplicación es 'gastos' y el modelo principal de esa aplicación es 'Moneda', entonces `sender.name` será igual a 'gastos' cuando se realicen las migraciones para el modelo 'Moneda'. Por lo tanto, el código que verifica si `sender.name == 'gastos'` se ejecutará en ese momento.

Si en el futuro agregas más modelos en tu aplicación 'gastos', este enfoque seguirá funcionando siempre y cuando `sender.name` sea igual al nombre de la aplicación 'gastos'.

Django maneja internamente la relación entre aplicaciones y modelos, por lo que este enfoque suele ser conveniente y funciona bien en la mayoría de los casos.
