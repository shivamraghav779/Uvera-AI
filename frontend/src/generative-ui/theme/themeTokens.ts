/**
 * Theme tokens -> CSS custom properties.
 *
 * This is the only place where a theme becomes CSS, and every value comes from
 * a fixed table or from a validated `#RRGGBB` colour. The model can choose
 * tokens; it can never supply CSS.
 */
import type { ColorRole, Theme } from "../schema/types";

import { mix, readableOn } from "./themeUtils";

const RADIUS: Record<Theme["radius"], string> = {
  none: "0px",
  sm: "4px",
  md: "8px",
  lg: "14px",
  full: "22px",
};

/** Inner padding of surfaces and height of controls. */
const DENSITY: Record<Theme["density"], { pad: string; control: string }> = {
  compact: { pad: "10px", control: "30px" },
  comfortable: { pad: "16px", control: "36px" },
  spacious: { pad: "22px", control: "42px" },
};

/** Gap between components. */
const SPACING: Record<Theme["spacing"], string> = {
  tight: "10px",
  normal: "16px",
  relaxed: "24px",
};

const SHADOW: Record<Theme["shadows"], string> = {
  none: "none",
  subtle: "0 1px 2px rgb(0 0 0 / 0.06), 0 1px 3px rgb(0 0 0 / 0.08)",
  medium: "0 2px 4px rgb(0 0 0 / 0.08), 0 8px 20px rgb(0 0 0 / 0.12)",
};

/** Bundled type families. A theme names one; it never supplies a font file or URL. */
const FONT: Record<Theme["typography"]["font"], string> = {
  sans: '"Inter Variable", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  serif: '"Fraunces Variable", ui-serif, Georgia, Cambria, "Times New Roman", serif',
  mono: '"JetBrains Mono Variable", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
  rounded: '"Nunito Variable", ui-rounded, "SF Pro Rounded", system-ui, sans-serif',
  grotesk: '"Space Grotesk Variable", "Inter Variable", ui-sans-serif, system-ui, sans-serif',
  geometric: '"Plus Jakarta Sans Variable", "Inter Variable", ui-sans-serif, system-ui, sans-serif',
};

/** Multiplier applied to every heading size, and the tracking that suits it. */
const HEADING_SCALE: Record<Theme["typography"]["heading_scale"], { size: string; tracking: string }> = {
  sm: { size: "0.9", tracking: "-0.005em" },
  md: { size: "1", tracking: "-0.015em" },
  lg: { size: "1.22", tracking: "-0.022em" },
  xl: { size: "1.55", tracking: "-0.032em" },
};

const HEADING_WEIGHT: Record<Theme["typography"]["heading_weight"], string> = {
  regular: "400",
  medium: "500",
  semibold: "600",
  bold: "700",
  black: "800",
};

/** Durations of the motion tokens; `none` collapses them so nothing animates. */
const MOTION: Record<Theme["motion"], { fast: string; normal: string; slow: string }> = {
  none: { fast: "0ms", normal: "0ms", slow: "0ms" },
  subtle: { fast: "120ms", normal: "220ms", slow: "420ms" },
  expressive: { fast: "160ms", normal: "320ms", slow: "640ms" },
};

const FONT_SIZE: Record<Theme["typography"]["scale"], string> = {
  sm: "13px",
  md: "14px",
  lg: "16px",
};

export type CssVariables = Record<`--g-${string}`, string>;

/** CSS variable holding the colour of a style tone. */
export const TONE_VARIABLE: Record<ColorRole, string> = {
  primary: "var(--g-primary)",
  secondary: "var(--g-secondary)",
  success: "var(--g-success)",
  warning: "var(--g-warning)",
  destructive: "var(--g-destructive)",
  neutral: "var(--g-muted-fg)",
};

export function themeToCssVariables(theme: Theme): CssVariables {
  const { colors } = theme;
  const density = DENSITY[theme.density];
  const heading = HEADING_SCALE[theme.typography.heading_scale];
  const motion = MOTION[theme.motion];
  return {
    "--g-primary": colors.primary,
    "--g-primary-fg": readableOn(colors.primary),
    "--g-secondary": colors.secondary,
    "--g-secondary-fg": readableOn(colors.secondary),
    "--g-bg": colors.background,
    "--g-surface": colors.surface,
    "--g-fg": colors.foreground,
    "--g-muted": colors.muted,
    // Secondary text: the foreground pulled towards the surface, still readable.
    "--g-muted-fg": mix(colors.foreground, colors.surface, 0.38),
    "--g-border": colors.border,
    "--g-destructive": colors.destructive,
    "--g-destructive-fg": readableOn(colors.destructive),
    "--g-success": colors.success,
    "--g-warning": colors.warning,
    "--g-chart-1": colors.primary,
    "--g-chart-2": colors.success,
    "--g-chart-3": colors.warning,
    "--g-chart-4": colors.secondary,
    "--g-chart-5": colors.destructive,
    "--g-chart-6": mix(colors.primary, colors.foreground, 0.45),
    "--g-radius": RADIUS[theme.radius],
    "--g-pad": density.pad,
    "--g-control-h": density.control,
    "--g-gap": SPACING[theme.spacing],
    "--g-shadow": SHADOW[theme.shadows],
    "--g-font": FONT[theme.typography.font],
    "--g-font-size": FONT_SIZE[theme.typography.scale],
    "--g-heading-font": FONT[theme.typography.heading_font ?? theme.typography.font],
    "--g-heading-scale": heading.size,
    "--g-heading-tracking": heading.tracking,
    "--g-heading-weight": HEADING_WEIGHT[theme.typography.heading_weight],
    // A second accent for gradients; a neighbouring hue of the primary when none is given.
    "--g-accent": colors.accent ?? mix(colors.primary, colors.secondary, 0.5),
    "--g-primary-soft": mix(colors.surface, colors.primary, theme.mode === "dark" ? 0.18 : 0.1),
    "--g-duration-fast": motion.fast,
    "--g-duration-normal": motion.normal,
    "--g-duration-slow": motion.slow,
    "--g-ease-standard": "cubic-bezier(0.2, 0, 0, 1)",
    "--g-ease-enter": "cubic-bezier(0, 0, 0, 1)",
    "--g-ease-exit": "cubic-bezier(0.3, 0, 1, 1)",
  };
}

export const CHART_COLOR_VARIABLES = [1, 2, 3, 4, 5, 6].map((n) => `var(--g-chart-${n})`);
