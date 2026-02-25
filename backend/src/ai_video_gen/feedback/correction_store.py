"""修正ログ管理（イベントソーシング）"""

from uuid import UUID

from pydantic import BaseModel

from ai_video_gen.services.supabase import get_supabase_client


class CorrectionEvent(BaseModel):
    """修正イベント"""
    project_id: str
    section_id: str | None = None
    stage: str  # script / narration / image / animation / composition
    category: str  # style / structural / content / technical
    field_path: str
    prior_value: str | None = None
    new_value: str | None = None
    original_prompt: str | None = None
    user_feedback: str | None = None
    original_image_path: str | None = None
    edited_image_path: str | None = None
    visual_diff_description: str | None = None


class CorrectionStore:
    """修正ログストア"""

    async def record_correction(self, event: CorrectionEvent) -> dict:
        """修正イベントを記録"""
        client = get_supabase_client()

        data = {
            "project_id": event.project_id,
            "section_id": event.section_id,
            "stage": event.stage,
            "category": event.category,
            "field_path": event.field_path,
            "prior_value": event.prior_value,
            "new_value": event.new_value,
            "original_prompt": event.original_prompt,
            "user_feedback": event.user_feedback,
            "original_image_path": event.original_image_path,
            "edited_image_path": event.edited_image_path,
            "visual_diff_description": event.visual_diff_description,
        }

        result = client.table("corrections").insert(data).execute()
        return result.data[0] if result.data else {}

    async def get_corrections(
        self,
        project_id: UUID | None = None,
        section_id: UUID | None = None,
        stage: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """修正ログを取得"""
        client = get_supabase_client()

        query = client.table("corrections").select("*")

        if project_id:
            query = query.eq("project_id", str(project_id))
        if section_id:
            query = query.eq("section_id", str(section_id))
        if stage:
            query = query.eq("stage", stage)
        if category:
            query = query.eq("category", category)

        query = query.order("created_at", desc=True).limit(limit)

        result = query.execute()
        return result.data or []

    async def get_recent_corrections(self, limit: int = 50) -> list[dict]:
        """最近の修正ログを取得"""
        client = get_supabase_client()

        result = (
            client.table("corrections")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return result.data or []

    async def get_corrections_by_category(self, category: str) -> list[dict]:
        """カテゴリ別の修正ログを取得"""
        return await self.get_corrections(category=category)

    async def get_correction_stats(self) -> dict:
        """修正統計を取得"""
        client = get_supabase_client()

        # 全件取得して集計（Supabaseの制限内で）
        result = client.table("corrections").select("stage, category").execute()
        corrections = result.data or []

        stats = {
            "total": len(corrections),
            "by_stage": {},
            "by_category": {},
        }

        for c in corrections:
            stage = c.get("stage", "unknown")
            category = c.get("category", "unknown")

            stats["by_stage"][stage] = stats["by_stage"].get(stage, 0) + 1
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        return stats


# シングルトンインスタンス
correction_store = CorrectionStore()
