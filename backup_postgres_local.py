"""
Backup alternativo sin pg_dump - usa psycopg2 directamente.
"""
import os
import io
import tempfile
import subprocess
from datetime import datetime, timezone

import boto3
import psycopg2
from cryptography.fernet import Fernet
from django.conf import settings


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')


def _get_fernet() -> Fernet:
    key = os.getenv('BACKUP_FERNET_KEY')
    if not key:
        raise RuntimeError('BACKUP_FERNET_KEY no está definido.')
    try:
        return Fernet(key)
    except Exception:
        return Fernet(key.encode())


def _r2_client():
    aws_id = os.getenv('AWS_ACCESS_KEY_ID') or getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY') or getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
    bucket = os.getenv('AWS_STORAGE_BUCKET_NAME') or getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    endpoint = os.getenv('AWS_S3_ENDPOINT_URL') or getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
    region = os.getenv('AWS_S3_REGION_NAME') or getattr(settings, 'AWS_S3_REGION_NAME', 'auto')

    if not all([aws_id, aws_secret, bucket, endpoint]):
        raise RuntimeError('Faltan variables R2.')

    client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=aws_id,
        aws_secret_access_key=aws_secret,
        region_name=region,
    )
    return client, bucket


def _upload_encrypted_to_r2(local_path: str, key_name: str) -> str:
    client, bucket = _r2_client()
    extra = {
        'ContentType': 'application/octet-stream',
        'ServerSideEncryption': 'AES256',
    }
    client.upload_file(local_path, bucket, key_name, ExtraArgs=extra)
    return f's3://{bucket}/{key_name}'


def _apply_retention(prefix: str, keep: int) -> None:
    client, bucket = _r2_client()
    resp = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    if resp.get('KeyCount', 0) == 0 or 'Contents' not in resp:
        return

    objs = sorted(resp['Contents'], key=lambda x: x['LastModified'], reverse=True)
    to_delete = objs[keep:]
    if not to_delete:
        return

    client.delete_objects(
        Bucket=bucket,
        Delete={'Objects': [{'Key': o['Key']} for o in to_delete]},
    )


def run_postgres_backup_no_pgdump(external_db_url: str) -> dict:
    """
    Backup de Postgres sin pg_dump - usa SQL directo via psycopg2.
    """
    env = os.getenv('ENV', os.getenv('DJANGO_ENV', 'development'))
    ts = _timestamp()
    prefix = f'backups/db/{env}/'
    retention = int(os.getenv('BACKUP_RETENTION_COUNT', '7'))

    with tempfile.TemporaryDirectory() as tmp:
        dump_path = os.path.join(tmp, f'pg-{ts}.sql')
        
        print(f"📊 Conectando a la base de datos...")
        # Usar pg_dump via subprocess si está disponible en PATH
        # Si no, usar psycopg2 para dump básico
        try:
            # Intentar con pg_dump primero
            cmd = ['pg_dump', external_db_url, '-f', dump_path]
            subprocess.check_call(cmd)
            print(f"✅ Dump generado con pg_dump")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: dump manual con psycopg2
            print(f"⚠️  pg_dump no disponible, usando dump SQL manual...")
            conn = psycopg2.connect(external_db_url)
            
            with open(dump_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("-- PostgreSQL database dump\n")
                f.write(f"-- Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
                
                cur = conn.cursor()
                
                # Get all tables
                cur.execute("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public' 
                    ORDER BY tablename;
                """)
                tables = [row[0] for row in cur.fetchall()]
                
                print(f"📋 Respaldando {len(tables)} tablas...")
                
                for table in tables:
                    print(f"   - {table}")
                    # Structure
                    cur.execute(f"""
                        SELECT 'CREATE TABLE ' || quote_ident('{table}') || ' (' ||
                        string_agg(quote_ident(column_name) || ' ' || data_type, ', ') || ');'
                        FROM information_schema.columns
                        WHERE table_name = '{table}'
                        GROUP BY table_name;
                    """)
                    
                    # Data
                    cur.execute(f"SELECT * FROM {table};")
                    rows = cur.fetchall()
                    
                    if rows:
                        f.write(f"\n-- Data for {table}\n")
                        cur.execute(f"""
                            SELECT column_name FROM information_schema.columns
                            WHERE table_name = '{table}'
                            ORDER BY ordinal_position;
                        """)
                        columns = [row[0] for row in cur.fetchall()]
                        
                        for row in rows:
                            values = []
                            for val in row:
                                if val is None:
                                    values.append('NULL')
                                elif isinstance(val, str):
                                    escaped = val.replace("'", "''")
                                    values.append(f"'{escaped}'")
                                else:
                                    values.append(str(val))
                            
                            f.write(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
                
                cur.close()
            conn.close()
            print(f"✅ Dump SQL manual generado")

        remote_name = f'{prefix}postgres-{ts}.sql.enc'

        # Cifrado con Fernet
        print(f"🔐 Cifrando backup...")
        fernet = _get_fernet()
        with open(dump_path, 'rb') as f:
            data = f.read()
        encrypted = fernet.encrypt(data)

        enc_path = f'{dump_path}.enc'
        with open(enc_path, 'wb') as f:
            f.write(encrypted)

        # Subir a R2
        print(f"☁️  Subiendo a Cloudflare R2...")
        r2_url = _upload_encrypted_to_r2(enc_path, remote_name)

        # Política de retención
        print(f"🗑️  Aplicando política de retención ({retention} backups)...")
        _apply_retention(prefix, retention)

        return {
            'engine': 'PostgreSQL',
            'object_key': remote_name,
            'r2_url': r2_url,
            'retention_kept': retention,
            'size_mb': round(len(encrypted) / 1024 / 1024, 2),
        }
