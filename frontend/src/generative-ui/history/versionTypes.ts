import type { DataMap, UIDocument } from "../schema/types";

/** A stored version after its document has passed client-side validation. */
export interface LoadedVersion {
  id: string;
  number: number;
  document: UIDocument;
  data: DataMap;
}

/** Something shown on the canvas instead of the working copy, read-only. */
export interface CanvasPreview {
  kind: "proposal" | "version";
  label: string;
  document: UIDocument;
  data: DataMap;
  /** Components to draw attention to. */
  highlightIds: string[];
  /** Set when previewing a stored version. */
  versionId?: string;
}
