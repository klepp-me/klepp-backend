from aiobotocore.client import AioBaseClient
from aiobotocore.session import get_session

from app.core.config import settings

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
