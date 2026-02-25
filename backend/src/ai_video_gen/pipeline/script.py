"""脚本生成パイプライン"""

from uuid import UUID

from ai_video_gen.models import ProjectState, SectionType
from ai_video_gen.services.claude import claude_service
from ai_video_gen.services.supabase import get_supabase_client


async def generate_script(project_id: UUID) -> dict:
    """プロジェクトの脚本を生成"""
    client = get_supabase_client()

    # プロジェクト取得
    result = client.table("projects").select("*").eq("id", str(project_id)).execute()
    if not result.data:
        raise ValueError(f"Project not found: {project_id}")

    project = result.data[0]
    theme = project["theme"]
    duration_target = project.get("duration_target")

    # 脚本生成
    script = await claude_service.generate_script(theme, duration_target)

    # プロジェクト更新
    client.table("projects").update({
        "script": script,
        "state": ProjectState.SCRIPT_DONE.value,
    }).eq("id", str(project_id)).execute()

    # セクション作成
    sections_data = []
    for idx, section in enumerate(script.get("sections", [])):
        section_type = section.get("type", "slide")
        # 有効なセクションタイプか確認
        try:
            SectionType(section_type)
        except ValueError:
            section_type = "slide"

        sections_data.append({
            "project_id": str(project_id),
            "section_index": idx,
            "type": section_type,
            "duration": section.get("duration"),
            "narration": section.get("narration"),
            "visual_spec": section.get("visual_spec"),
        })

    if sections_data:
        # 既存セクションを削除
        client.table("sections").delete().eq("project_id", str(project_id)).execute()
        # 新規セクション挿入
        client.table("sections").insert(sections_data).execute()

    return script


async def update_script(project_id: UUID, script: dict) -> dict:
    """脚本を手動更新"""
    client = get_supabase_client()

    # プロジェクト更新
    result = client.table("projects").update({
        "script": script,
    }).eq("id", str(project_id)).execute()

    if not result.data:
        raise ValueError(f"Project not found: {project_id}")

    # セクション更新
    sections_data = []
    for idx, section in enumerate(script.get("sections", [])):
        section_type = section.get("type", "slide")
        try:
            SectionType(section_type)
        except ValueError:
            section_type = "slide"

        sections_data.append({
            "project_id": str(project_id),
            "section_index": idx,
            "type": section_type,
            "duration": section.get("duration"),
            "narration": section.get("narration"),
            "visual_spec": section.get("visual_spec"),
        })

    if sections_data:
        client.table("sections").delete().eq("project_id", str(project_id)).execute()
        client.table("sections").insert(sections_data).execute()

    return script
