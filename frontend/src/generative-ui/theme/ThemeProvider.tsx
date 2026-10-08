/**
 * Applies a document's theme to a subtree as CSS custom properties.
 *
 * The variables are scoped to this element, so the generated UI is themed
 * without touching the editor around it, and several documents (e.g. a version
 * preview) can be themed differently on one screen.
 */
import { createContext, useContext, useMemo, useState, type CSSProperties, type ReactNode } from "react";

import { cn } from "@/utils/cn";

import type { Theme } from "../schema/types";

import { themeToCssVariables } from "./themeTokens";

const PortalContext = createContext<HTMLElement | null>(null);

/** Where overlays (dialogs) must mount to inherit the theme. */
export function usePortalContainer(): HTMLElement | null {
  return useContext(PortalContext);
}

interface ThemeProviderProps {
  theme: Theme;
  /** Exposed as `data-framework` for tests and adapter-specific styling. */
  framework: string;
  className?: string;
  children: ReactNode;
}

export function ThemeProvider({ theme, framework, className, children }: ThemeProviderProps) {
  const [root, setRoot] = useState<HTMLDivElement | null>(null);
  const style = useMemo(() => themeToCssVariables(theme) as CSSProperties, [theme]);
  return (
    <div
      ref={setRoot}
      style={style}
      data-theme-mode={theme.mode}
      data-framework={framework}
      // Token names, read by the stylesheet to pick surface, motion and gradient treatments.
      data-surface={theme.surface}
      data-motion={theme.motion}
      data-gradient={theme.gradient}
      className={cn("g-root", className)}
    >
      <PortalContext.Provider value={root}>{children}</PortalContext.Provider>
    </div>
  );
}
