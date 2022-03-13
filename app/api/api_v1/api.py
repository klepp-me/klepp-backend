from fastapi import APIRouter

from app.api.api_v1.endpoints import file

api_router = APIRouter()
api_router.include_router(file.router, tags=['files'], deprecated=True)
