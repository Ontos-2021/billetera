# Railway Deploy Runbook

## Objetivo

Dejar un flujo claro y único para operar este proyecto en Railway.

## Variables mínimas

- `ENV=production`
- `DEBUG=0`
- `SECRET_KEY`
- `DATABASE_URL`
- `APP_BASE_URL=https://your-app.up.railway.app`
- `ALLOWED_HOSTS=your-app.up.railway.app`
- `CSRF_TRUSTED_ORIGINS=https://your-app.up.railway.app`

Variables adicionales según features activas:

- R2: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`
- Google login: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- Mercado Pago: `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_PUBLIC_KEY`, `MERCADOPAGO_WEBHOOK_SECRET`
- Backups: `BACKUP_FERNET_KEY`, `BACKUP_WEBHOOK_TOKEN`

## Ruta de arranque canónica

- Startup principal: [entrypoint.sh](../entrypoint.sh)
- [Procfile](../Procfile) quedó alineado al mismo entrypoint para evitar drift.

## Qué hace el startup

1. `python manage.py check`
2. `python manage.py makemigrations --check --dry-run`
3. `python manage.py migrate --noinput`
4. `python manage.py collectstatic --noinput`
5. `python manage.py bootstrap_google_socialapp` si aplica
6. `gunicorn billetera.wsgi`

## Verificación post deploy

1. `GET /health/` debe devolver `200` con `{"status": "ok", "database": "ok"}`
2. El login web debe responder normalmente.
3. `POST /admin/tools/backup` sin header debe rechazar.
4. `POST /admin/tools/backup` con `X-Backup-Token` válido debe ejecutar el backup.

## Rollback básico

1. Restaurar la última versión estable del servicio en Railway.
2. Verificar `GET /health/`.
3. Si hubo cambios de datos sensibles, restaurar desde el backup cifrado en R2.

## Notas operativas

- La app ya no asume Koyeb ni Render como defaults.
- Si `APP_BASE_URL` no está definida, la app intenta derivarla desde `RAILWAY_PUBLIC_DOMAIN`.
- Los logs salen a consola para que Railway los capture directamente.