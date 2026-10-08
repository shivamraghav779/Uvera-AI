import { apiRequest } from "./client";
import type { ActionExecuteResponse } from "./types";

export const actionsApi = {
  /** Run one allowlisted action. The backend rejects anything not registered. */
  execute: (workspaceId: string, actionType: string, payload: Record<string, unknown>) =>
    apiRequest<ActionExecuteResponse>("/actions/execute", {
      method: "POST",
      body: { workspace_id: workspaceId, action_type: actionType, payload },
    }),
};
