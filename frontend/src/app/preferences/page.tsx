"use client";

import { useState } from "react";
import Link from "next/link";
import {
  usePreferences,
  usePreferenceProfile,
  useCorrectionStats,
  useEvolvePreferences,
  useDeletePreference,
  useCreatePreference,
} from "@/hooks/usePreferences";
import { Button } from "@/components/ui/button";

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const percentage = Math.round(confidence * 100);
  let colorClass = "bg-gray-200 text-gray-700";

  if (confidence >= 0.85) {
    colorClass = "bg-green-100 text-green-800";
  } else if (confidence >= 0.5) {
    colorClass = "bg-yellow-100 text-yellow-800";
  } else {
    colorClass = "bg-gray-100 text-gray-600";
  }

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
      {percentage}%
    </span>
  );
}

function CategoryBadge({ category }: { category: string }) {
  const colors: Record<string, string> = {
    style: "bg-purple-100 text-purple-800",
    structural: "bg-blue-100 text-blue-800",
    content: "bg-green-100 text-green-800",
    technical: "bg-orange-100 text-orange-800",
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${colors[category] || "bg-gray-100"}`}>
      {category}
    </span>
  );
}

function ScopeBadge({ scope, sectionType }: { scope: string; sectionType?: string }) {
  const label = sectionType ? `${scope}:${sectionType}` : scope;

  return (
    <span className="px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700">
      {label}
    </span>
  );
}

function DeleteConfirmButton({
  onConfirm,
  isPending,
}: {
  onConfirm: () => void;
  isPending?: boolean;
}) {
  const [showConfirm, setShowConfirm] = useState(false);

  if (showConfirm) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-sm text-destructive">削除？</span>
        <Button
          size="sm"
          variant="destructive"
          onClick={() => { onConfirm(); setShowConfirm(false); }}
          disabled={isPending}
        >
          {isPending ? "削除中..." : "削除"}
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowConfirm(false)}
        >
          キャンセル
        </Button>
      </div>
    );
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={() => setShowConfirm(true)}
      className="text-destructive hover:text-destructive"
    >
      削除
    </Button>
  );
}

export default function PreferencesPage() {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newPref, setNewPref] = useState({
    description: "",
    category: "style",
    scope: "global",
    section_type: "",
    confidence: 0.7,
  });

  const { data: preferences, isLoading: prefsLoading } = usePreferences();
  const { data: profile, isLoading: profileLoading } = usePreferenceProfile();
  const { data: stats } = useCorrectionStats();
  const evolve = useEvolvePreferences();
  const deletePref = useDeletePreference();
  const createPref = useCreatePreference();

  const handleEvolve = async () => {
    try {
      await evolve.mutateAsync(50);
    } catch {
      console.error("Failed to evolve preferences");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deletePref.mutateAsync(id);
    } catch {
      console.error("Failed to delete preference");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createPref.mutateAsync({
        description: newPref.description,
        category: newPref.category,
        scope: newPref.scope,
        section_type: newPref.section_type || undefined,
        confidence: newPref.confidence,
      });
      setShowAddForm(false);
      setNewPref({
        description: "",
        category: "style",
        scope: "global",
        section_type: "",
        confidence: 0.7,
      });
    } catch {
      console.error("Failed to create preference");
    }
  };

  if (prefsLoading || profileLoading) {
    return (
      <main className="container mx-auto px-4 py-8">
        <p className="text-muted-foreground">読み込み中...</p>
      </main>
    );
  }

  return (
    <main className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="mb-8">
        <Link href="/" className="text-muted-foreground hover:text-foreground">
          ← ダッシュボードに戻る
        </Link>
      </div>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">好み管理</h1>
          <p className="text-muted-foreground">
            修正履歴から学習した好みを確認・管理できます
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setShowAddForm(!showAddForm)} variant="outline">
            手動で追加
          </Button>
          <Button onClick={handleEvolve} disabled={evolve.isPending}>
            {evolve.isPending ? "学習中..." : "好みを学習"}
          </Button>
        </div>
      </div>

      {/* 統計サマリー */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold">{profile?.total_preferences || 0}</p>
          <p className="text-sm text-muted-foreground">好み数</p>
        </div>
        <div className="border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold">{profile?.high_confidence?.length || 0}</p>
          <p className="text-sm text-muted-foreground">自動適用</p>
        </div>
        <div className="border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold">{profile?.suggestions?.length || 0}</p>
          <p className="text-sm text-muted-foreground">提案中</p>
        </div>
        <div className="border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold">{stats?.total || 0}</p>
          <p className="text-sm text-muted-foreground">修正ログ</p>
        </div>
      </div>

      {/* 進化結果 */}
      {evolve.data && (
        <div className="mb-8 p-4 border rounded-lg bg-green-50">
          <p className="font-medium text-green-800">
            {evolve.data.corrections_analyzed}件の修正ログから
            {evolve.data.preferences_created}件の好みを学習しました
          </p>
        </div>
      )}

      {/* 手動追加フォーム */}
      {showAddForm && (
        <form onSubmit={handleCreate} className="mb-8 p-4 border rounded-lg bg-muted/50">
          <h3 className="font-medium mb-4">好みを手動で追加</h3>
          <div className="grid gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">説明</label>
              <input
                type="text"
                value={newPref.description}
                onChange={(e) => setNewPref({ ...newPref, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="例: コードブロックではダークテーマを使用"
                required
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">カテゴリ</label>
                <select
                  value={newPref.category}
                  onChange={(e) => setNewPref({ ...newPref, category: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="style">スタイル</option>
                  <option value="structural">構造</option>
                  <option value="content">コンテンツ</option>
                  <option value="technical">技術</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">スコープ</label>
                <select
                  value={newPref.scope}
                  onChange={(e) => setNewPref({ ...newPref, scope: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="global">グローバル</option>
                  <option value="section_type">セクションタイプ</option>
                  <option value="project">プロジェクト</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">確信度</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={newPref.confidence}
                  onChange={(e) => setNewPref({ ...newPref, confidence: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <span className="text-sm text-muted-foreground">{Math.round(newPref.confidence * 100)}%</span>
              </div>
            </div>
            {newPref.scope === "section_type" && (
              <div>
                <label className="block text-sm font-medium mb-1">セクションタイプ</label>
                <select
                  value={newPref.section_type}
                  onChange={(e) => setNewPref({ ...newPref, section_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="">選択してください</option>
                  <option value="title">タイトル</option>
                  <option value="slide">スライド</option>
                  <option value="code">コード</option>
                  <option value="summary">まとめ</option>
                </select>
              </div>
            )}
            <div className="flex gap-2">
              <Button type="submit" disabled={createPref.isPending}>
                {createPref.isPending ? "追加中..." : "追加"}
              </Button>
              <Button type="button" variant="outline" onClick={() => setShowAddForm(false)}>
                キャンセル
              </Button>
            </div>
          </div>
        </form>
      )}

      {/* 好み一覧 */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">学習済みの好み</h2>

        {!preferences?.length ? (
          <div className="text-center py-12 border rounded-lg">
            <p className="text-muted-foreground mb-4">
              まだ好みが登録されていません
            </p>
            <p className="text-sm text-muted-foreground">
              「好みを学習」ボタンを押すと、修正履歴から自動で好みを推論します
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {preferences.map((pref) => (
              <div
                key={pref.preference_id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50"
              >
                <div className="flex-1">
                  <p className="font-medium">{pref.description}</p>
                  <div className="flex gap-2 mt-2">
                    <CategoryBadge category={pref.category} />
                    <ScopeBadge scope={pref.scope} sectionType={pref.section_type} />
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <ConfidenceBadge confidence={pref.confidence} />
                  <DeleteConfirmButton
                    onConfirm={() => handleDelete(pref.preference_id)}
                    isPending={deletePref.isPending}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 修正ログ統計 */}
      {stats && stats.total > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">修正ログ統計</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="border rounded-lg p-4">
              <h3 className="font-medium mb-2">ステージ別</h3>
              <div className="space-y-1">
                {Object.entries(stats.by_stage).map(([stage, count]) => (
                  <div key={stage} className="flex justify-between text-sm">
                    <span>{stage}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="border rounded-lg p-4">
              <h3 className="font-medium mb-2">カテゴリ別</h3>
              <div className="space-y-1">
                {Object.entries(stats.by_category).map(([category, count]) => (
                  <div key={category} className="flex justify-between text-sm">
                    <span>{category}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
