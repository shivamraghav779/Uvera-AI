import type { HeightPreset, LayoutSpec } from "./types";
import { GRID_COLUMNS } from "./validators";

export const DEFAULT_LAYOUT: LayoutSpec = { span: GRID_COLUMNS, height: "auto" };

/** Pixel heights behind the height presets. The schema only ever stores the preset. */
export const HEIGHT_PX: Record<Exclude<HeightPreset, "auto">, number> = {
  sm: 200,
  md: 300,
  lg: 420,
  xl: 560,
};

/** Height a chart gets when its layout says "auto". */
export const DEFAULT_CHART_HEIGHT = 280;

export const DEFAULT_FRAMEWORK = "shadcn";
