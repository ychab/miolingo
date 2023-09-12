from pathlib import Path
from tempfile import gettempdir

from .base import *

EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Boost perf a little
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

STATIC_ROOT = Path(gettempdir(), 'miolingo', 'static')
MEDIA_ROOT = Path(gettempdir(), 'miolingo', 'media')

try:
    from .local import *
except ImportError:  # pragma: no cover
    pass
