from datetime import datetime, timezone
from typing import Any, Optional

from aiobotocore.client import AioBaseClient
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status

from api.dependencies import get_boto
from api.security import cognito_scheme, cognito_scheme_or_anonymous
from core.config import settings
from schemas.file import DeletedFileResponse, DeleteFile, FileResponse, HideFile, ListFilesResponse, ShowFile
from schemas.user import User

router = APIRouter()


@router.post('/hide', response_model=FileResponse)
async def hide_file(
    file: HideFile, session: AioBaseClient = Depends(get_boto), user: User = Depends(cognito_scheme)
) -> Any:
    """
    Put file in hidden bucket, which is still public, but not listed on the front page.
    """
    # Check if the file we try to hide exist
    file_exist = await session.list_objects_v2(Bucket=settings.S3_BUCKET_URL, Prefix=file.file_name)
    if not file_exist.get('Contents'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Could not find the provided file.')

    # Check that there is no file we would overwrite if we moved this file
    new_path = f'hidden/{file.file_name}'
    file_exist_as_hidden = await session.list_objects_v2(Bucket=settings.S3_BUCKET_HIDDEN_URL, Prefix=new_path)
    if file_exist_as_hidden.get('Contents'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='A hidden file with that name already exist.'
        )

    # Move file from gg.klepp.me bucket to hidden.gg.klepp.me bucket.
    await session.copy_object(
        Bucket=settings.S3_BUCKET_HIDDEN_URL,
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
    Move the file from the hidden bucket into the normal one, so that it is listed on the front page.
    """
    file_exist = await session.list_objects_v2(Bucket=settings.S3_BUCKET_HIDDEN_URL, Prefix=file.file_name)
    if not file_exist.get('Contents'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Could not find the provided file.')

    # Check that there is no file we would overwrite if we moved this file
    new_path = file.file_name.replace('hidden/', '', 1)
    file_exist_as_hidden = await session.list_objects_v2(Bucket=settings.S3_BUCKET_URL, Prefix=new_path)
    if file_exist_as_hidden.get('Contents'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='A file with that name already exist.')

    await session.copy_object(
        Bucket=settings.S3_BUCKET_URL,
        CopySource={'Bucket': settings.S3_BUCKET_HIDDEN_URL, 'Key': file.file_name},
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
    Delete file with filename. Works for both normal and hidden files.
    """
    if not file.file_name.startswith(f'{user.username}/'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You can only delete your own files.',
        )
    bucket = settings.S3_BUCKET_HIDDEN_URL if file.file_name.startswith('hidden/') else settings.S3_BUCKET_URL
    exist = await session.list_objects_v2(Bucket=bucket, Prefix=file.file_name)
    if not exist.get('Contents'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Could not find the file.')
    await session.delete_object(Bucket=bucket, Key=file.file_name)
    return DeletedFileResponse(file_name=file.file_name)


@router.get('/files', response_model=ListFilesResponse, dependencies=[Depends(cognito_scheme_or_anonymous)])
async def get_all_files(
    session: AioBaseClient = Depends(get_boto),
    folder: Optional[str] = Query(default=None, description='Folder path to only return files from. E.g. `hotfix/`'),
    next_page: Optional[str] = Query(default=None, alias='nextPage', description='The key for the next page'),
    page_size: int = Query(default=25, ge=1, le=1000, alias='pageSize', description='Number of videos to return'),
) -> dict[str, list[dict]]:
    """
    Get a list of all non-hidden files. Optional auth, don't matter if you're authenticated or not.
    """
    folder = f'{folder}/' if folder and not folder.endswith('/') else folder

    # SDK don't allow passing None, and empty strings are considered actual tokens..
    s3_list_kwargs = {'Bucket': settings.S3_BUCKET_URL, 'MaxKeys': page_size}
    if folder:
        s3_list_kwargs['Prefix'] = folder
    if next_page:
        s3_list_kwargs['ContinuationToken'] = next_page
    try:
        bucket = await session.list_objects_v2(**s3_list_kwargs)
    except ClientError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    file_list_response: dict[str, list[dict]] = {
        'files': [],
        'next_page': bucket.get('NextContinuationToken'),
    }

    for file in bucket.get('Contents', []):
        path: str = file['Key']
        if not path.endswith('.mp4'):
            continue
        split_path = path.split('/')
        if len(split_path) <= 1:
            # If a path don't contain at least a username, we don't want to list it at all.
            continue

        file_list_response['files'].append(
            {'file_name': path, 'datetime': file['LastModified'], 'username': split_path[0]}
        )

    return file_list_response


@router.get('/files/hidden', response_model=ListFilesResponse)
async def get_hidden_files_for_user(
    session: AioBaseClient = Depends(get_boto),
    next_page: Optional[str] = Query(default=None, alias='nextPage', description='The key for the next page'),
    page_size: int = Query(default=25, ge=1, le=1000, alias='pageSize', description='Number of videos to return'),
    user: User = Depends(cognito_scheme),
) -> dict[str, list[dict]]:
    """
    Get a list of all hidden files for that user.
    """
    # SDK don't allow passing None, and empty strings are considered actual tokens..
    s3_list_kwargs = {
        'Bucket': settings.S3_BUCKET_HIDDEN_URL,
        'MaxKeys': page_size,
        'Prefix': f'hidden/{user.username}',
    }
    if next_page:
        s3_list_kwargs['ContinuationToken'] = next_page
    try:
        bucket = await session.list_objects_v2(**s3_list_kwargs)
    except ClientError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

    file_list_response: dict[str, list[dict]] = {
        'files': [],
        'next_page': bucket.get('NextContinuationToken'),
    }

    for file in bucket.get('Contents', []):
        path: str = file['Key']
        if not path.endswith('.mp4') or not path.startswith('hidden/'):
            continue
        split_path = path.split('/')
        if len(split_path) <= 2:
            # If a path don't contain at least a username, we don't want to list it at all.
            continue

        file_list_response['files'].append(
            {'file_name': path, 'datetime': file['LastModified'], 'username': split_path[0]}
        )

    return file_list_response
