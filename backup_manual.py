"""
Script manual para hacer backup de la base de datos Postgres desde tu computadora.
Usa psycopg2 para el dump SQL y lo cifra antes de subir a R2.
"""
import os
import sys
import argparse
import getpass
from pathlib import Path
from urllib.parse import quote, urlparse

# Add Django to path
sys.path.insert(0, str(Path(__file__).parent / 'billetera'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'billetera.settings')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import django
django.setup()

from backup_postgres_local import run_postgres_backup_no_pgdump


def _env_first(*names: str) -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ''


def _build_db_url_from_env() -> str:
    direct_url = _env_first('EXTERNAL_DB_URL')
    if direct_url:
        return direct_url

    host = _env_first('EXTERNAL_DB_HOST', 'PGHOST')
    port = _env_first('EXTERNAL_DB_PORT', 'PGPORT')
    dbname = _env_first('EXTERNAL_DB_NAME', 'EXTERNAL_DB_DBNAME', 'PGDATABASE')
    user = _env_first('EXTERNAL_DB_USER', 'PGUSER')
    password = _env_first('EXTERNAL_DB_PASSWORD', 'PGPASSWORD')

    if not host:
        return ''

    auth = ''
    if user:
        auth = quote(user, safe='')
        if password:
            auth = f"{auth}:{quote(password, safe='')}"
        auth = f'{auth}@'

    host_part = host
    if port:
        host_part = f'{host}:{port}'

    path = f'/{quote(dbname, safe="")}' if dbname else ''
    return f'postgresql://{auth}{host_part}{path}'


def _normalize_db_url(url: str) -> str:
    """Normalize different user inputs into a postgres URL."""
    if not url:
        return url

    if '=' in url or url.startswith('postgres://') or url.startswith('postgresql://'):
        return url

    if '@' in url and not url.startswith('postgres'):
        return f'postgresql://{url}'

    parsed = urlparse('//' + url)
    host = parsed.hostname
    port = parsed.port
    path = parsed.path.lstrip('/') if parsed.path else ''

    if not host:
        return url

    dbname = path or _env_first('EXTERNAL_DB_NAME', 'EXTERNAL_DB_DBNAME', 'PGDATABASE') or input('Nombre de la base de datos (dbname): ').strip()
    user = _env_first('EXTERNAL_DB_USER', 'PGUSER') or input('Usuario de la base de datos (user): ').strip()
    while not user:
        user = input('Usuario (no vacío): ').strip()

    password = _env_first('EXTERNAL_DB_PASSWORD', 'PGPASSWORD')
    if not password:
        password = getpass.getpass('Password de la base de datos (password): ')

    auth = f"{quote(user, safe='')}:{quote(password, safe='')}@"
    host_part = host
    if port:
        host_part = f'{host}:{port}'

    return f'postgresql://{auth}{host_part}/{quote(dbname, safe="")}'


def _describe_target(url: str) -> str:
    if '=' in url and not url.startswith('postgres://') and not url.startswith('postgresql://'):
        pieces = dict(part.split('=', 1) for part in url.split() if '=' in part)
        host = pieces.get('host', 'database')
        port = pieces.get('port')
        dbname = pieces.get('dbname', '(sin dbname)')
        user = pieces.get('user', '(sin user)')
        suffix = f':{port}' if port else ''
        return f'{host}{suffix} | db={dbname} | user={user}'

    parsed = urlparse(url)
    host = parsed.hostname or 'database'
    port = f':{parsed.port}' if parsed.port else ''
    dbname = parsed.path.lstrip('/') or '(sin dbname)'
    user = parsed.username or '(sin user)'
    return f'{host}{port} | db={dbname} | user={user}'

if __name__ == '__main__':
    # IMPORTANTE: Pega aquí tu External Database URL del proveedor donde corre Postgres.

    parser = argparse.ArgumentParser(description='Backup manual de Postgres con cifrado y subida a R2.')
    parser.add_argument('external_db_url', nargs='?', help='External Database URL, DSN libpq o host:port[/dbname]')
    parser.add_argument('--check', action='store_true', help='Valida y muestra el destino de conexión sin ejecutar el backup')
    args = parser.parse_args()

    EXTERNAL_DB_URL = args.external_db_url or _build_db_url_from_env()

    if not EXTERNAL_DB_URL:
        EXTERNAL_DB_URL = input("Pega la External Database URL: ").strip()

    if not EXTERNAL_DB_URL:
        print("❌ Error: Debes proporcionar la External Database URL")
        sys.exit(1)

    EXTERNAL_DB_URL = _normalize_db_url(EXTERNAL_DB_URL)

    if args.check:
        print("✅ Configuración de conexión válida")
        print(f"📡 Destino: {_describe_target(EXTERNAL_DB_URL)}")
        sys.exit(0)

    print("🔐 Iniciando backup cifrado de la base de datos...")
    try:
        display = _describe_target(EXTERNAL_DB_URL)
    except Exception:
        display = 'database'
    print(f"📡 Conectando a: {display}")
    
    try:
        result = run_postgres_backup_no_pgdump(EXTERNAL_DB_URL)
        print(f"\n✅ Backup completado exitosamente!")
        print(f"   Engine: {result['engine']}")
        print(f"   Tamaño: {result['size_mb']} MB (cifrado)")
        print(f"   Archivo: {result['object_key']}")
        print(f"   URL R2: {result['r2_url']}")
        print(f"   Retención: {result['retention_kept']} backups mantenidos")
    except Exception as e:
        print(f"\n❌ Error al crear backup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
