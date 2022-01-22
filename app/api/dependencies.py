from aiobotocore.session import ClientCreatorContext, get_session
from fastapi import File, UploadFile
from fastapi.exceptions import HTTPException

from core.config import settings
from schemas.file import AllowedFile


async def file_format(file: UploadFile = File(...)) -> UploadFile:
    """
    Check file format is allowed
    """
    if file.content_type in [AllowedFile.JPEG, AllowedFile.MP4]:  # Rewrite to pydantic, but this hack works for now
        return file
    raise HTTPException(status_code=422, detail='File format not accepted')


session = get_session()


async def get_boto() -> ClientCreatorContext:
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
