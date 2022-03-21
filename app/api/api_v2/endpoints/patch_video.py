from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import yield_db_session
from app.api.security import cognito_signed_in
from app.models.klepp import Tag, TagBase, User, Video, VideoRead

router = APIRouter()


class VideoPatch(BaseModel):
    path: str
    display_name: Optional[str] = Field(default=None, regex=r'^[\s\w\d_-]*$', min_length=2, max_length=40)
    hidden: bool = Field(default=False)
    tags: list[TagBase] = Field(default=[])


@router.patch('/files', response_model=VideoRead)
async def patch_video(
    video_patch: VideoPatch,
    db_session: AsyncSession = Depends(yield_db_session),
    user: User = Depends(cognito_signed_in),
) -> Any:
    """
    Partially update a video.
    """
    excluded = video_patch.dict(exclude_unset=True)
    query_video = (
        select(Video)
        .where(and_(Video.path == video_patch.path, Video.user_id == user.id))
        .options(selectinload(Video.tags))
    )
    db_result = await db_session.exec(query_video)  # type: ignore
    video = db_result.one_or_none()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found. Ensure you own the file, and that the file already exist.',
        )
    if excluded_tags := excluded.get('tags'):
        # They want to update tags, fetch available tags first
        list_tag = [tag['name'] for tag in excluded_tags]
        query_tags = select(Tag).where(Tag.name.in_(list_tag))  # type: ignore
        tag_result = await db_session.exec(query_tags)  # type: ignore
        tags: list[Tag] = tag_result.all()
        if len(list_tag) != len(tags):
            db_list_tag = [tag.name for tag in tags]
            not_found_tags = [f'`{tag}`' for tag in list_tag if tag not in db_list_tag]
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Tag {", ".join(not_found_tags)} not found.',
            )
        video.tags = tags
        excluded.pop('tags')

    # Patch remaining attributes
    for key, value in excluded.items():
        setattr(video, key, value)

    db_session.add(video)
    await db_session.commit()
    # To keep responses equal between list and post APIs, we fetch it all
    query_video = (
        select(Video)
        .where(Video.path == video_patch.path)
        .options(selectinload(Video.user))
        .options(selectinload(Video.tags))
        .options(selectinload(Video.likes))
    )
    result = await db_session.exec(query_video)  # type: ignore
    return result.one_or_none()
