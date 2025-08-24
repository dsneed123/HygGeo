import os
from pathlib import Path
import logging

# For environment variables and database URL
try:
    from decouple import config
    import dj_database_url
except ImportError:
    # Fallback for development without these packages
    def config(key, default=None, cast=str):
        return os.environ.get(key, default)
    dj_database_url = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Hardcoded for development
logging.info(f"DEBUG is set to: {DEBUG}")

# ALLOWED_HOSTS for debug mode
ALLOWED_HOSTS = ['*']
logging.info(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")

# CSRF Trusted Origins for development
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://hyggeo.com',
    'https://www.hyggeo.com',
]
logging.info(f"CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")

# Temporary debugging middleware
logger = logging.getLogger(__name__)

class DebugCSRFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(f"Request Origin: {request.META.get('HTTP_ORIGIN')}")
        logger.info(f"Request Host: {request.META.get('HTTP_HOST')}")
        logger.info(f"CSRF Trusted Origins: {CSRF_TRUSTED_ORIGINS}")
        logger.info(f"Allowed Hosts: {ALLOWED_HOSTS}")
        logger.info(f"Session ID: {request.session.session_key}")
        logger.info(f"User: {request.user}")
        return self.get_response(request)

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap4',
    
    # Local apps
    'accounts',
    'experiences',
    # NOTE: Do NOT add 'survey' here - survey functionality is part of 'accounts' app
]

MIDDLEWARE = [
    'HygGeo.settings.DebugCSRFMiddleware',  # Temporary for debugging
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'HygGeo.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'accounts' / 'templates'],
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

WSGI_APPLICATION = 'HygGeo.wsgi.application'

# Database configuration (SQLite for development)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Los_Angeles'  # Pacific Time for Seattle
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'HygGeo' / 'static',
]

# Static file storage with WhiteNoise compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms Configuration
CRISPY_TEMPLATE_PACK = 'bootstrap4'
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap4'

# Authentication URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Messages framework configuration
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Session and CSRF settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_DOMAIN = None  # Allow cookies for all subdomains
SESSION_COOKIE_SECURE = False  # Allow cookies over HTTP in debug mode
CSRF_COOKIE_SECURE = False  # Allow CSRF cookies over HTTP in debug mode

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Custom settings for HygGeo
HYGGEO_SETTINGS = {
    'SUSTAINABILITY_FACTS_COUNT': 6,  # Number of facts to display on homepage
    'SURVEY_PAGINATION_SIZE': 5,  # Surveys per page in profile
    'USER_LIST_PAGINATION_SIZE': 12,  # Users per page in community
    'ENABLE_PROFILE_AVATARS': True,
    'MAX_AVATAR_SIZE': 2 * 1024 * 1024,  # 2MB
    'ALLOWED_AVATAR_TYPES': ['image/jpeg', 'image/png', 'image/gif'],
}

# Third-party integrations (for future use)
# GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')
# STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
# STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')

# Internationalization support for future expansion
LANGUAGES = [
    ('en', 'English'),
    ('da', 'Danish'),  # For hygge authenticity
    ('es', 'Spanish'),
    ('fr', 'French'),
]

# Django Debug Toolbar (for development)
if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        INTERNAL_IPS = ['127.0.0.1']
    except ImportError:
        pass