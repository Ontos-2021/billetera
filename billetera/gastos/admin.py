from django.contrib import admin
from .models import Gasto, Moneda, Categoria

# Registra los modelos y las clases de administración
admin.site.register(Gasto)
admin.site.register(Moneda)
admin.site.register(Categoria)