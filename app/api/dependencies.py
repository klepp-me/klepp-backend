from collections.abc import AsyncGenerator

from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.db import ASYNC_ENGINE

session = get_session()


async def get_boto() -> AioBaseClient:
    """
    Create a boto client which can be shared
    """
    async with session.create_client(
        's3',
        region_name=settings.AWS_REGION,
        aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
    ) as client:
        yield client


async def get_db_session() -> AsyncSession:
    """
    Return a session to the database
    """
    return AsyncSession(ASYNC_ENGINE, expire_on_commit=False)


async def yield_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a session to the database
    """
    async with AsyncSession(ASYNC_ENGINE, expire_on_commit=False) as db_session:
        yield db_session
