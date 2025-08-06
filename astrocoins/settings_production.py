"""
Настройки для продакшена
"""
import os
from .settings import *

# Отключаем режим отладки
DEBUG = False

# Разрешенные хосты
ALLOWED_HOSTS = ['algoritmika25.store', 'www.algoritmika25.store', 'localhost', '127.0.0.1']

# Настройки безопасности для продакшена
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Настройки базы данных PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'astrocoins'),
        'USER': os.getenv('DB_USER', 'astrocoins'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Настройки email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.beget.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'algoritmika25mails@algoritmika25.store'
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD', '3164579881245$Ss')
DEFAULT_FROM_EMAIL = 'Астрокоины <algoritmika25mails@algoritmika25.store>'

# Настройки логирования
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/astrocoins/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}

# Настройки кэширования
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Настройки статических файлов
STATIC_ROOT = '/var/www/astrocoins/staticfiles'
MEDIA_ROOT = '/var/www/astrocoins/media'

# Настройки сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Настройки CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://algoritmika25.store',
    'https://www.algoritmika25.store',
] 