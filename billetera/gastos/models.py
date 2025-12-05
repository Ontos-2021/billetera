from django.db import models
from django.db.models import Sum
from django.contrib.auth.models import User  # Importar el modelo de usuario
from django.utils import timezone  # Importar timezone


class Moneda(models.Model):
    nombre = models.CharField(max_length=30)
    codigo = models.CharField(max_length=3, unique=True)
    simbolo = models.CharField(max_length=5)

    def __str__(self):
        return self.nombre


# Initial data logic moved to gastos/signals.py to ensure it runs after migrations


class Categoria(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self) -> str:
        return self.nombre


class Tienda(models.Model):
    nombre = models.CharField(max_length=120)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tiendas', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('nombre', 'usuario')

    def __str__(self):
        return self.nombre


class Compra(models.Model):
    """
    Agrupa múltiples gastos de una misma compra/ticket.
    Permite mostrar compras globales como un único movimiento.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compras')
    fecha = models.DateTimeField(default=timezone.now)
    lugar = models.CharField(max_length=120, blank=True, help_text='Lugar o comercio donde se realizó la compra')
    tienda = models.ForeignKey(Tienda, on_delete=models.SET_NULL, null=True, blank=True, related_name='compras')
    cuenta = models.ForeignKey('cuentas.Cuenta', on_delete=models.SET_NULL, null=True, blank=True, related_name='compras')
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name='compras')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        items_count = self.items.count()
        return f"Compra en {self.lugar or 'Sin lugar'} - {items_count} items ({self.fecha.strftime('%d/%m/%Y')})"

    @property
    def total(self):
        """Retorna la suma de todos los gastos asociados a esta compra."""
        result = self.items.aggregate(total=Sum('monto'))
        return result['total'] or 0

    @property
    def items_count(self):
        """Retorna la cantidad de ítems en esta compra."""
        return self.items.count()


class Gasto(models.Model):
    usuario = models.ForeignKey(User,
                                on_delete=models.CASCADE,
                                related_name='gastos',  # Relación con usuario
                                null=True,
                                blank=True)
    descripcion = models.CharField(max_length=255)
    lugar = models.CharField(max_length=120, null=True, blank=True, help_text='Lugar o comercio donde se realizó la compra (ej: Carrefour, Kiosco, etc.)')
    tienda = models.ForeignKey(Tienda, on_delete=models.SET_NULL, null=True, blank=True, related_name='gastos')
    cantidad = models.PositiveIntegerField(default=1)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True, help_text='Monto de descuento aplicado')
    fecha = models.DateTimeField(default=timezone.now)
    moneda = models.ForeignKey(Moneda, on_delete=models.CASCADE, null=True, blank=True, related_name='gastos')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, null=True, blank=True, related_name='gastos')
    cuenta = models.ForeignKey('cuentas.Cuenta', on_delete=models.SET_NULL, null=True, blank=True, related_name='gastos')
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, null=True, blank=True, related_name='items',
                               help_text='Compra global a la que pertenece este gasto')

    def __str__(self):
        if self.moneda:
            return f"{self.descripcion} ({self.cantidad}) - {self.monto} {self.moneda.simbolo}"
        else:
            return f"{self.descripcion} ({self.cantidad}) - {self.monto}"

    @property
    def precio_unitario(self):
        if self.cantidad > 0:
            return self.monto / self.cantidad
        return self.monto
