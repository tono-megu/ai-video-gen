"""ElevenLabs API サービス（ナレーション音声生成）"""

import re

import httpx

from ai_video_gen.config import settings

# TTS用カタカナ変換辞書（大文字小文字区別なし）
TTS_CONVERSION_DICT: dict[str, str] = {
    # プログラミング言語
    "Python": "パイソン",
    "JavaScript": "ジャバスクリプト",
    "TypeScript": "タイプスクリプト",
    "Java": "ジャバ",
    "Ruby": "ルビー",
    "PHP": "ピーエイチピー",
    "Go": "ゴー",
    "Rust": "ラスト",
    "Swift": "スウィフト",
    "Kotlin": "コトリン",

    # Web技術
    "HTML": "エイチティーエムエル",
    "CSS": "シーエスエス",
    "API": "エーピーアイ",
    "REST": "レスト",
    "JSON": "ジェイソン",
    "XML": "エックスエムエル",
    "HTTP": "エイチティーティーピー",
    "HTTPS": "エイチティーティーピーエス",
    "URL": "ユーアールエル",
    "URI": "ユーアールアイ",
    "DOM": "ドム",
    "Ajax": "エイジャックス",
    "WebSocket": "ウェブソケット",

    # フレームワーク・ライブラリ
    "React": "リアクト",
    "Vue": "ビュー",
    "Angular": "アンギュラー",
    "Next.js": "ネクストジェイエス",
    "Node.js": "ノードジェイエス",
    "Express": "エクスプレス",
    "Django": "ジャンゴ",
    "Flask": "フラスク",
    "FastAPI": "ファストエーピーアイ",
    "Rails": "レイルズ",
    "Laravel": "ララベル",

    # データベース
    "SQL": "エスキューエル",
    "MySQL": "マイエスキューエル",
    "PostgreSQL": "ポストグレスキューエル",
    "MongoDB": "モンゴデービー",
    "Redis": "レディス",
    "SQLite": "エスキューライト",

    # クラウド・インフラ
    "AWS": "エーダブリューエス",
    "GCP": "ジーシーピー",
    "Azure": "アジュール",
    "Docker": "ドッカー",
    "Kubernetes": "クバネティス",
    "Linux": "リナックス",
    "Ubuntu": "ウブントゥ",
    "Git": "ギット",
    "GitHub": "ギットハブ",

    # 一般的な略語
    "AI": "エーアイ",
    "ML": "エムエル",
    "UI": "ユーアイ",
    "UX": "ユーエックス",
    "OS": "オーエス",
    "PC": "ピーシー",
    "CPU": "シーピーユー",
    "GPU": "ジーピーユー",
    "RAM": "ラム",
    "SSD": "エスエスディー",
    "HDD": "エイチディーディー",
    "USB": "ユーエスビー",
    "SDK": "エスディーケー",
    "IDE": "アイディーイー",
    "CLI": "シーエルアイ",
    "GUI": "ジーユーアイ",
    "npm": "エヌピーエム",
    "pip": "ピップ",

    # CSSプロパティ等
    "font-size": "フォントサイズ",
    "font-family": "フォントファミリー",
    "background": "バックグラウンド",
    "margin": "マージン",
    "padding": "パディング",
    "border": "ボーダー",
    "display": "ディスプレイ",
    "flex": "フレックス",
    "grid": "グリッド",
    "position": "ポジション",

    # その他
    "null": "ヌル",
    "undefined": "アンディファインド",
    "true": "トゥルー",
    "false": "フォルス",
    "function": "ファンクション",
    "class": "クラス",
    "import": "インポート",
    "export": "エクスポート",
    "async": "エイシンク",
    "await": "アウェイト",
    "Promise": "プロミス",
    "callback": "コールバック",
}


def convert_for_tts(text: str) -> str:
    """テキストをTTS用にカタカナ変換"""
    result = text

    # 辞書の単語を長い順にソート（部分一致を防ぐ）
    sorted_words = sorted(TTS_CONVERSION_DICT.keys(), key=len, reverse=True)

    for word in sorted_words:
        # 大文字小文字を区別しない置換
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        result = pattern.sub(TTS_CONVERSION_DICT[word], result)

    return result


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
        convert_to_katakana: bool = True,
    ) -> bytes | None:
        """テキストから音声を生成

        Args:
            text: 読み上げるテキスト
            voice_id: 使用する音声ID
            model_id: 使用するモデルID
            convert_to_katakana: 英語/略語をカタカナに変換するか
        """
        if not self.is_available:
            return None  # モックモードでは音声生成スキップ

        voice = voice_id or self.voice_id

        # TTS用にカタカナ変換
        tts_text = convert_for_tts(text) if convert_to_katakana else text

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{voice}",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": tts_text,
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
