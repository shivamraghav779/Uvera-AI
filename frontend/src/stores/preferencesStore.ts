/**
 * Personal preferences of this browser: how the editor looks and what a new
 * workspace starts with. This is the only state kept in localStorage, and none
 * of it is workspace content — workspaces live on the server.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ChromeTheme = "light" | "dark";

interface PreferencesState {
  chromeTheme: ChromeTheme;
  chatExpanded: boolean;
  /** Look applied to the first UI generated in a new workspace. Empty = backend default. */
  newWorkspaceThemePreset: string;
  newWorkspaceDesignSystem: string;
  newWorkspaceFramework: string;
  setChromeTheme: (theme: ChromeTheme) => void;
  setChatExpanded: (expanded: boolean) => void;
  setNewWorkspaceLook: (
    look: Partial<
      Pick<
        PreferencesState,
        "newWorkspaceThemePreset" | "newWorkspaceDesignSystem" | "newWorkspaceFramework"
      >
    >,
  ) => void;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      chromeTheme: "light",
      chatExpanded: false,
      newWorkspaceThemePreset: "",
      newWorkspaceDesignSystem: "",
      newWorkspaceFramework: "",
      setChromeTheme: (chromeTheme) => set({ chromeTheme }),
      setChatExpanded: (chatExpanded) => set({ chatExpanded }),
      setNewWorkspaceLook: (look) => set(look),
    }),
    { name: "generative-ui.preferences", version: 1 },
  ),
);
