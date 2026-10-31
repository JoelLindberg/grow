"""
Django settings for GROW project.

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(env_file):
    """
    Load environment variables from a .env file if it exists.
    Existing environment variables in os.environ take precedence.
    """
    if not env_file.exists():
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = value


# Determine environment file location:
# If ENV_FILE is set in the environment (e.g., via host provider web UI), use it.
# Otherwise, fall back to BASE_DIR / ".env" for standard local development.
env_file_env = os.environ.get("ENV_FILE")
if env_file_env:
    env_file = Path(env_file_env).expanduser().resolve()
else:
    env_file = BASE_DIR / ".env"

load_dotenv(env_file)

# SECURITY WARNING: keep the secret key used in production secret!
# In production, set this via the DJANGO_SECRET_KEY environment variable.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-me-in-production",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]


# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "django_htmx",
    # Local apps
    "accounts",
    "workouts",
    "nutrition",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Third-party
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------------
# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
# ---------------------------------------------------------------------------
# Uses MariaDB 11.4 when DB_ENGINE="mariadb" (set in .env for local dev & prod)
# or when DB_HOST is provided. Falls back to SQLite when DB_ENGINE="sqlite"
# or when no database environment variables are configured (e.g., lightweight CI).

DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite").lower()

if DB_ENGINE in ("mariadb", "mysql") or (DB_ENGINE != "sqlite" and os.environ.get("DB_HOST")):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "grow"),
            "USER": os.environ.get("DB_USER", "grow"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ---------------------------------------------------------------------------
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Internationalization
# https://docs.djangoproject.com/en/5.1/ref/settings/#std-setting-LANGUAGE_CODE
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Configurable static collection root:
# In production with Passenger where `public` is the web document root, set
# `STATIC_ROOT=public/static` (or an absolute path) in .env so `collectstatic`
# places assets directly where the web server serves them at line rate.
# Defaults to `BASE_DIR / "staticfiles"`.
static_root_env = os.environ.get("STATIC_ROOT")
if static_root_env:
    static_root_path = Path(static_root_env).expanduser()
    STATIC_ROOT = (
        static_root_path.resolve()
        if static_root_path.is_absolute()
        else (BASE_DIR / static_root_path).resolve()
    )
else:
    STATIC_ROOT = BASE_DIR / "staticfiles"


# ---------------------------------------------------------------------------
# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Login / Logout redirects
# ---------------------------------------------------------------------------

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"
