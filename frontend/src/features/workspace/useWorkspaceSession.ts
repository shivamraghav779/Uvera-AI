/**
 * Loads a workspace the way the product promises it loads:
 *   identify workspace -> fetch current version -> validate schema ->
 *   hydrate the workspace store -> render.
 * The browser keeps nothing between visits; this runs from the API every time.
 */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect } from "react";

import { queryKeys } from "@/services/api/queryKeys";
import { versionsApi } from "@/services/api/versions";
import { workspacesApi } from "@/services/api/workspaces";
import { useChatStore } from "@/stores/chatStore";
import { useEditorStore } from "@/stores/editorStore";
import { selectIsDirty, useWorkspaceStore } from "@/stores/workspaceStore";

import { useWorkspace } from "./queries";

export type SessionStatus = "loading" | "error" | "empty" | "invalid" | "ready";

export function useWorkspaceSession(workspaceId: string) {
  const queryClient = useQueryClient();
  const workspace = useWorkspace(workspaceId);
  const currentVersionId = workspace.data?.current_version_id ?? null;

  const version = useQuery({
    queryKey: queryKeys.version(workspaceId, currentVersionId ?? "none"),
    queryFn: ({ signal }) => versionsApi.get(workspaceId, currentVersionId!, signal),
    enabled: currentVersionId !== null,
    // A stored version never changes.
    staleTime: Infinity,
  });

  const baseId = useWorkspaceStore((state) => (state.workspaceId === workspaceId ? state.base?.id : null));
  const loadIssues = useWorkspaceStore((state) => state.loadIssues);

  // Entering a workspace starts from a clean slate.
  useEffect(() => {
    useWorkspaceStore.getState().open(workspaceId);
    useEditorStore.getState().reset();
    useChatStore.getState().reset();
  }, [workspaceId]);

  useEffect(() => {
    const incoming = version.data;
    if (!incoming) return;
    const state = useWorkspaceStore.getState();
    if (state.workspaceId === workspaceId && state.base?.id === incoming.id) return;
    const hasLocalWork = selectIsDirty(state) || useChatStore.getState().proposal !== null;
    if (state.base && hasLocalWork) {
      // Someone else moved the workspace on. Ask instead of discarding local work.
      useEditorStore.getState().setConflict({ currentVersionNumber: incoming.version_number });
      return;
    }
    state.hydrate(workspaceId, incoming);
  }, [version.data, workspaceId]);

  /** Drop local work and adopt whatever the server now has. */
  const reloadLatest = useCallback(async () => {
    useChatStore.getState().reset();
    useEditorStore.getState().setConflict(null);
    const latest = await queryClient.fetchQuery({
      queryKey: queryKeys.workspace(workspaceId),
      queryFn: () => workspacesApi.get(workspaceId),
      staleTime: 0,
    });
    if (!latest.current_version_id) return;
    const detail = await queryClient.fetchQuery({
      queryKey: queryKeys.version(workspaceId, latest.current_version_id),
      queryFn: () => versionsApi.get(workspaceId, latest.current_version_id!),
      staleTime: Infinity,
    });
    useWorkspaceStore.getState().hydrate(workspaceId, detail);
    void queryClient.invalidateQueries({ queryKey: queryKeys.versions(workspaceId), exact: true });
    void queryClient.invalidateQueries({ queryKey: queryKeys.messages(workspaceId), exact: true });
  }, [queryClient, workspaceId]);

  let status: SessionStatus;
  if (workspace.isError || version.isError) status = "error";
  else if (workspace.isPending) status = "loading";
  else if (currentVersionId === null) status = "empty";
  else if (baseId) status = "ready";
  else if (loadIssues) status = "invalid";
  else status = "loading";

  return {
    status,
    workspace: workspace.data,
    error: workspace.error ?? version.error,
    loadIssues,
    retry: () => {
      void workspace.refetch();
      if (currentVersionId) void version.refetch();
    },
    reloadLatest,
  };
}

