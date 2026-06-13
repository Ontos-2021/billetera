# 📝 Changelog - Billetera Virtual (MoneyFlow Mirror)

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [2026-06-13] - Estabilización de Producción e Integridad del Repositorio
### Añadido
- Añadido forzado de redirección SSL (`SECURE_SSL_REDIRECT`) configurable vía entorno en producción en [billetera/billetera/settings.py](billetera/billetera/settings.py).
- Añadida configuración HSTS en producción (`SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`) para mitigar vulnerabilidades Man-in-the-Middle en [billetera/billetera/settings.py](billetera/billetera/settings.py).

### Cambiado
- Convertida la codificación del archivo de dependencias crucial [requirements.txt](requirements.txt) de UTF-16 a UTF-8/ASCII portable, evitando fallas de lectura y parseo en pipelines de CI/CD, imágenes Docker y entornos Linux.

---

## [2026-03-19] - Auditoría Técnica, Seguridad y Mercado Pago
### Añadido
- Documento de prioridades técnicas en [AUDITORIA_PRIORIDADES_TECNICAS.md](AUDITORIA_PRIORIDADES_TECNICAS.md).
- Tests de regresión para seguridad de API en [billetera/usuarios/tests_api_security.py](billetera/usuarios/tests_api_security.py).
- Tests para firma e idempotencia del webhook de Mercado Pago en [billetera/usuarios/tests_mercadopago_webhook.py](billetera/usuarios/tests_mercadopago_webhook.py).

### Cambiado
- El arranque de producción dejó de generar migraciones en runtime.
- `Procfile` y `entrypoint.sh` ahora fallan rápido si existen cambios de modelos sin migraciones versionadas.
- Django REST Framework quedó con permisos autenticados por defecto.
- Los endpoints públicos de JWT y login social quedaron explicitados con `AllowAny`.

### Seguridad
- El webhook de Mercado Pago ahora valida firma con `MERCADOPAGO_WEBHOOK_SECRET`.
- El webhook evita reprocesar el mismo `payment_id` aprobado.
- La API dejó de depender de `AllowAny` como política global.

### Validación
- `python manage.py check` OK.
- `python manage.py test` OK.
- Suite de desarrollo dev integrada con 159 tests.

---

## [Anteriores] - Mejoras de UX, Deudas y Transacciones
### Añadido
- **Módulo de Deudas (`deudas`)**: Implementación completa de un sistema para registrar y saldar deudas integrado directamente al flujo financiero y reflejado en el Dashboard de usuario.
- **Cantidades xN**: Soporte en compras globales para mostrar cantidades de ítems adquiridos en un formato claro tipo `(xN)` en las listas de consumos recientes.
- **Exportación PDF**: Integración de WeasyPrint con compatibilidad Docker para descargar reportes financieros completos en PDF.
- **Gráficos e Indicadores**: Dashboard interactivo enriquecido con filtros de tiempo y gráficos analíticos.

### Cambiado
- **Aislamiento Multi-usuario (Privacidad)**: Isolation restrictiva de cuentas, gastos y deudas por usuario autenticado con tests de integración específicos de fuga de datos.
- **Edición Global**: Rediseño y optimización de las vistas para editar compras globales en bloque.
- **Estilos Mobile**: Ajuste de templates bajo pautas de diseño adaptativo Tailwind para móviles.
- **Saneamiento de Base de Datos**: Corrección del script de restauración (`restore_railway.py`) incluyendo sanitización de caracteres UTF-8 e instrucciones SQL conflictivas.

### Solucionado
- Corregido un bug crítico que impedía eliminar consumos o gastos bajo relaciones débiles.
- Reforzado el set con 153 validaciones de asertividad que protegen los balances.
- **Google OIDC con PKCE**: Inicio de sesión mediante Google usando OIDC con SimpleJWT en backend.
- **Cloudflare R2**: Gestión de archivos cargados por usuario directo a R2 mediante `django-storages`.
- **Respaldos Automatizables**: Sistema cifrado con clave Fernet que vuelca base de datos hacia R2, disparado por un webhook seguro.

