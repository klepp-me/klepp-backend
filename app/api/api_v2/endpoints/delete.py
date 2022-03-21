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
    file_path: str = Field(...)


@router.delete('/files', response_model=DeletedFileResponse)
async def delete_file(
    file_path: str,
    boto_session: AioBaseClient = Depends(get_boto),
    user: User = Depends(cognito_signed_in),
    db_session: AsyncSession = Depends(yield_db_session),
) -> dict[str, str]:
    """
    Delete file with filename
    """
    video_statement = select(Video).where(and_(Video.path == file_path, Video.user_id == user.id))
    db_result = await db_session.exec(video_statement)  # type: ignore
    video = db_result.first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='File not found. Ensure you own the file, and that the file already exist.',
        )
    await boto_session.delete_object(Bucket=settings.S3_BUCKET_URL, Key=file_path)
    await db_session.delete(video)
    await db_session.commit()
    return {'file_path': file_path}