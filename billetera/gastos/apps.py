from django.apps import AppConfig


class GastosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gastos'

    def ready(self):
        # Import signals to register post_migrate handlers
        import gastos.signals  # noqa: F401