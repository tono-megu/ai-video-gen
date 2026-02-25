# CLAUDE.md — ai-video-gen プロジェクト指示書

## プロジェクト概要

テーマ（プロンプト）を入力するだけで、教育・チュートリアル動画を半自動生成するWebアプリ。
複数AI APIのパイプラインで脚本→ビジュアル→音声→BGM→動画合成を一気通貫で行う。
各ステップでプレビュー・確認し、パート単位で再生成できるインタラクティブなワークフロー。
スライド画像はtldrawベースのエディタでGUI上で直接編集可能。

### 最重要機能：修正履歴のフィードバックループ

修正を構造化ログとして蓄積→LLMで好みを推論→プロンプトを自動改善。
5〜10本で骨子だけ渡せば好みの動画が全自動で出来上がることを目指す。

### 画像修正の学習（2段階）

1. **プロンプト修正ベース**：言葉で指示→再生成→差分を学習
2. **ビジュアルDiff**：tldrawで手動修正→Gemini Visionで差分言語化→好み蓄積

---

## チーム構成・運用

- チーム規模: 7人以上（エンジニア＋非エンジニア混在）
- 権限: 全員同じ（管理者/編集者の区別なし）
- 非エンジニアの作業: テーマ入力、脚本レビュー、スライド編集、動画チェック、全てGUI上で完結
- 予算: インフラ月額 ¥0〜¥5,000（AI API費用は別）

---

## アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         Frontend (Next.js 15 + tldraw)       │
│              Vercel にデプロイ                │
│              ↕ REST + WebSocket              │
├─────────────────────────────────────────────┤
│            Backend (FastAPI)                  │
│              Render にデプロイ                │
│              ↕ Supabase Client               │
├─────────────────────────────────────────────┤
│              Supabase                        │
│    PostgreSQL + Storage + Realtime           │
└─────────────────────────────────────────────┘
```

---

## 技術スタック

### Frontend

| 項目 | 技術 |
|------|------|
| フレームワーク | Next.js 15 (App Router) |
| 言語 | TypeScript |
| UI | Tailwind CSS + shadcn/ui |
| 画像エディタ | tldraw |
| API通信 | TanStack Query |
| リアルタイム | WebSocket (進捗通知) |

### Backend

| 項目 | 技術 |
|------|------|
| フレームワーク | FastAPI |
| 言語 | Python 3.12+ |
| 非同期 | asyncio + httpx |
| バリデーション | Pydantic v2 |
| 動画合成 | FFmpeg (typed-ffmpeg or subprocess) |
| コードアニメーション | Manim Community Edition |
| スライドレンダリング | Playwright (HTML→スクリーンショット) |
| 画像処理 | Pillow + Pygments |

### DB・ストレージ

| 項目 | 技術 |
|------|------|
| DB | Supabase PostgreSQL |
| ファイルストレージ | Supabase Storage |
| リアルタイム | Supabase Realtime |

### AI API

| 役割 | サービス |
|------|---------|
| 脚本生成 | Claude Opus 4.6 API |
| ナレーション | ElevenLabs API |
| 画像生成 | Gemini 3.1 Pro + Imagen 4 |
| 画像差分分析 | Gemini 3.1 Pro Vision |
| BGM | Suno API (Phase 3) |

---

## デプロイ構成

### 本番環境

| サービス | プラン | 月額 |
|---------|--------|------|
| Vercel | Free (Hobby) | ¥0 |
| Render | Free or Starter ($7) | ¥0〜¥1,000 |
| Supabase | Free | ¥0 |
| **合計** | | **¥0〜¥1,000** |

### Vercel (Frontend)

```json
// vercel.json
{
  "framework": "nextjs",
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/.next",
  "env": {
    "NEXT_PUBLIC_API_URL": "@api-url",
    "NEXT_PUBLIC_SUPABASE_URL": "@supabase-url",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "@supabase-anon-key"
  }
}
```

### Render (Backend)

```yaml
# render.yaml
services:
  - type: web
    name: ai-video-gen-api
    runtime: python
    buildCommand: |
      cd backend
      pip install uv
      uv sync
      playwright install chromium --with-deps
    startCommand: cd backend && uvicorn src.ai_video_gen.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: GOOGLE_API_KEY
        sync: false
      - key: ELEVENLABS_API_KEY
        sync: false
      - key: ELEVENLABS_VOICE_ID
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
      - key: SUPABASE_ANON_KEY
        sync: false
    healthCheckPath: /health
```

### Docker Compose (ローカル開発)

```yaml
# docker-compose.yml
version: "3.8"
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
      - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
    volumes:
      - ./frontend/src:/app/src
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - ./backend/src:/app/src
```

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# システム依存
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 依存インストール
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Playwright
RUN uv run playwright install chromium --with-deps

# ソースコード
COPY src/ ./src/

CMD ["uv", "run", "uvicorn", "src.ai_video_gen.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

CMD ["npm", "run", "dev"]
```

---

## チーム開発運用

### Git運用

```
リポジトリ: GitHub（無料）
ブランチ戦略: trunk-based development

main          ← 本番（Vercel/Render自動デプロイ）
  └── feature/xxx  ← 機能開発ブランチ
  └── fix/xxx      ← バグ修正ブランチ

ルール:
- mainへの直プッシュ禁止
- Pull Request必須（レビュー1人以上）
- CIが通らないとマージ不可
```

### CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: |
          cd backend
          uv sync
          uv run pytest

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: |
          cd frontend
          npm ci
          npm run lint
          npm run type-check

  # mainにマージ → Vercel/Renderが自動デプロイ
```

### タスク管理

```
GitHub Projects（カンバンボード）を使用

カラム:
- Backlog     … やること一覧
- In Progress … 作業中
- Review      … PRレビュー待ち
- Done        … 完了

ラベル:
- sprint/1〜7      … スプリント番号
- frontend         … フロントエンド
- backend          … バックエンド
- feedback-loop    … フィードバック機能
- bug              … バグ
- enhancement      … 改善
```

### チームメンバーの環境セットアップ手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/<org>/ai-video-gen.git
cd ai-video-gen

# 2. 環境変数をセット
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
# → APIキー等を記入

# 3. Docker Composeで起動（推奨）
docker compose up

# または個別起動:
# Backend
cd backend && uv sync && uv run uvicorn src.ai_video_gen.main:app --reload
# Frontend
cd frontend && npm install && npm run dev

# 4. ブラウザでアクセス
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs (Swagger UI)
```

### 非エンジニア向けガイド

```
■ 使い方（ブラウザのみ、インストール不要）

1. https://<your-app>.vercel.app にアクセス
2. 「新規プロジェクト」→ テーマを入力
3. 脚本が生成される → 確認して修正
4. スライドが生成される → tldrawエディタで直接編集可能
5. ナレーションが生成される → 再生して確認
6. 「動画合成」→ 完成動画をダウンロード

■ 修正のコツ
- 気に入らないスライドは「再生成」ボタンで何度でもやり直せます
- tldrawエディタで色、テキスト、図形を自由に変更できます
- 修正するほどAIが好みを学習し、次回から自動で反映されます
```

---

## ディレクトリ構成

```
ai-video-gen/
├── CLAUDE.md
├── README.md
├── docker-compose.yml
├── render.yaml
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   ├── .env.local.example
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx                     # ダッシュボード
│   │   │   ├── projects/
│   │   │   │   ├── new/page.tsx             # 新規作成
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx             # プロジェクト詳細
│   │   │   │       ├── script/page.tsx      # 脚本編集
│   │   │   │       ├── visuals/page.tsx     # スライド + tldraw
│   │   │   │       ├── narration/page.tsx   # ナレーション
│   │   │   │       └── compose/page.tsx     # 動画合成
│   │   │   └── preferences/page.tsx         # 好み管理
│   │   ├── components/
│   │   │   ├── ui/                          # shadcn/ui
│   │   │   ├── layout/                      # Header, Sidebar
│   │   │   ├── project/                     # ProjectCard, PipelineStatus
│   │   │   ├── script/                      # ScriptPreview, ScriptEditor
│   │   │   ├── visuals/
│   │   │   │   ├── SlideGallery.tsx
│   │   │   │   ├── SlideEditor.tsx          # tldraw統合
│   │   │   │   └── VisualDiffView.tsx
│   │   │   ├── narration/                   # AudioPlayer, WaveformView
│   │   │   └── feedback/                    # PreferenceList, ConfidenceBadge
│   │   ├── hooks/
│   │   │   ├── useProject.ts
│   │   │   ├── usePipeline.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── usePreferences.ts
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── supabase.ts
│   │   │   └── tldraw-config.ts
│   │   └── types/index.ts
│   └── public/
│
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── .env.example
│   ├── src/ai_video_gen/
│   │   ├── main.py                          # FastAPIアプリ
│   │   ├── config.py                        # pydantic-settings
│   │   ├── api/
│   │   │   ├── router.py                    # ルーター集約
│   │   │   ├── projects.py                  # /api/projects
│   │   │   ├── pipeline.py                  # /api/pipeline
│   │   │   ├── visuals.py                   # /api/visuals（差分含む）
│   │   │   ├── preferences.py               # /api/preferences
│   │   │   └── ws.py                        # WebSocket進捗通知
│   │   ├── models/
│   │   │   ├── schema.py                    # Script, Section, Project
│   │   │   └── corrections.py               # CorrectionEvent, Preference
│   │   ├── pipeline/
│   │   │   ├── orchestrator.py              # パイプライン全体制御
│   │   │   ├── script.py                    # Claude脚本生成
│   │   │   ├── visuals.py                   # Gemini画像 + Playwright
│   │   │   ├── narration.py                 # ElevenLabs
│   │   │   └── compose.py                   # FFmpeg合成
│   │   ├── services/
│   │   │   ├── claude.py
│   │   │   ├── gemini.py                    # 画像生成 + Vision
│   │   │   ├── elevenlabs.py
│   │   │   ├── ffmpeg.py
│   │   │   ├── manim_render.py
│   │   │   └── supabase.py                  # DB + Storage
│   │   ├── feedback/
│   │   │   ├── correction_store.py          # 修正ログ管理
│   │   │   ├── visual_diff.py               # Gemini Vision差分分析
│   │   │   ├── preference_engine.py         # CIPHER式好み推論
│   │   │   └── prompt_evolver.py            # プロンプト進化
│   │   ├── templates/slide.html             # Jinja2スライド
│   │   └── utils/
│   │       ├── hashing.py                   # DAG依存関係
│   │       └── storage.py                   # Supabase Storage操作
│   └── tests/
│       ├── test_schema.py
│       ├── test_pipeline.py
│       ├── test_feedback.py
│       └── test_api.py
│
└── supabase/
    └── migrations/
        ├── 001_projects.sql
        ├── 002_sections.sql
        ├── 003_corrections.sql
        └── 004_preferences.sql
```

---

## DBスキーマ

### projects
```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  theme TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'init',
  -- state: init / script_done / visuals_done / narration_done / composed
  script JSONB,
  duration_target FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### sections
```sql
CREATE TABLE sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  section_index INT NOT NULL,
  type TEXT NOT NULL,
  -- type: title / slide / code / code_typing / diagram / summary
  duration FLOAT,
  narration TEXT,
  visual_spec JSONB,
  slide_image_path TEXT,
  narration_audio_path TEXT,
  animation_video_path TEXT,
  generation_prompt TEXT,
  content_hash TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### corrections（追記専用イベントソーシング）
```sql
CREATE TABLE corrections (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id),
  section_id UUID REFERENCES sections(id),
  stage TEXT NOT NULL,              -- script / narration / image / animation / composition
  category TEXT NOT NULL,           -- style / structural / content / technical
  field_path TEXT NOT NULL,
  prior_value TEXT,
  new_value TEXT,
  original_prompt TEXT,
  user_feedback TEXT,
  original_image_path TEXT,
  edited_image_path TEXT,
  visual_diff_description TEXT,     -- Gemini Visionによる差分記述
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### preferences
```sql
CREATE TABLE preferences (
  preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  description TEXT NOT NULL,
  category TEXT NOT NULL,           -- style / structural / content / technical
  scope TEXT NOT NULL DEFAULT 'global',
  -- scope: global / project / section_type / specific
  section_type TEXT,
  project_id UUID REFERENCES projects(id),
  confidence FLOAT DEFAULT 0.5,
  source_corrections UUID[],
  is_active BOOLEAN DEFAULT TRUE,
  prompt_version INT DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Supabase Storage バケット
```
- project-slides/       # スライド画像 (PNG)
- project-narrations/   # ナレーション音声 (MP3)
- project-animations/   # コードアニメーション (MP4)
- project-outputs/      # 最終動画 (MP4)
- edited-images/        # tldrawエクスポート画像 (PNG)
```

---

## APIエンドポイント

### Projects
```
POST   /api/projects
GET    /api/projects
GET    /api/projects/{id}
DELETE /api/projects/{id}
```

### Pipeline
```
POST   /api/projects/{id}/generate-script
PUT    /api/projects/{id}/script
POST   /api/projects/{id}/generate-visuals
POST   /api/projects/{id}/generate-narration
POST   /api/projects/{id}/compose
POST   /api/projects/{id}/sections/{sid}/regenerate
```

### Visuals（画像編集・差分学習）
```
GET    /api/projects/{id}/sections/{sid}/slide
POST   /api/projects/{id}/sections/{sid}/slide/edit
POST   /api/projects/{id}/sections/{sid}/slide/diff
POST   /api/projects/{id}/sections/{sid}/slide/regenerate
```

### Preferences
```
GET    /api/preferences
GET    /api/preferences/profile
PUT    /api/preferences/{id}
DELETE /api/preferences/{id}
POST   /api/preferences/evolve
```

### WebSocket
```
WS     /ws/projects/{id}/progress
```

### Health Check
```
GET    /health
```

---

## tldraw統合

### エディタ組み込み
```tsx
import { Tldraw } from 'tldraw'
import 'tldraw/tldraw.css'

export function SlideEditor({ slideImageUrl, onSave }) {
  return (
    <Tldraw
      onMount={(editor) => {
        editor.createAssets([{
          id: 'slide-bg', type: 'image',
          props: { src: slideImageUrl, w: 1920, h: 1080 }
        }])
      }}
    />
  )
}
```

### ビジュアルDiffフロー
```
1. tldrawで編集 → editor.exportToBlob() でPNG取得
2. Supabase Storageにアップロード
3. POST /slide/diff → Gemini Visionが元画像と比較分析
4. 差分記述をcorrectionsテーブルに保存
5. preference_engineが好みルールを推論・更新
```

### Geminiビジュアル差分プロンプト
```python
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
```

---

## フィードバックループ

### 修正ログの記録タイミング

| アクション | 記録方法 |
|-----------|---------|
| 脚本を手動編集 | テキストdiffを記録 |
| セクション再生成（プロンプト修正） | 元/修正プロンプトの差分 |
| tldrawで画像を編集 | Gemini Visionで差分分析→記録 |
| ナレーション再生成 | パラメータ変更を記録 |

### 確信度スコア
- ≥ 0.85 → サイレント自動適用
- 0.50〜0.85 → ユーザーに提案
- < 0.50 → 記録のみ

### 好みヒエラルキー（4段階）
1. グローバル（全動画共通）
2. プロジェクト（シリーズ単位）
3. セクションタイプ（code / slide / diagram）
4. 個別オーバーライド

### DAG依存関係
```python
DEPENDENCY_MAP = {
    "script": ["narration", "images", "animations", "composition"],
    "narration": ["composition"],
    "images": ["composition"],
    "animations": ["composition"],
}
```

---

## 開発スプリント

| Sprint | 内容 | 見積 |
|--------|------|------|
| 1 | 基盤（FastAPI + Next.js + Supabase + Docker + CRUD） | 2〜3日 |
| 2 | 脚本生成（Claude + WebSocket + 編集UI） | 2〜3日 |
| 3 | ビジュアル + tldraw（Gemini + エディタ + Diff） | 3〜4日 |
| 4 | ナレーション（ElevenLabs + プレーヤーUI） | 1〜2日 |
| 5 | 動画合成（FFmpeg + プレビュー + DL） | 2〜3日 |
| 6 | フィードバックループ（CIPHER + 好みUI） | 3〜4日 |
| 7 | 統合テスト + CI/CD + デプロイ + サンプル動画 | 2〜3日 |
| **合計** | | **16〜22日** |

---

## 環境変数

### Backend (.env / .env.example)
```
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...
```

### Frontend (.env.local / .env.local.example)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

---

## コーディング規約

### Backend (Python)
- 型ヒント必須（`X | Y` 構文）
- async/await ベース
- pathlib.Path
- pydantic-settings
- pytest + pytest-asyncio
- docstring 日本語OK

### Frontend (TypeScript)
- strict mode
- function component + hooks
- Tailwind CSS のみ（CSS Modules不使用）
- TanStack Query
- react-hook-form + zod
- コメント日本語OK

### Git
- コミットメッセージ: 日本語OK
- PR テンプレート: 変更内容 + スクリーンショット
- mainブランチへの直プッシュ禁止

---

## 出力フォーマット

| プラットフォーム | 解像度 | アスペクト比 | Phase |
|----------------|--------|------------|-------|
| YouTube | 1920×1080 | 16:9 | MVP |
| YouTube Shorts | 1080×1920 | 9:16 | Phase 3 |
| TikTok / Reels | 1080×1920 | 9:16 | Phase 3 |
| Instagram | 1080×1080 | 1:1 | Phase 3 |
