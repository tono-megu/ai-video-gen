# AI Video Generator

テーマ（プロンプト）を入力するだけで、教育・チュートリアル動画を半自動生成するWebアプリです。

## 主な機能

### 動画生成パイプライン
- **脚本生成**: テーマを入力 → AIが構成・ナレーション原稿を自動生成
- **ビジュアル生成**: 各セクションのスライド画像を自動生成
- **ナレーション生成**: テキストから音声を自動生成
- **動画合成**: 画像・音声・BGMを合成して動画出力

### 脚本編集機能
- セクション単位での編集（タイプ、ナレーション、ビジュアル設定）
- ドラッグ&ドロップで並び替え
- セクションの分割（カーソル位置で分割 / ⌘+E）
- セクションの結合（複数選択して ⌘+J）
- Undo/Redo（⌘+Z / ⌘+Shift+Z）

### 好み学習システム
- 修正履歴を自動で蓄積
- AIが好みのパターンを推論
- 次回生成時に自動で反映

## 技術スタック

### Frontend
| 項目 | 技術 |
|------|------|
| フレームワーク | Next.js 15 (App Router) |
| 言語 | TypeScript |
| UI | Tailwind CSS + shadcn/ui |
| 状態管理 | TanStack Query |
| ドラッグ&ドロップ | @dnd-kit |

### Backend
| 項目 | 技術 |
|------|------|
| フレームワーク | FastAPI |
| 言語 | Python 3.12+ |
| 非同期 | asyncio + httpx |
| バリデーション | Pydantic v2 |

### インフラ
| 項目 | 技術 |
|------|------|
| DB | Supabase PostgreSQL |
| ストレージ | Supabase Storage |
| フロントエンド | Vercel |
| バックエンド | Render |

### AI API
| 役割 | サービス |
|------|---------|
| 脚本生成 | Gemini API |
| ナレーション | ElevenLabs API |
| 画像生成 | Gemini + Imagen |

## セットアップ

### 前提条件
- Node.js 20+
- Python 3.12+
- Docker（推奨）

### 環境変数の設定

```bash
# Backend
cp backend/.env.example backend/.env
# 以下を記入:
# - ANTHROPIC_API_KEY
# - GOOGLE_API_KEY
# - ELEVENLABS_API_KEY
# - SUPABASE_URL, SUPABASE_SERVICE_KEY, SUPABASE_ANON_KEY

# Frontend
cp frontend/.env.local.example frontend/.env.local
# 以下を記入:
# - NEXT_PUBLIC_API_URL
# - NEXT_PUBLIC_SUPABASE_URL
# - NEXT_PUBLIC_SUPABASE_ANON_KEY
```

### Docker Compose で起動（推奨）

```bash
docker compose up
```

### 個別に起動

```bash
# Backend
cd backend
uv sync
uv run uvicorn src.ai_video_gen.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

### アクセス
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs (Swagger UI)

## 使い方

1. トップページで「新規プロジェクト」をクリック
2. 動画のテーマを入力して作成
3. 脚本を確認・編集
4. ビジュアルを生成・編集
5. ナレーションを生成
6. 動画を合成してダウンロード

## ディレクトリ構成

```
ai-video-gen/
├── frontend/          # Next.js アプリ
│   ├── src/
│   │   ├── app/       # ページ
│   │   ├── components/# UIコンポーネント
│   │   ├── hooks/     # カスタムフック
│   │   └── lib/       # ユーティリティ
│   └── package.json
│
├── backend/           # FastAPI アプリ
│   ├── src/ai_video_gen/
│   │   ├── api/       # APIエンドポイント
│   │   ├── models/    # Pydanticモデル
│   │   ├── pipeline/  # 生成パイプライン
│   │   ├── services/  # 外部サービス連携
│   │   └── feedback/  # 好み学習
│   └── pyproject.toml
│
├── docker-compose.yml
└── CLAUDE.md          # 詳細設計書
```

## ライセンス

MIT
