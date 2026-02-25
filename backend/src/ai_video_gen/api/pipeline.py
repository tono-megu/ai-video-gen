"""パイプラインAPI"""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ai_video_gen.pipeline.script import generate_script, update_script, convert_document_to_script

router = APIRouter()


class ScriptUpdateRequest(BaseModel):
    """脚本更新リクエスト"""
    script: dict


class DocumentConvertRequest(BaseModel):
    """ドキュメント変換リクエスト"""
    document: str
    theme: str


class ScriptResponse(BaseModel):
    """脚本レスポンス"""
    script: dict
    message: str


@router.post("/{project_id}/generate-script", response_model=ScriptResponse)
async def api_generate_script(project_id: UUID) -> ScriptResponse:
    """脚本を生成"""
    try:
        script = await generate_script(project_id)
        return ScriptResponse(
            script=script,
            message="脚本を生成しました",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{project_id}/script", response_model=ScriptResponse)
async def api_update_script(
    project_id: UUID,
    request: ScriptUpdateRequest,
) -> ScriptResponse:
    """脚本を更新"""
    try:
        script = await update_script(project_id, request.script)
        return ScriptResponse(
            script=script,
            message="脚本を更新しました",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/convert-document", response_model=ScriptResponse)
async def api_convert_document(
    project_id: UUID,
    request: DocumentConvertRequest,
) -> ScriptResponse:
    """ドキュメントを脚本に変換"""
    try:
        script = await convert_document_to_script(
            project_id,
            request.document,
            request.theme,
        )
        return ScriptResponse(
            script=script,
            message="ドキュメントを脚本に変換しました",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
