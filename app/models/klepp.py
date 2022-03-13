import typing
import uuid
from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

if typing.TYPE_CHECKING:
    from app.models.user import User


class VideoTagLink(SQLModel, table=True):
    tag_id: uuid.UUID = Field(default=None, foreign_key='tag.id', primary_key=True, nullable=False)
    video_path: str = Field(default=None, foreign_key='video.path', primary_key=True, nullable=False)


class Tag(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)
    name: str = Field(...)

    videos: List['Video'] = Relationship(back_populates='tags', link_model=VideoTagLink)


class Video(SQLModel, table=True):
    path: str = Field(primary_key=True, nullable=False)
    display_name: str = Field(index=True)
    hidden: bool = Field(default=False)
    uploaded: datetime = Field(default=datetime.now())
    uri: str = Field(...)
    expire_at: Optional[datetime] = Field(default=None, nullable=True)

    user_id: uuid.UUID = Field(foreign_key='user.id', nullable=False)
    username: 'User' = Relationship(back_populates='videos')

    tags: List[Tag] = Relationship(back_populates='videos', link_model=VideoTagLink)
