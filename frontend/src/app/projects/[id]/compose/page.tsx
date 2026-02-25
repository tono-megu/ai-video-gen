"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useProject } from "@/hooks/useProject";
import { useComposeVideo, useComposeStatus } from "@/hooks/usePipeline";
import { Button } from "@/components/ui/button";

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ComposePage() {
  const params = useParams();
  const projectId = params.id as string;
  const { data: project, isLoading, error, refetch } = useProject(projectId);
  const composeStatus = useComposeStatus(projectId);
  const composeVideo = useComposeVideo();
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  const handleCompose = async () => {
    try {
      const result = await composeVideo.mutateAsync(projectId);
      if (result.video_url) {
        setVideoUrl(result.video_url);
      }
      refetch();
      composeStatus.refetch();
    } catch (error) {
      console.error("Failed to compose video:", error);
    }
  };

  const handleDownload = () => {
    if (!videoUrl) return;

    const link = document.createElement("a");
    link.href = videoUrl;
    link.download = `${project?.theme || "video"}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (isLoading) {
    return (
      <main className="container mx-auto px-4 py-8">
        <p className="text-muted-foreground">読み込み中...</p>
      </main>
    );
  }

  if (error || !project) {
    return (
      <main className="container mx-auto px-4 py-8">
        <p className="text-destructive">プロジェクトの読み込みに失敗しました</p>
        <Link href="/" className="text-primary hover:underline">
          ダッシュボードに戻る
        </Link>
      </main>
    );
  }

  const status = composeStatus.data;
  const canCompose = status?.can_compose || project.state === "narration_done";
  const isComposed = project.state === "composed";

  return (
    <main className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <Link
          href={`/projects/${projectId}/narration`}
          className="text-muted-foreground hover:text-foreground"
        >
          ← ナレーションに戻る
        </Link>
      </div>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">動画合成</h1>
          <p className="text-muted-foreground">{project.theme}</p>
        </div>
      </div>

      {!canCompose && (
        <div className="text-center py-12 border rounded-lg">
          <p className="text-muted-foreground mb-4">
            先にナレーションを生成してください
          </p>
          <Link href={`/projects/${projectId}/narration`}>
            <Button>ナレーションページへ</Button>
          </Link>
        </div>
      )}

      {canCompose && (
        <div className="space-y-8">
          {/* ステータス情報 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="border rounded-lg p-4 text-center">
              <p className="text-2xl font-bold">
                {status?.sections_count || project.sections?.length || 0}
              </p>
              <p className="text-sm text-muted-foreground">セクション</p>
            </div>
            <div className="border rounded-lg p-4 text-center">
              <p className="text-2xl font-bold">
                {formatDuration(status?.total_duration || 0)}
              </p>
              <p className="text-sm text-muted-foreground">合計時間</p>
            </div>
            <div className="border rounded-lg p-4 text-center">
              <p className="text-2xl font-bold">
                {formatFileSize(status?.estimated_size || 0)}
              </p>
              <p className="text-sm text-muted-foreground">推定サイズ</p>
            </div>
            <div className="border rounded-lg p-4 text-center">
              <p className="text-2xl font-bold">
                {status?.ffmpeg_available ? "OK" : "N/A"}
              </p>
              <p className="text-sm text-muted-foreground">FFmpeg</p>
            </div>
          </div>

          {/* アクションボタン */}
          <div className="flex gap-4 justify-center">
            <Button
              onClick={handleCompose}
              disabled={composeVideo.isPending}
              size="lg"
            >
              {composeVideo.isPending
                ? "合成中..."
                : isComposed
                ? "再合成"
                : "動画を合成"}
            </Button>
            {videoUrl && (
              <Button onClick={handleDownload} variant="outline" size="lg">
                ダウンロード
              </Button>
            )}
          </div>

          {/* エラー表示 */}
          {composeVideo.isError && (
            <p className="text-destructive text-center">
              動画の合成に失敗しました
            </p>
          )}

          {/* 動画プレビュー */}
          {videoUrl && (
            <div className="border rounded-lg overflow-hidden">
              <video
                src={videoUrl}
                controls
                className="w-full"
                style={{ maxHeight: "540px" }}
              />
            </div>
          )}

          {/* FFmpeg警告 */}
          {status && !status.ffmpeg_available && (
            <div className="p-4 border rounded-lg bg-muted/50">
              <p className="text-sm text-muted-foreground">
                注意: FFmpegがインストールされていないため、動画は生成されません。
                プロジェクト状態のみ更新されます。
              </p>
            </div>
          )}

          {/* 完了メッセージ */}
          {isComposed && !videoUrl && (
            <div className="text-center py-8 border rounded-lg bg-muted/50">
              <p className="text-lg font-medium mb-2">動画合成が完了しています</p>
              <p className="text-muted-foreground">
                「再合成」ボタンをクリックすると動画を再生成できます
              </p>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
