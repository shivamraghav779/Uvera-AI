import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";

import type { ValidationEnvironment } from "@/generative-ui/mutation/mutationValidator";
import { usableFrameworkIds } from "@/generative-ui/registry/capabilityRegistry";
import { queryKeys } from "@/services/api/queryKeys";
import { uiApi } from "@/services/api/ui";
import { workspacesApi } from "@/services/api/workspaces";

export function useWorkspaces() {
  return useQuery({ queryKey: queryKeys.workspaces, queryFn: ({ signal }) => workspacesApi.list(signal) });
}

export function useWorkspace(workspaceId: string) {
  return useQuery({
    queryKey: queryKeys.workspace(workspaceId),
    queryFn: ({ signal }) => workspacesApi.get(workspaceId, signal),
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (title?: string) => workspacesApi.create(title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.workspaces }),
  });
}

export function useRenameWorkspace(workspaceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (title: string) => workspacesApi.rename(workspaceId, title),
    onSuccess: (workspace) => {
      queryClient.setQueryData(queryKeys.workspace(workspaceId), workspace);
      void queryClient.invalidateQueries({ queryKey: queryKeys.workspaces, exact: true });
    },
  });
}

export function useDeleteWorkspace() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (workspaceId: string) => workspacesApi.remove(workspaceId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.workspaces, exact: true }),
  });
}

// The catalogues only change when the backend is redeployed.
const CATALOGUE = { staleTime: Infinity } as const;

export function useThemeCatalog() {
  return useQuery({ queryKey: queryKeys.themes, queryFn: ({ signal }) => uiApi.themes(signal), ...CATALOGUE });
}

export function useFrameworkCatalog() {
  return useQuery({
    queryKey: queryKeys.frameworks,
    queryFn: ({ signal }) => uiApi.frameworks(signal),
    ...CATALOGUE,
  });
}

export function useCapabilities() {
  return useQuery({
    queryKey: queryKeys.capabilities,
    queryFn: ({ signal }) => uiApi.capabilities(signal),
    ...CATALOGUE,
  });
}

/** What local validation may accept: frameworks with an adapter here, registered design systems. */
export function useValidationEnvironment(): ValidationEnvironment {
  const { data: catalog } = useFrameworkCatalog();
  return useMemo(
    () => ({
      frameworks: usableFrameworkIds(catalog),
      designSystems: catalog?.design_systems.map((system) => system.id),
    }),
    [catalog],
  );
}
