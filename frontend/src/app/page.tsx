"use client";

import Link from "next/link";
import { useProjects } from "@/hooks/useProject";
import { Button } from "@/components/ui/button";

export default function Home() {
  const { data: projects, isLoading, error } = useProjects();

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">AI Video Generator</h1>
        <Link href="/projects/new">
          <Button>新規プロジェクト</Button>
        </Link>
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
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="block p-6 rounded-lg border bg-card hover:border-primary transition-colors"
            >
              <h2 className="font-semibold mb-2">{project.theme}</h2>
              <p className="text-sm text-muted-foreground">
                状態: {project.state}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                作成日: {new Date(project.created_at).toLocaleDateString("ja-JP")}
              </p>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
