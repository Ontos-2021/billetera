from django.contrib import admin
from .models import Gasto, Moneda

# Registra los modelos y las clases de administración
admin.site.register(Gasto)
admin.site.register(Moneda)
