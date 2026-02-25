"""ナレーション生成パイプライン"""

import base64
from uuid import UUID

from ai_video_gen.models import ProjectState
from ai_video_gen.services.elevenlabs import elevenlabs_service
from ai_video_gen.services.supabase import get_supabase_client


async def generate_narrations(project_id: UUID) -> list[dict]:
    """プロジェクトの全セクションのナレーションを生成"""
    client = get_supabase_client()

    # プロジェクト取得
    project_result = client.table("projects").select("*").eq("id", str(project_id)).execute()
    if not project_result.data:
        raise ValueError(f"Project not found: {project_id}")

    project = project_result.data[0]
    if project["state"] == "init":
        raise ValueError("Script must be generated first")

    # セクション取得
    sections_result = (
        client.table("sections")
        .select("*")
        .eq("project_id", str(project_id))
        .order("section_index")
        .execute()
    )

    sections = sections_result.data or []
    results = []

    for section in sections:
        narration_text = section.get("narration") or ""
        if not narration_text:
            results.append({
                "section_id": section["id"],
                "section_index": section["section_index"],
                "status": "skipped",
                "message": "ナレーションテキストがありません",
            })
            continue

        # 音声生成
        audio_bytes = await elevenlabs_service.generate_speech(narration_text)

        if audio_bytes:
            # Base64エンコードしてdata URLとして保存
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            audio_data_url = f"data:audio/mpeg;base64,{audio_base64}"

            # セクション更新
            client.table("sections").update({
                "narration_audio_path": audio_data_url,
            }).eq("id", section["id"]).execute()

            results.append({
                "section_id": section["id"],
                "section_index": section["section_index"],
                "status": "generated",
                "duration": elevenlabs_service.estimate_duration(narration_text),
            })
        else:
            # モックモード: 推定時間のみ設定
            estimated_duration = elevenlabs_service.estimate_duration(narration_text)

            # セクション更新（durationのみ）
            client.table("sections").update({
                "duration": estimated_duration,
            }).eq("id", section["id"]).execute()

            results.append({
                "section_id": section["id"],
                "section_index": section["section_index"],
                "status": "mock",
                "duration": estimated_duration,
                "message": "APIキー未設定のためモックモード",
            })

    # プロジェクト状態更新
    client.table("projects").update({
        "state": ProjectState.NARRATION_DONE.value,
    }).eq("id", str(project_id)).execute()

    return results


async def regenerate_section_narration(
    project_id: UUID,
    section_id: UUID,
    narration_text: str | None = None,
) -> dict:
    """特定セクションのナレーションを再生成"""
    client = get_supabase_client()

    # セクション取得
    section_result = (
        client.table("sections")
        .select("*")
        .eq("id", str(section_id))
        .eq("project_id", str(project_id))
        .execute()
    )

    if not section_result.data:
        raise ValueError(f"Section not found: {section_id}")

    section = section_result.data[0]

    # ナレーションテキストが指定されていれば更新
    if narration_text:
        client.table("sections").update({
            "narration": narration_text,
        }).eq("id", str(section_id)).execute()
    else:
        narration_text = section.get("narration") or ""

    if not narration_text:
        return {
            "section_id": str(section_id),
            "section_index": section["section_index"],
            "status": "error",
            "message": "ナレーションテキストがありません",
        }

    # 音声生成
    audio_bytes = await elevenlabs_service.generate_speech(narration_text)

    if audio_bytes:
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        audio_data_url = f"data:audio/mpeg;base64,{audio_base64}"

        client.table("sections").update({
            "narration_audio_path": audio_data_url,
        }).eq("id", str(section_id)).execute()

        return {
            "section_id": str(section_id),
            "section_index": section["section_index"],
            "status": "generated",
            "audio_url": audio_data_url,
            "duration": elevenlabs_service.estimate_duration(narration_text),
        }
    else:
        estimated_duration = elevenlabs_service.estimate_duration(narration_text)

        client.table("sections").update({
            "duration": estimated_duration,
        }).eq("id", str(section_id)).execute()

        return {
            "section_id": str(section_id),
            "section_index": section["section_index"],
            "status": "mock",
            "duration": estimated_duration,
            "message": "APIキー未設定のためモックモード",
        }


async def get_section_narration(project_id: UUID, section_id: UUID) -> dict:
    """セクションのナレーション情報を取得"""
    client = get_supabase_client()

    section_result = (
        client.table("sections")
        .select("*")
        .eq("id", str(section_id))
        .eq("project_id", str(project_id))
        .execute()
    )

    if not section_result.data:
        raise ValueError(f"Section not found: {section_id}")

    section = section_result.data[0]

    return {
        "section_id": str(section_id),
        "section_index": section["section_index"],
        "type": section["type"],
        "narration_text": section.get("narration"),
        "audio_url": section.get("narration_audio_path"),
        "duration": section.get("duration"),
    }
