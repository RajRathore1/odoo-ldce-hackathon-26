"""Development settings. The default — see `manage.py`."""

from .base import *
from .base import REST_FRAMEWORK, env

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Wide open in dev so the frontend dev server (any port) and the admin panel can
# both talk to us without a config round-trip. `prod.py` narrows this.
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# The clickable HTML API explorer. Kept out of prod.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_RENDERER_CLASSES": (
        "core.renderers.EnvelopeJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
}

# Password reset tokens are printed to the console — there is no mail server.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

if env.bool("ENABLE_DJANGO_EXTENSIONS", default=True):
    try:
        import django_extensions  # noqa: F401

        INSTALLED_APPS = [*INSTALLED_APPS, "django_extensions"]
    except ImportError:
        # base.txt does not ship it; only dev.txt does.
        pass
