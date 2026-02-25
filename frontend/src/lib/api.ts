/**
 * APIクライアント
 */

import type { Project, ProjectCreate, ProjectUpdate } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      error.detail || `HTTP error ${response.status}`
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Projects API
export const projectsApi = {
  list: () => fetchApi<Project[]>("/api/projects"),

  get: (id: string) => fetchApi<Project>(`/api/projects/${id}`),

  create: (data: ProjectCreate) =>
    fetchApi<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: string, data: ProjectUpdate) =>
    fetchApi<Project>(`/api/projects/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    fetchApi<void>(`/api/projects/${id}`, {
      method: "DELETE",
    }),
};
