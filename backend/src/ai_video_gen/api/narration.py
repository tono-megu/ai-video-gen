"""ナレーションAPI"""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_video_gen.pipeline.narration import (
    generate_narrations,
    get_section_narration,
    regenerate_section_narration,
)
from ai_video_gen.services.elevenlabs import elevenlabs_service

router = APIRouter()


class NarrationUpdateRequest(BaseModel):
    """ナレーション更新リクエスト"""
    narration_text: str


class NarrationResponse(BaseModel):
    """ナレーションレスポンス"""
    section_id: str
    section_index: int
    status: str
    duration: float | None = None
    audio_url: str | None = None
    narration_text: str | None = None
    message: str | None = None


class NarrationsResponse(BaseModel):
    """ナレーション生成レスポンス"""
    narrations: list[NarrationResponse]
    message: str


class VoiceResponse(BaseModel):
    """音声情報"""
    voice_id: str
    name: str
    category: str
    labels: dict


@router.post("/{project_id}/generate-narration", response_model=NarrationsResponse)
async def api_generate_narrations(project_id: UUID) -> NarrationsResponse:
    """全セクションのナレーションを生成"""
    try:
        results = await generate_narrations(project_id)
        narrations = [
            NarrationResponse(
                section_id=str(r["section_id"]),
                section_index=r["section_index"],
                status=r["status"],
                duration=r.get("duration"),
                message=r.get("message"),
            )
            for r in results
        ]
        return NarrationsResponse(
            narrations=narrations,
            message=f"{len([n for n in narrations if n.status in ('generated', 'mock')])}件のナレーションを生成しました",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/sections/{section_id}/narration", response_model=NarrationResponse)
async def api_get_narration(project_id: UUID, section_id: UUID) -> NarrationResponse:
    """セクションのナレーション情報を取得"""
    try:
        result = await get_section_narration(project_id, section_id)
        return NarrationResponse(
            section_id=result["section_id"],
            section_index=result["section_index"],
            status="available" if result.get("audio_url") else "not_generated",
            duration=result.get("duration"),
            audio_url=result.get("audio_url"),
            narration_text=result.get("narration_text"),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/sections/{section_id}/narration/regenerate", response_model=NarrationResponse)
async def api_regenerate_narration(
    project_id: UUID,
    section_id: UUID,
    request: NarrationUpdateRequest | None = None,
) -> NarrationResponse:
    """セクションのナレーションを再生成"""
    try:
        narration_text = request.narration_text if request else None
        result = await regenerate_section_narration(project_id, section_id, narration_text)
        return NarrationResponse(
            section_id=result["section_id"],
            section_index=result["section_index"],
            status=result["status"],
            duration=result.get("duration"),
            audio_url=result.get("audio_url"),
            message=result.get("message"),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices", response_model=list[VoiceResponse])
async def api_get_voices() -> list[VoiceResponse]:
    """利用可能な音声一覧を取得"""
    try:
        voices = await elevenlabs_service.get_voices()
        return [VoiceResponse(**v) for v in voices]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
