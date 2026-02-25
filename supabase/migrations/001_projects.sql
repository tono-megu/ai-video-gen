-- プロジェクトテーブル
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

-- state制約
ALTER TABLE projects ADD CONSTRAINT projects_state_check
  CHECK (state IN ('init', 'script_done', 'visuals_done', 'narration_done', 'composed'));

-- インデックス
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX idx_projects_state ON projects(state);

-- 更新日時自動更新トリガー
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_projects_updated_at
  BEFORE UPDATE ON projects
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
