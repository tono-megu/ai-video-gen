"""Gemini API サービス（画像生成 + Vision）"""

import base64
import json
from pathlib import Path

import httpx

from ai_video_gen.config import settings


class GeminiService:
    """Gemini API クライアント"""

    def __init__(self):
        self.api_key = settings.google_api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model = "gemini-2.0-flash-exp"  # 画像生成対応モデル

    @property
    def is_available(self) -> bool:
        """APIキーが設定されているか"""
        return bool(self.api_key)

    async def generate_slide_image(
        self,
        visual_spec: dict,
        section_type: str,
    ) -> bytes | None:
        """スライド画像を生成（Imagen使用）"""
        if not self.is_available:
            return None  # モックモードでは画像生成スキップ

        # visual_specからプロンプトを構築
        prompt = self._build_image_prompt(visual_spec, section_type)

        try:
            async with httpx.AsyncClient() as client:
                # Gemini 2.0 Flash で画像生成
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [{
                            "parts": [{
                                "text": prompt
                            }]
                        }],
                        "generationConfig": {
                            "responseModalities": ["image", "text"],
                        }
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()

                # 画像データを抽出
                for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        image_data = part["inlineData"]["data"]
                        return base64.b64decode(image_data)

                return None
        except Exception as e:
            print(f"Image generation failed: {e}")
            return None

    def _build_image_prompt(self, visual_spec: dict, section_type: str) -> str:
        """visual_specからプロンプトを構築"""
        base_prompt = "教育動画用のスライド画像を生成してください。シンプルでプロフェッショナルなデザイン、16:9のアスペクト比。"

        if section_type == "title":
            title = visual_spec.get("title", "")
            subtitle = visual_spec.get("subtitle", "")
            return f"{base_prompt} タイトルスライド: メインタイトル「{title}」、サブタイトル「{subtitle}」"

        elif section_type == "slide":
            heading = visual_spec.get("heading", "")
            bullets = visual_spec.get("bullets", [])
            bullets_text = "、".join(bullets)
            return f"{base_prompt} 説明スライド: 見出し「{heading}」、箇条書き: {bullets_text}"

        elif section_type == "code":
            language = visual_spec.get("language", "python")
            code = visual_spec.get("code", "")
            return f"{base_prompt} コードスライド: {language}のコードを表示。シンタックスハイライト付き。コード: {code[:200]}"

        elif section_type == "summary":
            points = visual_spec.get("points", [])
            points_text = "、".join(points)
            return f"{base_prompt} まとめスライド: ポイント: {points_text}"

        else:
            return f"{base_prompt} {json.dumps(visual_spec, ensure_ascii=False)}"

    async def analyze_visual_diff(
        self,
        original_image: bytes,
        edited_image: bytes,
    ) -> dict:
        """2つの画像を比較して差分を分析（Vision）"""
        if not self.is_available:
            return self._mock_visual_diff()

        prompt = """
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

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/models/gemini-2.0-flash-exp:generateContent",
                    params={"key": self.api_key},
                    json={
                        "contents": [{
                            "parts": [
                                {"text": prompt},
                                {
                                    "inlineData": {
                                        "mimeType": "image/png",
                                        "data": base64.b64encode(original_image).decode(),
                                    }
                                },
                                {
                                    "inlineData": {
                                        "mimeType": "image/png",
                                        "data": base64.b64encode(edited_image).decode(),
                                    }
                                },
                            ]
                        }],
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                result = response.json()

                content = result["candidates"][0]["content"]["parts"][0]["text"]
                # JSON部分を抽出
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                return json.loads(content.strip())
        except Exception as e:
            print(f"Visual diff analysis failed: {e}")
            return self._mock_visual_diff()

    def _mock_visual_diff(self) -> dict:
        """モック用の差分分析結果"""
        return {
            "changes": [
                {
                    "aspect": "配色",
                    "before": "デフォルト",
                    "after": "ユーザー編集",
                    "preference": "カスタマイズされた配色を好む傾向",
                }
            ],
            "overall_preference": "ユーザーはカスタマイズされたデザインを好む傾向があります",
        }


# シングルトンインスタンス
gemini_service = GeminiService()
