/**
 * パイプライン関連のカスタムフック
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function generateScriptApi(projectId: string): Promise<{ script: Record<string, unknown>; message: string }> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/generate-script`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}

async function updateScriptApi(
  projectId: string,
  script: Record<string, unknown>
): Promise<{ script: Record<string, unknown>; message: string }> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/script`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ script }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}

export function useGenerateScript() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => generateScriptApi(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useUpdateScript() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ projectId, script }: { projectId: string; script: Record<string, unknown> }) =>
      updateScriptApi(projectId, script),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
