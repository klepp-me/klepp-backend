from functools import lru_cache
from typing import List, Optional, Union

from decouple import config
from pydantic import AnyHttpUrl, BaseSettings, HttpUrl, validator
from pydantic.networks import AnyUrl


class Credentials(BaseSettings):
    AWS_ACCESS_KEY_ID = config('AWS_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_KEY')

    DATABASE_URL: AnyUrl = config('DATABASE_URL')


class Settings(Credentials):
    API_V1_STR: str = '/api/v1'

    ENVIRONMENT: str = config('ENVIRONMENT', 'dev')
    TESTING: bool = config('TESTING', False)
    SECRET_KEY: str = config('SECRET_KEY', None)

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator('BACKEND_CORS_ORIGINS', pre=True)
    def assemble_cors_origins(cls, value: Union[str, List[str]]) -> Union[List[str], str]:
        """
        Validate cors list
        """
        if isinstance(value, str) and not value.startswith('['):
            return [i.strip() for i in value.split(',')]
        elif isinstance(value, (list, str)):
            return value
        raise ValueError(value)

    PROJECT_NAME: str = 'klipp'
    SENTRY_DSN: Optional[HttpUrl] = None

    @validator('SENTRY_DSN', pre=True)
    def sentry_dsn_can_be_blank(cls, value: str) -> Optional[str]:
        """
        Validate sentry DSN
        """
        if not value:
            return None
        return value

    class Config:  # noqa
        case_sensitive = True


@lru_cache
def load_settings() -> Settings:
    """
    Load all settings
    """
    return Settings()
