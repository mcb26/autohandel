import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE_DIR = Path(__file__).resolve().parent.parent
if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-dev-key-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "leads",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "leads.context_processors.site_brand",
                "leads.context_processors.site_contact",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "de-de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "autopartner-default",
    }
}

EMAIL_BACKEND = os.getenv(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("DJANGO_EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.getenv("DJANGO_DEFAULT_FROM_EMAIL", "no-reply@example.com")
DEALER_NOTIFICATION_EMAIL = os.getenv("DJANGO_DEALER_NOTIFICATION_EMAIL", "")

# Telegram-Bot: neue Leads (Chat-ID, nicht Telefonnummer – siehe telegram_chat_id)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_NOTIFY_CHAT_IDS = env_list("TELEGRAM_NOTIFY_CHAT_ID", "")
# Öffentliche Basis-URL für Links im Dashboard (z. B. https://ihre-domain.de)
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

SITE_BRAND_NAME = os.getenv("SITE_BRAND_NAME", "AutoPark Grün")
SITE_LOGO_PATH = os.getenv("SITE_LOGO_PATH", "img/logo.png")
SITE_COMPANY_NAME = os.getenv("SITE_COMPANY_NAME", "AutoPark Grün GmbH")
SITE_ADDRESS = os.getenv("SITE_ADDRESS", "Zur Eisenhütte 4b, 45131 Essen")
SITE_PHONE = os.getenv("SITE_PHONE", "01577 6214498")
SITE_EMAIL = os.getenv("SITE_EMAIL", "info@autoparkgruen.com")
SITE_WHATSAPP = os.getenv("SITE_WHATSAPP", SITE_PHONE)
SITE_TELEGRAM = os.getenv("SITE_TELEGRAM", "@autoparkgruen")
SITE_INSTAGRAM = os.getenv("SITE_INSTAGRAM", "autoparkgruen")

HERO_IMAGE_ATTRIBUTION_URL = os.getenv(
    "HERO_IMAGE_ATTRIBUTION_URL",
    "https://www.magnific.com/de/fotos-kostenlos/foto-von-infiniti-g37-coupe-auf-dem-parkplatz_26260191.htm",
)
HERO_IMAGE_ATTRIBUTION_TITLE = os.getenv(
    "HERO_IMAGE_ATTRIBUTION_TITLE",
    "Foto von Infiniti G37 Coupé auf dem Parkplatz",
)
HERO_IMAGE_ATTRIBUTION_AUTHOR = os.getenv("HERO_IMAGE_ATTRIBUTION_AUTHOR", "halayalex")
HERO_IMAGE_ATTRIBUTION_SOURCE = os.getenv("HERO_IMAGE_ATTRIBUTION_SOURCE", "Magnific.com")
HERO_IMAGE_ATTRIBUTION_LICENSE = os.getenv(
    "HERO_IMAGE_ATTRIBUTION_LICENSE",
    "Kostenlose kommerzielle Nutzung mit Namensnennung (Magnific.com)",
)

CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", not DEBUG)
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
