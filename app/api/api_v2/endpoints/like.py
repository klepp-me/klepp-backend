from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.services import fetch_one_or_none_video
from app.api.dependencies import yield_db_session
from app.api.security import cognito_signed_in
from app.models.klepp import User, Video, VideoRead

router = APIRouter()


class VideoLikeUnlike(BaseModel):
    path: str


@router.post('/like', response_model=VideoRead, status_code=status.HTTP_201_CREATED)
async def add_like(
    path: VideoLikeUnlike,
    user: User = Depends(cognito_signed_in),
    db_session: AsyncSession = Depends(yield_db_session),
) -> Any:
    """
    Add a like to a video
    """
    video_statement = (
        select(Video)
        .where(and_(Video.path == path.path, Video.hidden == False))  # noqa
        .options(selectinload(Video.likes))
    )
    result = await db_session.exec(video_statement)  # type: ignore
    video: Video | None = result.one_or_none()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Video not found.',
        )
    video.likes.append(user)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return await fetch_one_or_none_video(video_path=video.path, db_session=db_session)


@router.delete('/like', response_model=VideoRead, status_code=status.HTTP_200_OK)
async def delete_like(
    path: VideoLikeUnlike,
    user: User = Depends(cognito_signed_in),
    db_session: AsyncSession = Depends(yield_db_session),
) -> Any:
    """
    Remove like to a video
    """
    video_statement = (
        select(Video)
        .where(
            and_(
                Video.path == path.path,
                Video.hidden == False,  # noqa
                Video.likes.any(name=user.name),  # type: ignore
            )
        )
        .options(selectinload(Video.likes))
    )
    result = await db_session.exec(video_statement)  # type: ignore
    video = result.one_or_none()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Video not found.',
        )
    video.likes.remove(user)
    db_session.add(video)
    await db_session.commit()
    await db_session.refresh(video)
    return await fetch_one_or_none_video(video_path=video.path, db_session=db_session)
