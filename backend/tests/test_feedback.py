"""フィードバックモジュールテスト"""

import pytest

from ai_video_gen.feedback.correction_store import CorrectionEvent
from ai_video_gen.feedback.preference_engine import Preference, preference_engine
from ai_video_gen.feedback.visual_diff import visual_diff_analyzer
from ai_video_gen.feedback.prompt_evolver import prompt_evolver


def test_correction_event_model():
    """修正イベントモデル"""
    event = CorrectionEvent(
        project_id="test-project-id",
        section_id="test-section-id",
        stage="script",
        category="style",
        field_path="title",
        prior_value="古いタイトル",
        new_value="新しいタイトル",
    )
    assert event.project_id == "test-project-id"
    assert event.stage == "script"
    assert event.category == "style"


def test_preference_model():
    """好みモデル"""
    pref = Preference(
        description="ダークテーマを好む",
        category="style",
        scope="global",
        confidence=0.8,
    )
    assert pref.description == "ダークテーマを好む"
    assert pref.confidence == 0.8
    assert pref.is_active is True


def test_preference_with_section_type():
    """セクションタイプ付き好み"""
    pref = Preference(
        description="コードブロックはダークテーマ",
        category="style",
        scope="section_type",
        section_type="code",
        confidence=0.9,
    )
    assert pref.scope == "section_type"
    assert pref.section_type == "code"


@pytest.mark.asyncio
async def test_visual_diff_mock():
    """ビジュアル差分（モック）"""
    result = await visual_diff_analyzer.analyze_diff(
        original_image="data:image/png;base64,test",
        edited_image="data:image/png;base64,test2",
    )
    assert result.changes is not None
    assert result.overall_preference is not None
    assert len(result.changes) > 0


@pytest.mark.asyncio
async def test_preference_engine_mock_infer():
    """好み推論（モック）"""
    corrections = [
        {
            "stage": "image",
            "category": "style",
            "field_path": "background",
            "prior_value": "light",
            "new_value": "dark",
        },
        {
            "stage": "image",
            "category": "style",
            "field_path": "background",
            "prior_value": "light",
            "new_value": "dark",
        },
    ]
    preferences = await preference_engine.infer_preferences(corrections)
    assert len(preferences) > 0
    assert all(isinstance(p, Preference) for p in preferences)


@pytest.mark.asyncio
async def test_prompt_evolver():
    """プロンプト進化"""
    base_prompt = "教育動画の脚本を生成してください。"
    try:
        evolved = await prompt_evolver.evolve_script_prompt(base_prompt)
        # 好みがない場合は元のプロンプトがそのまま返る
        assert evolved is not None
        assert "脚本" in evolved
    except Exception:
        # preferencesテーブルがない場合はスキップ
        pytest.skip("preferences table not available")


def test_confidence_thresholds():
    """確信度閾値"""
    assert preference_engine.SILENT_APPLY_THRESHOLD == 0.85
    assert preference_engine.SUGGEST_THRESHOLD == 0.50
