"""好みAPI"""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_video_gen.feedback.correction_store import CorrectionEvent, correction_store
from ai_video_gen.feedback.preference_engine import Preference, preference_engine
from ai_video_gen.feedback.visual_diff import visual_diff_analyzer

router = APIRouter()


# リクエスト/レスポンスモデル
class CorrectionRequest(BaseModel):
    """修正記録リクエスト"""
    project_id: str
    section_id: str | None = None
    stage: str
    category: str
    field_path: str
    prior_value: str | None = None
    new_value: str | None = None
    original_prompt: str | None = None
    user_feedback: str | None = None


class VisualDiffRequest(BaseModel):
    """ビジュアル差分リクエスト"""
    project_id: str
    section_id: str
    original_image: str  # data URL
    edited_image: str  # data URL


class PreferenceCreate(BaseModel):
    """好み作成リクエスト"""
    description: str
    category: str
    scope: str = "global"
    section_type: str | None = None
    project_id: str | None = None
    confidence: float = 0.5


class PreferenceUpdate(BaseModel):
    """好み更新リクエスト"""
    description: str | None = None
    confidence: float | None = None
    is_active: bool | None = None


class EvolveRequest(BaseModel):
    """プロンプト進化リクエスト"""
    limit: int = 50


# 修正ログAPI
@router.post("/corrections")
async def record_correction(request: CorrectionRequest) -> dict:
    """修正を記録"""
    try:
        event = CorrectionEvent(
            project_id=request.project_id,
            section_id=request.section_id,
            stage=request.stage,
            category=request.category,
            field_path=request.field_path,
            prior_value=request.prior_value,
            new_value=request.new_value,
            original_prompt=request.original_prompt,
            user_feedback=request.user_feedback,
        )
        result = await correction_store.record_correction(event)
        return {"status": "recorded", "event": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corrections")
async def get_corrections(
    project_id: str | None = None,
    stage: str | None = None,
    category: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """修正ログを取得"""
    try:
        project_uuid = UUID(project_id) if project_id else None
        return await correction_store.get_corrections(
            project_id=project_uuid,
            stage=stage,
            category=category,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corrections/stats")
async def get_correction_stats() -> dict:
    """修正統計を取得"""
    try:
        return await correction_store.get_correction_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ビジュアル差分API
@router.post("/visual-diff")
async def analyze_visual_diff(request: VisualDiffRequest) -> dict:
    """ビジュアル差分を分析"""
    try:
        result = await visual_diff_analyzer.analyze_diff(
            original_image=request.original_image,
            edited_image=request.edited_image,
        )

        # 修正ログにも記録
        event = CorrectionEvent(
            project_id=request.project_id,
            section_id=request.section_id,
            stage="image",
            category="style",
            field_path="slide_image",
            original_image_path=request.original_image[:100] + "...",  # 短縮
            edited_image_path=request.edited_image[:100] + "...",
            visual_diff_description=result.overall_preference,
        )
        await correction_store.record_correction(event)

        return {
            "changes": [c.model_dump() for c in result.changes],
            "overall_preference": result.overall_preference,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 好みAPI
@router.get("/preferences")
async def get_preferences(
    scope: str | None = None,
    category: str | None = None,
    section_type: str | None = None,
    min_confidence: float = 0.0,
    active_only: bool = True,
) -> list[dict]:
    """好みを取得"""
    try:
        return await preference_engine.get_preferences(
            scope=scope,
            category=category,
            section_type=section_type,
            min_confidence=min_confidence,
            active_only=active_only,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences/profile")
async def get_preference_profile() -> dict:
    """好みプロファイルを取得"""
    try:
        return await preference_engine.get_preference_profile()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences")
async def create_preference(request: PreferenceCreate) -> dict:
    """好みを作成"""
    try:
        pref = Preference(
            description=request.description,
            category=request.category,
            scope=request.scope,
            section_type=request.section_type,
            project_id=request.project_id,
            confidence=request.confidence,
        )
        result = await preference_engine.save_preference(pref)
        return {"status": "created", "preference": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/{preference_id}")
async def update_preference(preference_id: UUID, request: PreferenceUpdate) -> dict:
    """好みを更新"""
    try:
        updates = {}
        if request.description is not None:
            updates["description"] = request.description
        if request.confidence is not None:
            updates["confidence"] = request.confidence
        if request.is_active is not None:
            updates["is_active"] = request.is_active

        result = await preference_engine.update_preference(preference_id, updates)
        return {"status": "updated", "preference": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/preferences/{preference_id}")
async def deactivate_preference(preference_id: UUID) -> dict:
    """好みを無効化"""
    try:
        success = await preference_engine.deactivate_preference(preference_id)
        return {"status": "deactivated" if success else "failed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences/evolve")
async def evolve_preferences(request: EvolveRequest) -> dict:
    """修正ログから好みを推論して保存"""
    try:
        # 最近の修正ログを取得
        corrections = await correction_store.get_recent_corrections(limit=request.limit)

        if not corrections:
            return {"status": "no_corrections", "preferences": []}

        # 好みを推論
        inferred = await preference_engine.infer_preferences(corrections)

        # 保存
        saved = []
        for pref in inferred:
            result = await preference_engine.save_preference(pref)
            saved.append(result)

        return {
            "status": "evolved",
            "corrections_analyzed": len(corrections),
            "preferences_created": len(saved),
            "preferences": saved,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
