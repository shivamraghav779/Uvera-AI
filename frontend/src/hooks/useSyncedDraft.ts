import { useState } from "react";

/**
 * Local, editable copy of a prop that resets whenever the prop changes
 * (for example after an undo). Uses React's "adjust state while rendering"
 * pattern, so there is no extra effect pass.
 */
export function useSyncedDraft(value: string): [string, (next: string) => void] {
  const [source, setSource] = useState(value);
  const [draft, setDraft] = useState(value);
  if (source !== value) {
    setSource(value);
    setDraft(value);
  }
  return [draft, setDraft];
}
