from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, asc, or_
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import yield_db_session
from app.api.security import cognito_scheme_or_anonymous
from app.models.klepp import Video, VideoRead
from app.schemas.user import User as CognitoUser

router = APIRouter()


@router.get('/files', response_model=list[VideoRead])
async def get_all_files(
    session: AsyncSession = Depends(yield_db_session),
    user: CognitoUser | None = Depends(cognito_scheme_or_anonymous),
    username: Optional[str] = None,
    hidden: bool = False,
    tag: Optional[str] = None,
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
) -> list:
    """
    Get a list of all non-hidden files, unless you're the owner of the file, then you can request
    hidden files.
    Works both as anonymous user and as a signed in user.
    """
    statement = (
        select(Video)
        .options(selectinload(Video.user))
        .options(selectinload(Video.tags))
        .offset(offset=offset)
        .limit(limit=limit)
        .order_by(asc(Video.uploaded))
    )
    if username and username.islower() and username.isalnum():
        statement = statement.where(Video.user.has(name=username))  # type: ignore
    if user and hidden:
        statement = statement.where(
            or_(
                Video.hidden == False,  # noqa
                and_(Video.hidden == True, Video.user.has(name=user.username)),  # type:ignore
            )
        )
    else:
        statement = statement.where(Video.hidden == False)  # noqa
    if tag:
        statement = statement.where(Video.tags.any(name=tag))  # type: ignore

    results = await session.exec(statement)  # type: ignore
    return results.all()
