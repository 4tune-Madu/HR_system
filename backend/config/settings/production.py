from .base import *
from django.core.exceptions import ImproperlyConfigured


DEBUG = False

def required_environment(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} must be set for production.")
    return value


def environment_list(name):
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


SECRET_KEY = required_environment("SECRET_KEY")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("replace-"):
    raise ImproperlyConfigured("Production SECRET_KEY must be a unique random value of at least 50 characters.")

ALLOWED_HOSTS = environment_list("ALLOWED_HOSTS")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("ALLOWED_HOSTS must contain explicit production hostnames.")

CORS_ALLOWED_ORIGINS = environment_list("CORS_ALLOWED_ORIGINS")
CSRF_TRUSTED_ORIGINS = environment_list("CSRF_TRUSTED_ORIGINS")
APP_BASE_URL = required_environment("APP_BASE_URL").rstrip("/")
if not APP_BASE_URL.startswith("https://"):
    raise ImproperlyConfigured("APP_BASE_URL must use HTTPS in production.")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": required_environment("DB_NAME"),
        "USER": required_environment("DB_USER"),
        "PASSWORD": required_environment("DB_PASSWORD"),
        "HOST": required_environment("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = required_environment("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false").lower() == "true"
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured("Configure SMTP TLS or SSL, not both.")
EMAIL_TIMEOUT = 30
DEFAULT_FROM_EMAIL = required_environment("DEFAULT_FROM_EMAIL")

STATIC_ROOT = Path(required_environment("STATIC_ROOT"))
MEDIA_ROOT = Path(required_environment("MEDIA_ROOT"))
CELERY_BROKER_URL = required_environment("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = required_environment("CELERY_RESULT_BACKEND")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 3600

# Enable only behind a proxy that strips client-supplied forwarded headers.
if os.getenv("TRUST_PROXY_HTTPS", "false").lower() == "true":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
