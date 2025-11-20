"""
Development settings
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ['*']

# Additional apps for development
INSTALLED_APPS += [
    'django_extensions',  # Useful development tools
]

# Development-specific REST framework settings
if DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += [
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]

# Console email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Django Debug Toolbar (optional - uncomment if needed)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# Less restrictive CORS for development
CORS_ALLOW_ALL_ORIGINS = True

# Disable all caching in development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable template caching
TEMPLATES[0]['OPTIONS']['debug'] = True

# Disable Python bytecode caching
import sys
sys.dont_write_bytecode = True

# Logging - More verbose in development
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'

print(f">> Running in DEVELOPMENT mode")
print(f">> Database: {DATABASES['default']['NAME']} on {DATABASES['default']['HOST']}")
print(f">> Python bytecode caching: DISABLED")
print(f">> Django caching: DISABLED (DummyCache)")
