"""ビジュアル生成パイプライン"""

from uuid import UUID

from ai_video_gen.models import ProjectState
from ai_video_gen.services.gemini import gemini_service
from ai_video_gen.services.slide_renderer import generate_slide_data_url
from ai_video_gen.services.supabase import get_supabase_client


async def generate_visuals(project_id: UUID) -> list[dict]:
    """プロジェクトの全セクションのビジュアルを生成"""
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
        visual_spec = section.get("visual_spec") or {}
        section_type = section.get("type", "slide")

        # HTMLスライドを生成（data URL形式）
        slide_data_url = generate_slide_data_url(visual_spec, section_type)

        # Gemini APIで画像生成を試みる（オプション）
        # 今回はHTMLベースのスライドをメインとする
        # image_bytes = await gemini_service.generate_slide_image(visual_spec, section_type)

        # セクション更新（slide_image_pathにdata URLを保存）
        client.table("sections").update({
            "slide_image_path": slide_data_url,
        }).eq("id", section["id"]).execute()

        results.append({
            "section_id": section["id"],
            "section_index": section["section_index"],
            "type": section_type,
            "slide_url": slide_data_url,
        })

    # プロジェクト状態更新
    client.table("projects").update({
        "state": ProjectState.VISUALS_DONE.value,
    }).eq("id", str(project_id)).execute()

    return results


async def regenerate_section_visual(
    project_id: UUID,
    section_id: UUID,
    visual_spec: dict | None = None,
) -> dict:
    """特定セクションのビジュアルを再生成"""
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

    # visual_specが指定されていれば更新
    if visual_spec:
        client.table("sections").update({
            "visual_spec": visual_spec,
        }).eq("id", str(section_id)).execute()
    else:
        visual_spec = section.get("visual_spec") or {}

    section_type = section.get("type", "slide")

    # HTMLスライドを再生成
    slide_data_url = generate_slide_data_url(visual_spec, section_type)

    # セクション更新
    client.table("sections").update({
        "slide_image_path": slide_data_url,
    }).eq("id", str(section_id)).execute()

    return {
        "section_id": str(section_id),
        "section_index": section["section_index"],
        "type": section_type,
        "slide_url": slide_data_url,
    }


async def get_section_slide(project_id: UUID, section_id: UUID) -> dict:
    """セクションのスライド情報を取得"""
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
        "visual_spec": section.get("visual_spec"),
        "slide_url": section.get("slide_image_path"),
        "narration": section.get("narration"),
    }
