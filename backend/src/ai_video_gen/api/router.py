"""APIルーター集約"""

from fastapi import APIRouter

from ai_video_gen.api.pipeline import router as pipeline_router
from ai_video_gen.api.projects import router as projects_router
from ai_video_gen.api.visuals import router as visuals_router

api_router = APIRouter()

# プロジェクトAPI
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])

# パイプラインAPI
api_router.include_router(pipeline_router, prefix="/projects", tags=["pipeline"])

# ビジュアルAPI
api_router.include_router(visuals_router, prefix="/projects", tags=["visuals"])
