from logging.config import dictConfig

from asgi_correlation_id import correlation_id_filter

from app.core.config import settings

LOGGING: dict = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'correlation_id': {'()': correlation_id_filter(8 if settings.ENVIRONMENT == 'dev' else 32)},
    },
    'formatters': {
        'console': {
            'format': '%(levelname)-8s  [%(correlation_id)s] %(name)s:%(lineno)d    %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['correlation_id'],
            'formatter': 'console',
        },
    },
    'loggers': {
        # third-party packages
        'httpx': {'level': 'DEBUG'},
        'asgi_correlation_id': {'level': 'WARNING'},
        'arq': {'level': 'INFO', 'propagate': True},
    },
    'root': {'handlers': ['console'], 'level': 'DEBUG'},
}


def setup_logging() -> None:
    """
    Call this function to setup logging for the app.
    """
    dictConfig(LOGGING)
