from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Cargar variables de entorno desde .env en desarrollo
load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Determinar el entorno
ENV = os.getenv('ENV', 'development')  # Por defecto, el entorno es desarrollo
IS_PRODUCTION = ENV == 'production'  # Si el entorno es producción, IS_PRODUCTION es True

# Secret Key
# En desarrollo permitimos un valor por defecto para facilitar el arranque local,
# pero en producción exigimos que la variable de entorno esté definida.
DEFAULT_SECRET = 'clave_por_defecto_para_desarrollo'
SECRET_KEY = os.getenv('SECRET_KEY', DEFAULT_SECRET)
if IS_PRODUCTION and SECRET_KEY == DEFAULT_SECRET:
    raise ValueError("En producción debes definir SECRET_KEY en las variables de entorno.")
if not SECRET_KEY:
    # Si no está definida (ni siquiera el default) se lanza error en cualquier entorno
    raise ValueError("La variable de entorno SECRET_KEY no está definida.")

# Debug - Independiente del entorno para permitir debugging en producción
DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 'yes']

# Allowed Hosts — configurable vía variable de entorno
# Formato esperado: ALLOWED_HOSTS=host1.com,host2.example
from urllib.parse import urlparse
from typing import Optional

def _normalize_host(value: str) -> Optional[str]:
    v = (value or '').strip()
    if not v:
        return None
    # If the user provided a full URL, extract the netloc (host[:port])
    if v.startswith('http://') or v.startswith('https://'):
        parsed = urlparse(v)
        return parsed.netloc or parsed.path
    # otherwise assume it's already a host
    return v

env_hosts = os.getenv('ALLOWED_HOSTS', '')
if env_hosts:
    ALLOWED_HOSTS = [h for h in (_normalize_host(x) for x in env_hosts.split(',')) if h]
else:
    # Valores por defecto según entorno
    if IS_PRODUCTION:
        ALLOWED_HOSTS = ['classic-pippy-ontos-b4c068be.koyeb.app', '.koyeb.app']
    else:
        ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'whitenoise.runserver_nostatic',  # WhiteNoise para servir archivos estáticos en producción
    'storages',  # django-storages for Cloudflare R2
    'gastos',
    'usuarios',
    'ingresos',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Middleware de WhiteNoise para archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'billetera.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Agrega la ruta a la carpeta templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'billetera.wsgi.application'

# Database Configuration
if IS_PRODUCTION:
    # Use a connection pool timeout to avoid opening/closing too many DB connections
    DATABASES = {
        'default': dj_database_url.config(default=os.getenv('DATABASE_URL'), conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / "db.sqlite3",
        }
    }

# Validadores de contraseña
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalización
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# Configuración de archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
if IS_PRODUCTION:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # WhiteNoise para producción

# Media files configuration
if IS_PRODUCTION:
    # Cloudflare R2 settings (enable storage backend only if required env vars are present)
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "auto")
    AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", "virtual")

    AWS_LOCATION = 'media'

    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and AWS_STORAGE_BUCKET_NAME and AWS_S3_ENDPOINT_URL:
        # Enable S3 storage backend
        DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
        AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
        AWS_DEFAULT_ACL = None
        AWS_S3_FILE_OVERWRITE = False
        AWS_S3_VERIFY = True
        AWS_S3_SIGNATURE_VERSION = 's3v4'  # Required for R2
        AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN') or None

        # Try to construct a sane MEDIA_URL for R2; if it fails, fall back to filesystem media URL
        try:
            endpoint_host = AWS_S3_ENDPOINT_URL.replace('https://', '').replace('http://', '').strip('/')
            MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.{endpoint_host}/{AWS_LOCATION}/"
        except Exception:
            MEDIA_URL = f"/{AWS_LOCATION}/"
    else:
        # Fallback to filesystem media if R2 vars not present
        MEDIA_URL = '/media/'
        MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CSRF Trusted Origins — normalizar entradas de entorno
if IS_PRODUCTION:
    env_csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
    default_origins = ['https://billetera-production.up.railway.app', 'https://classic-pippy-ontos-b4c068be.koyeb.app']
    if env_csrf_origins:
        parsed = []
        for o in [p.strip() for p in env_csrf_origins.split(',') if p.strip()]:
            # Ensure scheme is present; default to https
            if not o.startswith('http://') and not o.startswith('https://'):
                o = 'https://' + o
            parsed.append(o)
        CSRF_TRUSTED_ORIGINS = parsed + default_origins
    else:
        CSRF_TRUSTED_ORIGINS = default_origins
else:
    CSRF_TRUSTED_ORIGINS = ['http://localhost', 'http://127.0.0.1:8000']

# Configuración de inicio de sesión
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'inicio_usuarios'
LOGOUT_REDIRECT_URL = 'login'

# Auto Field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Seguridad adicional en producción
if IS_PRODUCTION:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    # Allow Django to detect HTTPS when behind a proxy (Railway/Koyeb/etc.)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Respect forwarded host header from the platform (Render, Railway, etc.)
    USE_X_FORWARDED_HOST = True
