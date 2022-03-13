from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import create_engine

from app.core.config import settings

ASYNC_ENGINE = create_async_engine(settings.DATABASE_URL, echo=True)  # echo can be True/False or 'debug'

SYNC_ENGINE = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''), echo='debug')
