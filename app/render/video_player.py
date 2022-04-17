from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory='templates')

router = APIRouter()


@router.get('/', response_class=HTMLResponse, include_in_schema=False)
async def render_video_page(request: Request, path: str):
    return templates.TemplateResponse('video.html', {'request': request, 'path': path})
