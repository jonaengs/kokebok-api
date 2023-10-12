from pathlib import Path
from typing import Literal

import environ
from django.core.management.utils import get_random_secret_key

# Declare env vars with their type and default value
env = environ.Env(
    #
    DEBUG=(bool, False),
    ENV_FILE=(str, ".env"),  # Defauly to prod settings file
    STRICT_SSL=(bool, True),
    ALLOWED_HOSTS=(list, []),
    TRUSTED_ORIGINS=(list, []),
    OCR_ENABLED=(bool, True),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read .env file. "Live" env variables have precedence over .env file contents
env.read_env(BASE_DIR / env("ENV_FILE"))

DEBUG = env("DEBUG")
STRICT_SSL = env("STRICT_SSL")
if STRICT_SSL:
    assert not DEBUG, "Don't enable strict SSL measures in debug mode"

SECRET_KEY = env.str("SECRET_KEY", default=get_random_secret_key())

ALLOWED_HOSTS = env("ALLOWED_HOSTS")
TRUSTED_ORIGINS = env("TRUSTED_ORIGINS")

# User model
AUTH_USER_MODEL = "core.User"


# Security policies
# We use Django's sessions for auth and secure endpoints using CSRF tokens

# CORS
if DEBUG:
    CORS_ORIGIN_WHITELIST = ["http://localhost", "http://127.0.0.1"]
else:
    CORS_ORIGIN_WHITELIST = ["https://" + domain for domain in TRUSTED_ORIGINS]
CORS_EXPOSE_HEADERS = ["Content-Type", "X-CSRFToken"]
CORS_ALLOW_CREDENTIALS = True  # Allows cookies to be sent with CORs

# Session
SESSION_COOKIE_SAMESITE = "Strict"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG  # Don't require HTTPS cookie transfer in local dev

# CSRF
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG  # Don't require HTTPS cookie transfer in local dev
CSRF_TRUSTED_ORIGINS = CORS_ORIGIN_WHITELIST

# SSL
# Leave out if deploying to fly -- all .dev domains require HTTPS automatically
# SECURE_SSL_REDIRECT = STRICT_SSL
if STRICT_SSL:
    SECURE_HSTS_SECONDS = 31536000  # One year

# OTHER
X_FRAME_OPTIONS = "DENY"  # Disallow iframes of the site


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",  # Whitenoise
    "django.contrib.staticfiles",
    "ninja",  # needed to self-host staticfiles for API docs
    "corsheaders",
    "storages",
    # My apps
    "core",
    "recipes",
]

MIDDLEWARE = [
    "csp.middleware.CSPMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Whitenoise
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "kokebok.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "kokebok.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": env.db(),
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "data/staticfiles"
static_files_storage = {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    "OPTIONS": {},
}

# Media files
if DEBUG:
    MEDIA_URL = "media/"
    MEDIA_ROOT = BASE_DIR / "data/mediafiles"
    media_files_storage = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {},
    }
else:
    # AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}  # useless w/o CF

    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"
    media_files_storage = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "location": "private",
            "default_acl": "private",
            "custom_domain": False,
            "signature_version": "s3v4",
            "region_name": env("AWS_S3_REGION_NAME"),
            "bucket_name": env("AWS_STORAGE_BUCKET_NAME"),
            "querystring_expire": 60 * 60,  # one hour (unit is seconds)
        },
    }


STORAGES = {
    "default": media_files_storage,
    "staticfiles": static_files_storage,
}


# CSP (Content Security Policy) Settings
# About the safety of "data:": https://security.stackexchange.com/q/94993
CSP_IMG_SRC = ("'self'", "data:") + (
    (AWS_S3_CUSTOM_DOMAIN,) if not DEBUG else tuple()
)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_SCRIPT_SRC = "'self'"
CSP_CONNECT_SRC = "'self'"
CSP_DEFAULT_SRC = "'none'"
# Set these two to True when debugging CSP issues!
CSP_REPORT_ONLY = False
CSP_REPORT_URI = False


# OCR (likely Google Cloud) provider
OCR_ENABLED = env("OCR_ENABLED")
OCR_PROVIDER: Literal["Google", "Amazon"] = "Google"
if OCR_ENABLED:
    if OCR_PROVIDER == "Google":
        GOOGLE_CLOUD_CREDENTIALS = {
            "type": "service_account",
            "project_id": env("GOOGLE_PROJECT_ID"),
            "private_key_id": env("GOOGLE_PRIVATE_KEY_ID"),
            "private_key": env("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": env("GOOGLE_CLIENT_EMAIL"),
            "client_id": env("GOOGLE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": env("GOOGLE_CLIENT_X509_CERT_URL"),
            "universe_domain": "googleapis.com",
        }


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
