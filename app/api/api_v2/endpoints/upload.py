from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import aiofiles
from aiobotocore.client import AioBaseClient
from aiofiles import os
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import get_boto
from app.api.security import cognito_scheme
from app.api.services import await_ffmpeg
from app.core.config import settings
from app.schemas.file import FileResponse
from app.schemas.user import User

router = APIRouter()


@router.post('/files', response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description='File to upload'),
    file_name: Optional[str] = Form(
        default=None, alias='fileName', example='my_file.mp4', regex=r'^[\s\w\d_-]*$', min_length=2, max_length=40
    ),
    session: AioBaseClient = Depends(get_boto),
    user: User = Depends(cognito_scheme),
) -> Any:
    """
    Upload a file.
    """
    if not file:
        raise HTTPException(status_code=400, detail='You must provide a file.')

    if file.content_type != 'video/mp4':
        raise HTTPException(status_code=400, detail='Currently only support for video/mp4 files through this API.')

    file_name = f'{file_name}.mp4' if file_name and not file_name.endswith('.mp4') else file_name
    new_file_name = f'{user.username}/{file_name or file.filename}'

    exist = await session.list_objects_v2(Bucket=settings.S3_BUCKET_URL, Prefix=new_file_name)
    if exist.get('Contents'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='File already exist in s3.')

    # Save video
    temp_name = uuid4().hex
    async with aiofiles.open(f'{temp_name}.mp4', 'wb') as video:
        while content := await file.read(1024):
            await video.write(content)  # type: ignore

    # Video
    await session.put_object(
        Bucket=settings.S3_BUCKET_URL,
        Key=new_file_name,
        Body=f'{temp_name}.mp4',
        ACL='public-read',
    )

    await await_ffmpeg(url=f'{temp_name}.mp4', name=f'{temp_name}.png')
    # Thumbnail
    async with aiofiles.open(f'{temp_name}.png', 'rb+') as thumbnail_img:
        await session.put_object(
            Bucket=settings.S3_BUCKET_URL,
            Key=new_file_name.replace('.mp4', '.png'),
            Body=await thumbnail_img.read(),
            ACL='public-read',
        )

    # Cleanup
    await os.remove(f'{temp_name}.png')
    await os.remove(f'{temp_name}.mp4')

    return {
        'file_name': new_file_name,
        'username': user.username,
        'datetime': datetime.now(timezone.utc).isoformat(' ', 'seconds'),
    }
