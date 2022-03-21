from fastapi import APIRouter

from api.api_v2.endpoints.video import delete, list_videos, patch_video, upload
from app.api.api_v2.endpoints import tags, user_thumbnail

api_router = APIRouter()
api_router.include_router(list_videos.router, tags=['files'])
api_router.include_router(upload.router, tags=['files'])
api_router.include_router(delete.router, tags=['files'])
api_router.include_router(patch_video.router, tags=['files'])
api_router.include_router(tags.router, tags=['tags'])
api_router.include_router(user_thumbnail.router, tags=['user'])
