/**
 * プロジェクト関連の型定義
 */

export type ProjectState =
  | "init"
  | "script_done"
  | "visuals_done"
  | "narration_done"
  | "composed";

export type SectionType =
  | "title"
  | "slide"
  | "code"
  | "code_typing"
  | "diagram"
  | "summary";

export interface Section {
  id: string;
  project_id: string;
  section_index: number;
  type: SectionType;
  duration?: number;
  narration?: string;
  visual_spec?: Record<string, unknown>;
  slide_image_path?: string;
  narration_audio_path?: string;
  animation_video_path?: string;
  generation_prompt?: string;
  content_hash?: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  theme: string;
  state: ProjectState;
  script?: Record<string, unknown>;
  duration_target?: number;
  created_at: string;
  updated_at: string;
  sections: Section[];
}

export interface ProjectCreate {
  theme: string;
  duration_target?: number;
}

export interface ProjectUpdate {
  theme?: string;
  state?: ProjectState;
  script?: Record<string, unknown>;
  duration_target?: number;
}
