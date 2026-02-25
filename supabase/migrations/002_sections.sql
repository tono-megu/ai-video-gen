-- セクションテーブル
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

-- type制約
ALTER TABLE sections ADD CONSTRAINT sections_type_check
  CHECK (type IN ('title', 'slide', 'code', 'code_typing', 'diagram', 'summary'));

-- インデックス
CREATE INDEX idx_sections_project_id ON sections(project_id);
CREATE INDEX idx_sections_order ON sections(project_id, section_index);

-- 更新日時自動更新トリガー
CREATE TRIGGER trigger_sections_updated_at
  BEFORE UPDATE ON sections
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
