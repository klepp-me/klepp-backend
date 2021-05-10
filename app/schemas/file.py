from enum import Enum
from typing import List

from pydantic import BaseModel, HttpUrl


class AllowedFile(str, Enum):
    JPEG = 'image/jpeg'


class DeletedFileResponse(BaseModel):
    file_name: str


class FileResponse(BaseModel):
    file_name: str
    uri: HttpUrl


class ListFilesResponse(BaseModel):
    files: List[FileResponse]


class SummaryPayloadSchema(BaseModel):
    url: str


class SummaryResponseSchema(SummaryPayloadSchema):
    id: int
