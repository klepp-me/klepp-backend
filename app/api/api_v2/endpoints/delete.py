from aiobotocore.client import AioBaseClient
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_boto, yield_db_session
from app.api.security import cognito_signed_in
from app.core.config import settings
from app.models.klepp import User, Video

router = APIRouter()


class DeletedFileResponse(BaseModel):
    path: str = Field(...)


@router.delete('/files', response_model=DeletedFileResponse)
async def delete_file(
    path: DeletedFileResponse,
    boto_session: AioBaseClient = Depends(get_boto),
    user: User = Depends(cognito_signed_in),
    db_session: AsyncSession = Depends(yield_db_session),
) -> dict[str, str]:
    """
    Delete file with filename
    """
    video_statement = select(Video).where(and_(Video.path == path.path, Video.user_id == user.id))
    db_result = await db_session.exec(video_statement)  # type: ignore
    video = db_result.one_or_none()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found. Ensure you own the file, and that the file already exist.',
        )
    await boto_session.delete_object(Bucket=settings.S3_BUCKET_URL, Key=video.path)
    if video.thumbnail_uri:
        await boto_session.delete_object(
            Bucket=settings.S3_BUCKET_URL, key=video.thumbnail_uri.split('https://gg.klepp.me/')[0]
        )
    await db_session.delete(video)
    await db_session.commit()
    return {'path': path.path}
