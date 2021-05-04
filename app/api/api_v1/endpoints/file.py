from typing import Any

from aiobotocore.client import BaseClient
from fastapi import APIRouter, Depends, UploadFile

from api.dependencies import file_format, get_boto
from core.config import Settings, load_settings

router = APIRouter()


@router.post('/upload/')
async def upload_file(session: BaseClient = Depends(get_boto), file: UploadFile = Depends(file_format)) -> Any:
    """
    Retrieve contracts
    """
    await session.put_object(Bucket='klepp', Key=f'jonas/{file.filename}', Body=await file.read())
    # session.put_object(Bucket='klepp', key='test', Body='lol')
    return {'filename': file.filename, 'type': file.content_type}


@router.get('/ping')
async def pong(settings: Settings = Depends(load_settings)) -> dict:
    """
    Ping function for testing
    """
    return {'ping': 'pong!', 'environment': settings.ENVIRONMENT, 'testing': settings.TESTING}
