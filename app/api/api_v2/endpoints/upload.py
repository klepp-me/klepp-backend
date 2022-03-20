import asyncio
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

import aiofiles
from aiobotocore.client import AioBaseClient
from aiofiles import os
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_boto, yield_db_session
from app.api.security import cognito_signed_in
from app.api.services import await_ffmpeg
from app.core.config import settings
from app.models.klepp import User, Video
from app.schemas.file import FileResponse

router = APIRouter()


async def upload_video(boto_session: AioBaseClient, path: str, temp_video_name: str) -> None:
    """
    Upload a stored file to s3
    """
    async with aiofiles.open(temp_video_name, 'rb+') as video_file:
        await boto_session.put_object(
            Bucket=settings.S3_BUCKET_URL,
            Key=path,
            Body=await video_file.read(),
            ACL='public-read',
        )


@router.post('/files', response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description='File to upload'),
    file_name: Optional[str] = Form(
        default=None, alias='fileName', example='my_file.mp4', regex=r'^[\s\w\d_-]*$', min_length=2, max_length=40
    ),
    boto_session: AioBaseClient = Depends(get_boto),
    user: User = Depends(cognito_signed_in),
    db_session: AsyncSession = Depends(yield_db_session),
) -> Any:
    """
    Upload a file.
    """
    if not file:
        raise HTTPException(status_code=400, detail='You must provide a file.')

    if file.content_type != 'video/mp4':
        raise HTTPException(status_code=400, detail='Currently only support for video/mp4 files through this API.')

    upload_file_name = f'{file_name}.mp4' if file_name else file.filename
    s3_path = f'{user.name}/{upload_file_name}'

    exist = await boto_session.list_objects_v2(Bucket=settings.S3_BUCKET_URL, Prefix=s3_path)
    if exist.get('Contents'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Video already exist in s3.')

    # Save video
    temp_name = uuid4().hex
    async with aiofiles.open(f'{temp_name}.mp4', 'wb') as video:
        while content := await file.read(1024):
            await video.write(content)  # type: ignore

    upload_task = asyncio.create_task(
        upload_video(boto_session=boto_session, path=s3_path, temp_video_name=f'{temp_name}.mp4')
    )
    ffmpeg_task = asyncio.create_task(await_ffmpeg(url=f'{temp_name}.mp4', name=f'{temp_name}.png'))
    await asyncio.gather(upload_task, ffmpeg_task)

    async with aiofiles.open(f'{temp_name}.png', 'rb+') as thumbnail_img:
        await boto_session.put_object(
            Bucket=settings.S3_BUCKET_URL,
            Key=s3_path.replace('.mp4', '.png'),
            Body=await thumbnail_img.read(),
            ACL='public-read',
        )

    # Cleanup
    remove_video = asyncio.create_task(os.remove(f'{temp_name}.mp4'))
    remove_thumbnail = asyncio.create_task(os.remove(f'{temp_name}.png'))
    await asyncio.gather(remove_video, remove_thumbnail)

    db_video: Video = Video(
        path=s3_path, display_name=file_name, user=user, user_id=user.id, uri=f'https://gg.klepp.me/{s3_path}'
    )
    db_session.add(db_video)
    await db_session.commit()

    return {
        'file_name': file_name,
        'username': user.name,
        'datetime': datetime.now(timezone.utc).isoformat(' ', 'seconds'),
    }
