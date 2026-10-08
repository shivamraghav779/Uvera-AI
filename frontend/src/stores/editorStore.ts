/** Editor UI state: mode, selection, open panels. Never persisted. */
import { create } from "zustand";

export type EditorMode = "view" | "edit";
export type SidePanel = "none" | "inspector" | "history";
export type Device = "desktop" | "tablet" | "mobile";

/** The server's current version is no longer the one this client is working from. */
export interface VersionConflict {
  currentVersionNumber: number | null;
}

interface EditorState {
  mode: EditorMode;
  selectedId: string | null;
  panel: SidePanel;
  device: Device;
  conflict: VersionConflict | null;
  /** Version being compared with the current one, if the comparison dialog is open. */
  compareVersionId: string | null;
  /** Where the user is inside a generated application (`null`: its home screen). */
  appPath: string | null;
  setAppPath: (path: string | null) => void;
  /** The same, inside whatever is being previewed. A preview never moves the working copy. */
  previewPath: string | null;
  setPreviewPath: (path: string | null) => void;
  setConflict: (conflict: VersionConflict | null) => void;
  setCompareVersionId: (versionId: string | null) => void;
  setMode: (mode: EditorMode) => void;
  select: (componentId: string | null) => void;
  setPanel: (panel: SidePanel) => void;
  togglePanel: (panel: Exclude<SidePanel, "none">) => void;
  setDevice: (device: Device) => void;
  reset: () => void;
}

const INITIAL = {
  mode: "view",
  selectedId: null,
  panel: "none",
  device: "desktop",
  conflict: null,
  compareVersionId: null,
  appPath: null,
  previewPath: null,
} as const;

export const useEditorStore = create<EditorState>((set) => ({
  ...INITIAL,
  // Leaving edit mode clears the selection: view mode is the clean final experience.
  setMode: (mode) =>
    set((state) => ({
      mode,
      selectedId: mode === "edit" ? state.selectedId : null,
      panel: mode === "view" && state.panel === "inspector" ? "none" : state.panel,
    })),
  select: (selectedId) =>
    set((state) => ({
      selectedId,
      panel: selectedId && state.panel === "none" ? "inspector" : state.panel,
    })),
  setPanel: (panel) => set({ panel }),
  togglePanel: (panel) => set((state) => ({ panel: state.panel === panel ? "none" : panel })),
  setDevice: (device) => set({ device }),
  // Another screen has other components: what was selected is no longer on show.
  setAppPath: (appPath) => set((state) => (state.appPath === appPath ? state : { appPath, selectedId: null })),
  setPreviewPath: (previewPath) => set({ previewPath }),
  setConflict: (conflict) => set({ conflict }),
  setCompareVersionId: (compareVersionId) => set({ compareVersionId }),
  reset: () => set(INITIAL),
}));
