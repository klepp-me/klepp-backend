import asyncio
import functools
from typing import Any
from uuid import uuid4

import aiofiles
from aiobotocore.client import AioBaseClient
from aiofiles import os
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession

from api.security import cognito_signed_in, generate_api_key_internals, get_fernet
from app.api.dependencies import get_boto, yield_db_session
from app.api.services import await_ffmpeg, generate_user_thumbnail
from app.core.config import settings
from app.models.klepp import ListResponse, User, UserRead, UserReadAPIKey

router = APIRouter()


@router.put('/me', response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def user_thumbnail(
    file: UploadFile = File(..., description='File to upload'),
    user: User = Depends(cognito_signed_in),
    db_session: AsyncSession = Depends(yield_db_session),
    boto_session: AioBaseClient = Depends(get_boto),
) -> Any:
    """
    Upload a profile thumbnail.
    This is behind a CDN, so it might take a little while for it to update
    """
    if not file:
        raise HTTPException(status_code=400, detail='You must provide a file.')
    allowed_formats = ['image/jpg', 'image/jpeg', 'image/png']
    if file.content_type not in allowed_formats:
        raise HTTPException(status_code=400, detail=f'Currently only support for {",".join(allowed_formats)}')

    # Save thumbnail
    temp_name = uuid4().hex
    output_name = f'{temp_name}.png'
    async with aiofiles.open(temp_name, 'wb') as img:
        while content := await file.read(1024):
            await img.write(content)  # type: ignore
    # Scale it
    await await_ffmpeg(functools.partial(generate_user_thumbnail, temp_name, output_name))

    # Upload thumbnail, delete original, delete old thumbnail in s3
    profile_pic_path = f'{user.name}/profile/{output_name}'
    async with aiofiles.open(temp_name, 'rb+') as thumbnail_img:
        await boto_session.put_object(
            Bucket=settings.S3_BUCKET_URL,
            Key=profile_pic_path,
            Body=await thumbnail_img.read(),
            ACL='public-read',
        )

    # Cleanup
    remove_original = asyncio.create_task(os.remove(temp_name))
    remove_thumbnail = asyncio.create_task(os.remove(output_name))
    if user.thumbnail_uri:
        delete_old_s3_thumbnail = asyncio.create_task(
            boto_session.delete_object(
                Bucket=settings.S3_BUCKET_URL, Key=user.thumbnail_uri.split('https://gg.klepp.me/')[1]
            )
        )
    await asyncio.gather(remove_original, remove_thumbnail, delete_old_s3_thumbnail)

    user.thumbnail_uri = f'https://gg.klepp.me/{profile_pic_path}'
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user.dict()


@router.post('/me/generate-api-key', response_model=ListResponse[UserReadAPIKey], dependencies=[])
async def api_key(
    db_session: AsyncSession = Depends(yield_db_session),
    user: User = Depends(cognito_signed_in),
) -> User:
    """
    Get a list of users
    """
    api_key_and_salt = generate_api_key_internals()
    user.api_key = get_fernet(api_key_and_salt.salt).encrypt(api_key_and_salt.api_key)
    user.salt = api_key_and_salt.salt
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    user.api_key = api_key_and_salt.api_key
    return user
