import typing
import uuid
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

if typing.TYPE_CHECKING:
    from app.models.klepp import Video


class User(SQLModel, table=True):
    """
    We store usernames just to be able to add likes, comments etc.
    All authentication is done through Cognito in AWS.
    I've decided to not have username as the primary key, since a username could change.
    """

    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)
    name: str = Field(index=True)
    videos: List['Video'] = Relationship(back_populates='username')
