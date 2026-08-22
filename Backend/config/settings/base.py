"""
Shared settings. Never used directly — import it from `dev.py` or `prod.py`.

Default settings module is `config.settings.dev` (set in `manage.py`).
"""

from datetime import timedelta
from pathlib import Path

import environ

# Backend/config/settings/base.py -> parents[2] == Backend/
BASE_DIR = Path(__file__).resolve().parents[2]

env = environ.Env(
    DEBUG=(bool, False),
    # At least 32 bytes: SIMPLE_JWT signs with HS256, and PyJWT warns
    # (InsecureKeyLengthWarning) on anything shorter.
    SECRET_KEY=(str, "dev-only-insecure-key-change-me-before-deploying"),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOW_ALL_ORIGINS=(bool, False),
    CORS_ALLOWED_ORIGINS=(list, []),
    FRONTEND_BASE_URL=(str, "http://localhost:5173"),
    ACCESS_TOKEN_LIFETIME_MINUTES=(int, 60),
    REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
    PASSWORD_RESET_TOKEN_TTL_MINUTES=(int, 30),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")


# ---------------------------------------------------------------- applications

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

# `core` is registered so its AppConfig can attach the SQLite PRAGMA hook.
# It holds abstract models only, so it never produces a migration.
LOCAL_APPS = [
    "core",
    "apps.accounts",
    "apps.geo",
    "apps.activities",
    "apps.trips",
    "apps.budget",
    "apps.dashboard",
    "apps.community",
    "apps.analytics",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Dev B appends "apps.analytics.middleware.ActivityLogMiddleware" here in B5.2.
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ------------------------------------------------------------------- database

# SQLite. WAL mode and foreign-key enforcement are applied per connection in
# `core/apps.py` — see the comment there for why it is a signal and not OPTIONS.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            # Wait rather than fail immediately when another connection holds
            # the write lock. WAL makes this rare, but `runserver` + a shell
            # + pytest can still overlap.
            "timeout": 20,
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Seed data lives in one project-level directory rather than being scattered
# across each app's own `fixtures/`. Django only searches app directories by
# default, so without this `loaddata dev_seed` cannot find the file.
FIXTURE_DIRS = [BASE_DIR / "fixtures"]

# ⚠️ Must be set before the very first `migrate`. Changing it afterwards means
# deleting db.sqlite3 and every migration.
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --------------------------------------------------------- i18n / static / media

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------- rest framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Locked down by default — public endpoints opt out with AllowAny.
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_RENDERER_CLASSES": ("core.renderers.EnvelopeJSONRenderer",),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ),
    # Set globally so *every* list endpoint is paginated with no per-view work.
    # Opt out on bounded aggregates only: `pagination_class = None`.
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DATE_FORMAT": "%Y-%m-%d",
    "DATE_INPUT_FORMATS": ["%Y-%m-%d"],
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%SZ",
    "TIME_FORMAT": "%H:%M:%S",
    # Left at DRF's default (True) on purpose: money serialises as "48200.00",
    # which is what docs/API.md promises the frontend. Flipping this to False
    # would turn every amount into a JSON float and silently break that contract.
    "COERCE_DECIMAL_TO_STRING": True,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("ACCESS_TOKEN_LIFETIME_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("REFRESH_TOKEN_LIFETIME_DAYS")),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    # NOT set here. simplejwt binds TOKEN_OBTAIN_SERIALIZER as a class attribute
    # at import time of its views, so pointing it at a serializer that does not
    # exist yet breaks `runserver`. Task A1.4 sets `serializer_class` directly on
    # our own login view instead — same result, no import-order landmine.
}

SPECTACULAR_SETTINGS = {
    "TITLE": "GlobeTrotter API",
    "DESCRIPTION": (
        "Personalized multi-city travel planner.\n\n"
        "**Every response is enveloped** as `{success, message, data}`. "
        "List payloads live at `data.results`, pagination meta at `data.pagination`.\n\n"
        "User API is under `/api/v1/`, admin API under `/api/v1/admin/`."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v1",
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "docExpansion": "none",
    },
    "TAGS": [
        {"name": "auth", "description": "Registration, login, tokens, password reset"},
        {"name": "profile", "description": "The authenticated user's own account"},
        {"name": "geo", "description": "Countries, cities, saved destinations"},
        {"name": "activities", "description": "Activity catalog"},
        {"name": "dashboard", "description": "Home screen aggregate"},
        {"name": "trips", "description": "Trips, stops, itinerary, calendar, sharing"},
        {"name": "budget", "description": "Expenses and cost breakdown"},
        {"name": "community", "description": "Posts, comments, likes"},
        {"name": "admin", "description": "Admin-only. Requires role=ADMIN"},
    ],
}


# --------------------------------------------------------------------- app

# Used by core.utils.build_share_url() to turn a share_token into a link the
# frontend can actually open.
FRONTEND_BASE_URL = env("FRONTEND_BASE_URL").rstrip("/")

PASSWORD_RESET_TOKEN_TTL_MINUTES = env("PASSWORD_RESET_TOKEN_TTL_MINUTES")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.db.backends": {"level": "INFO", "handlers": ["console"], "propagate": False},
    },
}
