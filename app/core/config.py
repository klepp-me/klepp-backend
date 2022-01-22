from typing import List

from pydantic import AnyHttpUrl, BaseSettings, Field


class AWS(BaseSettings):
    # General
    AWS_REGION: str = Field('eu-north-1')

    # Auth
    AWS_USER_POOL_ID: str = Field(..., env='AWS_USER_POOL_ID')
    AWS_OPENAPI_CLIENT_ID: str = Field(..., env='AWS_OPENAPI_CLIENT_ID')

    # Management
    AWS_S3_ACCESS_KEY_ID: str = Field(..., env='AWS_S3_ACCESS_KEY_ID')
    AWS_S3_SECRET_ACCESS_KEY: str = Field(..., env='AWS_S3_SECRET_ACCESS_KEY')


class Settings(AWS):
    API_V1_STR: str = '/api/v1'

    ENVIRONMENT: str = Field('dev', env='ENVIRONMENT')
    TESTING: bool = Field(False, env='TESTING')
    SECRET_KEY: str = Field(..., env='SECRET_KEY')

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    PROJECT_NAME: str = 'klepp.me'

    class Config:  # noqa
        env_file = '../.env'
        env_file_encoding = 'utf-8'
        case_sensitive = True


settings: Settings = Settings()
