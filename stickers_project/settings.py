import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'your-secret-key'  # ВНИМАНИЕ: Замените на уникальный ключ в продакшене!

DEBUG = True  # ВНИМАНИЕ: Установите False в продакшене!

ALLOWED_HOSTS = [] # ВНИМАНИЕ: Заполните для продакшена!

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'stickers.apps.StickersConfig',  # Ваше приложение stickers
    'social_django',                 # Для социальной аутентификации
    'background_task',               # Для фоновых задач
    # 'channels', # Если вы используете Django Channels, добавьте его сюда (обычно не нужно для Channels v3+)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware', # Для поддержки языков
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'stickers_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Общая папка для шаблонов проекта, если нужна
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',      # Для social_django
                'social_django.context_processors.login_redirect', # Для social_django
            ],
        },
    },
]

WSGI_APPLICATION = 'stickers_project.wsgi.application'

# Добавлено для Django Channels
ASGI_APPLICATION = 'stickers.asgi.application' # Указывает на ASGI конфигурацию в вашем приложении stickers

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

LANGUAGE_CODE = 'en-us' # Язык по умолчанию

LANGUAGES = [
    ('ru', 'Russian'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'UTC'

USE_I18N = True # Включить интернационализацию

USE_TZ = True # Использовать часовые пояса

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "stickers/static"  # Статические файлы вашего приложения stickers
]
STATIC_ROOT = BASE_DIR / "staticfiles" # Для сбора статики в продакшене

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media' # Для загружаемых пользователем файлов

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2', # Аутентификация через Google
    'django.contrib.auth.backends.ModelBackend', # Стандартная аутентификация Django
)

# Настройки social_django для Google OAuth2
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = 'your-google-client-id' # ВНИМАНИЕ: Замените на ваш Client ID
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'your-google-client-secret' # ВНИМАНИЕ: Замените на ваш Client Secret

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/' # Куда перенаправлять после успешной социальной аутентификации
SOCIAL_AUTH_LOGIN_ERROR_URL = '/login/' # Куда перенаправлять при ошибке социальной аутентификации
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/profile/' # Куда перенаправлять нового пользователя после регистрации через соцсеть

LOGIN_URL = 'login' # URL для стандартного входа

# Настройки для django-background-tasks
# BACKGROUND_TASK_RUN_ASYNC = True # Если хотите запускать задачи асинхронно (может потребовать доп. настройки)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log', # Путь к лог-файлу
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO', # Уровень логирования для Django (можно поставить DEBUG для более подробных логов)
            'propagate': True,
        },
        'stickers.views': { # Логирование для конкретного модуля вашего приложения
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'background_task': { # Логирование для django-background-tasks
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}