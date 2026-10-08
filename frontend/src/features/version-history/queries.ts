import { useQuery } from "@tanstack/react-query";

import { queryKeys } from "@/services/api/queryKeys";
import { versionsApi } from "@/services/api/versions";

export function useVersions(workspaceId: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.versions(workspaceId),
    queryFn: ({ signal }) => versionsApi.list(workspaceId, signal),
    enabled,
  });
}

/** Changes that turn `versionId` into the current version. */
export function useComparison(workspaceId: string, versionId: string | null) {
  return useQuery({
    queryKey: queryKeys.comparison(workspaceId, versionId ?? "none", undefined),
    queryFn: ({ signal }) => versionsApi.compare(workspaceId, versionId!, undefined, signal),
    enabled: versionId !== null,
  });
}
