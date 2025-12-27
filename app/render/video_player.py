import typing

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import yield_db_session
from app.models.klepp import Video

if typing.TYPE_CHECKING:
    from starlette.templating import _TemplateResponse

templates = Jinja2Templates(directory='templates')

router = APIRouter()


@router.get('/', response_class=HTMLResponse, include_in_schema=False)
async def render_video_page(
    request: Request, path: str, session: AsyncSession = Depends(yield_db_session)
) -> '_TemplateResponse':
    """
    Static site for share.klepp.me?path=<path>
    """
    video_statement = (
        select(Video)
        .options(selectinload(Video.user))  # type: ignore[arg-type]
        .options(selectinload(Video.tags))  # type: ignore[arg-type]
        .options(selectinload(Video.likes))  # type: ignore[arg-type]
        .order_by(desc(Video.uploaded_at))  # type: ignore[arg-type]
    )
    if path:
        # Short route, specific path requested. This cannot be a `files/{path}` API due to `/` in video paths.
        video_statement = video_statement.where(Video.path == path)
        video_response = await session.exec(video_statement)
        if found := video_response.one_or_none():
            return templates.TemplateResponse('video.html', {'request': request, 'video_dict': found.model_dump()})
    return templates.TemplateResponse('404.html', {'request': request})
