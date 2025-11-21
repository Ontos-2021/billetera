# Guía de Configuración Robusta para Deploys con Django + Docker + Railway

Esta guía resume las mejores prácticas para lograr un entorno de despliegue estable y resistente a fallos cuando usás **Django**, **Docker**, **S3** y **Railway**.

---

## 1. Estructura mental del flujo de deploy

1. **Build**
   - Railway clona tu repo.
   - Construye tu imagen Docker línea por línea.
2. **Run**
   - Railway ejecuta la imagen con tus variables de entorno.
   - Corre tu `entrypoint.sh`.
3. **Health**
   - Railway chequea si tu aplicación escucha en `$PORT`.
4. **Logs**
   - Railway registra logs de build y runtime.
   - Si el proceso principal muere → CRASH LOOP.

---

## 2. Reglas esenciales para un Dockerfile robusto

### Usá Python sin buffer
```dockerfile
ENV PYTHONUNBUFFERED=1
```

### No fijes el puerto dentro del Dockerfile
```dockerfile
CMD ["sh", "-c", "gunicorn proyecto.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]
```

### Evitá imágenes pesadas
Usá siempre imágenes slim:

```dockerfile
FROM python:3.11-slim
```

### Copiá primero `requirements.txt`, luego el resto del código
Esto acelera builds y evita recaches innecesarios.

---

## 3. Guidelines para el `entrypoint.sh`

### 3.1. No ocultar errores al esperar la base de datos
Evitar:
```bash
migrate --noinput >/dev/null 2>&1
```

Usar:
```bash
until python manage.py migrate --noinput; do
    echo "DB no lista, reintentando..."
    sleep 5
done
```

### 3.2. No correr `migrate` dos veces
El loop ya hace `migrate`.
No repetirlo después.

### 3.3. Mantener script simple y visible
Incluí logs explícitos:

```bash
echo "Iniciando migraciones..."
python manage.py migrate --noinput
```

### 3.4. Usar `exec` para Gunicorn
Esto asegura señales correctas:

```bash
exec gunicorn proyecto.wsgi --bind 0.0.0.0:${PORT:-8000}
```

---

## 4. Variables de entorno críticas

### Django
- `DJANGO_SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS=*` (o dominio correspondiente)

### Base de datos
- `DATABASE_URL` (Railway normalmente la entrega entera)

### S3
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_REGION_NAME`

---

## 5. Checklist antes del deploy

### Local
- `docker build --no-cache .`
- `docker run --env-file .env -p 8000:8000 imagen`
- Verificar migraciones localmente.

### Railway
- Confirmar estado de la DB (¿Running o Suspended?).
- Verificar que `DATABASE_URL` sea el mismo del servicio Django.
- Confirmar que Django use `${PORT}`.

---

## 6. Cómo diagnosticar problemas de arranque

### Si el build falla:
- Revisar **Build Logs**.
- Revisar dependencias rotas, compilación, paths incorrectos.

### Si el contenedor arranca y muere:
- Revisar **Runtime Logs**.
- Buscar:
  - errores de migración,
  - errores de conexión a la DB,
  - variables faltantes,
  - settings mal configurados.

### Si no conecta a la base de datos:
- Confirmar DB activa.
- Probar conexión desde tu máquina con:
```bash
psql "$DATABASE_URL"
```
- Confirmar host / puerto / contraseña.

---

## 7. Consejos para ambientes gratuitos

- Las bases de datos pueden tardar mucho más en despertar.
- Evitá loops silenciosos.
- No dependas de que la DB esté siempre viva.
- Considerá mantener un “health ping” si Railway lo permite.

---

## 8. Resumen rápido (TL;DR)

- No ocultes errores en el entrypoint.
- Usá `${PORT:-8000}`.
- Revisá estado real de la DB en Railway.
- Probá todo localmente con `--env-file`.
- Mantené logs limpios y visibles.
- No dupliques migraciones.
- Python sin buffer.
- Gunicorn con `exec`.

---

Si querés, puedo sumarte plantillas completas de `Dockerfile`, `entrypoint.sh`, `.env.example`, y `docker-compose.yml`.