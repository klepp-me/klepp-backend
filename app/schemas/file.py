from enum import Enum
from typing import List

from pydantic import AnyUrl, BaseModel


class AllowedFile(str, Enum):
    JPEG = 'image/jpeg'
    MP4 = 'video/mp4'


class DeletedFileResponse(BaseModel):
    file_name: str


class FileResponse(BaseModel):
    file_name: str
    uri: AnyUrl


class ListFilesResponse(BaseModel):
    files: List[FileResponse]
