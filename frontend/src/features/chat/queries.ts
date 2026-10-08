import { useQuery } from "@tanstack/react-query";

import { conversationsApi } from "@/services/api/conversations";
import { queryKeys } from "@/services/api/queryKeys";

export function useMessages(workspaceId: string) {
  return useQuery({
    queryKey: queryKeys.messages(workspaceId),
    queryFn: ({ signal }) => conversationsApi.list(workspaceId, signal),
  });
}
