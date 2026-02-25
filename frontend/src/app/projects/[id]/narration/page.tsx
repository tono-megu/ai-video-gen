"use client";

import { useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useProject } from "@/hooks/useProject";
import { useGenerateNarrations } from "@/hooks/usePipeline";
import { Button } from "@/components/ui/button";

function AudioPlayer({ audioUrl, label }: { audioUrl?: string; label: string }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const handlePlayPause = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  if (!audioUrl) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground text-sm">
        <span className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
          -
        </span>
        <span>音声未生成</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <audio
        ref={audioRef}
        src={audioUrl}
        onEnded={() => setIsPlaying(false)}
        onPause={() => setIsPlaying(false)}
        onPlay={() => setIsPlaying(true)}
      />
      <button
        onClick={handlePlayPause}
        className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 transition-colors"
        title={isPlaying ? "一時停止" : "再生"}
      >
        {isPlaying ? "⏸" : "▶"}
      </button>
      <span className="text-sm text-muted-foreground">{label}</span>
    </div>
  );
}

function NarrationSection({
  section,
}: {
  section: {
    id: string;
    section_index: number;
    type: string;
    narration?: string;
    narration_audio_path?: string;
    duration?: number;
  };
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  const typeLabels: Record<string, string> = {
    title: "タイトル",
    slide: "スライド",
    code: "コード",
    code_typing: "コードタイピング",
    diagram: "図解",
    summary: "まとめ",
  };

  const durationLabel = section.duration
    ? `${Math.round(section.duration)}秒`
    : "時間未設定";

  return (
    <div className="border rounded-lg p-4 bg-card">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs bg-secondary px-2 py-1 rounded">
            {section.section_index + 1}
          </span>
          <span className="text-sm font-medium">
            {typeLabels[section.type] || section.type}
          </span>
          <span className="text-xs text-muted-foreground">{durationLabel}</span>
        </div>
        <AudioPlayer
          audioUrl={section.narration_audio_path}
          label={durationLabel}
        />
      </div>

      {section.narration && (
        <div>
          <p
            className={`text-sm text-muted-foreground ${!isExpanded ? "line-clamp-2" : ""}`}
          >
            {section.narration}
          </p>
          {section.narration.length > 100 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-xs text-primary mt-1"
            >
              {isExpanded ? "折りたたむ" : "続きを読む"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function NarrationPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { data: project, isLoading, error, refetch } = useProject(projectId);
  const generateNarrations = useGenerateNarrations();

  const handleGenerateNarrations = async () => {
    try {
      await generateNarrations.mutateAsync(projectId);
      refetch();
    } catch (error) {
      console.error("Failed to generate narrations:", error);
    }
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

  const hasVisuals = ["visuals_done", "narration_done", "composed"].includes(project.state);
  const sections = project.sections || [];
  const hasAudio = sections.some((s) => s.narration_audio_path);

  return (
    <main className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <Link
          href={`/projects/${projectId}/visuals`}
          className="text-muted-foreground hover:text-foreground"
        >
          ← ビジュアルに戻る
        </Link>
      </div>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">ナレーション</h1>
          <p className="text-muted-foreground">{project.theme}</p>
        </div>
        <div className="flex gap-2">
          {hasVisuals && (
            <Button
              onClick={handleGenerateNarrations}
              disabled={generateNarrations.isPending}
            >
              {generateNarrations.isPending
                ? "生成中..."
                : hasAudio
                ? "全て再生成"
                : "ナレーション生成"}
            </Button>
          )}
          {project.state === "narration_done" && (
            <Link href={`/projects/${projectId}/compose`}>
              <Button variant="outline">次へ: 動画合成 →</Button>
            </Link>
          )}
        </div>
      </div>

      {!hasVisuals && (
        <div className="text-center py-12 border rounded-lg">
          <p className="text-muted-foreground mb-4">
            先にビジュアルを生成してください
          </p>
          <Link href={`/projects/${projectId}/visuals`}>
            <Button>ビジュアルページへ</Button>
          </Link>
        </div>
      )}

      {hasVisuals && sections.length === 0 && (
        <div className="text-center py-12 border rounded-lg">
          <p className="text-muted-foreground">セクションがありません</p>
        </div>
      )}

      {sections.length > 0 && (
        <div className="space-y-4">
          {sections.map((section) => (
            <NarrationSection key={section.id} section={section} />
          ))}
        </div>
      )}

      {generateNarrations.isError && (
        <p className="text-destructive mt-4">ナレーションの生成に失敗しました</p>
      )}

      {!hasAudio && hasVisuals && (
        <div className="mt-8 p-4 border rounded-lg bg-muted/50">
          <p className="text-sm text-muted-foreground">
            注意: ElevenLabs APIキーが設定されていない場合、モックモードで動作します。
            音声は生成されませんが、推定時間が設定されます。
          </p>
        </div>
      )}
    </main>
  );
}
