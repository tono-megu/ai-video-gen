"""FastAPIアプリケーションエントリーポイント"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_video_gen.api.router import api_router
from ai_video_gen.config import settings

app = FastAPI(
    title="AI Video Generator API",
    description="教育・チュートリアル動画を半自動生成するAPI",
    version="0.1.0",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# APIルーター登録
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "version": "0.1.0"}
