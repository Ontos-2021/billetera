from django.contrib import admin
from .models import Gasto, Moneda, Categoria, Compra


class GastoInline(admin.TabularInline):
    """Inline para mostrar los gastos de una compra."""
    model = Gasto
    extra = 0
    fields = ('descripcion', 'categoria', 'cantidad', 'monto')
    readonly_fields = ('descripcion', 'categoria', 'cantidad', 'monto')
    can_delete = False
    show_change_link = True


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    """Admin para gestionar compras globales."""
    list_display = ('id', 'lugar', 'usuario', 'fecha', 'cuenta', 'moneda', 'items_count', 'get_total')
    list_filter = ('moneda', 'cuenta', 'fecha')
    search_fields = ('lugar', 'usuario__username')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    inlines = [GastoInline]
    
    def get_total(self, obj):
        return f"{obj.moneda.simbolo}{obj.total}"
    get_total.short_description = 'Total'
    
    def items_count(self, obj):
        return obj.items_count
    items_count.short_description = 'Items'


# Registra los modelos y las clases de administración
admin.site.register(Gasto)
admin.site.register(Moneda)
admin.site.register(Categoria)