from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, BaseSettings, Field


class Credentials(BaseSettings):
    AWS_ACCESS_KEY_ID: str = Field(..., env='AWS_ID')
    AWS_SECRET_ACCESS_KEY: str = Field(..., env='AWS_SECRET_KEY')


class Settings(Credentials):
    API_V1_STR: str = '/api/v1'

    ENVIRONMENT: str = Field('dev', env='ENVIRONMENT')
    TESTING: bool = Field(False, env='TESTING')
    SECRET_KEY: str = Field(..., env='SECRET_KEY')

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    PROJECT_NAME: str = 'klepp'

    class Config:  # noqa
        env_file = '../.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True


@lru_cache
def load_settings() -> Settings:
    """
    Load all settings
    """
    return Settings()
