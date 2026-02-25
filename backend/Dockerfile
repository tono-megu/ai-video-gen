FROM python:3.12-slim

WORKDIR /app

# システム依存
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 依存インストール
COPY pyproject.toml ./
RUN uv sync --frozen || uv sync

# Playwright（Phase 3で使用）
# RUN uv run playwright install chromium --with-deps

# ソースコード
COPY src/ ./src/

CMD ["uv", "run", "uvicorn", "src.ai_video_gen.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
