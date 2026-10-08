/** Transient state of the assistant: the request in flight and the proposal awaiting a decision. */
import { create } from "zustand";

import type { ProposalProgress } from "@/services/api/stream";
import type { GenerationJobRead, ProposalRead } from "@/services/api/types";

export type AssistantStatus = "idle" | "thinking" | "applying";

interface ChatState {
  status: AssistantStatus;
  /** The user's message while the model is working (the server has it; the list has not refetched). */
  pendingMessage: string | null;
  /** What the server says it is doing right now. */
  progress: ProposalProgress | null;
  /** The generation job being followed, as last reported by the server. */
  job: GenerationJobRead | null;
  /** The instruction that produced the current proposal; recorded with the saved version. */
  instruction: string | null;
  proposal: ProposalRead | null;
  /** Which steps of a 'mutate' proposal the user has kept (parallel to `proposal.steps`). */
  acceptedSteps: boolean[];
  error: string | null;
  /** Text to place in the input (used by suggestions and "ask about this"). */
  draft: string;
  /** Incremented to ask the input to take focus. */
  focusToken: number;

  startRequest: (message: string) => void;
  setProgress: (progress: ProposalProgress) => void;
  setJob: (job: GenerationJobRead) => void;
  /** Stop showing a request that ended without a proposal or an error (it was cancelled). */
  settle: () => void;
  receiveProposal: (proposal: ProposalRead) => void;
  toggleStep: (index: number) => void;
  setStatus: (status: AssistantStatus) => void;
  fail: (message: string) => void;
  clearProposal: () => void;
  clearError: () => void;
  setDraft: (draft: string) => void;
  requestFocus: () => void;
  reset: () => void;
}

const INITIAL = {
  status: "idle",
  pendingMessage: null,
  progress: null,
  job: null,
  instruction: null,
  proposal: null,
  acceptedSteps: [],
  error: null,
  draft: "",
  focusToken: 0,
} as const satisfies Partial<ChatState>;

export const useChatStore = create<ChatState>((set) => ({
  ...INITIAL,
  startRequest: (pendingMessage) =>
    set({
      status: "thinking",
      pendingMessage,
      progress: null,
      job: null,
      instruction: pendingMessage,
      proposal: null,
      acceptedSteps: [],
      error: null,
    }),
  receiveProposal: (proposal) =>
    set({
      status: "idle",
      pendingMessage: null,
      progress: null,
      job: null,
      proposal,
      acceptedSteps: proposal.steps.map(() => true),
    }),
  toggleStep: (index) =>
    set((state) => ({
      acceptedSteps: state.acceptedSteps.map((kept, i) => (i === index ? !kept : kept)),
    })),
  setStatus: (status) => set({ status }),
  setProgress: (progress) => set({ progress }),
  setJob: (job) => set({ job }),
  settle: () => set({ status: "idle", pendingMessage: null, progress: null, job: null }),
  fail: (error) => set({ status: "idle", pendingMessage: null, progress: null, job: null, error }),
  clearProposal: () => set({ proposal: null, acceptedSteps: [] }),
  clearError: () => set({ error: null }),
  setDraft: (draft) => set({ draft }),
  requestFocus: () => set((state) => ({ focusToken: state.focusToken + 1 })),
  reset: () => set({ ...INITIAL, acceptedSteps: [] }),
}));
