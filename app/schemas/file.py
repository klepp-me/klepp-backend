import datetime
from typing import List, Optional
from urllib.parse import quote

from pydantic import BaseModel, Field, root_validator, validator

from core.config import settings


class FileName(BaseModel):
    file_name: str = Field(..., alias='fileName')

    class Config:
        allow_population_by_field_name = True


class DeletedFileResponse(FileName):
    pass


class FileResponse(FileName):
    uri: str
    datetime: datetime.datetime
    username: str

    @root_validator(pre=True)
    def extract_uri(cls, value: dict) -> dict:
        """
        Extract file_name and create an uri
        """
        value['uri'] = f'https://{settings.S3_BUCKET_URL}/{quote(value["file_name"])}'
        return value


class HideFile(FileName):
    @validator('file_name')
    def validate_file_name(cls, value: str) -> str:
        """
        Validate file path is according to specification
        """
        if value.startswith('hidden/'):
            raise ValueError('Must not start with `hidden/`')
        return value


class ShowFile(FileName):
    @validator('file_name')
    def validate_file_name(cls, value: str) -> str:
        """
        Validate file path is according to specification
        """
        if not value.startswith('hidden/'):
            raise ValueError('File must start with `hidden/`')
        return value


class DeleteFile(FileName):
    pass


class ListFilesResponse(BaseModel):
    files: List[FileResponse] = Field(default=[])
    next_page: Optional[str] = Field(default=None, description='Next page key.', alias='nextPage')

    class Config:
        allow_population_by_field_name = True
