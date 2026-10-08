/** Helpers shared by adapters. Styling is expressed through theme variables only. */
import type { CSSProperties } from "react";

import type { ColorRole } from "../../schema/types";
import { TONE_VARIABLE } from "../../theme/themeTokens";

import type { FeedbackTone } from "./types";

const FEEDBACK_VARIABLE: Record<FeedbackTone, string> = {
  neutral: "var(--g-muted-fg)",
  info: "var(--g-primary)",
  success: "var(--g-success)",
  warning: "var(--g-warning)",
  danger: "var(--g-destructive)",
};

/** Sets `--tone` for a subtree; classes such as `text-g-tone` then pick it up. */
export function toneStyle(tone: ColorRole | undefined): CSSProperties | undefined {
  return tone ? ({ "--tone": TONE_VARIABLE[tone] } as CSSProperties) : undefined;
}

export function feedbackStyle(tone: FeedbackTone): CSSProperties {
  return { "--tone": FEEDBACK_VARIABLE[tone] } as CSSProperties;
}

/** A translucent wash of the current tone, for tinted backgrounds. */
export const TONE_WASH = "bg-[color-mix(in_srgb,var(--tone,var(--g-primary))_12%,transparent)]";
