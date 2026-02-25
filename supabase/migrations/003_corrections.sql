-- 修正ログテーブル（追記専用イベントソーシング）
CREATE TABLE corrections (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id),
  section_id UUID REFERENCES sections(id),
  stage TEXT NOT NULL,
  -- stage: script / narration / image / animation / composition
  category TEXT NOT NULL,
  -- category: style / structural / content / technical
  field_path TEXT NOT NULL,
  prior_value TEXT,
  new_value TEXT,
  original_prompt TEXT,
  user_feedback TEXT,
  original_image_path TEXT,
  edited_image_path TEXT,
  visual_diff_description TEXT,
  -- Gemini Visionによる差分記述
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- stage制約
ALTER TABLE corrections ADD CONSTRAINT corrections_stage_check
  CHECK (stage IN ('script', 'narration', 'image', 'animation', 'composition'));

-- category制約
ALTER TABLE corrections ADD CONSTRAINT corrections_category_check
  CHECK (category IN ('style', 'structural', 'content', 'technical'));

-- インデックス
CREATE INDEX idx_corrections_project_id ON corrections(project_id);
CREATE INDEX idx_corrections_section_id ON corrections(section_id);
CREATE INDEX idx_corrections_created_at ON corrections(created_at DESC);
