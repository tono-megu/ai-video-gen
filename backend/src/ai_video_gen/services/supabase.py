"""Supabaseクライアント"""

from functools import lru_cache

from supabase import Client, create_client

from ai_video_gen.config import settings


@lru_cache
def get_supabase_client() -> Client:
    """Supabaseクライアントを取得（シングルトン）"""
    return create_client(settings.supabase_url, settings.supabase_service_key)


# グローバルクライアント
supabase_client = None


def init_supabase() -> Client | None:
    """Supabaseクライアントを初期化"""
    global supabase_client
    if settings.supabase_url and settings.supabase_service_key:
        supabase_client = get_supabase_client()
    return supabase_client
