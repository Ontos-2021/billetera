---
applyTo: '**'
---
````markdown
# MoneyFlow Mirror · Railway Deployment Instructions

Resumen operativo para desplegar el proyecto sin drift.

## Plataforma objetivo

- Runtime: Django 4 + Gunicorn
- Plataforma: Railway
- DB: PostgreSQL vía `DATABASE_URL`
- Media: Cloudflare R2
- Startup canónico: `entrypoint.sh`

## Variables mínimas

- `ENV=production`
- `DEBUG=0`
- `SECRET_KEY`
- `DATABASE_URL`
- `APP_BASE_URL=https://your-app.up.railway.app`
- `ALLOWED_HOSTS=your-app.up.railway.app`
- `CSRF_TRUSTED_ORIGINS=https://your-app.up.railway.app`

## Validaciones previas

```bash
cd billetera
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Flujo de arranque esperado

1. `python manage.py check`
2. `python manage.py makemigrations --check --dry-run`
3. `python manage.py migrate --noinput`
4. `python manage.py collectstatic --noinput`
5. `python manage.py bootstrap_google_socialapp` si aplica
6. `gunicorn billetera.wsgi`

## Verificaciones post deploy

- `GET /health/` debe devolver `200`
- `POST /admin/tools/backup` sin header debe rechazar
- `POST /admin/tools/backup` con `X-Backup-Token` válido debe responder `200`
- Login web y `/api/token/` deben seguir funcionando

## Fuente de verdad adicional

- `docs/RAILWAY_DEPLOY.md`
- `README.md`
- `.github/workflows/ci.yml`

````