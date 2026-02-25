"""動画合成API"""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_video_gen.pipeline.compose import compose_video, get_compose_status

router = APIRouter()


class ComposeStatusResponse(BaseModel):
    """合成状態レスポンス"""
    project_id: str
    state: str
    is_composed: bool
    can_compose: bool
    ffmpeg_available: bool
    sections_count: int
    total_duration: float
    estimated_size: int


class ComposeResponse(BaseModel):
    """合成レスポンス"""
    status: str
    video_url: str | None = None
    duration: float
    sections_count: int
    estimated_size: int
    message: str | None = None


@router.get("/{project_id}/compose/status", response_model=ComposeStatusResponse)
async def api_get_compose_status(project_id: UUID) -> ComposeStatusResponse:
    """動画合成の状態を取得"""
    try:
        result = await get_compose_status(project_id)
        return ComposeStatusResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/compose", response_model=ComposeResponse)
async def api_compose_video(project_id: UUID) -> ComposeResponse:
    """動画を合成"""
    try:
        result = await compose_video(project_id)
        return ComposeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
