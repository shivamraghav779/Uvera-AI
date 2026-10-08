import { createContext, useContext } from "react";

import type { Operation } from "../mutation/mutationTypes";
import type { PageNode } from "../schema/types";

/** What editable cells need from the canvas they live in. */
export interface EditorContextValue {
  page: PageNode;
  selectedId: string | null;
  select: (componentId: string | null) => void;
  /** Request a change. The owner validates it; it may be refused. */
  apply: (operations: Operation[]) => void;
}

export const EditorContext = createContext<EditorContextValue | null>(null);

export function useEditor(): EditorContextValue {
  const value = useContext(EditorContext);
  if (!value) throw new Error("Editable elements must be rendered inside a WorkspaceCanvas in edit mode.");
  return value;
}
