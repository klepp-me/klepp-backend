from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import create_engine
from sqlmodel.sql.expression import Select, SelectOfScalar

from app.core.config import settings

ASYNC_ENGINE = create_async_engine(settings.DATABASE_URL, echo=False)  # echo can be True/False or 'debug'

SYNC_ENGINE = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''), echo='debug')

SelectOfScalar.inherit_cache = True  # type: ignore
Select.inherit_cache = True  # type: ignore
