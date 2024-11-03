from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Cargar variables de entorno desde .env en desarrollo
load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Determinar el entorno
ENV = os.getenv('ENV', 'production')
IS_PRODUCTION = ENV == 'production'

# Secret Key
SECRET_KEY = os.getenv('SECRET_KEY', 'clave_por_defecto_para_desarrollo')
if not SECRET_KEY:
    raise ValueError("La variable de entorno SECRET_KEY no está definida.")

# Debug
DEBUG = not IS_PRODUCTION

# Allowed Hosts
if IS_PRODUCTION:
    ALLOWED_HOSTS = ['billetera-production.up.railway.app']
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

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
if IS_PRODUCTION:
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
if IS_PRODUCTION:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  # WhiteNoise para producción

# Configuración de archivos de medios
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configura WhiteNoise para servir archivos de medios
WHITENOISE_ALLOW_ALL_ORIGINS = True
WHITENOISE_ROOT = MEDIA_ROOT

# CSRF Trusted Origins
if IS_PRODUCTION:
    CSRF_TRUSTED_ORIGINS = ['https://billetera-production.up.railway.app']
else:
    CSRF_TRUSTED_ORIGINS = ['http://localhost']

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
