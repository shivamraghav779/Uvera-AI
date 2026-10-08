import { apiRequest } from "./client";
import type { VersionComparison, VersionCreate, VersionDetail, VersionSummary } from "./types";

export const versionsApi = {
  list: (workspaceId: string, signal?: AbortSignal) =>
    apiRequest<VersionSummary[]>(`/workspaces/${workspaceId}/versions`, { signal }),
  get: (workspaceId: string, versionId: string, signal?: AbortSignal) =>
    apiRequest<VersionDetail>(`/workspaces/${workspaceId}/versions/${versionId}`, { signal }),
  /** Persist an approved change. Fails with VERSION_CONFLICT when the base is stale. */
  create: (workspaceId: string, body: VersionCreate) =>
    apiRequest<VersionDetail>(`/workspaces/${workspaceId}/versions`, { method: "POST", body }),
  /** Make an old version current by appending a copy; history is never rewritten. */
  restore: (workspaceId: string, versionId: string, baseVersionId: string, proposalId?: string) =>
    apiRequest<VersionDetail>(`/workspaces/${workspaceId}/versions/${versionId}/restore`, {
      method: "POST",
      body: { base_version_id: baseVersionId, proposal_id: proposalId },
    }),
  compare: (workspaceId: string, versionId: string, withVersionId?: string, signal?: AbortSignal) =>
    apiRequest<VersionComparison>(`/workspaces/${workspaceId}/versions/${versionId}/compare`, {
      query: { with: withVersionId },
      signal,
    }),
};
