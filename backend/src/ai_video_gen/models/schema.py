"""プロジェクトとセクションのスキーマ定義"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectState(str, Enum):
    """プロジェクトの状態"""

    INIT = "init"
    SCRIPT_DONE = "script_done"
    VISUALS_DONE = "visuals_done"
    NARRATION_DONE = "narration_done"
    COMPOSED = "composed"


class SectionType(str, Enum):
    """セクションの種類"""

    TITLE = "title"
    SLIDE = "slide"
    CODE = "code"
    CODE_TYPING = "code_typing"
    DIAGRAM = "diagram"
    SUMMARY = "summary"


class SectionCreate(BaseModel):
    """セクション作成用スキーマ"""

    section_index: int
    type: SectionType
    duration: float | None = None
    narration: str | None = None
    visual_spec: dict | None = None


class Section(BaseModel):
    """セクションスキーマ"""

    id: UUID
    project_id: UUID
    section_index: int
    type: SectionType
    duration: float | None = None
    narration: str | None = None
    visual_spec: dict | None = None
    slide_image_path: str | None = None
    narration_audio_path: str | None = None
    animation_video_path: str | None = None
    generation_prompt: str | None = None
    content_hash: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    """プロジェクト作成用スキーマ"""

    theme: str = Field(..., min_length=1, max_length=500, description="動画のテーマ")
    duration_target: float | None = Field(None, ge=30, le=3600, description="目標動画時間（秒）")


class ProjectUpdate(BaseModel):
    """プロジェクト更新用スキーマ"""

    theme: str | None = Field(None, min_length=1, max_length=500)
    state: ProjectState | None = None
    script: dict | None = None
    duration_target: float | None = Field(None, ge=30, le=3600)


class Project(BaseModel):
    """プロジェクトスキーマ"""

    id: UUID
    theme: str
    state: ProjectState
    script: dict | None = None
    duration_target: float | None = None
    created_at: datetime
    updated_at: datetime
    sections: list[Section] = []
