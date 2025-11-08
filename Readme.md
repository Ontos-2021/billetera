# 💸 Billetera Virtual - Proyecto Django 🐍💻

💸 **Billetera Virtual** es una aplicación 🌐 desarrollada con Django 🐍 que permite a los usuarios 👥 gestionar sus finanzas 💰 personales. Los usuarios pueden realizar un seguimiento 📊 de sus ingresos 📈 y gastos 💸, categorizar sus movimientos 📁 y mantener un control eficiente de su presupuesto (En desarrollo 🚧).

## ⚙️ Funcionalidades Principales 🔧

- **💸 Gastos**:

  - 📋 Lista de Gastos: Visualiza 👀 todos los gastos registrados.
  - ➕ Crear Gasto: Agrega nuevos gastos, especificando descripción 📝, monto 💲, moneda 💵 y categoría 📊.
  - ✏️ Editar Gasto: Modifica los detalles de un gasto existente.
  - 🗑️ Eliminar Gasto: Elimina gastos registrados.

- **📈 Ingresos**:

  - 📋 Lista de Ingresos: Visualiza todos los ingresos registrados.
  - ➕ Crear Ingreso: Registra nuevos ingresos, especificando detalles como monto 💲 y categoría 📊.
  - ✏️ Editar Ingreso: Actualiza los detalles de ingresos existentes.
  - 🗑️ Eliminar Ingreso: Permite eliminar ingresos si es necesario.

- **💱 Monedas y Categorías**:

  - 💵 Monedas: Permite utilizar diferentes monedas 💰 para ingresos 📈 y gastos 💸.
  - 📊 Categorías: Organiza ingresos 📈 y gastos 💸 con categorías para un mejor seguimiento.

- **👤 Perfil de Usuario**:

  - 🔐 Registro y Autenticación: Los usuarios pueden registrarse ✍️, iniciar sesión 🔑 y gestionar su perfil 🖋️.

## ⚙️ Requisitos 📋

- 🐍 Python 3.11+
- 🐳 Docker y Docker Compose (para desarrollo local)
- 🗄️ PostgreSQL (incluido en Docker)
- ☁️ Cloudflare R2 (para almacenamiento de archivos)

## 🔧 Configuración del Entorno

### 🔒 Variables de Entorno

**⚠️ IMPORTANTE**: Nunca subas archivos `.env` con credenciales reales al repositorio.

1. **Para desarrollo local**:
   ```bash
   cp .env.local.example .env
   # Edita .env con tus credenciales reales
   ```

2. **Para producción (Koyeb)**:
   - Configura las variables en el panel de Koyeb
   - Usa `.env.koyeb.example` como referencia

### 📋 Variables Requeridas

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `ENV` | Entorno (development/production) | `production` |
| `DEBUG` | Modo debug (0/1) | `0` |
| `SECRET_KEY` | Clave secreta de Django | `your-secret-key` |
| `DATABASE_URL` | URL de la base de datos | `postgresql://...` |
| `ALLOWED_HOSTS` | Hosts permitidos | `localhost,your-app.koyeb.app` |
| `AWS_ACCESS_KEY_ID` | Clave de acceso R2 | `your-r2-access-key` |
| `AWS_SECRET_ACCESS_KEY` | Clave secreta R2 | `your-r2-secret-key` |
| `AWS_STORAGE_BUCKET_NAME` | Nombre del bucket | `your-bucket-name` |
| `AWS_S3_ENDPOINT_URL` | Endpoint de R2 | `https://account.r2.cloudflarestorage.com` |
| `BACKUP_FERNET_KEY` | Clave Fernet para cifrar respaldos | `gAAAAABk...` |
| `BACKUP_WEBHOOK_TOKEN` | Token para endpoint /admin/tools/backup | `mi-token-backup` |
| `BACKUP_RETENTION_COUNT` | Cantidad de backups a conservar | `7` |

- 🐍 Python 3.x ([Documentación oficial](https://www.python.org/doc/))
- 🐍 Django 4.2 (se instala junto con las dependencias del entorno virtual 🌐) ([Documentación oficial](https://docs.djangoproject.com/en/stable/))

## 🚀 Instalación y Configuración ⚙️

1. 🌀 Clona este repositorio en tu máquina local 🖥️:

   ```
   git clone <URL_del_repositorio>
   ```

2. 🔧 Crea un entorno virtual para el proyecto:

   ```
   python3 -m venv myenv
   ```

3. 🚀 Activa el entorno virtual:

   - 🐧 En Linux/macOS:
     ```
     source myenv/bin/activate
     ```
   - 🪟 En Windows:
     ```
     myenv\Scripts\activate
     ```

4. 📦 Instala las dependencias del proyecto:

   ```
   pip install -r requirements.txt
   ```

5. ⚒️ Realiza las migraciones de la base de datos 🗃️ para preparar la estructura:

   ```
   python manage.py migrate
   ```

   > **Nota:** Si encuentras problemas durante la migración (como errores de permisos), verifica que tengas las dependencias correctamente instaladas y permisos adecuados para ejecutar comandos de Django.

6. 🔑 Crea un superusuario (admin 👑) para acceder al panel de administración:

   ```
   python manage.py createsuperuser
   ```

7. 🚀 Inicia el servidor de desarrollo 🌐:

   ```
   python manage.py runserver
   ```

8. 🌍 Accede a la aplicación en tu navegador web 🖥️:

   ```
   http://127.0.0.1:8000/
   ```

9. 🔒 Para acceder al panel de administración 🛠️, utiliza las credenciales del superusuario:

   ```
   http://127.0.0.1:8000/admin/
   ```

## 📝 Uso 💡

- **📊 Registro de Gastos e Ingresos**: Puedes registrar ingresos 📈 y gastos 💸 con sus respectivas categorías 📁 y monedas 💱, permitiendo un control claro de tus finanzas 💰.
- **👀 Visualización y ✏️ Edición**: Consulta y edita tus gastos 💸 e ingresos 📈 para mantener la información actualizada 🔄 y organizada 📂.
- **📋 Panel de Usuario**: Accede a tu panel de control 🕹️ para obtener una visión general de tus finanzas 📊.

### 🔐 Respaldo de Base de Datos (Manual / Webhook)

Se añadió un sistema de respaldo cifrado que genera un dump (Postgres) o copia (SQLite), lo cifra con Fernet y lo sube a Cloudflare R2 con retención automática.

1. Generar una clave Fernet una sola vez:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
2. Definir en variables de entorno: `BACKUP_FERNET_KEY`, opcional `BACKUP_RETENTION_COUNT`, `BACKUP_WEBHOOK_TOKEN`.
3. Ejecutar manualmente en el contenedor/entorno:
   ```bash
   python manage.py backup_db
   ```
4. Disparar vía endpoint protegido (requiere header `X-Backup-Token` igual a `BACKUP_WEBHOOK_TOKEN` o usuario staff autenticado):
   ```bash
   curl -H "X-Backup-Token: $BACKUP_WEBHOOK_TOKEN" https://tu-dominio/admin/tools/backup
   ```
5. Respuesta JSON ejemplo:
   ```json
   {"status":"ok","engine":"django.db.backends.postgresql","object_key":"backups/db/production/postgres-20250101-120000.dump.enc","r2_url":"s3://bucket/backups/db/production/postgres-20250101-120000.dump.enc","retention_kept":7}
   ```

Notas:
- Asegúrate de que la imagen Docker tenga `postgresql-client` instalado para usar `pg_dump`.
- Para instancias gratuitas (Render/Koyeb) puedes programar un GitHub Action que haga `curl` al endpoint.
- Política de retención elimina automáticamente los backups más antiguos bajo el prefijo `backups/db/<ENV>/`.

## 🤝 Contribuciones 💪

Si deseas contribuir a este proyecto, serás bienvenido 🤗. Puedes abrir **issues** para reportar problemas ⚠️ o sugerencias 💡 y realizar **pull requests** con mejoras ✨ o nuevas funcionalidades 🚀.

## 📜 Licencia ⚖️

Este proyecto está bajo la licencia MIT 📝. Siéntete libre de usar, modificar 🔄 y distribuir el código 💻.

> **Nota:** Para más detalles sobre las licencias y su elección, puedes consultar la [guía de licencias de software](https://choosealicense.com/).

## 🔐 Autenticación: Google OIDC (Authorization Code + PKCE)

Hemos añadido soporte en backend para iniciar sesión mediante Google usando OIDC Authorization Code Flow con PKCE. El backend usa `django-allauth` + `dj-rest-auth` para el intercambio del código y `djangorestframework-simplejwt` para emitir nuestros JWTs (access + refresh).

Puntos clave:

- El frontend obtiene el `authorization_code` y el `code_verifier` (PKCE) desde Google Identity Services o AppAuth.
- El cliente envía al backend la payload JSON: `{ "code": "<AUTH_CODE>", "code_verifier": "<PKCE_VERIFIER>", "redirect_uri": "<REDIRECT_URI>" }` al endpoint `/auth/social/google/`.
- El backend intercambia el código por tokens con Google vía `allauth`, valida `id_token` y crea/obtiene el usuario.
- El backend devuelve los JWTs (access, refresh) generados por SimpleJWT.

Variables de entorno necesarias (ejemplo):

```env
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=https://tu-dominio.com/auth/google/callback/
GOOGLE_HOSTED_DOMAIN=example.com  # opcional, si quieres forzar dominio
```

Comando conveniente para enlazar la SocialApp a tu Site (usa las envs anteriores):

```bash
python manage.py bootstrap_google_socialapp
```

Más detalles y ejemplos de cliente en `billetera/usuarios/README.md`.

