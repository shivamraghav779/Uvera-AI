import { AI_TIMEOUT_MS, apiRequest } from "./client";
import { requestProposalStream, type ProposalProgress } from "./stream";
import type {
  Capabilities,
  ComponentCatalog,
  FrameworkCatalog,
  GenerateUIRequest,
  MutateUIRequest,
  ProposalRead,
  ThemeCatalog,
} from "./types";

export const uiApi = {
  /** Ask for a new UI. Returns a proposal; nothing is saved. */
  generate: (body: GenerateUIRequest) =>
    apiRequest<ProposalRead>("/ui/generate", { method: "POST", body, timeoutMs: AI_TIMEOUT_MS }),
  /** Ask for changes to the current UI. Returns a proposal; nothing is saved. */
  mutate: (body: MutateUIRequest) =>
    apiRequest<ProposalRead>("/ui/mutate", { method: "POST", body, timeoutMs: AI_TIMEOUT_MS }),
  /** `generate`, reporting progress while the model works. */
  generateStream: (body: GenerateUIRequest, onProgress: (progress: ProposalProgress) => void) =>
    requestProposalStream("/ui/generate/stream", body, onProgress),
  /** `mutate` with an instruction, reporting progress while the model works. */
  mutateStream: (
    body: MutateUIRequest,
    onProgress: (progress: ProposalProgress) => void,
    timeoutMs?: number,
  ) => requestProposalStream("/ui/mutate/stream", body, onProgress, timeoutMs),
  components: (signal?: AbortSignal) => apiRequest<ComponentCatalog>("/ui/components", { signal }),
  frameworks: (signal?: AbortSignal) => apiRequest<FrameworkCatalog>("/ui/frameworks", { signal }),
  themes: (signal?: AbortSignal) => apiRequest<ThemeCatalog>("/ui/themes", { signal }),
  capabilities: (signal?: AbortSignal) => apiRequest<Capabilities>("/ui/capabilities", { signal }),
};
