/**
 * Writing versions. Every write names the version it was prepared against;
 * when the server says that base is stale, the user is asked to reload instead
 * of anything being overwritten.
 */
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import { summariseOperations } from "@/generative-ui/mutation/mutationPreview";
import { isApiError } from "@/services/api/client";
import { queryKeys } from "@/services/api/queryKeys";
import type { VersionCreate, VersionDetail, WorkspaceRead } from "@/services/api/types";
import { versionsApi } from "@/services/api/versions";
import { useChatStore } from "@/stores/chatStore";
import { useEditorStore } from "@/stores/editorStore";
import { toast } from "@/stores/toastStore";
import { selectPendingOperations, useWorkspaceStore } from "@/stores/workspaceStore";

/** Make a version returned by the server the current state everywhere. */
export function useAdoptVersion(workspaceId: string) {
  const queryClient = useQueryClient();
  return useCallback(
    (version: VersionDetail) => {
      queryClient.setQueryData(queryKeys.version(workspaceId, version.id), version);
      queryClient.setQueryData<WorkspaceRead>(queryKeys.workspace(workspaceId), (workspace) =>
        workspace
          ? { ...workspace, current_version_id: version.id, current_version_number: version.version_number }
          : workspace,
      );
      useWorkspaceStore.getState().hydrate(workspaceId, version);
      void queryClient.invalidateQueries({ queryKey: queryKeys.versions(workspaceId), exact: true });
      void queryClient.invalidateQueries({ queryKey: queryKeys.workspace(workspaceId), exact: true });
      void queryClient.invalidateQueries({ queryKey: queryKeys.workspaces, exact: true });
    },
    [queryClient, workspaceId],
  );
}

/** Report a failed write. A stale base opens the conflict dialog. */
export function reportWriteError(error: unknown): void {
  if (isApiError(error, "VERSION_CONFLICT")) {
    const current = error.details[0]?.current_version_number;
    useEditorStore.getState().setConflict({
      currentVersionNumber: typeof current === "number" ? current : null,
    });
    return;
  }
  toast.error(isApiError(error) ? error.message : "The change could not be saved.");
}

export function useCreateVersion(workspaceId: string) {
  const adopt = useAdoptVersion(workspaceId);
  return useMutation({
    mutationFn: (body: VersionCreate) => versionsApi.create(workspaceId, body),
    onSuccess: (version) => {
      adopt(version);
      toast.success(`Saved as version ${version.version_number}.`);
    },
    onError: reportWriteError,
  });
}

/** Save the editor's unsaved operations as a new version. */
export function useSaveEdits(workspaceId: string) {
  const create = useCreateVersion(workspaceId);
  const save = useCallback(() => {
    const state = useWorkspaceStore.getState();
    const operations = selectPendingOperations(state);
    if (!state.base || operations.length === 0) return;
    create.mutate({
      base_version_id: state.base.id,
      source: "manual_edit",
      description: summariseOperations(operations, state.base.document).slice(0, 300),
      operations: operations as VersionCreate["operations"],
    });
  }, [create]);
  return { save, isSaving: create.isPending };
}

export function useRestoreVersion(workspaceId: string) {
  const adopt = useAdoptVersion(workspaceId);
  return useMutation({
    mutationFn: ({ versionId, proposalId }: { versionId: string; proposalId?: string }) => {
      const base = useWorkspaceStore.getState().base;
      if (!base) throw new Error("No current version to restore from.");
      return versionsApi.restore(workspaceId, versionId, base.id, proposalId);
    },
    onSuccess: (version) => {
      adopt(version);
      useChatStore.getState().clearProposal();
      toast.success(`${version.description} — now version ${version.version_number}.`);
    },
    onError: reportWriteError,
  });
}
