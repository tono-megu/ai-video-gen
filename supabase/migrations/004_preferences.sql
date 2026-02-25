-- 好みテーブル
CREATE TABLE preferences (
  preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  -- category: style / structural / content / technical
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

-- category制約
ALTER TABLE preferences ADD CONSTRAINT preferences_category_check
  CHECK (category IN ('style', 'structural', 'content', 'technical'));

-- scope制約
ALTER TABLE preferences ADD CONSTRAINT preferences_scope_check
  CHECK (scope IN ('global', 'project', 'section_type', 'specific'));

-- section_type制約
ALTER TABLE preferences ADD CONSTRAINT preferences_section_type_check
  CHECK (section_type IS NULL OR section_type IN ('title', 'slide', 'code', 'code_typing', 'diagram', 'summary'));

-- インデックス
CREATE INDEX idx_preferences_category ON preferences(category);
CREATE INDEX idx_preferences_scope ON preferences(scope);
CREATE INDEX idx_preferences_active ON preferences(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_preferences_project_id ON preferences(project_id);

-- 更新日時自動更新トリガー
CREATE TRIGGER trigger_preferences_updated_at
  BEFORE UPDATE ON preferences
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
