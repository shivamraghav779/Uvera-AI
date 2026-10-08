/**
 * State of the open workspace's UI.
 *
 *   base     the current version as stored by the server (source of truth)
 *   history  the working copy plus undo/redo of unsaved edits
 *   preview  a proposal or old version being looked at, never editable
 *
 * Natural-language edits and direct manipulation both end up here as
 * operations, applied through the same validated path. Nothing in this store
 * is persisted in the browser: a reload re-reads everything from the API.
 */
import { create } from "zustand";

import {
  canRedo,
  canUndo,
  createHistory,
  isDirty,
  pushEdit,
  redo,
  undo,
  type EditHistory,
} from "@/generative-ui/history/editHistory";
import type { CanvasPreview, LoadedVersion } from "@/generative-ui/history/versionTypes";
import type { Operation } from "@/generative-ui/mutation/mutationTypes";
import { applyValidated, type ValidationEnvironment } from "@/generative-ui/mutation/mutationValidator";
import { parseDocument, shareStructure } from "@/generative-ui/schema/normalization";
import type { DataMap, UIDocument, ValidationIssue, ValidationResult } from "@/generative-ui/schema/types";
import { dataMapSchema } from "@/generative-ui/schema/validators";

export interface IncomingVersion {
  id: string;
  version_number: number;
  document: unknown;
  data?: unknown;
}

interface WorkspaceState {
  workspaceId: string | null;
  base: LoadedVersion | null;
  history: EditHistory | null;
  preview: CanvasPreview | null;
  /** Why the current version could not be displayed, if it could not. */
  loadIssues: ValidationIssue[] | null;

  /** Start (or switch to) a workspace with nothing loaded yet. */
  open: (workspaceId: string) => void;
  /** Adopt a version from the server as the new base. Returns false if it is invalid. */
  hydrate: (workspaceId: string, version: IncomingVersion) => boolean;
  /** Apply operations to the working copy. The state changes only if the result is valid. */
  applyOperations: (
    operations: Operation[],
    environment?: ValidationEnvironment,
  ) => ValidationResult<UIDocument>;
  undo: () => void;
  redo: () => void;
  /** Drop unsaved edits and return to the base version. */
  discard: () => void;
  setPreview: (preview: CanvasPreview | null) => void;
}

function parseData(input: unknown): DataMap {
  const parsed = dataMapSchema.safeParse(input ?? {});
  return parsed.success ? parsed.data : {};
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  workspaceId: null,
  base: null,
  history: null,
  preview: null,
  loadIssues: null,

  open: (workspaceId) => {
    if (get().workspaceId === workspaceId) return;
    set({ workspaceId, base: null, history: null, preview: null, loadIssues: null });
  },

  hydrate: (workspaceId, version) => {
    const parsed = parseDocument(version.document);
    if (!parsed.ok) {
      // Keep whatever valid state is on screen; report instead of rendering garbage.
      set({ workspaceId, loadIssues: parsed.issues });
      return false;
    }
    const previous = get().base?.document;
    const document = shareStructure(previous, parsed.value);
    set({
      workspaceId,
      base: { id: version.id, number: version.version_number, document, data: parseData(version.data) },
      history: createHistory(document),
      preview: null,
      loadIssues: null,
    });
    return true;
  },

  applyOperations: (operations, environment) => {
    const { history } = get();
    if (!history) {
      return { ok: false, issues: [{ stage: "operation", path: "", message: "No UI is loaded." }] };
    }
    const result = applyValidated(history.present.document, operations, environment);
    if (result.ok) {
      const document = shareStructure(history.present.document, result.value);
      set({ history: pushEdit(history, document, operations) });
      return { ok: true, value: document };
    }
    return result;
  },

  undo: () => set((state) => (state.history ? { history: undo(state.history) } : state)),
  redo: () => set((state) => (state.history ? { history: redo(state.history) } : state)),
  discard: () =>
    set((state) => (state.base ? { history: createHistory(state.base.document) } : state)),
  setPreview: (preview) => set({ preview }),
}));

// --- Selectors -----------------------------------------------------------------

export const selectDraft = (state: WorkspaceState): UIDocument | null =>
  state.history?.present.document ?? null;
export const selectPendingOperations = (state: WorkspaceState): Operation[] =>
  state.history?.present.operations ?? EMPTY_OPERATIONS;
export const selectIsDirty = (state: WorkspaceState): boolean =>
  state.history ? isDirty(state.history) : false;
export const selectCanUndo = (state: WorkspaceState): boolean =>
  state.history ? canUndo(state.history) : false;
export const selectCanRedo = (state: WorkspaceState): boolean =>
  state.history ? canRedo(state.history) : false;

const EMPTY_OPERATIONS: Operation[] = [];
