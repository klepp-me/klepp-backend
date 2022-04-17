from fastapi import APIRouter

from app.render import video_player

api_router = APIRouter()
api_router.include_router(video_player.router, tags=['video'])
