"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useCreateProject } from "@/hooks/useProject";
import { Button } from "@/components/ui/button";

export default function NewProjectPage() {
  const router = useRouter();
  const createProject = useCreateProject();
  const [theme, setTheme] = useState("");
  const [durationTarget, setDurationTarget] = useState<number | undefined>(180);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!theme.trim()) return;

    try {
      const project = await createProject.mutateAsync({
        theme: theme.trim(),
        duration_target: durationTarget,
      });
      router.push(`/projects/${project.id}`);
    } catch (error) {
      console.error("Failed to create project:", error);
    }
  };

  return (
    <main className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="mb-8">
        <Link href="/" className="text-muted-foreground hover:text-foreground">
          ← ダッシュボードに戻る
        </Link>
      </div>

      <h1 className="text-3xl font-bold mb-8">新規プロジェクト作成</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="theme" className="block text-sm font-medium mb-2">
            テーマ
          </label>
          <input
            id="theme"
            type="text"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            placeholder="例: Pythonの基礎、React Hooksの使い方"
            className="w-full px-4 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
            required
          />
          <p className="text-sm text-muted-foreground mt-1">
            動画で解説したいテーマを入力してください
          </p>
        </div>

        <div>
          <label htmlFor="duration" className="block text-sm font-medium mb-2">
            目標動画時間（秒）
          </label>
          <input
            id="duration"
            type="number"
            value={durationTarget || ""}
            onChange={(e) =>
              setDurationTarget(e.target.value ? Number(e.target.value) : undefined)
            }
            placeholder="180"
            min={30}
            max={3600}
            className="w-full px-4 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <p className="text-sm text-muted-foreground mt-1">
            30秒〜3600秒（1時間）の範囲で指定できます
          </p>
        </div>

        <div className="flex gap-4">
          <Button
            type="submit"
            disabled={!theme.trim() || createProject.isPending}
          >
            {createProject.isPending ? "作成中..." : "プロジェクトを作成"}
          </Button>
          <Link href="/">
            <Button type="button" variant="outline">
              キャンセル
            </Button>
          </Link>
        </div>

        {createProject.isError && (
          <p className="text-destructive">
            エラーが発生しました。もう一度お試しください。
          </p>
        )}
      </form>
    </main>
  );
}
