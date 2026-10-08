/**
 * Translates layout *intent* (a column span and a height preset) into CSS.
 *
 * The document never contains pixels or positions. Everything about how a span
 * becomes a width, how it collapses on small screens, and how a drag distance
 * snaps back to a span lives here.
 */
import type { CSSProperties } from "react";

import { HEIGHT_PX } from "../schema/defaults";
import type { HeightPreset, LayoutSpec } from "../schema/types";
import { GRID_COLUMNS, HEIGHT_PRESETS } from "../schema/validators";

/** Span used at tablet width: small items pair up, wide ones take the row. */
export function tabletSpan(span: number): number {
  return span <= GRID_COLUMNS / 2 ? GRID_COLUMNS / 2 : GRID_COLUMNS;
}

export function heightInPixels(height: HeightPreset): number | undefined {
  return height === "auto" ? undefined : HEIGHT_PX[height];
}

/** Inline style of a grid cell. Only CSS variables and a min-height: no positions. */
export function cellStyle(layout: LayoutSpec): CSSProperties {
  return {
    "--span": layout.span,
    "--span-md": tabletSpan(layout.span),
    minHeight: heightInPixels(layout.height),
  } as CSSProperties;
}

export function clampSpan(span: number): number {
  return Math.min(Math.max(Math.round(span), 1), GRID_COLUMNS);
}

/** The span whose width is closest to `widthPx` in a grid `gridWidthPx` wide. */
export function spanFromWidth(widthPx: number, gridWidthPx: number, gapPx: number): number {
  const column = (gridWidthPx - (GRID_COLUMNS - 1) * gapPx) / GRID_COLUMNS;
  if (column <= 0) return GRID_COLUMNS;
  return clampSpan((widthPx + gapPx) / (column + gapPx));
}

const AUTO_THRESHOLD_PX = 140;

/** The height preset closest to `heightPx`; small values mean "size to content". */
export function heightFromPixels(heightPx: number): HeightPreset {
  if (heightPx < AUTO_THRESHOLD_PX) return "auto";
  let closest: HeightPreset = "sm";
  for (const preset of HEIGHT_PRESETS) {
    if (preset === "auto") continue;
    if (Math.abs(HEIGHT_PX[preset] - heightPx) < Math.abs(HEIGHT_PX[closest as "sm"] - heightPx)) {
      closest = preset;
    }
  }
  return closest;
}

/** Rows the flow grid produces for a list of spans (used for keyboard hints and tests). */
export function flowRows<T extends { layout: LayoutSpec }>(items: readonly T[]): T[][] {
  const rows: T[][] = [];
  let used = GRID_COLUMNS;
  for (const item of items) {
    if (used + item.layout.span > GRID_COLUMNS) {
      rows.push([]);
      used = 0;
    }
    rows.at(-1)!.push(item);
    used += item.layout.span;
  }
  return rows;
}
