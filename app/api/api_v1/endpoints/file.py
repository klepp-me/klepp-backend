from aiobotocore.client import BaseClient
from fastapi import APIRouter, Depends, UploadFile

from api.dependencies import file_format, get_boto
from core.config import settings
from schemas.file import DeletedFileResponse, FileResponse, ListFilesResponse

router = APIRouter()


@router.post('/file/', response_model=FileResponse)
async def upload_file(session: BaseClient = Depends(get_boto), file: UploadFile = Depends(file_format)) -> FileResponse:
    """
    Retrieve contracts
    """
    await session.put_object(Bucket='kleppcat', Key=f'jonas/haha/{file.filename}', Body=await file.read())
    return FileResponse(
        file_name=file.filename, uri=f'https://kleppcat.s3.eu-north-1.amazonaws.com/jonas/haha{file.filename}'
    )


@router.delete('/file/{file_name}', response_model=DeletedFileResponse)
async def delete_file(file_name: str, session: BaseClient = Depends(get_boto)) -> DeletedFileResponse:
    """
    Delete file with filename
    """
    await session.delete_object(Bucket='kleppcat', Key=f'jonas/haha/{file_name}')

    return DeletedFileResponse(file_name=file_name)


@router.get('/file/files', response_model=ListFilesResponse)
async def get_all_files(session: BaseClient = Depends(get_boto)) -> ListFilesResponse:
    """
    Get a list of all users files or smf.
    """
    bucket = await session.list_objects(Bucket='kleppcat')
    file_list_response: ListFilesResponse = ListFilesResponse(files=[])

    for file in bucket['Contents']:
        path = file['Key']
        file_list_response.files.append(
            FileResponse(file_name=path, uri=f'https://kleppcat.s3.eu-north-1.amazonaws.com/{path}')
        )

    return file_list_response


@router.get('/ping')
async def pong() -> dict:
    """
    Ping function for testing
    """
    return {'ping': 'pong!', 'environment': settings.ENVIRONMENT, 'testing': settings.TESTING}
