/**
 * Undo/redo for unsaved edits in the editor.
 *
 * This is deliberately separate from version history: it lives in memory, covers
 * only the edits made since the last saved version, and is cleared when a
 * version is saved or loaded. Persistent history is the backend's UIVersions.
 */
import type { Operation } from "../mutation/mutationTypes";
import type { UIDocument } from "../schema/types";

export const HISTORY_LIMIT = 100;

export interface EditSnapshot {
  document: UIDocument;
  /** Every operation applied since the saved version, in order. */
  operations: Operation[];
}

export interface EditHistory {
  past: EditSnapshot[];
  present: EditSnapshot;
  future: EditSnapshot[];
}

export function createHistory(document: UIDocument): EditHistory {
  return { past: [], present: { document, operations: [] }, future: [] };
}

/** Record a new state. Anything that had been undone can no longer be redone. */
export function pushEdit(history: EditHistory, document: UIDocument, applied: Operation[]): EditHistory {
  return {
    past: [...history.past, history.present].slice(-HISTORY_LIMIT),
    present: { document, operations: [...history.present.operations, ...applied] },
    future: [],
  };
}

export function undo(history: EditHistory): EditHistory {
  const previous = history.past.at(-1);
  if (!previous) return history;
  return {
    past: history.past.slice(0, -1),
    present: previous,
    future: [history.present, ...history.future],
  };
}

export function redo(history: EditHistory): EditHistory {
  const [next, ...rest] = history.future;
  if (!next) return history;
  return { past: [...history.past, history.present], present: next, future: rest };
}

export const canUndo = (history: EditHistory): boolean => history.past.length > 0;
export const canRedo = (history: EditHistory): boolean => history.future.length > 0;
export const isDirty = (history: EditHistory): boolean => history.present.operations.length > 0;
