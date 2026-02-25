"""パイプラインテスト"""

import pytest

from ai_video_gen.services.claude import claude_service
from ai_video_gen.services.gemini import gemini_service
from ai_video_gen.services.elevenlabs import elevenlabs_service
from ai_video_gen.services.ffmpeg import ffmpeg_service
from ai_video_gen.services.slide_renderer import generate_slide_data_url


@pytest.mark.asyncio
async def test_claude_mock_script():
    """Claude脚本生成（モック）"""
    script = await claude_service.generate_script("テスト動画", duration_target=60)
    assert "title" in script
    assert "sections" in script
    assert len(script["sections"]) > 0


@pytest.mark.asyncio
async def test_gemini_mock_image():
    """Gemini画像生成（モック）"""
    # APIキーがない場合はNoneを返す（モックモード）
    image_data = await gemini_service.generate_slide_image(
        {"title": "テスト", "bullets": ["ポイント1"]},
        "slide"
    )
    # モックモードではNone、実際のAPIではbytes
    assert image_data is None or isinstance(image_data, bytes)


@pytest.mark.asyncio
async def test_elevenlabs_mock_audio():
    """ElevenLabs音声生成（モック）"""
    # APIキーがない場合はNoneを返す（モックモード）
    audio_data = await elevenlabs_service.generate_speech("テストナレーション")
    # モックモードではNone、実際のAPIではbytes
    assert audio_data is None or isinstance(audio_data, bytes)


@pytest.mark.asyncio
async def test_ffmpeg_check():
    """FFmpeg存在確認"""
    available = await ffmpeg_service.check_ffmpeg()
    # True or False どちらでもテスト通過
    assert isinstance(available, bool)


def test_ffmpeg_estimate_size():
    """FFmpegファイルサイズ推定"""
    size = ffmpeg_service.estimate_file_size(60)  # 1分
    assert size > 0
    assert size < 100 * 1024 * 1024  # 100MB未満


def test_slide_renderer():
    """スライドレンダラー"""
    visual_spec = {
        "title": "テストスライド",
        "bullet_points": ["ポイント1", "ポイント2"],
        "background_color": "#1a1a2e",
    }
    html = generate_slide_data_url(visual_spec, "slide")
    assert html is not None
    assert "data:text/html" in html


def test_slide_renderer_code():
    """コードスライドレンダラー"""
    visual_spec = {
        "title": "Pythonコード",
        "code": "print('Hello, World!')",
        "language": "python",
    }
    html = generate_slide_data_url(visual_spec, "code")
    assert html is not None
    assert "data:text/html" in html
