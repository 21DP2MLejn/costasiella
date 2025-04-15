"""
Django settings for development
"""
import sys
from os import path
from app.settings.common import *

from django.core.files.storage import FileSystemStorage

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# This tests whether the second commandline argument (after ./manage.py) was test.
TESTING = False
if len(sys.argv) >= 1:
    if sys.argv[1] == 'test':
        TESTING = True

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'My Name <my_from_email@domain.com>'

# Override allauth settings for development
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Make email verification optional during development

##
# CSRF Settings
##
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://dev.costasiella.com:3000',
    'http://localhost:3001',
    'http://dev.costasiella.com:3001'
]


# Media root
# https://docs.djangoproject.com/en/2.1/topics/files/
MEDIA_ROOT = os.path.join(os.getcwd(), "costasiella", "media")
if 'GITHUB_WORKFLOW' in os.environ:
    MEDIA_ROOT = os.path.join(os.getcwd(), "costasiella", "media_test")

# Protected media root
MEDIA_PROTECTED_ROOT = os.path.join(os.getcwd(), "costasiella", "media_protected")
if 'GITHUB_WORKFLOW' in os.environ:
    MEDIA_PROTECTED_ROOT = os.path.join(os.getcwd(), "costasiella", "media_protected_test")
MEDIA_PROTECTED_STORAGE = FileSystemStorage(location=MEDIA_PROTECTED_ROOT, base_url=MEDIA_PROTECTED_PUBLIC_URL)

# Orphaned files cleanup
ORPHANED_APPS_MEDIABASE_DIRS = {
    'costasiella': {
        'root': MEDIA_ROOT,  # MEDIA_ROOT => default location(s) of your uploaded items e.g. /var/www/mediabase
        'skip': (               # optional iterable of subfolders to preserve, e.g. sorl.thumbnail cache
            path.join(MEDIA_ROOT, 'cache'),
        ),
        'exclude': ('.gitignore',) # optional iterable of files to preserve
    }
}

# Uncomment the line below to disable user signups
# ACCOUNT_ADAPTER = 'costasiella.allauth_adapters.account_adapter_no_signup.AccountAdapterNoSignup'

# Re-enable this once it doesn't break promises
# 'graphene_django.debug.DjangoDebugMiddleware'
if DEBUG:
    GRAPHENE['MIDDLEWARE'].append('costasiella.middlewares.DjangoDebugMiddleware')

# GraphQL JWT settings with long expiration. Uncomment during development if useful for graphiQL auth for example.
GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=5),  # Default = 5 minutes
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),  # Default = 7 days
    'JWT_LONG_RUNNING_REFRESH_TOKEN': True,
    'JWT_COOKIE_SAMESITE': 'Lax'
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE
    if not middleware.startswith('defender')
]

# Vault configuration
VAULT_ADDR = "http://localhost:8200" 
VAULT_TOKEN = "hvs.GGxVJCtFULelpUu8dxbp3gOu"      
VAULT_TRANSIT_KEY = "costasiella"   

# Django-defender settIS_URL = None  # Add this line
DEFENDER_STORE_ACCESS_ATTEMPTS = True
DEFENDER_ENABLED = False
DEFENDER_USE_REDIS = False
DEFENDER_STORE_ACCESS_ATTEMPTS_IN_DB = True
DEFENDER_LOCK_OUT_BY_IP_AND_USERNAME = True
DEFENDER_DISABLE_IP_LOCKOUT = True  # Change this to True
DEFENDER_DISABLE_USERNAME_LOCKOUT = True  # Change this to True
DEFENDER_COOLOFF_TIME = 300
DEFENDER_LOCKOUT_TEMPLATE = None
DEFENDER_LOGIN_FAILURE_LIMIT = 3

#CELERY_BROKER_URL = "redis://localhost:6379/1"

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'pulsefitnessauto@gmail.com'  # Your Gmail address
EMAIL_HOST_PASSWORD = 'fiag wpjh knbe zsql'  # Gmail App Password


# Detailed logging for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(os.getcwd(), 'logs', 'debug.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'graphql': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'costasiella': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}