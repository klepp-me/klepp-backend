from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AWS(BaseSettings):
    # General
    AWS_REGION: str = Field(default='eu-north-1')
    S3_BUCKET_URL: str = Field(default='gg.klepp.me')

    # Auth
    AWS_USER_POOL_ID: str = Field(...)
    AWS_OPENAPI_CLIENT_ID: str = Field(...)

    # Management
    AWS_S3_ACCESS_KEY_ID: str = Field(...)
    AWS_S3_SECRET_ACCESS_KEY: str = Field(...)


class Settings(AWS):
    PROJECT_NAME: str = 'klepp.me'
    API_V1_STR: str = '/api/v1'
    API_V2_STR: str = '/api/v2'

    ENVIRONMENT: str = Field(default='dev')
    TESTING: bool = Field(default=False)
    SECRET_KEY: str = Field(...)
    DATABASE_URL: str = Field(..., alias='AZURE_DATABASE_URL')

    @field_validator('DATABASE_URL', mode='before')
    @classmethod
    def fix_postgres_url(cls, value: str) -> str:
        """
        Replace Heroku postgres connection string to an async one, and change the prefix
        """
        return value.replace('postgres://', 'postgresql+asyncpg://')

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = ['http://localhost:3000', 'http://localhost:5555']  # type: ignore

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore',
    )


settings: Settings = Settings()
