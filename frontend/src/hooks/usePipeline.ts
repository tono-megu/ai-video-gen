/**
 * パイプライン関連のカスタムフック
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Script API
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

// Visuals API
interface SlideResponse {
  section_id: string;
  section_index: number;
  type: string;
  slide_url?: string;
  visual_spec?: Record<string, unknown>;
  narration?: string;
}

interface VisualsResponse {
  slides: SlideResponse[];
  message: string;
}

async function generateVisualsApi(projectId: string): Promise<VisualsResponse> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/generate-visuals`, {
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

async function regenerateSlideApi(
  projectId: string,
  sectionId: string,
  visualSpec?: Record<string, unknown>
): Promise<SlideResponse> {
  const response = await fetch(
    `${API_URL}/api/projects/${projectId}/sections/${sectionId}/slide/regenerate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: visualSpec ? JSON.stringify({ visual_spec: visualSpec }) : undefined,
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP error ${response.status}`);
  }

  return response.json();
}

// Script Hooks
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

// Visuals Hooks
export function useGenerateVisuals() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => generateVisualsApi(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

export function useRegenerateSlide() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      sectionId,
      visualSpec,
    }: {
      projectId: string;
      sectionId: string;
      visualSpec?: Record<string, unknown>;
    }) => regenerateSlideApi(projectId, sectionId, visualSpec),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
    },
  });
}

// Narration API
interface NarrationResponse {
  section_id: string;
  section_index: number;
  status: string;
  duration?: number;
  audio_url?: string;
  message?: string;
}

interface NarrationsResponse {
  narrations: NarrationResponse[];
  message: string;
}

async function generateNarrationsApi(projectId: string): Promise<NarrationsResponse> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/generate-narration`, {
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

// Narration Hooks
export function useGenerateNarrations() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => generateNarrationsApi(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

// Compose API
interface ComposeStatusResponse {
  project_id: string;
  state: string;
  is_composed: boolean;
  can_compose: boolean;
  ffmpeg_available: boolean;
  sections_count: number;
  total_duration: number;
  estimated_size: number;
}

interface ComposeResponse {
  status: string;
  video_url?: string;
  duration: number;
  sections_count: number;
  estimated_size: number;
  message?: string;
}

async function getComposeStatusApi(projectId: string): Promise<ComposeStatusResponse> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/compose/status`, {
    method: "GET",
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

async function composeVideoApi(projectId: string): Promise<ComposeResponse> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/compose`, {
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

// Compose Hooks
export function useComposeStatus(projectId: string) {
  return useQuery({
    queryKey: ["compose-status", projectId],
    queryFn: () => getComposeStatusApi(projectId),
    enabled: !!projectId,
  });
}

export function useComposeVideo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (projectId: string) => composeVideoApi(projectId),
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({ queryKey: ["projects", projectId] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["compose-status", projectId] });
    },
  });
}
