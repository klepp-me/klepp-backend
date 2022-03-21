import asyncio
from typing import Any, Optional
from uuid import uuid4

import aiofiles
from aiobotocore.client import AioBaseClient
from aiofiles import os
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_boto, yield_db_session
from app.api.security import cognito_signed_in
from app.api.services import await_ffmpeg
from app.core.config import settings
from app.models.klepp import User, Video, VideoRead

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


@router.post('/files', response_model=VideoRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(..., description='File to upload'),
    file_name: Optional[str] = Form(
        default=None, example='my_file', regex=r'^[\s\w\d_-]*$', min_length=2, max_length=40
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
    video_uri = f'https://gg.klepp.me/{s3_path}'
    thumbnail_uri = f'https://gg.klepp.me/{user.name}/{upload_file_name}'.replace('.mp4', '.png')

    exist = await boto_session.list_objects_v2(Bucket=settings.S3_BUCKET_URL, Prefix=s3_path)
    if exist.get('Contents'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Video already exist in s3.')

    # Save video
    temp_name = uuid4().hex
    temp_vido_name = f'{temp_name}.mp4'
    temp_thumbnail_name = f'{temp_name}.png'
    async with aiofiles.open(temp_vido_name, 'wb') as video:
        while content := await file.read(1024):
            await video.write(content)  # type: ignore

    # Upload video and generate thumbnail
    upload_task = asyncio.create_task(
        upload_video(boto_session=boto_session, path=s3_path, temp_video_name=temp_vido_name)
    )
    ffmpeg_task = asyncio.create_task(await_ffmpeg(url=temp_vido_name, name=temp_thumbnail_name))
    await asyncio.gather(upload_task, ffmpeg_task)

    # Upload thumbnail and clean up
    async with aiofiles.open(temp_thumbnail_name, 'rb+') as thumbnail_img:
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

    # Add to DB and fetch it
    db_video: Video = Video(
        path=s3_path,
        display_name=upload_file_name,
        user=user,
        user_id=user.id,
        uri=video_uri,
        thumbnail_uri=thumbnail_uri,
    )
    db_session.add(db_video)
    await db_session.commit()
    # To keep responses equal between list and post APIs, we fetch it all
    query_video = (
        select(Video)
        .where(Video.path == db_video.path)
        .options(selectinload(Video.user))
        .options(selectinload(Video.tags))
        .options(selectinload(Video.likes))
    )
    result = await db_session.exec(query_video)  # type: ignore
    return result.first()
