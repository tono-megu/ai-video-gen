"""ElevenLabs API サービス（ナレーション音声生成）"""

import httpx

from ai_video_gen.config import settings


class ElevenLabsService:
    """ElevenLabs API クライアント"""

    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"  # デフォルト: Rachel
        self.base_url = "https://api.elevenlabs.io/v1"

    @property
    def is_available(self) -> bool:
        """APIキーが設定されているか"""
        return bool(self.api_key)

    async def generate_speech(
        self,
        text: str,
        voice_id: str | None = None,
        model_id: str = "eleven_multilingual_v2",
    ) -> bytes | None:
        """テキストから音声を生成"""
        if not self.is_available:
            return None  # モックモードでは音声生成スキップ

        voice = voice_id or self.voice_id

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{voice}",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": text,
                        "model_id": model_id,
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.75,
                            "style": 0.0,
                            "use_speaker_boost": True,
                        },
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                return response.content
        except Exception as e:
            print(f"Speech generation failed: {e}")
            return None

    async def get_voices(self) -> list[dict]:
        """利用可能な音声一覧を取得"""
        if not self.is_available:
            return self._get_mock_voices()

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return [
                    {
                        "voice_id": v["voice_id"],
                        "name": v["name"],
                        "category": v.get("category", ""),
                        "labels": v.get("labels", {}),
                    }
                    for v in data.get("voices", [])
                ]
        except Exception as e:
            print(f"Failed to get voices: {e}")
            return self._get_mock_voices()

    def _get_mock_voices(self) -> list[dict]:
        """モック用の音声一覧"""
        return [
            {"voice_id": "mock_male_1", "name": "太郎（男性）", "category": "generated", "labels": {"gender": "male", "language": "ja"}},
            {"voice_id": "mock_female_1", "name": "花子（女性）", "category": "generated", "labels": {"gender": "female", "language": "ja"}},
            {"voice_id": "mock_neutral_1", "name": "アナウンサー", "category": "professional", "labels": {"gender": "neutral", "language": "ja"}},
        ]

    def estimate_duration(self, text: str) -> float:
        """テキストからおおよその音声時間を推定（秒）"""
        # 日本語: 約4文字/秒、英語: 約15文字/秒として概算
        # 混在を想定して約6文字/秒で計算
        chars = len(text)
        return max(1.0, chars / 6.0)


# シングルトンインスタンス
elevenlabs_service = ElevenLabsService()
