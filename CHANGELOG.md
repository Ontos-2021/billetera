# 📝 Changelog - Billetera Virtual (MoneyFlow Mirror)

Todos los cambios notables en este proyecto serán documentados en este archivo.

## [2026-06-13] - Estabilización de Producción e Integridad del Repositorio
### Añadido
- Añadido forzado de redirección SSL (`SECURE_SSL_REDIRECT`) configurable vía entorno en producción en [billetera/billetera/settings.py](billetera/billetera/settings.py).
- Añadida configuración HSTS en producción (`SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`) para mitigar vulnerabilidades Man-in-the-Middle en [billetera/billetera/settings.py](billetera/billetera/settings.py).

### Cambiado
- Convertida la codificación del archivo de dependencias crucial [requirements.txt](requirements.txt) de UTF-16 a UTF-8/ASCII portable, evitando fallas de lectura y parseo en pipelines de CI/CD, imágenes Docker y entornos Linux.

---

## [Recientes] - Mejoras de UX, Deudas y Transacciones
### Añadido
- **Módulo de Deudas (`deudas`)**: Implementación completa de un sistema para registrar y saldar deudas integrado directamente al flujo financiero y reflejado en el Dashboard de usuario.
- **Cantidades xN**: Soporte en compras globales para mostrar cantidades de ítems adquiridos en un formato claro tipo `(xN)` en las listas de consumos recientes.
- **Exportación PDF**: Integración de WeasyPrint con compatibilidad Docker para descargar reportes financieros completos en PDF.
- **Gráficos e Indicadores**: Dashboard interactivo enriquecido con filtros de tiempo y gráficos analíticos.

### Cambiado
- **Aislamiento Multi-usuario (Privacidad)**: Refuerzo riguroso del aislamiento de cuentas, gastos y deudas por usuario autenticado. Se añadieron tests de integración específicos cubriendo posibles fugas de datos.
- **Edición Global**: Rediseño y optimización de las vistas para editar compras globales en bloque.
- **Estilos Mobile**: Ajuste integral de los templates bajo pautas de diseño adaptativo para pantallas móviles.
- **Saneamiento de Base de Datos**: Corrección del script de restauración (`restore_railway.py`) incluyendo sanitización de caracteres UTF-8 e instrucciones SQL conflictivas.

### Solucionado
- Corregido un bug crítico que impedía eliminar consumos o gastos bajo ciertas combinaciones de relaciones débiles.
- Reforzado el set de tests con 153 validaciones que protegen la asertividad y consistencia de los balances.

---

## [Anteriores] - Google OIDC, R2 y Núcleo del Sistema
### Añadido
- **Google OIDC con PKCE**: Soporte de flujo de autorización por código y PKCE desde el frontend para autenticar con Google mediante `django-allauth` + `dj-rest-auth`, devolviendo JWTs basados en SimpleJWT.
- **Cloudflare R2**: Gestión e integración de archivos cargados por usuario (Media) usando el backend de `django-storages` directo al bucket de Storage R2 en producción.
- **Respaldos Automatizables**: Sistema cifrado con clave Fernet que vuelca la base de datos (Postgres o SQLite) y lo almacena directo en Clouflare R2. Endpoint REST `/admin/tools/backup` protegido por token.
