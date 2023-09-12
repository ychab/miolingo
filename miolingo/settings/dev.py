from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['*']

INSTALLED_APPS += [
    'django_extensions',
    'debug_toolbar',
]

INTERNAL_IPS = ('127.0.0.1',)
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# Allow all hosts for dev, @see https://github.com/ottoyiu/django-cors-headers
CORS_ORIGIN_ALLOW_ALL = True

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

for logger in LOGGING['loggers'].values():
    logger['handlers'] = ['console']
    logger['level'] = 'DEBUG'

AUTH_PASSWORD_VALIDATORS = []

try:
    from .local import *
except ImportError:
    pass
