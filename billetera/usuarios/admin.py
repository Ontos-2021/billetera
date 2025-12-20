from django.contrib import admin
from .models import PerfilUsuario, Plan, Suscripcion

admin.site.register(PerfilUsuario)

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio')

@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'plan', 'activo', 'fecha_fin')
    list_filter = ('plan', 'activo')
