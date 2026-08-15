from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv
load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv('DEBUG', '0') == '1'

SECRET_KEY = os.getenv('SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            'SECRET_KEY nao definida. Gere uma e coloque no .env antes de subir em producao.'
        )
    SECRET_KEY = 'dev-only-insecure-key'

ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', '').split(',') if h.strip()]
if not ALLOWED_HOSTS:
    if not DEBUG:
        raise ImproperlyConfigured(
            'ALLOWED_HOSTS nao definida. Liste os dominios da loja no .env.'
        )
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

if not DEBUG:
    # Padrao desligado porque o site roda em HTTP puro (sem TLS no Nginx ainda).
    # Cookie marcado Secure so e enviado pelo navegador em HTTPS — com TLS ligado
    # em producao, defina COOKIES_SECURE=1 no .env para religar essa protecao.
    SESSION_COOKIE_SECURE = os.getenv('COOKIES_SECURE', '0') == '1'
    CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    CSRF_TRUSTED_ORIGINS = [f'https://{h}' for h in ALLOWED_HOSTS if h != '*']
INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'django.contrib.sites','django.contrib.sitemaps',
    'rest_framework','core','store','api','panel',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'loja.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'store.context_processors.cart_count',
        'store.context_processors.tracking_ids',
    ]},
}]
WSGI_APPLICATION = 'loja.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3'}}
if os.getenv('DB_HOST'):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME','loja'),
        'USER': os.getenv('DB_USER','loja'),
        'PASSWORD': os.getenv('DB_PASSWORD',''),
        'HOST': os.getenv('DB_HOST','127.0.0.1'),
        'PORT': os.getenv('DB_PORT','5432'),
    }
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'}]
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'},
}
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1

# Preencha no .env quando as contas existirem — sem isso os scripts nao entram na pagina.
GA4_MEASUREMENT_ID = os.getenv('GA4_MEASUREMENT_ID', '')
META_PIXEL_ID = os.getenv('META_PIXEL_ID', '')

# WhatsApp Business API (Meta) — sem isso o site cai no link wa.me manual.
WHATSAPP_CLOUD_API_TOKEN = os.getenv('WHATSAPP_CLOUD_API_TOKEN', '')
WHATSAPP_CLOUD_PHONE_ID = os.getenv('WHATSAPP_CLOUD_PHONE_ID', '')

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Case See <naoresponda@casesee.com.br>')
if os.getenv('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', '1') == '1'
elif DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'loja-locmem-cache',
    }
}
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.SessionAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.AllowAny'],
    'DEFAULT_THROTTLE_RATES': {'checkout': '10/min'},
}
