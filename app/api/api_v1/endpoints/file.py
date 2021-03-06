from datetime import datetime, timezone
from typing import Any, Optional

from aiobotocore.client import AioBaseClient
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import get_boto
from app.api.security import cognito_scheme, cognito_scheme_or_anonymous
from app.core.config import settings
from app.schemas.schemas_v1.file import (
    DeletedFileResponse,
    DeleteFile,
    FileResponse,
    HideFile,
    ListFilesResponse,
    ShowFile,
)
from app.schemas.schemas_v1.user import User

router = APIRouter()


@router.post('/hide', response_model=FileResponse)
async def hide_file(
    file: HideFile, session: AioBaseClient = Depends(get_boto), user: User = Depends(cognito_scheme)
) -> Any:
    """
    Put file in hidden folder, which is still public, but not listed on the front page.
    """
    new_path = file.file_name.replace(user.username, f'{user.username}/hidden')

    exist = await session.list_objects_v2(Bucket=settings.S3_BUCKET_URL, Prefix=file.file_name)
    if not exist.get('Contents'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Could not find the provided file.')

    await session.copy_object(
        ACL='public-read',
        Bucket=settings.S3_BUCKET_URL,
        CopySource={'Bucket': settings.S3_BUCKET_URL, 'Key': file.file_name},
        Key=new_path,
    )
    await session.delete_object(Bucket=settings.S3_BUCKET_URL, Key=file.file_name)

    return {
        'file_name': new_path,
        'datetime': datetime.now(timezone.utc).isoformat(' ', 'seconds'),
        'username': user.username,
    }


@router.post('/show', response_model=FileResponse)
async def show_file(
    file: ShowFile, session: AioBaseClient = Depends(get_boto), user: User = Depends(cognito_scheme)
) -> Any:
    """
    Remove the file from the hidden folder, so that it is listed on the front page.
    """
    new_path = file.file_name.replace(f'{user.username}/hidden', user.username)
    exist = await session.list_objects_v2(Bucket=settings.S3_BUCKET_URL, Prefix=file.file_name)
    if not exist.get('Contents'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Could not find the provided file.')

    await session.copy_object(
        ACL='public-read',
        Bucket=settings.S3_BUCKET_URL,
        CopySource={'Bucket': settings.S3_BUCKET_URL, 'Key': file.file_name},
        Key=new_path,
    )
    await session.delete_object(Bucket=settings.S3_BUCKET_URL, Key=file.file_name)

    return {
        'file_name': new_path,
        'username': user.username,
        'datetime': datetime.now(timezone.utc).isoformat(' ', 'seconds'),
    }


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
    Upload a file
    """
    if not file:
        raise HTTPException(status_code=400, detail='You must provide a file.')

    if file.content_type != 'video/mp4':
        raise HTTPException(status_code=400, detail='Currently only support for video/mp4 files through this API.')

    file_name = f'{file_name}.mp4' if file_name and not file_name.endswith('.mp4') else file_name

    new_file_name = f'{user.username}/{file_name or file.filename}'
    exist = await session.list_objects_v2(Bucket=settings.S3_BUCKET_URL, Prefix=new_file_name)
    if exist.get('Contents'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='File already exist.')
    await session.put_object(
        Bucket=settings.S3_BUCKET_URL,
        Key=new_file_name,
        Body=await file.read(),
        ACL='public-read',
    )

    return {
        'file_name': new_file_name,
        'username': user.username,
        'datetime': datetime.now(timezone.utc).isoformat(' ', 'seconds'),
    }


@router.delete('/files', response_model=DeletedFileResponse)
async def delete_file(
    file: DeleteFile, session: AioBaseClient = Depends(get_boto), user: User = Depends(cognito_scheme)
) -> DeletedFileResponse:
    """
    Delete file with filename
    """
    if not file.file_name.startswith(f'{user.username}/'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can only delete your own files.',
        )
    exist = await session.list_objects_v2(Bucket=settings.S3_BUCKET_URL, Prefix=file.file_name)
    if not exist.get('Contents'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Could not find the file.')
    await session.delete_object(Bucket=settings.S3_BUCKET_URL, Key=file.file_name)
    return DeletedFileResponse(file_name=file.file_name)


@router.get('/files', response_model=ListFilesResponse)
async def get_all_files(
    session: AioBaseClient = Depends(get_boto), user: User | None = Depends(cognito_scheme_or_anonymous)
) -> dict[str, list[dict]]:
    """
    Get a list of all non-hidden files, unless you're the owner of the file.
    Works both as anonymous user and as a signed in user.
    """
    bucket = await session.list_objects_v2(Bucket=settings.S3_BUCKET_URL)

    if not user:
        user = User(username='AnonymousUser')

    file_list_response: dict[str, list[dict]] = {'files': [], 'hidden_files': []}

    for file in bucket['Contents']:
        path: str = file['Key']
        if not path.endswith('.mp4'):
            continue
        split_path = path.split('/')
        if len(split_path) <= 1:
            # If a path don't contain at least a username, we don't want to list it at all.
            continue
        path_owner = split_path[0]
        if path_owner != user.username and split_path[1] == 'hidden':
            continue

        if path_owner == user.username and split_path[1] == 'hidden':
            file_list_response['hidden_files'].append(
                {'file_name': path, 'datetime': file['LastModified'], 'username': path_owner}
            )
        file_list_response['files'].append(
            {'file_name': path, 'datetime': file['LastModified'], 'username': path_owner}
        )

    return file_list_response
