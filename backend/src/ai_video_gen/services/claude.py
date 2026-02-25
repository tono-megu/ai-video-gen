"""Claude API サービス（脚本生成）"""

import json
from typing import AsyncIterator

import httpx

from ai_video_gen.config import settings

# 脚本生成プロンプト
SCRIPT_SYSTEM_PROMPT = """あなたは教育動画の脚本家です。
与えられたテーマに基づいて、教育・チュートリアル動画の脚本を作成してください。

出力形式は以下のJSONで返してください：
{
  "title": "動画タイトル",
  "description": "動画の概要（1-2文）",
  "sections": [
    {
      "type": "title",
      "duration": 5,
      "narration": "タイトル画面のナレーション",
      "visual_spec": {"title": "タイトルテキスト", "subtitle": "サブタイトル"}
    },
    {
      "type": "slide",
      "duration": 30,
      "narration": "このセクションのナレーション...",
      "visual_spec": {"heading": "見出し", "bullets": ["ポイント1", "ポイント2"]}
    },
    {
      "type": "code",
      "duration": 45,
      "narration": "コードの説明...",
      "visual_spec": {"language": "python", "code": "print('Hello')"}
    },
    {
      "type": "summary",
      "duration": 10,
      "narration": "まとめのナレーション",
      "visual_spec": {"points": ["まとめ1", "まとめ2"]}
    }
  ]
}

セクションタイプ:
- title: タイトル画面
- slide: スライド（箇条書き等）
- code: コード表示
- code_typing: コードタイピングアニメーション
- diagram: 図解
- summary: まとめ

注意:
- 各セクションのdurationは秒数
- narrationは話し言葉で自然に
- 目標時間に合わせてセクション数を調整
- JSONのみを出力（説明文不要）
"""


class ClaudeService:
    """Claude API クライアント"""

    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-sonnet-4-20250514"

    @property
    def is_available(self) -> bool:
        """APIキーが設定されているか"""
        return bool(self.api_key)

    async def generate_script(
        self,
        theme: str,
        duration_target: float | None = None,
    ) -> dict:
        """脚本を生成"""
        if not self.is_available:
            return self._generate_mock_script(theme, duration_target)

        user_prompt = f"テーマ: {theme}"
        if duration_target:
            user_prompt += f"\n目標時間: {duration_target}秒"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": SCRIPT_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            # レスポンスからJSONを抽出
            content = result["content"][0]["text"]
            # JSON部分を抽出（```json ... ``` で囲まれている場合も対応）
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())

    async def generate_script_stream(
        self,
        theme: str,
        duration_target: float | None = None,
    ) -> AsyncIterator[str]:
        """脚本をストリーミング生成"""
        if not self.is_available:
            # モックモード: 段階的に返す
            mock_script = self._generate_mock_script(theme, duration_target)
            yield json.dumps(mock_script, ensure_ascii=False)
            return

        user_prompt = f"テーマ: {theme}"
        if duration_target:
            user_prompt += f"\n目標時間: {duration_target}秒"

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,
                    "stream": True,
                    "system": SCRIPT_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=120.0,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if data["type"] == "content_block_delta":
                            yield data["delta"].get("text", "")

    def _generate_mock_script(
        self,
        theme: str,
        duration_target: float | None = None,
    ) -> dict:
        """モック脚本を生成（APIキーがない場合）"""
        target = duration_target or 180

        return {
            "title": f"{theme} 入門",
            "description": f"{theme}について基礎から学ぶチュートリアル動画です。",
            "sections": [
                {
                    "type": "title",
                    "duration": 5,
                    "narration": f"こんにちは！今日は{theme}について学んでいきましょう。",
                    "visual_spec": {
                        "title": f"{theme} 入門",
                        "subtitle": "基礎から学ぶチュートリアル",
                    },
                },
                {
                    "type": "slide",
                    "duration": int(target * 0.2),
                    "narration": f"まず、{theme}とは何かについて説明します。{theme}は非常に重要な概念で、多くの場面で活用されています。",
                    "visual_spec": {
                        "heading": f"{theme}とは？",
                        "bullets": [
                            "基本的な概念の説明",
                            "なぜ重要なのか",
                            "どのような場面で使われるか",
                        ],
                    },
                },
                {
                    "type": "code",
                    "duration": int(target * 0.3),
                    "narration": f"それでは、実際のコードを見てみましょう。これが{theme}の基本的な使い方です。",
                    "visual_spec": {
                        "language": "python",
                        "code": f"# {theme}の基本例\nprint('Hello, {theme}!')\n\n# 変数の定義\nvalue = 42\nprint(f'値: {{value}}')",
                    },
                },
                {
                    "type": "slide",
                    "duration": int(target * 0.25),
                    "narration": f"{theme}を使う際のポイントをまとめます。これらを押さえておけば、基本的な使い方はマスターできます。",
                    "visual_spec": {
                        "heading": "ポイント",
                        "bullets": [
                            "ポイント1: 基本を理解する",
                            "ポイント2: 実際に手を動かす",
                            "ポイント3: エラーを恐れない",
                        ],
                    },
                },
                {
                    "type": "summary",
                    "duration": int(target * 0.1),
                    "narration": f"以上で{theme}の基礎は終わりです。ぜひ実際に試してみてください。ご視聴ありがとうございました！",
                    "visual_spec": {
                        "points": [
                            f"{theme}の基本を学びました",
                            "実際のコード例を確認しました",
                            "次のステップに進む準備ができました",
                        ],
                    },
                },
            ],
        }


# シングルトンインスタンス
claude_service = ClaudeService()
