import datetime
from typing import List

from pydantic import AnyUrl, BaseModel, Field, validator


class FileName(BaseModel):
    file_name: str = Field(..., alias='fileName')

    class Config:
        allow_population_by_field_name = True


class DeletedFileResponse(FileName):
    pass


class FileResponse(FileName):
    uri: AnyUrl
    datetime: datetime.datetime
    username: str


class HideFile(FileName):
    @validator('file_name')
    def validate_file_name(cls, value: str) -> str:
        """
        Validate file path is according to specification
        """
        if '/hidden/' in value:
            raise ValueError('Must not contain /hidden/')
        return value


class ShowFile(FileName):
    @validator('file_name')
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
    files: List[FileResponse] = Field(default=[])
    hidden_files: List[FileResponse] = Field(default=[], alias='hiddenFiles')

    class Config:
        allow_population_by_field_name = True
