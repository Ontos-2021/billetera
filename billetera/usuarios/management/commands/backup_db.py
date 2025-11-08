from django.core.management.base import BaseCommand
from usuarios.backup import run_database_backup


class Command(BaseCommand):
    help = "Genera un respaldo cifrado de la base de datos y lo sube a Cloudflare R2."

    def handle(self, *args, **options):
        result = run_database_backup()
        self.stdout.write(self.style.SUCCESS(f"Backup OK: {result['object_key']} (retención {result['retention_kept']})"))