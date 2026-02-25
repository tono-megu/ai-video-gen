"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useProject } from "@/hooks/useProject";
import { useGenerateScript, useUpdateScript } from "@/hooks/usePipeline";
import { Button } from "@/components/ui/button";
import type { Project } from "@/types";

// ワークフローナビゲーション
function WorkflowNav({ projectId, currentStep, state }: { projectId: string; currentStep: string; state: string }) {
  const steps = [
    { id: "script", label: "脚本", href: `/projects/${projectId}`, available: true },
    { id: "visuals", label: "ビジュアル", href: `/projects/${projectId}/visuals`, available: state !== "init" },
    { id: "narration", label: "ナレーション", href: `/projects/${projectId}/narration`, available: ["visuals_done", "narration_done", "composed"].includes(state) },
    { id: "compose", label: "動画合成", href: `/projects/${projectId}/compose`, available: ["narration_done", "composed"].includes(state) },
  ];

  return (
    <div className="flex gap-2 mb-8 border-b pb-4">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center">
          {index > 0 && <span className="mx-2 text-muted-foreground">→</span>}
          {step.available ? (
            <Link
              href={step.href}
              className={`px-4 py-2 rounded-md transition-colors ${
                currentStep === step.id
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary hover:bg-secondary/80"
              }`}
            >
              {step.label}
            </Link>
          ) : (
            <span className="px-4 py-2 rounded-md bg-muted text-muted-foreground cursor-not-allowed">
              {step.label}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

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

// 脚本テンプレート
const SCRIPT_TEMPLATE = {
  title: "動画タイトル",
  description: "動画の概要を入力",
  sections: [
    {
      type: "title",
      duration: 5,
      narration: "こんにちは！今日は〇〇について学んでいきましょう。",
      visual_spec: { title: "タイトル", subtitle: "サブタイトル" }
    },
    {
      type: "slide",
      duration: 30,
      narration: "まず、〇〇とは何かについて説明します。",
      visual_spec: { heading: "見出し", bullets: ["ポイント1", "ポイント2", "ポイント3"] }
    },
    {
      type: "code",
      duration: 45,
      narration: "実際のコードを見てみましょう。",
      visual_spec: { language: "python", code: "print('Hello, World!')" }
    },
    {
      type: "summary",
      duration: 10,
      narration: "以上でまとめです。ご視聴ありがとうございました！",
      visual_spec: { points: ["学んだこと1", "学んだこと2"] }
    }
  ]
};

function ScriptEditor({ project }: { project: Project }) {
  const generateScript = useGenerateScript();
  const updateScript = useUpdateScript();
  const [isEditing, setIsEditing] = useState(false);
  const [editedScript, setEditedScript] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);
  const [isManualMode, setIsManualMode] = useState(false);
  const [documentText, setDocumentText] = useState("");
  const [isConverting, setIsConverting] = useState(false);

  const handleGenerateScript = async () => {
    try {
      await generateScript.mutateAsync(project.id);
    } catch (error) {
      console.error("Failed to generate script:", error);
    }
  };

  const handleStartEdit = () => {
    setEditedScript(JSON.stringify(project.script, null, 2));
    setParseError(null);
    setIsEditing(true);
  };

  const handleStartManual = () => {
    setIsManualMode(true);
    setDocumentText("");
  };

  const handleConvertDocument = async () => {
    if (!documentText.trim()) return;

    setIsConverting(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/projects/${project.id}/convert-document`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ document: documentText, theme: project.theme }),
        }
      );

      if (!response.ok) throw new Error("変換に失敗しました");

      const data = await response.json();
      await updateScript.mutateAsync({ projectId: project.id, script: data.script });
      setIsManualMode(false);
      setDocumentText("");
    } catch (error) {
      console.error("Failed to convert document:", error);
      setParseError("ドキュメントの変換に失敗しました。もう一度お試しください。");
    } finally {
      setIsConverting(false);
    }
  };

  const handleSaveEdit = async () => {
    try {
      const parsed = JSON.parse(editedScript);
      setParseError(null);
      await updateScript.mutateAsync({ projectId: project.id, script: parsed });
      setIsEditing(false);
    } catch (error) {
      if (error instanceof SyntaxError) {
        setParseError("JSONの形式が正しくありません。確認してください。");
      } else {
        console.error("Failed to update script:", error);
      }
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
              <Link href={`/projects/${project.id}/visuals`}>
                <Button>次へ: ビジュアル →</Button>
              </Link>
            </>
          )}
          {isEditing && (
            <>
              <Button onClick={handleSaveEdit} disabled={updateScript.isPending}>
                {updateScript.isPending ? "保存中..." : "保存"}
              </Button>
              <Button variant="outline" onClick={() => { setIsEditing(false); setParseError(null); }}>
                キャンセル
              </Button>
            </>
          )}
        </div>
      </div>

      {generateScript.isError && (
        <p className="text-destructive">脚本の生成に失敗しました</p>
      )}

      {parseError && (
        <p className="text-destructive">{parseError}</p>
      )}

      {!script && !isEditing && !isManualMode && (
        <div className="border rounded-lg p-6 text-center">
          <p className="text-muted-foreground mb-4">
            脚本を作成してください
          </p>
          {generateScript.isPending ? (
            <p className="text-primary">AIが脚本を生成中...</p>
          ) : (
            <div className="flex gap-4 justify-center">
              <button
                onClick={handleGenerateScript}
                className="text-left p-4 border rounded-lg max-w-xs hover:border-primary hover:bg-muted/50 transition-colors cursor-pointer"
              >
                <h3 className="font-medium mb-2">AIで生成</h3>
                <p className="text-sm text-muted-foreground">テーマに基づいてAIが自動で脚本を作成します</p>
              </button>
              <button
                onClick={handleStartManual}
                className="text-left p-4 border rounded-lg max-w-xs hover:border-primary hover:bg-muted/50 transition-colors cursor-pointer"
              >
                <h3 className="font-medium mb-2">ドキュメントから作成</h3>
                <p className="text-sm text-muted-foreground">メモや原稿を貼り付けてAIがナレーション形式に変換</p>
              </button>
            </div>
          )}
        </div>
      )}

      {isManualMode && (
        <div className="border rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">ドキュメントを貼り付けてください</h3>
            <Button variant="outline" onClick={() => setIsManualMode(false)}>
              キャンセル
            </Button>
          </div>
          <p className="text-sm text-muted-foreground">
            箇条書き、メモ、原稿など、どんな形式でもOKです。AIがナレーション形式の脚本に変換します。
          </p>
          <textarea
            value={documentText}
            onChange={(e) => setDocumentText(e.target.value)}
            placeholder={`例:\n・Pythonとは何か\n・変数の使い方\n・print関数の説明\n・サンプルコード: print("Hello")\n・まとめ`}
            className="w-full h-64 p-4 border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          />
          <div className="flex gap-2">
            <Button
              onClick={handleConvertDocument}
              disabled={isConverting || !documentText.trim()}
            >
              {isConverting ? "変換中..." : "脚本に変換"}
            </Button>
          </div>
        </div>
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
      <div className="mb-4">
        <Link href="/" className="text-muted-foreground hover:text-foreground">
          ← ダッシュボードに戻る
        </Link>
      </div>

      <div className="mb-4">
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

      <WorkflowNav projectId={projectId} currentStep="script" state={project.state} />

      <ScriptEditor project={project} />
    </main>
  );
}
