"""Gemini Visionによるビジュアル差分分析"""

import base64
import json

from pydantic import BaseModel

from ai_video_gen.config import settings


VISUAL_DIFF_PROMPT = """
2つの教育動画用スライド画像を比較してください。
画像1（AI生成の元画像）と画像2（ユーザーが手動修正した画像）の違いを分析し、
ユーザーが何を好んだのかを以下の観点で記述してください：
- レイアウト・余白
- 配色・コントラスト
- フォント・文字サイズ
- 図解・アイコンのスタイル
- テキスト内容の変更
- 全体の雰囲気・トーン

JSON形式で出力:
{
  "changes": [
    {"aspect": "配色", "before": "明るい青背景", "after": "ダークグレー背景",
     "preference": "コード解説スライドではダーク背景を好む"}
  ],
  "overall_preference": "全体的な好みの傾向を1文で"
}
"""


class VisualChange(BaseModel):
    """ビジュアル変更"""
    aspect: str
    before: str
    after: str
    preference: str


class VisualDiffResult(BaseModel):
    """ビジュアル差分結果"""
    changes: list[VisualChange]
    overall_preference: str


class VisualDiffAnalyzer:
    """ビジュアル差分分析器"""

    def __init__(self):
        self.api_key = settings.google_api_key

    async def analyze_diff(
        self,
        original_image: str,
        edited_image: str,
    ) -> VisualDiffResult:
        """2つの画像の差分を分析"""
        if not self.api_key:
            # モックモード
            return self._mock_diff_result()

        import httpx

        # 画像データを準備
        original_data = self._prepare_image_data(original_image)
        edited_data = self._prepare_image_data(edited_image)

        # Gemini Vision APIを呼び出し
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={self.api_key}",
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": VISUAL_DIFF_PROMPT},
                                {
                                    "inline_data": {
                                        "mime_type": original_data["mime_type"],
                                        "data": original_data["data"],
                                    }
                                },
                                {
                                    "inline_data": {
                                        "mime_type": edited_data["mime_type"],
                                        "data": edited_data["data"],
                                    }
                                },
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 1024,
                    },
                },
            )

            if response.status_code != 200:
                raise RuntimeError(f"Gemini Vision API error: {response.text}")

            result = response.json()
            text = result["candidates"][0]["content"]["parts"][0]["text"]

            # JSONを抽出してパース
            return self._parse_diff_result(text)

    def _prepare_image_data(self, image: str) -> dict:
        """画像データを準備"""
        if image.startswith("data:"):
            # data URL形式
            parts = image.split(",", 1)
            mime_type = parts[0].split(":")[1].split(";")[0]
            data = parts[1]
            return {"mime_type": mime_type, "data": data}
        else:
            # ファイルパスの場合（Supabase Storage URL等）
            # 実際にはhttpxでダウンロードが必要
            return {"mime_type": "image/png", "data": ""}

    def _parse_diff_result(self, text: str) -> VisualDiffResult:
        """Geminiの出力をパース"""
        # JSON部分を抽出
        try:
            # ```json ... ``` を除去
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text.strip())

            changes = [
                VisualChange(
                    aspect=c.get("aspect", ""),
                    before=c.get("before", ""),
                    after=c.get("after", ""),
                    preference=c.get("preference", ""),
                )
                for c in data.get("changes", [])
            ]

            return VisualDiffResult(
                changes=changes,
                overall_preference=data.get("overall_preference", ""),
            )
        except (json.JSONDecodeError, KeyError, IndexError):
            # パースに失敗した場合はモック結果を返す
            return self._mock_diff_result()

    def _mock_diff_result(self) -> VisualDiffResult:
        """モック差分結果"""
        return VisualDiffResult(
            changes=[
                VisualChange(
                    aspect="配色",
                    before="明るい背景",
                    after="ダーク背景",
                    preference="コード解説ではダーク背景を好む",
                ),
                VisualChange(
                    aspect="レイアウト",
                    before="中央寄せ",
                    after="左寄せ",
                    preference="テキストは左寄せを好む",
                ),
            ],
            overall_preference="落ち着いた色調でシンプルなレイアウトを好む傾向",
        )

    async def describe_single_image(self, image: str) -> str:
        """単一画像の内容を記述"""
        if not self.api_key:
            return "画像の説明（モックモード）: スライド画像"

        import httpx

        image_data = self._prepare_image_data(image)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={self.api_key}",
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": "この教育動画用スライド画像の内容を簡潔に日本語で説明してください。"},
                                {
                                    "inline_data": {
                                        "mime_type": image_data["mime_type"],
                                        "data": image_data["data"],
                                    }
                                },
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 256,
                    },
                },
            )

            if response.status_code != 200:
                return f"画像の説明を取得できませんでした: {response.status_code}"

            result = response.json()
            return result["candidates"][0]["content"]["parts"][0]["text"]


# シングルトンインスタンス
visual_diff_analyzer = VisualDiffAnalyzer()
