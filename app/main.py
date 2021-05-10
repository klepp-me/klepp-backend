import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.api_v1.api import api_router
from core.config import settings
from db.db_init import init_db

log = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """
    Setup app
    :return:
    """
    application = FastAPI(title=settings.PROJECT_NAME, openapi_url=f'{settings.API_V1_STR}/openapi.json')

    # Set all CORS enabled origins
    if settings.BACKEND_CORS_ORIGINS:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )

    application.include_router(api_router, prefix=settings.API_V1_STR)

    return application


app = create_application()


@app.on_event('startup')
async def startup_event() -> None:
    """
    Startup:
      - Init db
    """
    log.info('Starting up...')
    init_db(app)
