#!/bin/bash
set -e

# Verificar errores de código antes de intentar conectar a la BD
echo "Checking project integrity..."
python manage.py check

# Fallar rápido si hay cambios de modelos sin migraciones versionadas
echo "Checking migration consistency..."
python manage.py makemigrations --check --dry-run

# Esperar a que la base de datos esté disponible (retry)
echo "Waiting for database..."
until python manage.py migrate --noinput; do
  echo "Database not ready yet. Retrying in 5 seconds..."
  sleep 5
done

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Bootstrapping Site and Google SocialApp (idempotent)..."
python manage.py bootstrap_google_socialapp || echo "Bootstrap command skipped (missing envs)."

echo "Starting Gunicorn..."
exec gunicorn billetera.wsgi --bind 0.0.0.0:${PORT:-8000}
