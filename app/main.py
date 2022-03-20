from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.api.api_v2.api import api_router as api_v2_router
from app.api.security import cognito_scheme
from app.core.config import settings
from app.core.logging_config import setup_logging

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f'{settings.API_V2_STR}/openapi.json',
    swagger_ui_oauth2_redirect_url='/oauth2-redirect',
    swagger_ui_init_oauth={
        'usePkceWithAuthorizationCodeGrant': True,
        'clientId': settings.AWS_OPENAPI_CLIENT_ID,
    },
    on_startup=[setup_logging, cognito_scheme.openid_config.load_config],
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r'.*',
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_v2_router, prefix=settings.API_V2_STR)
