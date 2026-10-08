import { apiRequest } from "./client";
import type { WorkspaceRead } from "./types";

export const workspacesApi = {
  list: (signal?: AbortSignal) => apiRequest<WorkspaceRead[]>("/workspaces", { signal }),
  get: (workspaceId: string, signal?: AbortSignal) =>
    apiRequest<WorkspaceRead>(`/workspaces/${workspaceId}`, { signal }),
  create: (title?: string) =>
    apiRequest<WorkspaceRead>("/workspaces", { method: "POST", body: title ? { title } : {} }),
  rename: (workspaceId: string, title: string) =>
    apiRequest<WorkspaceRead>(`/workspaces/${workspaceId}`, { method: "PATCH", body: { title } }),
  remove: (workspaceId: string) =>
    apiRequest<void>(`/workspaces/${workspaceId}`, { method: "DELETE" }),
};
