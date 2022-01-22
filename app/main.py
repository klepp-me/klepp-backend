from fastapi import FastAPI, Security
from fastapi.middleware.cors import CORSMiddleware

from api.api_v1.api import api_router
from api.security import CognitoAuthorizationCodeBearerBase
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f'{settings.API_V1_STR}/openapi.json',
    swagger_ui_oauth2_redirect_url='/oauth2-redirect',
    swagger_ui_init_oauth={
        'usePkceWithAuthorizationCodeGrant': True,
        'clientId': settings.AWS_OPENAPI_CLIENT_ID,
    },
)

cognito_scheme = CognitoAuthorizationCodeBearerBase()
# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

app.include_router(api_router, prefix=settings.API_V1_STR, dependencies=[Security(cognito_scheme)])
