from fastapi import APIRouter

from api.api_v1.endpoints import file, summaries

api_router = APIRouter()
api_router.include_router(file.router, tags=['files'])
api_router.include_router(summaries.router, prefix='/summaries', tags=['summaries'])
