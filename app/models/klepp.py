import uuid
from datetime import datetime, timedelta, timezone
from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import Column, DateTime
from sqlmodel import Field, Relationship, SQLModel

ResponseModel = TypeVar('ResponseModel')


def generate_expire_at() -> datetime:
    """
    Generate util for video expiry date
    """
    return datetime.now(timezone.utc) + timedelta(weeks=12)


class ListResponse(BaseModel, Generic[ResponseModel]):
    total_count: int
    response: list[ResponseModel]


class VideoTagLink(SQLModel, table=True):
    tag_id: uuid.UUID = Field(default=None, foreign_key='tag.id', primary_key=True, nullable=False)
    video_path: str = Field(default=None, foreign_key='video.path', primary_key=True, nullable=False)


class VideoLikeLink(SQLModel, table=True):
    video_path: str = Field(foreign_key='video.path', primary_key=True, nullable=False)
    user_id: uuid.UUID = Field(foreign_key='user.id', primary_key=True, nullable=False)


class UserBase(SQLModel):
    name: str = Field(index=True)
    thumbnail_uri: str | None = Field(default=None, nullable=True)


class User(UserBase, table=True):
    """
    We store usernames just to be able to add likes, comments etc.
    All authentication is done through Cognito in AWS.
    I've decided to not have username as the primary key, since a username could change.
    """

    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)
    videos: list['Video'] = Relationship(back_populates='user')
    liked_videos: list['Video'] = Relationship(back_populates='likes', link_model=VideoLikeLink)


class UserRead(UserBase):
    pass


class TagBase(SQLModel):
    name: str = Field(...)


class Tag(TagBase, table=True):
    id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)

    videos: list['Video'] = Relationship(back_populates='tags', link_model=VideoTagLink)


class TagRead(TagBase):
    pass


class VideoBase(SQLModel):
    path: str = Field(primary_key=True, nullable=False, description='s3 path, primary key')
    display_name: str = Field(index=True, description='Display name of the video')
    hidden: bool = Field(default=False, description='Whether the file can be seen by anyone on the frontpage')
    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description='When the file was uploaded',
        sa_column=Column(DateTime(timezone=True)),
    )
    uri: str = Field(..., description='Link to the video')
    expire_at: datetime | None = Field(
        description='When the file is to be deleted',
        default_factory=generate_expire_at,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )


class Video(VideoBase, table=True):
    user_id: uuid.UUID = Field(foreign_key='user.id', nullable=False, description='User primary key')
    user: User = Relationship(back_populates='videos')
    thumbnail_uri: str | None = Field(default=None, nullable=True)

    tags: list[Tag] = Relationship(back_populates='videos', link_model=VideoTagLink)
    likes: list[User] = Relationship(back_populates='liked_videos', link_model=VideoLikeLink)


class VideoRead(VideoBase):
    user: 'UserRead'
    tags: list['TagRead']
    thumbnail_uri: str | None = Field(default=None, description='If it exist, we have a thumbnail for the video')
    likes: list['UserRead']
