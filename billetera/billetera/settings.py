# Django settings for billetera project.
from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Secret Key
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')  # Clave por defecto solo para desarrollo.

# Debug
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Allowed Hosts
if os.getenv('ENV') == 'production':
    ALLOWED_HOSTS = ['billetera-production.up.railway.app']
else:
    ALLOWED_HOSTS = ['*']

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
if os.getenv('ENV') == 'production':
    DATABASES = {
        'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
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
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # WhiteNoise para producción

# Configuración de archivos de medios
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost').split(',')

# Configuración de inicio de sesión
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'inicio_usuarios'
LOGOUT_REDIRECT_URL = 'login'

# Auto Field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Seguridad adicional en producción
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
