"use client";

import { useState } from "react";
import Link from "next/link";
import { useProjects, useDeleteProject } from "@/hooks/useProject";
import { Button } from "@/components/ui/button";

const stateLabels: Record<string, string> = {
  init: "初期化",
  script_done: "脚本完了",
  visuals_done: "ビジュアル完了",
  narration_done: "ナレーション完了",
  composed: "完成",
};

function ProjectCard({ project }: { project: { id: string; theme: string; state: string; created_at: string } }) {
  const deleteProject = useDeleteProject();
  const [showConfirm, setShowConfirm] = useState(false);

  const handleDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowConfirm(true);
  };

  const confirmDelete = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await deleteProject.mutateAsync(project.id);
    } catch (error) {
      console.error("Failed to delete project:", error);
    }
    setShowConfirm(false);
  };

  const cancelDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setShowConfirm(false);
  };

  return (
    <Link
      href={`/projects/${project.id}`}
      className="block p-6 rounded-lg border bg-card hover:border-primary transition-colors relative"
    >
      <div className="flex items-start justify-between">
        <h2 className="font-semibold mb-2">{project.theme}</h2>
        {!showConfirm && (
          <button
            onClick={handleDelete}
            className="text-muted-foreground hover:text-destructive transition-colors p-1"
            title="プロジェクトを削除"
          >
            🗑️
          </button>
        )}
      </div>
      <p className="text-sm text-muted-foreground">
        状態: {stateLabels[project.state] || project.state}
      </p>
      <p className="text-xs text-muted-foreground mt-2">
        作成日: {new Date(project.created_at).toLocaleDateString("ja-JP")}
      </p>

      {showConfirm && (
        <div className="absolute inset-0 bg-background/95 rounded-lg flex flex-col items-center justify-center p-4">
          <p className="text-sm mb-3 text-center">
            「{project.theme}」を削除しますか？
          </p>
          <div className="flex gap-2">
            <button
              onClick={confirmDelete}
              disabled={deleteProject.isPending}
              className="px-3 py-1.5 bg-destructive text-destructive-foreground rounded text-sm hover:bg-destructive/90 disabled:opacity-50"
            >
              {deleteProject.isPending ? "削除中..." : "削除"}
            </button>
            <button
              onClick={cancelDelete}
              className="px-3 py-1.5 bg-secondary rounded text-sm hover:bg-secondary/80"
            >
              キャンセル
            </button>
          </div>
        </div>
      )}
    </Link>
  );
}

export default function Home() {
  const { data: projects, isLoading, error } = useProjects();

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">AI Video Generator</h1>
        <div className="flex gap-2">
          <Link href="/preferences">
            <Button variant="outline">好み管理</Button>
          </Link>
          <Link href="/projects/new">
            <Button>新規プロジェクト</Button>
          </Link>
        </div>
      </div>

      {isLoading && <p className="text-muted-foreground">読み込み中...</p>}

      {error && (
        <p className="text-destructive">
          エラーが発生しました: {error.message}
        </p>
      )}

      {projects && projects.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">
            プロジェクトがまだありません
          </p>
          <Link href="/projects/new">
            <Button>最初のプロジェクトを作成</Button>
          </Link>
        </div>
      )}

      {projects && projects.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </main>
  );
}
