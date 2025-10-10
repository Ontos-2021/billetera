# Copilot Repo Instructions — Billetera (Django)

## Contexto del proyecto
- Framework: Django 4.x, Python 3.12
- DB: Postgres (DATABASE_URL), entorno producción en Render (reverse proxy, HTTPS)
- Static files: WhiteNoise + `collectstatic`
- Media: S3/R2 opcional
- Objetivo: App de gastos/ingresos con auth estándar

## Cómo quiero que trabajes
- Cuando te pida diagnosticar errores (500/400/403), seguí este orden:
  1) Revisar logs recientes y el traceback.
  2) Buscar migraciones faltantes o no aplicadas.
  3) Validar `ALLOWED_HOSTS` (sin esquema) y `CSRF_TRUSTED_ORIGINS` (con https://).
  4) Confirmar `SECURE_PROXY_SSL_HEADER` y `USE_X_FORWARDED_HOST`.
  5) Verificar `DEBUG=False`, `SECRET_KEY`, `DATABASE_URL` y comandos de arranque (gunicorn).

- Para cambios de código: proponé un PR con descripción, pasos de test y *rollback plan*.

## Estilo de salida
- Explicá el “por qué” (root cause), “cómo se reproduce” y “cómo se soluciona”.
- Dame **checklists concretas** y comandos exactos.
- Incluí riesgos y pruebas automáticas si aplica.

## Seguridad / buenas prácticas
- Nunca loguear secretos.
- Señalar patrones inseguros (inyección, CSRF, cookies inseguras).
- Preferir migraciones y señales `post_migrate` para datos iniciales.
