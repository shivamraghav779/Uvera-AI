import { apiRequest } from "./client";
import type { MessageRead } from "./types";

export const conversationsApi = {
  list: (workspaceId: string, signal?: AbortSignal) =>
    apiRequest<MessageRead[]>(`/workspaces/${workspaceId}/messages`, { query: { limit: 200 }, signal }),
};
