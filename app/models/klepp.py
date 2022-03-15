import uuid
from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class UserBase(SQLModel):
    name: str = Field(index=True)


class User(UserBase, table=True):
    """
    We store usernames just to be able to add likes, comments etc.
    All authentication is done through Cognito in AWS.
    I've decided to not have username as the primary key, since a username could change.
    """

    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)
    videos: List['Video'] = Relationship(back_populates='user')


class UserRead(UserBase):
    pass


class VideoTagLink(SQLModel, table=True):
    tag_id: uuid.UUID = Field(default=None, foreign_key='tag.id', primary_key=True, nullable=False)
    video_path: str = Field(default=None, foreign_key='video.path', primary_key=True, nullable=False)


class TagBase(SQLModel):
    name: str = Field(...)


class Tag(TagBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)

    videos: List['Video'] = Relationship(back_populates='tags', link_model=VideoTagLink)


class TagRead(TagBase):
    pass


class VideoBase(SQLModel):
    path: str = Field(primary_key=True, nullable=False)
    display_name: str = Field(index=True)
    hidden: bool = Field(default=False)
    uploaded: datetime = Field(default=datetime.now())
    uri: str = Field(...)
    expire_at: Optional[datetime] = Field(default=None, nullable=True)


class Video(VideoBase, table=True):
    user_id: uuid.UUID = Field(foreign_key='user.id', nullable=False)
    user: 'User' = Relationship(back_populates='videos')

    tags: List[Tag] = Relationship(back_populates='videos', link_model=VideoTagLink)


class VideoRead(VideoBase):
    user: 'UserRead'
    tags: List['TagRead']
