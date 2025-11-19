#!/bin/bash
set -e

# Verificar errores de código antes de intentar conectar a la BD
echo "Checking project integrity..."
python manage.py check

# Esperar a que la base de datos esté disponible (retry)
echo "Waiting for database..."
RETRIES=30
until python manage.py migrate --noinput >/dev/null 2>&1 || [ $RETRIES -le 0 ]; do
  echo "Database not ready yet. Retries left: $RETRIES"
  RETRIES=$((RETRIES-1))
  sleep 5
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Bootstrapping Site and Google SocialApp (idempotent)..."
python manage.py bootstrap_google_socialapp || echo "Bootstrap command skipped (missing envs)."

echo "Starting Gunicorn..."
exec gunicorn billetera.wsgi --bind 0.0.0.0:8000
