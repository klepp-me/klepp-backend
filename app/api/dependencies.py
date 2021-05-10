from aiobotocore import get_session
from aiobotocore.session import ClientCreatorContext
from fastapi import File, UploadFile
from fastapi.exceptions import HTTPException

from core.config import settings
from schemas.file import AllowedFile


async def file_format(file: UploadFile = File(...)) -> UploadFile:
    """
    Check file format is text
    """
    if file.content_type == AllowedFile.JPEG:
        return file
    raise HTTPException(status_code=422, detail='File format not accepted')


session = get_session()


async def get_boto() -> ClientCreatorContext:
    """
    Create a boto client which can be shared
    """
    async with session.create_client(
        's3',
        region_name='eu-north-1',
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    ) as client:
        yield client
