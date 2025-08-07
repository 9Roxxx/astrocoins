import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-only-for-development-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['algoritmika25.store', 'www.algoritmika25.store', '127.0.0.1', 'localhost']

# Настройки безопасности для продакшена (когда DEBUG=False)
if not DEBUG:
    # HTTPS настройки
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 год
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Proxy settings
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True
    
    # Дополнительные настройки безопасности
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
    
    # Настройки сессий для продакшена
    SESSION_COOKIE_AGE = 3600  # 1 час
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    
else:
    # Настройки для разработки
    SECURE_SSL_REDIRECT = False
    SECURE_PROXY_SSL_HEADER = None
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    USE_X_FORWARDED_HOST = False
    USE_X_FORWARDED_PORT = False
# Минимальные настройки безопасности для разработки
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Настройки сессий для разработки (переопределены выше для продакшена)
if DEBUG:
    SESSION_COOKIE_AGE = 7200  # 2 часа для удобства разработки
    SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Для удобства разработки

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'core',
    'rest_framework',
    'allauth',
    'allauth.account',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'astrocoins.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'core/templates'),
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

WSGI_APPLICATION = 'astrocoins.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'astrocoins'),
        'USER': os.getenv('DB_USER', 'astrocoins'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Настройки кэширования для продакшена
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 минут
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Настройки кэширования страниц
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'astrocoins'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Whitenoise settings
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1 year in seconds
WHITENOISE_COMPRESSION_ENABLED = True

# Настройка для обработки статических файлов
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Additional Whitenoise settings
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Security settings have been moved to the top of the file

# Messages settings
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# Email settings
# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.beget.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'algoritmika25mails@algoritmika25.store'
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD', '3164579881245$Ss')  # Установите через переменную окружения
DEFAULT_FROM_EMAIL = 'Астрокоины <algoritmika25mails@algoritmika25.store>'

# Django-allauth settings
ACCOUNT_LOGIN_METHODS = {'email', 'username'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_USERNAME_MIN_LENGTH = 4
ACCOUNT_PASSWORD_MIN_LENGTH = 8

# Переводы сообщений django-allauth
ACCOUNT_ERROR_MESSAGES = {
    'username_taken': 'Это имя пользователя уже занято.',
    'email_taken': 'Пользователь с таким email уже существует.',
    'password_mismatch': 'Пароли не совпадают.',
    'invalid_login': 'Неверное имя пользователя или пароль.',
    'inactive': 'Этот аккаунт неактивен.',
}

# Переводы сообщений валидации пароля
AUTH_PASSWORD_VALIDATORS_MESSAGES = {
    'password_too_similar': 'Пароль слишком похож на другую вашу личную информацию.',
    'password_too_short': 'Пароль должен содержать как минимум 8 символов.',
    'password_too_common': 'Этот пароль слишком простой.',
    'password_entirely_numeric': 'Пароль не может состоять только из цифр.',
}

# Тексты для шаблонов
ACCOUNT_FORMS = {
    'login': 'allauth.account.forms.LoginForm',
    'signup': 'allauth.account.forms.SignupForm',
    'reset_password': 'allauth.account.forms.ResetPasswordForm',
}

# Дополнительные настройки безопасности
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True  # Выход после смены пароля
ACCOUNT_PRESERVE_USERNAME_CASING = False  # Игнорировать регистр в именах пользователей
ACCOUNT_USERNAME_BLACKLIST = ['admin', 'administrator', 'moderator']  # Запрещенные имена пользователей

# Rate limiting settings
ACCOUNT_RATE_LIMITS = {
    'login': '5/5m',  # 5 попыток каждые 5 минут
    'login_failed': '5/5m',  # 5 неудачных попыток каждые 5 минут
    'signup': '5/5m',  # 5 регистраций каждые 5 минут
    'send_mail': '5/5m'  # 5 писем каждые 5 минут
}

# URLs для аутентификации
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_URL = 'account_logout'
LOGOUT_REDIRECT_URL = 'account_login'

# Настройки логирования для продакшена
if not DEBUG:
    import os
    log_dir = os.getenv('LOG_DIR', '/var/log/astrocoins')
    # Создаем директорию для логов, если её нет
    os.makedirs(log_dir, exist_ok=True)
    
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
                'filename': os.path.join(log_dir, 'django.log'),
                'formatter': 'verbose',
            },
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
        },
        'root': {
            'handlers': ['console'],  # В продакшене только консоль, файл по желанию
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'core': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }