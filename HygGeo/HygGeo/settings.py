"""
Django settings for HygGeo project.
Combining Danish hygge with sustainable travel.
"""

import os
from pathlib import Path

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
SECRET_KEY = config('SECRET_KEY', default="9+=@w$wb%i+o4cj4a0a92%ja6^i0t)c!vj93a=+c6c&4__p8-2")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Updated ALLOWED_HOSTS for production
if DEBUG:
    ALLOWED_HOSTS = ['*']
else:
    allowed_hosts = config('ALLOWED_HOSTS', default='localhost,127.0.0.1')
    ALLOWED_HOSTS = [host.strip() for host in allowed_hosts.split(',')]

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'https://*.ondigitalocean.app',
    'https://starfish-app-jmri5.ondigitalocean.app',
    'https://hyggeo.com',
    'https://www.hyggeo.com',
]

# Site URL for email links
if DEBUG:
    SITE_URL = 'http://localhost:8000'
else:
    SITE_URL = config('SITE_URL', default='https://hyggeo.com')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth

    # Third-party apps
    'storages',  # Required for DigitalOcean Spaces
    'crispy_forms',
    'crispy_bootstrap4',

    # OAuth and Authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    # Local apps
    'accounts',
    'experiences',
    'task_management',
    # NOTE: Do NOT add 'survey' here - survey functionality is part of 'accounts' app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add for static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Required for allauth
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

# Database configuration
database_url = config('DATABASE_URL', default=None)
if database_url:
    if dj_database_url:
        # Use dj_database_url if available
        DATABASES = {
            'default': dj_database_url.parse(database_url)
        }
    else:
        # Manual PostgreSQL configuration as fallback
        import os
        db_url = os.environ.get('DATABASE_URL', '')
        if 'postgresql' in db_url:
            # Extract components from DATABASE_URL manually
            # Format: postgresql://user:password@host:port/database?sslmode=require
            print(f"Manually parsing DATABASE_URL: {db_url}")
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': 'defaultdb',  # You'll need to check your actual DB name
                    'USER': 'doadmin',    # Default DigitalOcean user
                    'HOST': db_url.split('@')[1].split(':')[0],
                    'PORT': '25060',
                    'OPTIONS': {
                        'sslmode': 'require',
                    },
                }
            }
        else:
            # Fallback to SQLite
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                }
            }
else:
    # Development database (SQLite)
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
    BASE_DIR / 'static',
]

# Static file storage with WhiteNoise compression
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# WhiteNoise caching configuration for better performance
WHITENOISE_MAX_AGE = 31536000  # 1 year in seconds for static files
WHITENOISE_IMMUTABLE_FILE_TEST = lambda path, url: True  # All static files are immutable

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
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')

# Enable HTML emails
EMAIL_USE_HTML = True

# Default email sender
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=f'HygGeo <{config("EMAIL_HOST_USER", default="noreply@hyggeo.com")}>')

# Django Sites Framework (required for allauth)
SITE_ID = 3

# Messages framework configuration
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'info',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# Security settings - conditional based on environment
if DEBUG:
    # Development security settings (relaxed for local development)
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_SECONDS = 0
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = None
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    # Explicitly disable secure cookies for development
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False
else:
    # Production security settings
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    X_FRAME_OPTIONS = 'DENY'
    
    # Session cookies - secure since cookies work now
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_PATH = '/'
    
    # CSRF cookies - stable working configuration
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = False  # Must be False for forms to read
    CSRF_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_PATH = '/'
    CSRF_USE_SESSIONS = False     # Use cookies for CSRF

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Session configuration - back to database sessions (now PostgreSQL)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Database sessions
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_PATH = '/'
SESSION_COOKIE_SAMESITE = 'Lax'

# Cache configuration (for production, consider Redis)
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
        'django.security.csrf': {
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
    'MAX_AVATAR_SIZE': 10 * 1024 * 1024,  # 10MB
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

# =============================================================================
# MEDIA FILES CONFIGURATION - CLOUDFLARE R2
# =============================================================================

# Cloudflare R2 configuration (S3-compatible storage)
print(f"Configuring Cloudflare R2 for media files (DEBUG={DEBUG})")

# Cloudflare R2 credentials and configuration
AWS_ACCESS_KEY_ID = config('CLOUDFLARE_ACCESS_ID', default='')
AWS_SECRET_ACCESS_KEY = config('CLOUDFLARE_SECRET_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('CLOUDFLARE_BUCKET_NAME', default='hyggeo-images')

# R2 endpoint - Account ID: 601ebb5191a1c06898f94fac4a9cc451
AWS_S3_ENDPOINT_URL = config('CLOUDFLARE_ENDPOINT_URL',
                              default='https://601ebb5191a1c06898f94fac4a9cc451.r2.cloudflarestorage.com')

# R2 file settings - Optimized for performance with long cache times
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=31536000, immutable',  # 1 year cache for media files
}
AWS_LOCATION = 'media'
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = False  # Don't add authentication to URLs

# Important: R2 doesn't use ACLs by default, so we don't set AWS_DEFAULT_ACL
# All objects in R2 are private by default, use custom domain for public access

# R2 Public URL configuration
# Use custom R2.dev domain or custom domain for public access
AWS_S3_CUSTOM_DOMAIN = config('CLOUDFLARE_PUBLIC_DOMAIN',
                              default=f'pub-{AWS_STORAGE_BUCKET_NAME}.r2.dev')

# Media files served from R2 public URL
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

print(f"Cloudflare R2 configured:")
print(f"   - Bucket: {AWS_STORAGE_BUCKET_NAME}")
print(f"   - Endpoint: {AWS_S3_ENDPOINT_URL}")
print(f"   - Public Domain: {AWS_S3_CUSTOM_DOMAIN}")
print(f"   - Media URL: {MEDIA_URL}")

# Fallback for local development if R2 credentials are not set
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    print("WARNING: R2 credentials not found, falling back to local storage")
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

print(f"Django DEBUG: {DEBUG}, Storage: Cloudflare R2")

# Set DEFAULT_FILE_STORAGE setting for all environments
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
print(f"Set DEFAULT_FILE_STORAGE = {DEFAULT_FILE_STORAGE}")

# =============================================================================
# DJANGO ALLAUTH CONFIGURATION
# =============================================================================

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # Default Django auth
    'allauth.account.auth_backends.AuthenticationBackend',  # Allauth
]

# Allauth settings (using new format)
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # 'mandatory' for production
ACCOUNT_LOGIN_METHODS = ['email']
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = True

# Social account settings
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True

# Google OAuth provider settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
        'FETCH_USERINFO': True,
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret': config('GOOGLE_CLIENT_SECRET', default=''),
            'key': ''
        }
    }
}

# Redirect URLs for OAuth
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
SOCIALACCOUNT_LOGIN_ON_GET = True