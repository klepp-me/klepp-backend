from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import yield_db_session
from app.api.security import cognito_scheme_or_anonymous
from app.schemas.file import ListFilesResponse
from app.schemas.user import User

router = APIRouter()


@router.get('/files', response_model=ListFilesResponse)
async def get_all_files(
    session: AsyncSession = Depends(yield_db_session), user: User | None = Depends(cognito_scheme_or_anonymous)
) -> list:
    """
    Get a list of all non-hidden files, unless you're the owner of the file.
    Works both as anonymous user and as a signed in user.
    """
    return []
