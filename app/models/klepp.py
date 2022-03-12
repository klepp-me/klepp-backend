from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class Tag(str, Enum):
    csgo = 'csgo'
    eft = 'eft'
    ace = 'ace'
    fail = 'fail'


class Video(SQLModel, table=True):
    path: str = Field(primary_key=True, nullable=False)
    hidden: bool = Field(default=False)
    uploaded: datetime = Field(default=datetime.now())
    uri: str = Field(...)
    username: str = Field(...)
    tags: list[Tag] = Field(default=[])
    expire_at: datetime = Field(...)
