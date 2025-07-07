from fastapi import APIRouter
from .endpoints import video_analysis, file, stage_matching

api_router = APIRouter()
api_router.include_router(video_analysis.router)
api_router.include_router(file.router)
api_router.include_router(stage_matching.router)

__all__ = ["api_router"]