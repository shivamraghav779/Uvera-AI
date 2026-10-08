/** Query keys in one place so invalidation cannot miss a spelling. */
export const queryKeys = {
  workspaces: ["workspaces"] as const,
  workspace: (workspaceId: string) => ["workspaces", workspaceId] as const,
  versions: (workspaceId: string) => ["workspaces", workspaceId, "versions"] as const,
  version: (workspaceId: string, versionId: string) =>
    ["workspaces", workspaceId, "versions", versionId] as const,
  comparison: (workspaceId: string, versionId: string, withVersionId: string | undefined) =>
    ["workspaces", workspaceId, "versions", versionId, "compare", withVersionId ?? "current"] as const,
  latestJob: (workspaceId: string) => ["workspaces", workspaceId, "latest-job"] as const,
  messages: (workspaceId: string) => ["workspaces", workspaceId, "messages"] as const,
  themes: ["ui", "themes"] as const,
  frameworks: ["ui", "frameworks"] as const,
  capabilities: ["ui", "capabilities"] as const,
  dataSources: ["data-sources"] as const,
  datasets: ["data-sources", "datasets"] as const,
  authConfig: ["auth", "config"] as const,
};
