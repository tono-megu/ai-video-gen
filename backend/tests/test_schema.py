"""スキーマのテスト"""

import pytest
from pydantic import ValidationError

from ai_video_gen.models import ProjectCreate, ProjectState, SectionType


def test_project_create_valid():
    """正常なプロジェクト作成"""
    project = ProjectCreate(theme="Pythonの基礎", duration_target=300)
    assert project.theme == "Pythonの基礎"
    assert project.duration_target == 300


def test_project_create_minimal():
    """最小限のプロジェクト作成"""
    project = ProjectCreate(theme="テスト")
    assert project.theme == "テスト"
    assert project.duration_target is None


def test_project_create_empty_theme():
    """空のテーマはエラー"""
    with pytest.raises(ValidationError):
        ProjectCreate(theme="")


def test_project_create_invalid_duration():
    """不正な動画時間はエラー"""
    with pytest.raises(ValidationError):
        ProjectCreate(theme="テスト", duration_target=10)  # 30秒未満


def test_project_state_values():
    """プロジェクト状態の値"""
    assert ProjectState.INIT.value == "init"
    assert ProjectState.SCRIPT_DONE.value == "script_done"
    assert ProjectState.COMPOSED.value == "composed"


def test_section_type_values():
    """セクション種類の値"""
    assert SectionType.TITLE.value == "title"
    assert SectionType.CODE.value == "code"
    assert SectionType.SLIDE.value == "slide"
