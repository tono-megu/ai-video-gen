"""APIルーター集約"""

from fastapi import APIRouter

from ai_video_gen.api.compose import router as compose_router
from ai_video_gen.api.narration import router as narration_router
from ai_video_gen.api.pipeline import router as pipeline_router
from ai_video_gen.api.preferences import router as preferences_router
from ai_video_gen.api.projects import router as projects_router
from ai_video_gen.api.visuals import router as visuals_router

api_router = APIRouter()

# プロジェクトAPI
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])

# パイプラインAPI
api_router.include_router(pipeline_router, prefix="/projects", tags=["pipeline"])

# ビジュアルAPI
api_router.include_router(visuals_router, prefix="/projects", tags=["visuals"])

# ナレーションAPI
api_router.include_router(narration_router, prefix="/projects", tags=["narration"])

# 動画合成API
api_router.include_router(compose_router, prefix="/projects", tags=["compose"])

# 好み・フィードバックAPI
api_router.include_router(preferences_router, prefix="/feedback", tags=["feedback"])
