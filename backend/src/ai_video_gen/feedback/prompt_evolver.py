"""プロンプト進化エンジン"""

from uuid import UUID

from ai_video_gen.config import settings
from ai_video_gen.feedback.preference_engine import preference_engine


class PromptEvolver:
    """プロンプト進化エンジン"""

    def __init__(self):
        self.api_key = settings.anthropic_api_key

    async def evolve_script_prompt(
        self,
        base_prompt: str,
        section_type: str | None = None,
        project_id: UUID | None = None,
    ) -> str:
        """脚本生成プロンプトを進化させる"""
        # 適用可能な好みを取得
        preferences = await preference_engine.get_applicable_preferences(
            section_type=section_type,
            project_id=project_id,
        )

        # 確信度が閾値以上の好みのみ適用
        high_confidence_prefs = [
            p for p in preferences
            if p.get("confidence", 0) >= preference_engine.SILENT_APPLY_THRESHOLD
        ]

        if not high_confidence_prefs:
            return base_prompt

        # 好みを追加指示として組み込む
        pref_instructions = self._format_preferences_as_instructions(high_confidence_prefs)

        evolved_prompt = f"""{base_prompt}

## ユーザーの好み（自動適用）
以下のスタイル・構造の好みを反映してください：
{pref_instructions}
"""

        return evolved_prompt

    async def evolve_visual_prompt(
        self,
        base_prompt: str,
        section_type: str | None = None,
        project_id: UUID | None = None,
    ) -> str:
        """ビジュアル生成プロンプトを進化させる"""
        preferences = await preference_engine.get_applicable_preferences(
            section_type=section_type,
            project_id=project_id,
        )

        # スタイル関連の好みをフィルタ
        style_prefs = [
            p for p in preferences
            if p.get("category") == "style"
            and p.get("confidence", 0) >= preference_engine.SILENT_APPLY_THRESHOLD
        ]

        if not style_prefs:
            return base_prompt

        pref_instructions = self._format_preferences_as_instructions(style_prefs)

        evolved_prompt = f"""{base_prompt}

スタイルの好み:
{pref_instructions}
"""

        return evolved_prompt

    async def evolve_narration_prompt(
        self,
        base_prompt: str,
        project_id: UUID | None = None,
    ) -> str:
        """ナレーション生成プロンプトを進化させる"""
        preferences = await preference_engine.get_applicable_preferences(
            project_id=project_id,
        )

        # コンテンツ関連の好みをフィルタ
        content_prefs = [
            p for p in preferences
            if p.get("category") in ("content", "style")
            and p.get("confidence", 0) >= preference_engine.SILENT_APPLY_THRESHOLD
        ]

        if not content_prefs:
            return base_prompt

        pref_instructions = self._format_preferences_as_instructions(content_prefs)

        evolved_prompt = f"""{base_prompt}

トーン・スタイルの好み:
{pref_instructions}
"""

        return evolved_prompt

    def _format_preferences_as_instructions(self, preferences: list[dict]) -> str:
        """好みを指示文として整形"""
        lines = []
        for pref in preferences:
            desc = pref.get("description", "")
            confidence = pref.get("confidence", 0)
            scope = pref.get("scope", "global")
            section_type = pref.get("section_type")

            if section_type:
                lines.append(f"- [{section_type}] {desc} (確信度: {confidence:.0%})")
            else:
                lines.append(f"- {desc} (確信度: {confidence:.0%})")

        return "\n".join(lines)

    async def suggest_prompt_improvements(
        self,
        current_prompt: str,
        project_id: UUID | None = None,
    ) -> list[dict]:
        """プロンプト改善を提案"""
        preferences = await preference_engine.get_applicable_preferences(
            project_id=project_id,
        )

        # 提案レベルの好みを取得
        suggestions_prefs = [
            p for p in preferences
            if preference_engine.SUGGEST_THRESHOLD
            <= p.get("confidence", 0)
            < preference_engine.SILENT_APPLY_THRESHOLD
        ]

        suggestions = []
        for pref in suggestions_prefs:
            suggestions.append({
                "preference_id": pref.get("preference_id"),
                "description": pref.get("description"),
                "confidence": pref.get("confidence"),
                "category": pref.get("category"),
                "action": f"この好みをプロンプトに追加: {pref.get('description')}",
            })

        return suggestions

    async def get_evolution_history(self, project_id: UUID) -> list[dict]:
        """プロンプト進化履歴を取得"""
        # 好みのprompt_versionを追跡
        preferences = await preference_engine.get_preferences()

        history = []
        for pref in preferences:
            if pref.get("project_id") == str(project_id):
                history.append({
                    "preference_id": pref.get("preference_id"),
                    "description": pref.get("description"),
                    "prompt_version": pref.get("prompt_version", 1),
                    "confidence": pref.get("confidence"),
                    "created_at": pref.get("created_at"),
                })

        return sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)

    async def create_personalized_system_prompt(
        self,
        base_system_prompt: str,
        project_id: UUID | None = None,
    ) -> str:
        """パーソナライズされたシステムプロンプトを生成"""
        profile = await preference_engine.get_preference_profile()

        if not profile.get("high_confidence"):
            return base_system_prompt

        # 高確信度の好みをシステムプロンプトに組み込む
        pref_section = "## ユーザープロファイル\nこのユーザーには以下の好みがあります：\n"

        for pref in profile["high_confidence"][:10]:  # 最大10件
            pref_section += f"- {pref['description']}\n"

        return f"{base_system_prompt}\n\n{pref_section}"


# シングルトンインスタンス
prompt_evolver = PromptEvolver()
