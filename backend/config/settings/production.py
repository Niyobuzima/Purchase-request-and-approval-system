"""
Production settings
"""
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Enable Upstash Redis by default in production
# Set USE_UPSTASH=False in .env to use standard Redis instead
USE_UPSTASH = config('USE_UPSTASH', default=True, cast=bool)

# Must specify allowed hosts in production
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Production email backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Stricter CORS settings
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='').split(',')

# Production-specific settings
MIDDLEWARE += [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For serving static files
]

# Static files with WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Logging - Less verbose in production, but log to file
LOGGING['loggers']['django']['level'] = 'WARNING'
LOGGING['loggers']['apps']['level'] = 'INFO'

# Add error logging handler
LOGGING['handlers']['error_file'] = {
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'error.log',
    'maxBytes': 1024 * 1024 * 10,  # 10MB
    'backupCount': 5,
    'formatter': 'verbose',
    'level': 'ERROR',
}

LOGGING['loggers']['django']['handlers'].append('error_file')
LOGGING['loggers']['apps']['handlers'].append('error_file')

print(f"🔒 Running in PRODUCTION mode")
