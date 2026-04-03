# Changelog

Todos los cambios relevantes del proyecto deberían registrarse acá.

## 2026-04-03

### Added

- Endpoint de health básico para verificación de DB.
- Workflow de CI mínimo para `check`, `makemigrations --check --dry-run` y `test`.
- Guía operativa de Railway en [docs/RAILWAY_DEPLOY.md](docs/RAILWAY_DEPLOY.md).
- Archivo de ejemplo de entorno para Railway.

### Changed

- El endpoint de backup ahora acepta solo `POST`.
- El token del backup se acepta solo por header `X-Backup-Token`.
- `Procfile` quedó alineado a [entrypoint.sh](entrypoint.sh) para usar un único startup flow.
- La configuración de producción deja de mezclar Koyeb y Render, y pasa a centrarse en Railway.
- Se agregó configuración mínima de logging para operar en Railway.

### Removed

- Artefactos de despliegue específicos de Koyeb.

### Validation

- `python manage.py check` OK.
- `python manage.py makemigrations --check --dry-run` OK.
- `python manage.py test` OK.
- Suite validada localmente con `165` tests.

## 2026-03-19

### Added

- Documento de prioridades técnicas en [AUDITORIA_PRIORIDADES_TECNICAS.md](AUDITORIA_PRIORIDADES_TECNICAS.md).
- Tests de regresión para seguridad de API en [billetera/usuarios/tests_api_security.py](billetera/usuarios/tests_api_security.py).
- Tests para firma e idempotencia del webhook de Mercado Pago en [billetera/usuarios/tests_mercadopago_webhook.py](billetera/usuarios/tests_mercadopago_webhook.py).

### Changed

- El arranque de producción dejó de generar migraciones en runtime.
- `Procfile` y `entrypoint.sh` ahora fallan rápido si existen cambios de modelos sin migraciones versionadas.
- Django REST Framework quedó con permisos autenticados por defecto.
- Los endpoints públicos de JWT y login social quedaron explicitados con `AllowAny`.

### Security

- El webhook de Mercado Pago ahora valida firma con `MERCADOPAGO_WEBHOOK_SECRET`.
- El webhook evita reprocesar el mismo `payment_id` aprobado.
- La API dejó de depender de `AllowAny` como política global.

### Validation

- `python manage.py check` OK.
- `python manage.py test` OK.
- Suite validada localmente con `159` tests.