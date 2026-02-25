"""脚本生成サービス（Claude / Gemini 対応）"""

import json
from typing import AsyncIterator

import httpx

from ai_video_gen.config import settings

# ドキュメント変換プロンプト
DOCUMENT_CONVERT_PROMPT = """あなたは教育動画の脚本家です。
ユーザーが提供したドキュメント（箇条書き、メモ、原稿など）を、動画脚本に変換してください。

【最重要】原稿の文章をできる限りそのまま使用してください：
- 入力された文章の言い回し・表現を変えない
- 語尾の変更は最小限に（「です」「ます」の統一程度）
- 余計な言葉（「ですね」「〜しましょう」「それでは」等）を追加しない
- 説明や補足を勝手に追加しない
- 文章の順序を変えない

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

【セクション分割のルール】
- 1セクション＝1つのトピック（1スライド分）に分割
- 原稿の段落や話題の切り替わりでセクションを分ける
- 段落が長い場合はトピック単位に分割

注意:
- 箇条書きはスライドのbulletsに、コードはcodeセクションに
- JSONのみを出力（説明文不要）
"""

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

【重要】セクション分割のルール：
- 1セクション＝1つのトピック（1スライド分）に細かく分割する
- 「〇〇とは」「〇〇の種類」「〇〇の使い方」のような単位で分ける
- 悪い例: 「CSSの基本」で1セクション（粗すぎる）
- 良い例: 「CSSとは何か」「プロパティとは」「セレクタの種類」「クラスセレクタ」「IDセレクタ」で5セクション
- 各セクションは15〜45秒程度のナレーションが目安

注意:
- 各セクションのdurationは秒数
- narrationは話し言葉で自然に
- 目標時間に合わせてセクション数を調整
- JSONのみを出力（説明文不要）
"""


class ClaudeService:
    """脚本生成サービス（Claude / Gemini 対応）"""

    def __init__(self):
        self.claude_api_key = settings.anthropic_api_key
        self.gemini_api_key = settings.google_api_key
        self.claude_base_url = "https://api.anthropic.com/v1"
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.claude_model = "claude-sonnet-4-20250514"
        self.gemini_model = "gemini-2.0-flash"

    @property
    def is_available(self) -> bool:
        """いずれかのAPIキーが設定されているか"""
        return bool(self.claude_api_key) or bool(self.gemini_api_key)

    @property
    def use_gemini(self) -> bool:
        """Geminiを使用するか"""
        return not self.claude_api_key and bool(self.gemini_api_key)

    async def generate_script(
        self,
        theme: str,
        duration_target: float | None = None,
    ) -> dict:
        """脚本を生成"""
        if not self.is_available:
            return self._generate_mock_script(theme, duration_target)

        if self.use_gemini:
            return await self._generate_script_gemini(theme, duration_target)
        else:
            return await self._generate_script_claude(theme, duration_target)

    async def _generate_script_claude(
        self,
        theme: str,
        duration_target: float | None = None,
    ) -> dict:
        """Claude APIで脚本を生成"""
        user_prompt = f"テーマ: {theme}"
        if duration_target:
            user_prompt += f"\n目標時間: {duration_target}秒"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.claude_base_url}/messages",
                headers={
                    "x-api-key": self.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.claude_model,
                    "max_tokens": 4096,
                    "system": SCRIPT_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            content = result["content"][0]["text"]
            return self._extract_json(content)

    async def _generate_script_gemini(
        self,
        theme: str,
        duration_target: float | None = None,
    ) -> dict:
        """Gemini APIで脚本を生成"""
        user_prompt = f"テーマ: {theme}"
        if duration_target:
            user_prompt += f"\n目標時間: {duration_target}秒"

        full_prompt = f"{SCRIPT_SYSTEM_PROMPT}\n\n{user_prompt}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.gemini_base_url}/models/{self.gemini_model}:generateContent",
                params={"key": self.gemini_api_key},
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.5,
                        "maxOutputTokens": 4096,
                    },
                },
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            content = result["candidates"][0]["content"]["parts"][0]["text"]
            return self._extract_json(content)

    def _extract_json(self, content: str) -> dict:
        """レスポンスからJSONを抽出"""
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

        # Geminiはストリーミング非対応なので通常生成
        if self.use_gemini:
            script = await self._generate_script_gemini(theme, duration_target)
            yield json.dumps(script, ensure_ascii=False)
            return

        user_prompt = f"テーマ: {theme}"
        if duration_target:
            user_prompt += f"\n目標時間: {duration_target}秒"

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.claude_base_url}/messages",
                headers={
                    "x-api-key": self.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.claude_model,
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

    async def convert_document(self, document: str, theme: str) -> dict:
        """ドキュメントをナレーション形式の脚本に変換"""
        if not self.is_available:
            return self._generate_mock_script_from_document(document, theme)

        if self.use_gemini:
            return await self._convert_document_gemini(document, theme)
        else:
            return await self._convert_document_claude(document, theme)

    async def _convert_document_claude(self, document: str, theme: str) -> dict:
        """Claude APIでドキュメントを脚本に変換"""
        user_prompt = f"テーマ: {theme}\n\n以下のドキュメントを脚本に変換してください:\n\n{document}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.claude_base_url}/messages",
                headers={
                    "x-api-key": self.claude_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.claude_model,
                    "max_tokens": 4096,
                    "system": DOCUMENT_CONVERT_PROMPT,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            content = result["content"][0]["text"]
            return self._extract_json(content)

    async def _convert_document_gemini(self, document: str, theme: str) -> dict:
        """Gemini APIでドキュメントを脚本に変換"""
        user_prompt = f"テーマ: {theme}\n\n以下のドキュメントを脚本に変換してください:\n\n{document}"
        full_prompt = f"{DOCUMENT_CONVERT_PROMPT}\n\n{user_prompt}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.gemini_base_url}/models/{self.gemini_model}:generateContent",
                params={"key": self.gemini_api_key},
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 4096,
                    },
                },
                timeout=120.0,
            )
            response.raise_for_status()
            result = response.json()

            content = result["candidates"][0]["content"]["parts"][0]["text"]
            return self._extract_json(content)

    def _generate_mock_script_from_document(self, document: str, theme: str) -> dict:
        """モック脚本を生成（ドキュメントベース）"""
        # ドキュメントを行に分割
        lines = [line.strip() for line in document.split("\n") if line.strip()]

        sections = [
            {
                "type": "title",
                "duration": 5,
                "narration": f"こんにちは！今日は{theme}について学んでいきましょう。",
                "visual_spec": {
                    "title": f"{theme}",
                    "subtitle": "入力ドキュメントに基づく解説",
                },
            }
        ]

        # ドキュメントの各行をスライドに変換
        for i, line in enumerate(lines[:5]):  # 最大5行まで
            sections.append({
                "type": "slide",
                "duration": 30,
                "narration": f"{line}について説明しますね。これは非常に重要なポイントです。",
                "visual_spec": {
                    "heading": line[:30] if len(line) > 30 else line,
                    "bullets": [line],
                },
            })

        sections.append({
            "type": "summary",
            "duration": 10,
            "narration": f"以上で{theme}の説明は終わりです。ご視聴ありがとうございました！",
            "visual_spec": {
                "points": lines[:3] if len(lines) >= 3 else lines,
            },
        })

        return {
            "title": f"{theme}",
            "description": f"入力されたドキュメントに基づく{theme}の解説動画です。",
            "sections": sections,
        }

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
