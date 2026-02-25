"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useProject } from "@/hooks/useProject";
import { useGenerateScript, useUpdateScript } from "@/hooks/usePipeline";
import { Button } from "@/components/ui/button";
import type { Project } from "@/types";

function ScriptSection({
  section,
  index,
}: {
  section: Project["script"] extends { sections: infer S } ? S extends Array<infer T> ? T : never : never;
  index: number;
}) {
  const sectionTypeLabels: Record<string, string> = {
    title: "タイトル",
    slide: "スライド",
    code: "コード",
    code_typing: "コードタイピング",
    diagram: "図解",
    summary: "まとめ",
  };

  return (
    <div className="border rounded-lg p-4 bg-card">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs bg-secondary px-2 py-1 rounded">
          {index + 1}
        </span>
        <span className="text-sm font-medium">
          {sectionTypeLabels[(section as { type?: string }).type || "slide"] || (section as { type?: string }).type}
        </span>
        <span className="text-xs text-muted-foreground">
          {(section as { duration?: number }).duration}秒
        </span>
      </div>
      <p className="text-sm text-muted-foreground mb-2">
        {(section as { narration?: string }).narration}
      </p>
      {(section as { visual_spec?: Record<string, unknown> }).visual_spec && (
        <details className="text-xs">
          <summary className="cursor-pointer text-muted-foreground">
            ビジュアル設定
          </summary>
          <pre className="mt-2 p-2 bg-muted rounded overflow-x-auto">
            {JSON.stringify((section as { visual_spec?: Record<string, unknown> }).visual_spec, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

function ScriptEditor({ project }: { project: Project }) {
  const generateScript = useGenerateScript();
  const updateScript = useUpdateScript();
  const [isEditing, setIsEditing] = useState(false);
  const [editedScript, setEditedScript] = useState("");

  const handleGenerateScript = async () => {
    try {
      await generateScript.mutateAsync(project.id);
    } catch (error) {
      console.error("Failed to generate script:", error);
    }
  };

  const handleStartEdit = () => {
    setEditedScript(JSON.stringify(project.script, null, 2));
    setIsEditing(true);
  };

  const handleSaveEdit = async () => {
    try {
      const parsed = JSON.parse(editedScript);
      await updateScript.mutateAsync({ projectId: project.id, script: parsed });
      setIsEditing(false);
    } catch (error) {
      console.error("Failed to update script:", error);
    }
  };

  const script = project.script as {
    title?: string;
    description?: string;
    sections?: Array<{
      type: string;
      duration: number;
      narration: string;
      visual_spec?: Record<string, unknown>;
    }>;
  } | null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">脚本</h2>
        <div className="flex gap-2">
          {!script && (
            <Button
              onClick={handleGenerateScript}
              disabled={generateScript.isPending}
            >
              {generateScript.isPending ? "生成中..." : "脚本を生成"}
            </Button>
          )}
          {script && !isEditing && (
            <>
              <Button
                variant="outline"
                onClick={handleGenerateScript}
                disabled={generateScript.isPending}
              >
                {generateScript.isPending ? "再生成中..." : "再生成"}
              </Button>
              <Button variant="outline" onClick={handleStartEdit}>
                編集
              </Button>
            </>
          )}
          {isEditing && (
            <>
              <Button onClick={handleSaveEdit} disabled={updateScript.isPending}>
                {updateScript.isPending ? "保存中..." : "保存"}
              </Button>
              <Button variant="outline" onClick={() => setIsEditing(false)}>
                キャンセル
              </Button>
            </>
          )}
        </div>
      </div>

      {generateScript.isError && (
        <p className="text-destructive">脚本の生成に失敗しました</p>
      )}

      {!script && !generateScript.isPending && (
        <p className="text-muted-foreground">
          「脚本を生成」ボタンをクリックして、AIに脚本を作成してもらいましょう
        </p>
      )}

      {isEditing ? (
        <textarea
          value={editedScript}
          onChange={(e) => setEditedScript(e.target.value)}
          className="w-full h-96 p-4 border rounded-md bg-background font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary"
        />
      ) : (
        script && (
          <div className="space-y-4">
            <div className="border-b pb-4">
              <h3 className="text-lg font-medium">{script.title}</h3>
              <p className="text-muted-foreground">{script.description}</p>
            </div>

            <div className="space-y-3">
              {script.sections?.map((section, index) => (
                <ScriptSection key={index} section={section} index={index} />
              ))}
            </div>
          </div>
        )
      )}
    </div>
  );
}

export default function ProjectDetailPage() {
  const params = useParams();
  const projectId = params.id as string;
  const { data: project, isLoading, error } = useProject(projectId);

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
        <p className="text-destructive">
          プロジェクトの読み込みに失敗しました
        </p>
        <Link href="/" className="text-primary hover:underline">
          ダッシュボードに戻る
        </Link>
      </main>
    );
  }

  const stateLabels: Record<string, string> = {
    init: "初期化",
    script_done: "脚本完了",
    visuals_done: "ビジュアル完了",
    narration_done: "ナレーション完了",
    composed: "完成",
  };

  return (
    <main className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <Link href="/" className="text-muted-foreground hover:text-foreground">
          ← ダッシュボードに戻る
        </Link>
      </div>

      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold">{project.theme}</h1>
          <span className="text-sm bg-secondary px-2 py-1 rounded">
            {stateLabels[project.state] || project.state}
          </span>
        </div>
        <p className="text-muted-foreground">
          作成日: {new Date(project.created_at).toLocaleDateString("ja-JP")}
          {project.duration_target && ` / 目標時間: ${project.duration_target}秒`}
        </p>
      </div>

      <ScriptEditor project={project} />
    </main>
  );
}
