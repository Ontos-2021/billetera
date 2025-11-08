import os
import shutil
import tempfile
import subprocess
from datetime import datetime, timezone

import boto3
from cryptography.fernet import Fernet
from django.conf import settings


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')


def _get_fernet() -> Fernet:
    key = os.getenv('BACKUP_FERNET_KEY')
    if not key:
        raise RuntimeError('BACKUP_FERNET_KEY no está definido. Genera uno con Fernet.generate_key().')
    # Admite str o bytes
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
        raise RuntimeError('Faltan variables R2: AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY/AWS_STORAGE_BUCKET_NAME/AWS_S3_ENDPOINT_URL')

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


def run_database_backup() -> dict:
    """
    Crea un respaldo cifrado de la base de datos y lo sube a R2 (Cloudflare).
    Retorna un diccionario con información del respaldo.
    """
    db_engine = settings.DATABASES['default']['ENGINE']
    env = os.getenv('ENV', os.getenv('DJANGO_ENV', 'development'))
    ts = _timestamp()
    prefix = f'backups/db/{env}/'
    retention = int(os.getenv('BACKUP_RETENTION_COUNT', '7'))

    with tempfile.TemporaryDirectory() as tmp:
        if 'postgresql' in db_engine:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise RuntimeError('DATABASE_URL no está definido para Postgres.')

            dump_path = os.path.join(tmp, f'pg-{ts}.dump')
            if shutil.which('pg_dump') is None:
                raise RuntimeError('pg_dump no encontrado. Instala postgresql-client en el contenedor.')

            cmd = ['pg_dump', database_url, '-Fc', '-f', dump_path]
            subprocess.check_call(cmd)

            to_encrypt_path = dump_path
            remote_name = f'{prefix}postgres-{ts}.dump.enc'

        elif 'sqlite3' in db_engine:
            src = settings.DATABASES['default']['NAME']
            if not os.path.exists(src):
                raise RuntimeError(f'Archivo SQLite no encontrado: {src}')
            copy_path = os.path.join(tmp, f'sqlite-{ts}.sqlite3')
            shutil.copy2(src, copy_path)
            to_encrypt_path = copy_path
            remote_name = f'{prefix}sqlite-{ts}.sqlite3.enc'
        else:
            raise RuntimeError(f'Motor de BD no soportado para backup: {db_engine}')

        # Cifrado con Fernet
        fernet = _get_fernet()
        with open(to_encrypt_path, 'rb') as f:
            data = f.read()
        encrypted = fernet.encrypt(data)

        enc_path = f'{to_encrypt_path}.enc'
        with open(enc_path, 'wb') as f:
            f.write(encrypted)

        # Subir a R2
        r2_url = _upload_encrypted_to_r2(enc_path, remote_name)

        # Política de retención
        _apply_retention(prefix, retention)

        return {
            'engine': db_engine,
            'object_key': remote_name,
            'r2_url': r2_url,
            'retention_kept': retention,
        }
