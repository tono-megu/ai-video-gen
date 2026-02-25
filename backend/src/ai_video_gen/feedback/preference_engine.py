"""CIPHER式好み推論エンジン"""

from uuid import UUID

from pydantic import BaseModel

from ai_video_gen.config import settings
from ai_video_gen.services.supabase import get_supabase_client


class Preference(BaseModel):
    """ユーザーの好み"""
    preference_id: str | None = None
    description: str
    category: str  # style / structural / content / technical
    scope: str = "global"  # global / project / section_type / specific
    section_type: str | None = None
    project_id: str | None = None
    confidence: float = 0.5
    source_corrections: list[str] = []
    is_active: bool = True
    prompt_version: int = 1


class PreferenceEngine:
    """好み推論エンジン"""

    # 確信度閾値
    SILENT_APPLY_THRESHOLD = 0.85  # 自動適用
    SUGGEST_THRESHOLD = 0.50  # 提案
    # < 0.50 は記録のみ

    def __init__(self):
        self.api_key = settings.anthropic_api_key

    async def infer_preferences(
        self,
        corrections: list[dict],
    ) -> list[Preference]:
        """修正ログから好みを推論"""
        if not corrections:
            return []

        if not self.api_key:
            # モックモード
            return self._mock_infer_preferences(corrections)

        import httpx

        # 修正ログを整形
        corrections_text = self._format_corrections(corrections)

        prompt = f"""
以下はユーザーが教育動画のコンテンツに加えた修正ログです。
これらの修正パターンから、ユーザーの好みを推論してください。

修正ログ:
{corrections_text}

以下の形式でJSON配列として出力してください:
[
  {{
    "description": "好みの説明（具体的に）",
    "category": "style" | "structural" | "content" | "technical",
    "scope": "global" | "section_type" | "project",
    "section_type": "title" | "slide" | "code" | "summary" | null,
    "confidence": 0.0-1.0（確信度）
  }}
]

注意:
- 複数回同じパターンの修正があれば確信度を上げる
- 1-2回のみの修正は確信度0.3-0.5程度
- 5回以上の一貫した修正は確信度0.8以上
"""

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1024,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                },
            )

            if response.status_code != 200:
                return self._mock_infer_preferences(corrections)

            result = response.json()
            text = result["content"][0]["text"]

            return self._parse_preferences(text, corrections)

    def _format_corrections(self, corrections: list[dict]) -> str:
        """修正ログをテキスト形式に整形"""
        lines = []
        for c in corrections:
            line = f"- [{c.get('stage', '?')}][{c.get('category', '?')}] {c.get('field_path', '?')}: "
            if c.get("prior_value") and c.get("new_value"):
                line += f"'{c['prior_value']}' → '{c['new_value']}'"
            if c.get("user_feedback"):
                line += f" (フィードバック: {c['user_feedback']})"
            if c.get("visual_diff_description"):
                line += f" (ビジュアル差分: {c['visual_diff_description']})"
            lines.append(line)
        return "\n".join(lines)

    def _parse_preferences(
        self,
        text: str,
        corrections: list[dict],
    ) -> list[Preference]:
        """推論結果をパース"""
        import json

        try:
            # JSON部分を抽出
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            # JSON配列の開始位置を探す
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                text = text[start:end]

            data = json.loads(text.strip())

            correction_ids = [c.get("event_id", "") for c in corrections if c.get("event_id")]

            preferences = []
            for item in data:
                pref = Preference(
                    description=item.get("description", ""),
                    category=item.get("category", "style"),
                    scope=item.get("scope", "global"),
                    section_type=item.get("section_type"),
                    confidence=float(item.get("confidence", 0.5)),
                    source_corrections=correction_ids[:5],  # 最大5件
                )
                preferences.append(pref)

            return preferences

        except (json.JSONDecodeError, KeyError, ValueError):
            return self._mock_infer_preferences(corrections)

    def _mock_infer_preferences(self, corrections: list[dict]) -> list[Preference]:
        """モック推論結果"""
        # 修正数に基づいて確信度を計算
        confidence = min(0.9, 0.3 + len(corrections) * 0.1)

        return [
            Preference(
                description="コードブロックではダークテーマを使用",
                category="style",
                scope="section_type",
                section_type="code",
                confidence=confidence,
            ),
            Preference(
                description="タイトルスライドはシンプルなデザインを好む",
                category="style",
                scope="section_type",
                section_type="title",
                confidence=confidence * 0.8,
            ),
        ]

    async def save_preference(self, preference: Preference) -> dict:
        """好みをDBに保存"""
        client = get_supabase_client()

        data = {
            "description": preference.description,
            "category": preference.category,
            "scope": preference.scope,
            "section_type": preference.section_type,
            "project_id": preference.project_id,
            "confidence": preference.confidence,
            "source_corrections": preference.source_corrections,
            "is_active": preference.is_active,
            "prompt_version": preference.prompt_version,
        }

        result = client.table("preferences").insert(data).execute()
        return result.data[0] if result.data else {}

    async def get_preferences(
        self,
        scope: str | None = None,
        category: str | None = None,
        section_type: str | None = None,
        min_confidence: float = 0.0,
        active_only: bool = True,
    ) -> list[dict]:
        """好みを取得"""
        client = get_supabase_client()

        query = client.table("preferences").select("*")

        if scope:
            query = query.eq("scope", scope)
        if category:
            query = query.eq("category", category)
        if section_type:
            query = query.eq("section_type", section_type)
        if min_confidence > 0:
            query = query.gte("confidence", min_confidence)
        if active_only:
            query = query.eq("is_active", True)

        query = query.order("confidence", desc=True)

        result = query.execute()
        return result.data or []

    async def get_applicable_preferences(
        self,
        section_type: str | None = None,
        project_id: UUID | None = None,
    ) -> list[dict]:
        """適用可能な好みを優先度順で取得"""
        client = get_supabase_client()

        # 4段階のヒエラルキーで取得
        all_prefs = []

        # 1. グローバル
        global_result = (
            client.table("preferences")
            .select("*")
            .eq("scope", "global")
            .eq("is_active", True)
            .execute()
        )
        all_prefs.extend(global_result.data or [])

        # 2. プロジェクト
        if project_id:
            project_result = (
                client.table("preferences")
                .select("*")
                .eq("scope", "project")
                .eq("project_id", str(project_id))
                .eq("is_active", True)
                .execute()
            )
            all_prefs.extend(project_result.data or [])

        # 3. セクションタイプ
        if section_type:
            type_result = (
                client.table("preferences")
                .select("*")
                .eq("scope", "section_type")
                .eq("section_type", section_type)
                .eq("is_active", True)
                .execute()
            )
            all_prefs.extend(type_result.data or [])

        # 4. 個別（プロジェクト + セクションタイプ）
        if project_id and section_type:
            specific_result = (
                client.table("preferences")
                .select("*")
                .eq("scope", "specific")
                .eq("project_id", str(project_id))
                .eq("section_type", section_type)
                .eq("is_active", True)
                .execute()
            )
            all_prefs.extend(specific_result.data or [])

        # 確信度でソート
        all_prefs.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return all_prefs

    async def update_preference(
        self,
        preference_id: UUID,
        updates: dict,
    ) -> dict:
        """好みを更新"""
        client = get_supabase_client()

        result = (
            client.table("preferences")
            .update(updates)
            .eq("preference_id", str(preference_id))
            .execute()
        )

        return result.data[0] if result.data else {}

    async def deactivate_preference(self, preference_id: UUID) -> bool:
        """好みを無効化"""
        client = get_supabase_client()

        result = (
            client.table("preferences")
            .update({"is_active": False})
            .eq("preference_id", str(preference_id))
            .execute()
        )

        return bool(result.data)

    async def get_preference_profile(self) -> dict:
        """ユーザーの好みプロファイルを取得"""
        prefs = await self.get_preferences(active_only=True, min_confidence=0.5)

        profile = {
            "total_preferences": len(prefs),
            "by_category": {},
            "by_scope": {},
            "high_confidence": [],
            "suggestions": [],
        }

        for pref in prefs:
            category = pref.get("category", "unknown")
            scope = pref.get("scope", "unknown")
            confidence = pref.get("confidence", 0)

            profile["by_category"][category] = profile["by_category"].get(category, 0) + 1
            profile["by_scope"][scope] = profile["by_scope"].get(scope, 0) + 1

            if confidence >= self.SILENT_APPLY_THRESHOLD:
                profile["high_confidence"].append({
                    "id": pref.get("preference_id"),
                    "description": pref.get("description"),
                    "confidence": confidence,
                })
            elif confidence >= self.SUGGEST_THRESHOLD:
                profile["suggestions"].append({
                    "id": pref.get("preference_id"),
                    "description": pref.get("description"),
                    "confidence": confidence,
                })

        return profile


# シングルトンインスタンス
preference_engine = PreferenceEngine()
