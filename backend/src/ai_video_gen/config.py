"""アプリケーション設定"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境変数から読み込む設定"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_anon_key: str = ""

    # AI APIs (Sprint 2以降で使用)
    anthropic_api_key: str = ""
    google_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # アプリケーション設定
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
