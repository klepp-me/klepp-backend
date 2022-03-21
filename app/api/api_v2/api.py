from fastapi import APIRouter

from app.api.api_v2.endpoints import delete, list_videos, patch_video, upload

api_router = APIRouter()
api_router.include_router(list_videos.router, tags=['files'])
api_router.include_router(upload.router, tags=['files'])
api_router.include_router(delete.router, tags=['files'])
api_router.include_router(patch_video.router, tags=['files'])
