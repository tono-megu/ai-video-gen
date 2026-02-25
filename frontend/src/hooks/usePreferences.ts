/**
 * 好み・フィードバック関連のカスタムフック
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// 型定義
interface Preference {
  preference_id: string;
  description: string;
  category: string;
  scope: string;
  section_type?: string;
  project_id?: string;
  confidence: number;
  is_active: boolean;
  created_at: string;
}

interface PreferenceProfile {
  total_preferences: number;
  by_category: Record<string, number>;
  by_scope: Record<string, number>;
  high_confidence: Array<{
    id: string;
    description: string;
    confidence: number;
  }>;
  suggestions: Array<{
    id: string;
    description: string;
    confidence: number;
  }>;
}

interface Correction {
  event_id: string;
  project_id: string;
  section_id?: string;
  stage: string;
  category: string;
  field_path: string;
  prior_value?: string;
  new_value?: string;
  user_feedback?: string;
  visual_diff_description?: string;
  created_at: string;
}

interface CorrectionStats {
  total: number;
  by_stage: Record<string, number>;
  by_category: Record<string, number>;
}

// API関数
async function getPreferences(params?: {
  scope?: string;
  category?: string;
  min_confidence?: number;
}): Promise<Preference[]> {
  const searchParams = new URLSearchParams();
  if (params?.scope) searchParams.set("scope", params.scope);
  if (params?.category) searchParams.set("category", params.category);
  if (params?.min_confidence)
    searchParams.set("min_confidence", params.min_confidence.toString());

  const response = await fetch(
    `${API_URL}/api/feedback/preferences?${searchParams.toString()}`
  );
  if (!response.ok) throw new Error("Failed to fetch preferences");
  return response.json();
}

async function getPreferenceProfile(): Promise<PreferenceProfile> {
  const response = await fetch(`${API_URL}/api/feedback/preferences/profile`);
  if (!response.ok) throw new Error("Failed to fetch preference profile");
  return response.json();
}

async function createPreference(data: {
  description: string;
  category: string;
  scope?: string;
  section_type?: string;
  confidence?: number;
}): Promise<{ status: string; preference: Preference }> {
  const response = await fetch(`${API_URL}/api/feedback/preferences`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to create preference");
  return response.json();
}

async function updatePreference(
  id: string,
  data: {
    description?: string;
    confidence?: number;
    is_active?: boolean;
  }
): Promise<{ status: string; preference: Preference }> {
  const response = await fetch(`${API_URL}/api/feedback/preferences/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to update preference");
  return response.json();
}

async function deletePreference(
  id: string
): Promise<{ status: string }> {
  const response = await fetch(`${API_URL}/api/feedback/preferences/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Failed to delete preference");
  return response.json();
}

async function evolvePreferences(
  limit?: number
): Promise<{
  status: string;
  corrections_analyzed: number;
  preferences_created: number;
  preferences: Preference[];
}> {
  const response = await fetch(`${API_URL}/api/feedback/preferences/evolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ limit: limit || 50 }),
  });
  if (!response.ok) throw new Error("Failed to evolve preferences");
  return response.json();
}

async function getCorrections(params?: {
  project_id?: string;
  stage?: string;
  category?: string;
  limit?: number;
}): Promise<Correction[]> {
  const searchParams = new URLSearchParams();
  if (params?.project_id) searchParams.set("project_id", params.project_id);
  if (params?.stage) searchParams.set("stage", params.stage);
  if (params?.category) searchParams.set("category", params.category);
  if (params?.limit) searchParams.set("limit", params.limit.toString());

  const response = await fetch(
    `${API_URL}/api/feedback/corrections?${searchParams.toString()}`
  );
  if (!response.ok) throw new Error("Failed to fetch corrections");
  return response.json();
}

async function getCorrectionStats(): Promise<CorrectionStats> {
  const response = await fetch(`${API_URL}/api/feedback/corrections/stats`);
  if (!response.ok) throw new Error("Failed to fetch correction stats");
  return response.json();
}

async function recordCorrection(data: {
  project_id: string;
  section_id?: string;
  stage: string;
  category: string;
  field_path: string;
  prior_value?: string;
  new_value?: string;
  user_feedback?: string;
}): Promise<{ status: string; event: Correction }> {
  const response = await fetch(`${API_URL}/api/feedback/corrections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error("Failed to record correction");
  return response.json();
}

// Hooks
export function usePreferences(params?: {
  scope?: string;
  category?: string;
  min_confidence?: number;
}) {
  return useQuery({
    queryKey: ["preferences", params],
    queryFn: () => getPreferences(params),
  });
}

export function usePreferenceProfile() {
  return useQuery({
    queryKey: ["preference-profile"],
    queryFn: getPreferenceProfile,
  });
}

export function useCreatePreference() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createPreference,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
      queryClient.invalidateQueries({ queryKey: ["preference-profile"] });
    },
  });
}

export function useUpdatePreference() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof updatePreference>[1] }) =>
      updatePreference(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
      queryClient.invalidateQueries({ queryKey: ["preference-profile"] });
    },
  });
}

export function useDeletePreference() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deletePreference,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
      queryClient.invalidateQueries({ queryKey: ["preference-profile"] });
    },
  });
}

export function useEvolvePreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: evolvePreferences,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
      queryClient.invalidateQueries({ queryKey: ["preference-profile"] });
    },
  });
}

export function useCorrections(params?: {
  project_id?: string;
  stage?: string;
  category?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["corrections", params],
    queryFn: () => getCorrections(params),
  });
}

export function useCorrectionStats() {
  return useQuery({
    queryKey: ["correction-stats"],
    queryFn: getCorrectionStats,
  });
}

export function useRecordCorrection() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: recordCorrection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["corrections"] });
      queryClient.invalidateQueries({ queryKey: ["correction-stats"] });
    },
  });
}
