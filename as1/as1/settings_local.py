"""
تنظیمات محلی برای اجرای پروژه روی سیستم لوکال
این فایل برای توسعه محلی استفاده می‌شود
"""

from .settings import *
import os
from pathlib import Path

# Override TEMPLATES for local development
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # as1/templates
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# تنظیمات محلی برای توسعه
DEBUG = True

# هاست‌های مجاز برای محیط محلی
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0']

# تنظیمات CORS برای محیط محلی
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# مسیر دیتابیس محلی
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# تنظیمات CSRF برای محیط محلی
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# تنظیمات ایمن برای محیط محلی (در محیط واقعی از متغیرهای محیطی استفاده کنید)
if os.getenv('OPENAI_API_KEY'):
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
else:
    # مقدار پیش‌فرض برای محیط محلی (در محیط واقعی تنظیم نکنید)
    OPENAI_API_KEY = 'your-local-api-key-here'

# Google OAuth settings for local development
if os.getenv('GOOGLE_CLIENT_ID'):
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
else:
    # مقدار پیش‌فرض برای محیط محلی (در محیط واقعی تنظیم نکنید)
    GOOGLE_CLIENT_ID = '123456789-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com'

if os.getenv('GOOGLE_CLIENT_SECRET'):
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
else:
    # مقدار پیش‌فرض برای محیط محلی (در محیط واقعی تنظیم نکنید)
    GOOGLE_CLIENT_SECRET = 'your-google-client-secret-here'
