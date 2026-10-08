import { apiRequest } from "./client";
import type { GenerationJobCreate, GenerationJobRead } from "./types";

/**
 * Generation runs as a background job on the server. A client starts one and
 * polls it; closing the tab loses nothing, because the job and its result
 * (a proposal, never a saved version) stay on the server.
 */
export const generationApi = {
  start: (body: GenerationJobCreate) =>
    apiRequest<GenerationJobRead>("/generation/jobs", { method: "POST", body }),
  get: (jobId: string, signal?: AbortSignal) =>
    apiRequest<GenerationJobRead>(`/generation/jobs/${jobId}`, { signal }),
  /** The workspace's most recent job, or `null`. Used to resume after a reload. */
  latest: (workspaceId: string, signal?: AbortSignal) =>
    apiRequest<GenerationJobRead | null>("/generation/jobs", { query: { workspace_id: workspaceId }, signal }),
  cancel: (jobId: string) => apiRequest<GenerationJobRead>(`/generation/jobs/${jobId}/cancel`, { method: "POST" }),
};
