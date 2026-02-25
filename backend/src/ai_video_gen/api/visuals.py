"""ビジュアルAPI"""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_video_gen.pipeline.visuals import (
    generate_visuals,
    get_section_slide,
    regenerate_section_visual,
)

router = APIRouter()


class VisualSpec(BaseModel):
    """ビジュアル設定"""
    visual_spec: dict


class SlideResponse(BaseModel):
    """スライドレスポンス"""
    section_id: str
    section_index: int
    type: str
    slide_url: str | None = None
    visual_spec: dict | None = None
    narration: str | None = None


class VisualsResponse(BaseModel):
    """ビジュアル生成レスポンス"""
    slides: list[SlideResponse]
    message: str


@router.post("/{project_id}/generate-visuals", response_model=VisualsResponse)
async def api_generate_visuals(project_id: UUID) -> VisualsResponse:
    """全セクションのビジュアルを生成"""
    try:
        results = await generate_visuals(project_id)
        slides = [
            SlideResponse(
                section_id=str(r["section_id"]),
                section_index=r["section_index"],
                type=r["type"],
                slide_url=r["slide_url"],
            )
            for r in results
        ]
        return VisualsResponse(
            slides=slides,
            message=f"{len(slides)}件のスライドを生成しました",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/sections/{section_id}/slide", response_model=SlideResponse)
async def api_get_slide(project_id: UUID, section_id: UUID) -> SlideResponse:
    """セクションのスライド情報を取得"""
    try:
        result = await get_section_slide(project_id, section_id)
        return SlideResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/sections/{section_id}/slide/regenerate", response_model=SlideResponse)
async def api_regenerate_slide(
    project_id: UUID,
    section_id: UUID,
    request: VisualSpec | None = None,
) -> SlideResponse:
    """セクションのスライドを再生成"""
    try:
        visual_spec = request.visual_spec if request else None
        result = await regenerate_section_visual(project_id, section_id, visual_spec)
        return SlideResponse(
            section_id=result["section_id"],
            section_index=result["section_index"],
            type=result["type"],
            slide_url=result["slide_url"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}/sections/{section_id}/slide", response_model=SlideResponse)
async def api_update_slide(
    project_id: UUID,
    section_id: UUID,
    request: VisualSpec,
) -> SlideResponse:
    """セクションのビジュアル設定を更新して再生成"""
    try:
        result = await regenerate_section_visual(project_id, section_id, request.visual_spec)
        return SlideResponse(
            section_id=result["section_id"],
            section_index=result["section_index"],
            type=result["type"],
            slide_url=result["slide_url"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
