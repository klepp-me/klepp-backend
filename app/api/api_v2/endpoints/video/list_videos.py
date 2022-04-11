import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import yield_db_session
from app.api.security import cognito_scheme_or_anonymous
from app.models.klepp import ListResponse, Video, VideoRead
from app.schemas.schemas_v1.user import User as CognitoUser

router = APIRouter()


@router.get('/files', response_model=ListResponse[VideoRead])
async def get_all_files(
    session: AsyncSession = Depends(yield_db_session),
    user: CognitoUser | None = Depends(cognito_scheme_or_anonymous),
    username: Optional[str] = None,
    name: Optional[str] = None,
    hidden: bool = False,
    tag: list[str] = Query(default=[]),
    offset: int = 0,
    limit: int = Query(default=100, lte=100),
) -> dict[str, int | list]:
    """
    Get a list of all non-hidden files, unless you're the owner of the file, then you can request
    hidden files.
    Works both as anonymous user and as a signed in user.
    """
    # Video query
    video_statement = (
        select(Video)
        .options(selectinload(Video.user))
        .options(selectinload(Video.tags))
        .options(selectinload(Video.likes))
        .order_by(desc(Video.uploaded_at))
    )
    if username:
        video_statement = video_statement.where(Video.user.has(name=username))  # type: ignore
    if name:
        video_statement = video_statement.where(Video.display_name.contains(name))  # type: ignore
    if user and hidden:
        video_statement = video_statement.where(
            and_(Video.hidden == True, Video.user.has(name=user.username)),  # type:ignore  # noqa
        )
    else:
        video_statement = video_statement.where(Video.hidden == False)  # noqa

    for t in tag:
        video_statement = video_statement.where(Video.tags.any(name=t))  # type: ignore

    # Total count query based on query params, without pagination
    count_statement = select(func.count('*')).select_from(video_statement)  # type: ignore

    # Add pagination
    video_statement = video_statement.offset(offset=offset).limit(limit=limit)
    # Do DB requests async
    tasks = [
        asyncio.create_task(session.exec(video_statement)),  # type: ignore
        asyncio.create_task(session.exec(count_statement)),
    ]
    results, count = await asyncio.gather(*tasks)
    count_number = count.one_or_none()
    return {'total_count': count_number, 'response': results.all()}
