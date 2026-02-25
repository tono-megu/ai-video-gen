"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useProject } from "@/hooks/useProject";
import { useGenerateScript, useUpdateScript } from "@/hooks/usePipeline";
import { useUndoRedo, useUndoRedoKeyboard } from "@/hooks/useUndoRedo";
import { Button } from "@/components/ui/button";
import type { Project } from "@/types";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

// 削除確認ボタン
function DeleteConfirmButton({
  onConfirm,
  label,
  size = "sm"
}: {
  onConfirm: () => void;
  label: string;
  size?: "sm" | "md";
}) {
  const [showConfirm, setShowConfirm] = useState(false);

  if (showConfirm) {
    return (
      <div className="flex items-center gap-1">
        <span className={`text-destructive ${size === "sm" ? "text-xs" : "text-sm"}`}>
          {label}を削除？
        </span>
        <button
          onClick={() => { onConfirm(); setShowConfirm(false); }}
          className={`bg-destructive text-destructive-foreground rounded hover:bg-destructive/90 ${
            size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1"
          }`}
        >
          削除
        </button>
        <button
          onClick={() => setShowConfirm(false)}
          className={`bg-secondary rounded hover:bg-secondary/80 ${
            size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1"
          }`}
        >
          キャンセル
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => setShowConfirm(true)}
      className={`bg-destructive/10 text-destructive hover:bg-destructive/20 rounded ${
        size === "sm" ? "text-xs px-3 py-1.5" : "text-sm px-4 py-2"
      }`}
      title={`${label}を削除`}
    >
      削除
    </button>
  );
}

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

// セクションの型定義
type ScriptSectionData = {
  type: string;
  duration: number;
  narration: string;
  visual_spec?: Record<string, unknown>;
};

const SECTION_TYPE_LABELS: Record<string, string> = {
  title: "タイトル",
  slide: "スライド",
  code: "コード",
  code_typing: "コードタイピング",
  diagram: "図解",
  summary: "まとめ",
};

const SECTION_TYPES = ["title", "slide", "code", "code_typing", "diagram", "summary"];

// 読み取り専用セクション表示
function ScriptSectionView({
  section,
  index,
}: {
  section: ScriptSectionData;
  index: number;
}) {
  return (
    <div className="border rounded-lg p-4 bg-card">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs bg-secondary px-2 py-1 rounded">
          {index + 1}
        </span>
        <span className="text-sm font-medium">
          {SECTION_TYPE_LABELS[section.type] || section.type}
        </span>
      </div>
      <p className="text-sm text-muted-foreground mb-2">
        {section.narration}
      </p>
      {section.visual_spec && (
        <details className="text-xs">
          <summary className="cursor-pointer text-muted-foreground">
            ビジュアル設定
          </summary>
          <pre className="mt-2 p-2 bg-muted rounded overflow-x-auto">
            {JSON.stringify(section.visual_spec, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}

// visual_specのフィールドを更新するヘルパー
function updateVisualSpec(
  section: ScriptSectionData,
  field: string,
  value: unknown
): ScriptSectionData {
  return {
    ...section,
    visual_spec: {
      ...(section.visual_spec || {}),
      [field]: value,
    },
  };
}

// ソート可能なセクションカード
function SortableSectionCard({
  id,
  section,
  index,
  totalSections,
  isSelected,
  onSelect,
  onUpdate,
  onDelete,
  onSplitAtPosition,
  onAddBelow,
}: {
  id: string;
  section: ScriptSectionData;
  index: number;
  totalSections: number;
  isSelected: boolean;
  onSelect: (selected: boolean) => void;
  onUpdate: (updated: ScriptSectionData) => void;
  onDelete: () => void;
  onSplitAtPosition: (position: number) => void;
  onAddBelow: () => void;
}) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [editingVisualSpec, setEditingVisualSpec] = useState(false);
  const [visualSpecText, setVisualSpecText] = useState("");
  const [splitMode, setSplitMode] = useState(false);
  const [cursorPosition, setCursorPosition] = useState<number | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const vs = (section.visual_spec || {}) as Record<string, unknown>;

  const handleVisualSpecEdit = () => {
    setVisualSpecText(JSON.stringify(section.visual_spec || {}, null, 2));
    setEditingVisualSpec(true);
  };

  const handleVisualSpecSave = () => {
    try {
      const parsed = JSON.parse(visualSpecText);
      onUpdate({ ...section, visual_spec: parsed });
      setEditingVisualSpec(false);
    } catch {
      alert("JSONの形式が正しくありません");
    }
  };

  // セクションタイプに応じたビジュアル編集フィールド
  const renderVisualFields = () => {
    switch (section.type) {
      case "title":
        return (
          <div className="space-y-2">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">タイトル</label>
              <input
                type="text"
                value={(vs.title as string) || ""}
                onChange={(e) => onUpdate(updateVisualSpec(section, "title", e.target.value))}
                className="w-full p-2 border rounded text-sm bg-background"
                placeholder="メインタイトル"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">サブタイトル</label>
              <input
                type="text"
                value={(vs.subtitle as string) || ""}
                onChange={(e) => onUpdate(updateVisualSpec(section, "subtitle", e.target.value))}
                className="w-full p-2 border rounded text-sm bg-background"
                placeholder="サブタイトル（任意）"
              />
            </div>
          </div>
        );
      case "slide":
        return (
          <div className="space-y-2">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">見出し</label>
              <input
                type="text"
                value={(vs.heading as string) || ""}
                onChange={(e) => onUpdate(updateVisualSpec(section, "heading", e.target.value))}
                className="w-full p-2 border rounded text-sm bg-background"
                placeholder="スライドの見出し"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">箇条書き（1行1項目）</label>
              <textarea
                value={((vs.bullets as string[]) || []).join("\n")}
                onChange={(e) => onUpdate(updateVisualSpec(section, "bullets", e.target.value.split("\n").filter(Boolean)))}
                className="w-full p-2 border rounded text-sm bg-background resize-none"
                rows={3}
                placeholder="ポイント1&#10;ポイント2&#10;ポイント3"
              />
            </div>
          </div>
        );
      case "code":
      case "code_typing":
        return (
          <div className="space-y-2">
            <div>
              <label className="text-xs text-muted-foreground block mb-1">プログラミング言語</label>
              <input
                type="text"
                value={(vs.language as string) || "python"}
                onChange={(e) => onUpdate(updateVisualSpec(section, "language", e.target.value))}
                className="w-full p-2 border rounded text-sm bg-background"
                placeholder="python, javascript, etc."
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1">コード</label>
              <textarea
                value={(vs.code as string) || ""}
                onChange={(e) => onUpdate(updateVisualSpec(section, "code", e.target.value))}
                className="w-full p-2 border rounded text-sm bg-background font-mono resize-none"
                rows={5}
                placeholder="コードを入力..."
              />
            </div>
          </div>
        );
      case "summary":
        return (
          <div>
            <label className="text-xs text-muted-foreground block mb-1">まとめポイント（1行1項目）</label>
            <textarea
              value={((vs.points as string[]) || []).join("\n")}
              onChange={(e) => onUpdate(updateVisualSpec(section, "points", e.target.value.split("\n").filter(Boolean)))}
              className="w-full p-2 border rounded text-sm bg-background resize-none"
              rows={3}
              placeholder="まとめ1&#10;まとめ2&#10;まとめ3"
            />
          </div>
        );
      case "diagram":
        return (
          <div>
            <label className="text-xs text-muted-foreground block mb-1">図解の説明</label>
            <textarea
              value={(vs.description as string) || ""}
              onChange={(e) => onUpdate(updateVisualSpec(section, "description", e.target.value))}
              className="w-full p-2 border rounded text-sm bg-background resize-none"
              rows={2}
              placeholder="図解の内容を説明..."
            />
          </div>
        );
      default:
        return null;
    }
  };

  // 分割を実行
  const handleSplit = (position?: number) => {
    const pos = position ?? cursorPosition;
    if (pos !== null && pos > 0 && pos < section.narration.length) {
      onSplitAtPosition(pos);
      setSplitMode(false);
      setCursorPosition(null);
    }
  };

  // テキストエリアでの ⌘+E 直接分割
  const handleTextareaKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "e") {
      e.preventDefault();
      const target = e.target as HTMLTextAreaElement;
      const pos = target.selectionStart;
      if (pos > 0 && pos < section.narration.length) {
        handleSplit(pos);
      }
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`border rounded-lg bg-card overflow-hidden ${isSelected ? "ring-2 ring-primary" : ""}`}
    >
      {/* ヘッダー */}
      <div className="flex items-center gap-2 p-3 bg-muted/30">
        {/* 選択チェックボックス */}
        <input
          type="checkbox"
          checked={isSelected}
          onChange={(e) => onSelect(e.target.checked)}
          className="w-4 h-4 rounded"
          title="結合用に選択"
        />
        {/* ドラッグハンドル */}
        <button
          {...attributes}
          {...listeners}
          className="p-1 cursor-grab hover:bg-muted rounded"
          title="ドラッグして並び替え"
        >
          ⋮⋮
        </button>
        <span className="text-xs bg-secondary px-2 py-1 rounded font-medium">
          {index + 1}
        </span>
        <select
          value={section.type}
          onChange={(e) => onUpdate({ ...section, type: e.target.value })}
          className="text-sm bg-background border rounded px-2 py-1"
        >
          {SECTION_TYPES.map((type) => (
            <option key={type} value={type}>
              {SECTION_TYPE_LABELS[type]}
            </option>
          ))}
        </select>
        <div className="flex-1" />
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-1 hover:bg-muted rounded text-sm"
          title={isExpanded ? "折りたたむ" : "展開"}
        >
          {isExpanded ? "▼" : "▶"}
        </button>
      </div>

      {/* ナレーション（常に表示） */}
      <div className="p-3 border-t">
        <div className="flex items-center justify-between mb-1">
          <label className="text-xs text-muted-foreground">
            ナレーション <span className="text-muted-foreground/60">(⌘+E で分割)</span>
          </label>
          {!splitMode ? (
            <button
              onClick={() => setSplitMode(true)}
              className="text-xs text-primary hover:underline"
              title="クリックした位置でセクションを分割"
            >
              ✂️ 分割モード
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-xs text-orange-500">
                分割位置をクリックして選択 (⌘+E で確定)
              </span>
              <button
                onClick={handleSplit}
                disabled={cursorPosition === null}
                className="text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded disabled:opacity-50"
              >
                ここで分割
              </button>
              <button
                onClick={() => { setSplitMode(false); setCursorPosition(null); }}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                キャンセル
              </button>
            </div>
          )}
        </div>
        <textarea
          ref={textareaRef}
          value={section.narration}
          onChange={(e) => onUpdate({ ...section, narration: e.target.value })}
          onKeyDown={handleTextareaKeyDown}
          onClick={(e) => {
            if (splitMode) {
              const target = e.target as HTMLTextAreaElement;
              setCursorPosition(target.selectionStart);
            }
          }}
          onSelect={(e) => {
            if (splitMode) {
              const target = e.target as HTMLTextAreaElement;
              setCursorPosition(target.selectionStart);
            }
          }}
          className={`w-full p-2 border rounded text-sm bg-background resize-none ${splitMode ? "cursor-crosshair border-orange-500" : ""}`}
          rows={2}
          title="⌘+E でカーソル位置で分割"
        />
        {splitMode && cursorPosition !== null && (
          <div className="text-xs text-muted-foreground mt-1">
            分割位置: {cursorPosition}文字目
          </div>
        )}
      </div>

      {/* 展開時の詳細 */}
      {isExpanded && (
        <div className="p-3 border-t bg-muted/10 space-y-3">
          {/* ビジュアル設定（タイプ別フォーム） */}
          <div>
            <label className="text-xs text-muted-foreground block mb-2">ビジュアル設定</label>
            {renderVisualFields()}
          </div>

          {/* JSON直接編集（詳細設定） */}
          <details className="text-xs">
            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
              JSON直接編集（詳細設定）
            </summary>
            <div className="mt-2 space-y-2">
              {editingVisualSpec ? (
                <>
                  <textarea
                    value={visualSpecText}
                    onChange={(e) => setVisualSpecText(e.target.value)}
                    className="w-full p-2 border rounded text-xs font-mono bg-background"
                    rows={6}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={handleVisualSpecSave}
                      className="text-xs bg-primary text-primary-foreground px-2 py-1 rounded"
                    >
                      保存
                    </button>
                    <button
                      onClick={() => setEditingVisualSpec(false)}
                      className="text-xs bg-secondary px-2 py-1 rounded"
                    >
                      キャンセル
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex items-start gap-2">
                  <pre className="flex-1 p-2 bg-muted rounded text-xs overflow-x-auto">
                    {JSON.stringify(section.visual_spec || {}, null, 2)}
                  </pre>
                  <button
                    onClick={handleVisualSpecEdit}
                    className="text-xs text-primary hover:underline shrink-0"
                  >
                    編集
                  </button>
                </div>
              )}
            </div>
          </details>

          {/* アクションボタン */}
          <div className="flex gap-2 pt-2 border-t">
            <button
              onClick={onAddBelow}
              className="text-xs bg-secondary hover:bg-secondary/80 px-3 py-1.5 rounded"
              title="下に新しいセクションを追加"
            >
              + 下に追加
            </button>
            <div className="flex-1" />
            <DeleteConfirmButton onConfirm={onDelete} label="セクション" />
          </div>
        </div>
      )}
    </div>
  );
}

// 構造化エディタの状態型
type ScriptEditorState = {
  title: string;
  description: string;
  sections: ScriptSectionData[];
};

// 構造化エディタ
function StructuredScriptEditor({
  script,
  onSave,
  onCancel,
  isSaving,
}: {
  script: { title?: string; description?: string; sections?: ScriptSectionData[] };
  onSave: (script: { title: string; description: string; sections: ScriptSectionData[] }) => void;
  onCancel: () => void;
  isSaving: boolean;
}) {
  const initialState: ScriptEditorState = {
    title: script.title || "",
    description: script.description || "",
    sections: script.sections || [],
  };

  const {
    state,
    setState,
    undo,
    redo,
    canUndo,
    canRedo,
  } = useUndoRedo<ScriptEditorState>(initialState, { maxHistory: 10 });

  // 選択状態（結合用）
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());

  // DnD センサー
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // キーボードショートカット
  useUndoRedoKeyboard(undo, redo, true);

  // 結合ショートカット (⌘+J)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "j") {
        e.preventDefault();
        handleMergeSelected();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectedIndices, state]);

  const { title, description, sections } = state;

  // セクションIDを生成（DnD用）
  const sectionIds = sections.map((_, i) => `section-${i}`);

  const setTitle = useCallback((newTitle: string) => {
    setState({ ...state, title: newTitle });
  }, [state, setState]);

  const setDescription = useCallback((newDescription: string) => {
    setState({ ...state, description: newDescription });
  }, [state, setState]);

  const setSections = useCallback((newSections: ScriptSectionData[]) => {
    setState({ ...state, sections: newSections });
    setSelectedIndices(new Set()); // 選択をクリア
  }, [state, setState]);

  const updateSection = (index: number, updated: ScriptSectionData) => {
    const newSections = [...sections];
    newSections[index] = updated;
    setSections(newSections);
  };

  const deleteSection = (index: number) => {
    if (sections.length <= 1) {
      alert("最低1つのセクションが必要です");
      return;
    }
    setSections(sections.filter((_, i) => i !== index));
  };

  // カーソル位置で分割
  const splitSectionAtPosition = (index: number, position: number) => {
    const section = sections[index];
    const narration = section.narration;

    if (position <= 0 || position >= narration.length) {
      alert("分割位置が無効です");
      return;
    }

    const firstHalf: ScriptSectionData = {
      ...section,
      narration: narration.slice(0, position).trim(),
    };

    const secondHalf: ScriptSectionData = {
      type: section.type,
      narration: narration.slice(position).trim(),
      duration: 0,
      visual_spec: { ...section.visual_spec },
    };

    const newSections = [...sections];
    newSections.splice(index, 1, firstHalf, secondHalf);
    setSections(newSections);
  };

  // 選択されたセクションを結合
  const handleMergeSelected = () => {
    if (selectedIndices.size < 2) {
      alert("2つ以上のセクションを選択してください");
      return;
    }

    const sortedIndices = Array.from(selectedIndices).sort((a, b) => a - b);

    // 連続しているか確認
    for (let i = 1; i < sortedIndices.length; i++) {
      if (sortedIndices[i] - sortedIndices[i - 1] !== 1) {
        alert("隣接するセクションのみ結合できます");
        return;
      }
    }

    const sectionsToMerge = sortedIndices.map((i) => sections[i]);
    const mergedSection: ScriptSectionData = {
      type: sectionsToMerge[0].type,
      duration: sectionsToMerge.reduce((sum, s) => sum + (s.duration || 0), 0),
      narration: sectionsToMerge.map((s) => s.narration).join("\n"),
      visual_spec: sectionsToMerge[0].visual_spec,
    };

    const newSections = sections.filter((_, i) => !selectedIndices.has(i));
    newSections.splice(sortedIndices[0], 0, mergedSection);
    setSections(newSections);
  };

  // DnDハンドラー
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      const oldIndex = sectionIds.indexOf(active.id as string);
      const newIndex = sectionIds.indexOf(over.id as string);
      setSections(arrayMove(sections, oldIndex, newIndex));
    }
  };

  const addSection = (afterIndex: number) => {
    const newSection: ScriptSectionData = {
      type: "slide",
      duration: 0,
      narration: "新しいセクションのナレーションを入力してください。",
      visual_spec: { heading: "見出し", bullets: ["ポイント1"] },
    };
    const newSections = [...sections];
    newSections.splice(afterIndex + 1, 0, newSection);
    setSections(newSections);
  };

  const toggleSelection = (index: number, selected: boolean) => {
    const newSelected = new Set(selectedIndices);
    if (selected) {
      newSelected.add(index);
    } else {
      newSelected.delete(index);
    }
    setSelectedIndices(newSelected);
  };

  const handleSave = () => {
    onSave({ title, description, sections });
  };

  return (
    <div className="space-y-4">
      {/* タイトル・説明 */}
      <div className="space-y-3 border rounded-lg p-4">
        <div>
          <label className="text-sm font-medium block mb-1">タイトル</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border rounded bg-background"
          />
        </div>
        <div>
          <label className="text-sm font-medium block mb-1">説明</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-2 border rounded bg-background resize-none"
            rows={2}
          />
        </div>
      </div>

      {/* セクション一覧ヘッダー */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-medium">セクション ({sections.length})</h3>
          {selectedIndices.size >= 2 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleMergeSelected}
              title="選択したセクションを結合 (⌘+J)"
            >
              🔗 結合 ({selectedIndices.size}件)
            </Button>
          )}
        </div>
        <span className="text-xs text-muted-foreground">
          ドラッグで並び替え / チェックで選択して結合
        </span>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={sectionIds} strategy={verticalListSortingStrategy}>
          <div className="space-y-2">
            {sections.map((section, index) => (
              <SortableSectionCard
                key={sectionIds[index]}
                id={sectionIds[index]}
                section={section}
                index={index}
                totalSections={sections.length}
                isSelected={selectedIndices.has(index)}
                onSelect={(selected) => toggleSelection(index, selected)}
                onUpdate={(updated) => updateSection(index, updated)}
                onDelete={() => deleteSection(index)}
                onSplitAtPosition={(position) => splitSectionAtPosition(index, position)}
                onAddBelow={() => addSection(index)}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {/* 新規セクション追加ボタン */}
      <button
        onClick={() => addSection(sections.length - 1)}
        className="w-full p-3 border-2 border-dashed rounded-lg text-muted-foreground hover:border-primary hover:text-primary transition-colors"
      >
        + セクションを追加
      </button>

      {/* Undo/Redo・保存・キャンセル */}
      <div className="flex gap-2 justify-between pt-4 border-t">
        <div className="flex gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={undo}
            disabled={!canUndo}
            title="元に戻す (Ctrl+Z)"
          >
            ↩ 戻す
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={redo}
            disabled={!canRedo}
            title="やり直す (Ctrl+Shift+Z)"
          >
            ↪ やり直す
          </Button>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onCancel}>
            キャンセル
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? "保存中..." : "保存"}
          </Button>
        </div>
      </div>
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
        <StructuredScriptEditor
          script={script || { title: "", description: "", sections: [] }}
          onSave={async (updatedScript) => {
            try {
              await updateScript.mutateAsync({ projectId: project.id, script: updatedScript });
              setIsEditing(false);
            } catch (error) {
              console.error("Failed to update script:", error);
            }
          }}
          onCancel={() => setIsEditing(false)}
          isSaving={updateScript.isPending}
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
                <ScriptSectionView key={index} section={section as ScriptSectionData} index={index} />
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
