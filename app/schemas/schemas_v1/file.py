import datetime
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.config import settings


class FileName(BaseModel):
    file_name: str = Field(..., alias='fileName')

    model_config = ConfigDict(populate_by_name=True)


class DeletedFileResponse(FileName):
    pass


class FileResponse(FileName):
    uri: str
    datetime: datetime.datetime
    username: str

    @model_validator(mode='before')
    @classmethod
    def extract_uri(cls, value: dict) -> dict:
        """
        Extract file_name and create an uri
        """
        value['uri'] = f'https://{settings.S3_BUCKET_URL}/{quote(value["file_name"])}'
        return value


class HideFile(FileName):
    @field_validator('file_name')
    @classmethod
    def validate_file_name(cls, value: str) -> str:
        """
        Validate file path is according to specification
        """
        if '/hidden/' in value:
            raise ValueError('Must not contain /hidden/')
        return value


class ShowFile(FileName):
    @field_validator('file_name')
    @classmethod
    def validate_file_name(cls, value: str) -> str:
        """
        Validate file path is according to specification
        """
        if '/hidden/' not in value:
            raise ValueError('Must not contain /hidden/')
        return value


class DeleteFile(FileName):
    pass


class ListFilesResponse(BaseModel):
    files: list[FileResponse] = Field(default=[])
    hidden_files: list[FileResponse] = Field(default=[], alias='hiddenFiles')

    model_config = ConfigDict(populate_by_name=True)
