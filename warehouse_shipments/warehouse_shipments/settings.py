"""Настройки автономного учебного приложения. Вся предметная БД — через sqlite3."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "warehouse-local-coursework-31-development-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]").split(",")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "homepage.apps.HomepageConfig",
    "docks.apps.DocksConfig",
    "shipments.apps.ShipmentsConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "warehouse_shipments.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
}]
WSGI_APPLICATION = "warehouse_shipments.wsgi.application"
ASGI_APPLICATION = "warehouse_shipments.asgi.application"

# Django не подключается к предметной БД: модели, сессии и auth здесь не нужны.
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}
SHIPMENTS_DB_PATH = Path(os.environ.get("SHIPMENTS_DB_PATH", BASE_DIR / "data" / "shipments.db"))

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
X_FRAME_OPTIONS = "DENY"
