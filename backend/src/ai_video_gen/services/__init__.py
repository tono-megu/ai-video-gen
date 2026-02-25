"""サービス層"""

from ai_video_gen.services.supabase import get_supabase_client, supabase_client

__all__ = ["supabase_client", "get_supabase_client"]
