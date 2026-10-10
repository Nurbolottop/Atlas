from core.settings.base import *

DEBUG = False

# Cookies только по HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Приложение работает за nginx, который терминирует HTTPS.
# Без этого Django считает запрос http-запросом и ломает CSRF/редиректы.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# USE_X_FORWARDED_HOST не включаем: nginx передаёт настоящий Host, а
# X-Forwarded-Host пришёл бы от клиента как есть.

# Прочие security-заголовки
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS: браузер год ходит на сайт только по HTTPS. Поддомены и preload
# не включаем — на домене zeastudio.su живут и другие проекты.
SECURE_HSTS_SECONDS = 31536000

# =============================================================================
# LOGGING — при DEBUG=False ошибки иначе уходят в никуда
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
