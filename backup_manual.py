"""
Script manual para hacer backup de la base de datos Postgres desde tu computadora.
Usa psycopg2 para el dump SQL y lo cifra antes de subir a R2.
"""
import os
import sys
from pathlib import Path

# Add Django to path
sys.path.insert(0, str(Path(__file__).parent / 'billetera'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'billetera.settings')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import django
django.setup()

from backup_postgres_local import run_postgres_backup_no_pgdump

if __name__ == '__main__':
    # IMPORTANTE: Pega aquí tu External Database URL de Render
    # La encuentras en el dashboard de Render, sección "Connections" -> "External Database URL"
    
    EXTERNAL_DB_URL = os.getenv('EXTERNAL_DB_URL')
    
    if len(sys.argv) > 1:
        EXTERNAL_DB_URL = sys.argv[1]
        
    if not EXTERNAL_DB_URL:
        EXTERNAL_DB_URL = input("Pega la External Database URL de Render: ").strip()
    
    if not EXTERNAL_DB_URL:
        print("❌ Error: Debes proporcionar la External Database URL")
        sys.exit(1)
    
    print("🔐 Iniciando backup cifrado de la base de datos de Render...")
    print(f"📡 Conectando a: {EXTERNAL_DB_URL.split('@')[1] if '@' in EXTERNAL_DB_URL else 'database'}")
    
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
