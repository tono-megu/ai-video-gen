"""動画合成パイプライン"""

from uuid import UUID

from ai_video_gen.models import ProjectState
from ai_video_gen.services.ffmpeg import ffmpeg_service
from ai_video_gen.services.supabase import get_supabase_client


async def compose_video(project_id: UUID) -> dict:
    """プロジェクトの動画を合成"""
    client = get_supabase_client()

    # プロジェクト取得
    project_result = client.table("projects").select("*").eq("id", str(project_id)).execute()
    if not project_result.data:
        raise ValueError(f"Project not found: {project_id}")

    project = project_result.data[0]
    if project["state"] not in ("narration_done", "composed"):
        raise ValueError("Narration must be generated first")

    # セクション取得
    sections_result = (
        client.table("sections")
        .select("*")
        .eq("project_id", str(project_id))
        .order("section_index")
        .execute()
    )

    sections = sections_result.data or []
    if not sections:
        raise ValueError("No sections found")

    # 合計時間を計算
    total_duration = sum(s.get("duration") or 5.0 for s in sections)

    # FFmpegが利用可能か確認
    ffmpeg_available = await ffmpeg_service.check_ffmpeg()

    if ffmpeg_available:
        # 動画を合成
        video_data_url = await ffmpeg_service.compose_video(project_id, sections)

        # プロジェクト状態更新
        client.table("projects").update({
            "state": ProjectState.COMPOSED.value,
        }).eq("id", str(project_id)).execute()

        return {
            "status": "completed",
            "video_url": video_data_url,
            "duration": total_duration,
            "sections_count": len(sections),
            "estimated_size": ffmpeg_service.estimate_file_size(total_duration),
        }
    else:
        # モックモード: 動画は生成しないが状態は更新
        client.table("projects").update({
            "state": ProjectState.COMPOSED.value,
        }).eq("id", str(project_id)).execute()

        return {
            "status": "mock",
            "message": "FFmpegがインストールされていないため、動画は生成されませんでした",
            "duration": total_duration,
            "sections_count": len(sections),
            "estimated_size": ffmpeg_service.estimate_file_size(total_duration),
        }


async def get_compose_status(project_id: UUID) -> dict:
    """動画合成の状態を取得"""
    client = get_supabase_client()

    # プロジェクト取得
    project_result = client.table("projects").select("*").eq("id", str(project_id)).execute()
    if not project_result.data:
        raise ValueError(f"Project not found: {project_id}")

    project = project_result.data[0]

    # セクション取得
    sections_result = (
        client.table("sections")
        .select("*")
        .eq("project_id", str(project_id))
        .order("section_index")
        .execute()
    )

    sections = sections_result.data or []
    total_duration = sum(s.get("duration") or 5.0 for s in sections)

    # FFmpegが利用可能か確認
    ffmpeg_available = await ffmpeg_service.check_ffmpeg()

    return {
        "project_id": str(project_id),
        "state": project["state"],
        "is_composed": project["state"] == "composed",
        "can_compose": project["state"] in ("narration_done", "composed"),
        "ffmpeg_available": ffmpeg_available,
        "sections_count": len(sections),
        "total_duration": total_duration,
        "estimated_size": ffmpeg_service.estimate_file_size(total_duration),
    }
