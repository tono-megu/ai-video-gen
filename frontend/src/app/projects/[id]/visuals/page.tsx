"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useProject } from "@/hooks/useProject";
import { useGenerateVisuals } from "@/hooks/usePipeline";
import { Button } from "@/components/ui/button";

function SlidePreview({
  section,
  onEdit,
}: {
  section: {
    id: string;
    section_index: number;
    type: string;
    slide_image_path?: string;
    narration?: string;
    visual_spec?: Record<string, unknown>;
  };
  onEdit: () => void;
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

  return (
    <div className="border rounded-lg overflow-hidden bg-card">
      <div className="p-3 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs bg-secondary px-2 py-1 rounded">
            {section.section_index + 1}
          </span>
          <span className="text-sm font-medium">
            {typeLabels[section.type] || section.type}
          </span>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onEdit}>
            編集
          </Button>
        </div>
      </div>

      {section.slide_image_path ? (
        <div
          className="relative cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <iframe
            src={section.slide_image_path}
            className={`w-full border-0 ${isExpanded ? "h-[540px]" : "h-[180px]"}`}
            title={`Slide ${section.section_index + 1}`}
          />
          <div className="absolute bottom-2 right-2 text-xs bg-black/50 text-white px-2 py-1 rounded">
            {isExpanded ? "クリックで縮小" : "クリックで拡大"}
          </div>
        </div>
      ) : (
        <div className="h-[180px] flex items-center justify-center text-muted-foreground">
          スライド未生成
        </div>
      )}

      {section.narration && (
        <div className="p-3 border-t text-sm text-muted-foreground">
          <p className="line-clamp-2">{section.narration}</p>
        </div>
      )}
    </div>
  );
}

export default function VisualsPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { data: project, isLoading, error, refetch } = useProject(projectId);
  const generateVisuals = useGenerateVisuals();
  const [editingSection, setEditingSection] = useState<string | null>(null);

  const handleGenerateVisuals = async () => {
    try {
      await generateVisuals.mutateAsync(projectId);
      refetch();
    } catch (error) {
      console.error("Failed to generate visuals:", error);
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

  const hasScript = project.state !== "init";
  const sections = project.sections || [];

  return (
    <main className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <Link
          href={`/projects/${projectId}`}
          className="text-muted-foreground hover:text-foreground"
        >
          ← プロジェクトに戻る
        </Link>
      </div>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">ビジュアル編集</h1>
          <p className="text-muted-foreground">{project.theme}</p>
        </div>
        <div className="flex gap-2">
          {hasScript && (
            <Button
              onClick={handleGenerateVisuals}
              disabled={generateVisuals.isPending}
            >
              {generateVisuals.isPending
                ? "生成中..."
                : sections.some((s) => s.slide_image_path)
                ? "全て再生成"
                : "スライド生成"}
            </Button>
          )}
        </div>
      </div>

      {!hasScript && (
        <div className="text-center py-12 border rounded-lg">
          <p className="text-muted-foreground mb-4">
            先に脚本を生成してください
          </p>
          <Link href={`/projects/${projectId}`}>
            <Button>脚本ページへ</Button>
          </Link>
        </div>
      )}

      {hasScript && sections.length === 0 && (
        <div className="text-center py-12 border rounded-lg">
          <p className="text-muted-foreground">セクションがありません</p>
        </div>
      )}

      {sections.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sections.map((section) => (
            <SlidePreview
              key={section.id}
              section={section}
              onEdit={() => setEditingSection(section.id)}
            />
          ))}
        </div>
      )}

      {generateVisuals.isError && (
        <p className="text-destructive mt-4">ビジュアルの生成に失敗しました</p>
      )}
    </main>
  );
}
