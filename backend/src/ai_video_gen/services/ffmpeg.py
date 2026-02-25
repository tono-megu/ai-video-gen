"""FFmpeg サービス（動画合成）"""

import asyncio
import base64
import tempfile
from pathlib import Path
from uuid import UUID

from ai_video_gen.services.supabase import get_supabase_client


class FFmpegService:
    """FFmpeg 動画合成サービス"""

    def __init__(self):
        self.output_width = 1920
        self.output_height = 1080
        self.fps = 30

    async def check_ffmpeg(self) -> bool:
        """FFmpegがインストールされているか確認"""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False

    async def compose_video(
        self,
        project_id: UUID,
        sections: list[dict],
    ) -> str:
        """セクションから動画を合成"""
        client = get_supabase_client()

        # FFmpegが利用可能か確認
        if not await self.check_ffmpeg():
            raise RuntimeError("FFmpeg is not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            segment_files = []

            for idx, section in enumerate(sections):
                duration = section.get("duration") or 5.0
                slide_path = section.get("slide_image_path")
                audio_path = section.get("narration_audio_path")

                # スライドをPNGとして保存
                slide_file = tmppath / f"slide_{idx:03d}.png"
                if slide_path and slide_path.startswith("data:"):
                    # data URLからHTMLを抽出してスクリーンショット
                    # 簡易実装: 単色画像を生成
                    await self._create_placeholder_image(slide_file, section.get("type", "slide"))
                else:
                    await self._create_placeholder_image(slide_file, section.get("type", "slide"))

                # 音声ファイルを保存
                audio_file = None
                if audio_path and audio_path.startswith("data:audio"):
                    audio_file = tmppath / f"audio_{idx:03d}.mp3"
                    audio_data = audio_path.split(",")[1]
                    audio_file.write_bytes(base64.b64decode(audio_data))

                # セグメント動画を生成
                segment_file = tmppath / f"segment_{idx:03d}.mp4"
                await self._create_segment(
                    slide_file,
                    audio_file,
                    segment_file,
                    duration,
                )
                segment_files.append(segment_file)

            # セグメントを結合
            output_file = tmppath / "output.mp4"
            await self._concat_segments(segment_files, output_file)

            # 出力ファイルをbase64エンコード
            video_bytes = output_file.read_bytes()
            video_base64 = base64.b64encode(video_bytes).decode("utf-8")
            video_data_url = f"data:video/mp4;base64,{video_base64}"

            return video_data_url

    async def _create_placeholder_image(self, output_path: Path, section_type: str) -> None:
        """プレースホルダー画像を生成"""
        # 背景色を設定
        colors = {
            "title": "#1a1a2e",
            "slide": "#16213e",
            "code": "#0d1117",
            "summary": "#1a1a2e",
        }
        color = colors.get(section_type, "#1a1a2e")

        # FFmpegで単色画像を生成
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c={color}:s={self.output_width}x{self.output_height}:d=1",
            "-frames:v", "1",
            str(output_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

    async def _create_segment(
        self,
        image_path: Path,
        audio_path: Path | None,
        output_path: Path,
        duration: float,
    ) -> None:
        """セグメント動画を生成"""
        if audio_path and audio_path.exists():
            # 画像 + 音声
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-i", str(audio_path),
                "-c:v", "libx264",
                "-tune", "stillimage",
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                str(output_path),
            ]
        else:
            # 画像のみ（指定時間）
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(image_path),
                "-c:v", "libx264",
                "-t", str(duration),
                "-pix_fmt", "yuv420p",
                "-r", str(self.fps),
                str(output_path),
            ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg segment creation failed: {stderr.decode()}")

    async def _concat_segments(
        self,
        segment_files: list[Path],
        output_path: Path,
    ) -> None:
        """セグメントを結合"""
        if not segment_files:
            raise ValueError("No segments to concat")

        if len(segment_files) == 1:
            # 1つだけならコピー
            output_path.write_bytes(segment_files[0].read_bytes())
            return

        # concat用のリストファイルを作成
        list_file = output_path.parent / "concat_list.txt"
        with open(list_file, "w") as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path),
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg concat failed: {stderr.decode()}")

    def estimate_file_size(self, total_duration: float) -> int:
        """動画ファイルサイズを推定（バイト）"""
        # 概算: 1080p @ 30fps で約 5MB/分
        return int(total_duration / 60 * 5 * 1024 * 1024)


# シングルトンインスタンス
ffmpeg_service = FFmpegService()
