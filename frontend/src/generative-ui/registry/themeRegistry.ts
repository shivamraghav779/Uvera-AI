/**
 * Builds the operations behind "pick a theme / design system / framework".
 *
 * Presets come from the backend (`GET /ui/themes`, `/ui/frameworks`). Choosing
 * one produces a fully explicit operation, so the local mutation engine and the
 * backend apply exactly the same change.
 */
import type { FrameworkCatalog, ThemeCatalog } from "@/services/api/types";

import type { OperationOf } from "../mutation/mutationTypes";
import type { ThemePatch } from "../schema/types";
import { themePatchSchema } from "../schema/validators";

export function themePresetOperation(
  catalog: ThemeCatalog,
  presetId: string,
): OperationOf<"SET_THEME"> | null {
  const preset = catalog.presets.find((candidate) => candidate.id === presetId);
  if (!preset) return null;
  // A preset is colours only; shape tokens stay with the design system.
  return {
    type: "SET_THEME",
    preset: preset.id,
    tokens: { mode: preset.theme.mode, colors: stripEmpty(preset.theme.colors) as ThemePatch["colors"] },
  };
}

export function designSystemOperation(
  catalog: FrameworkCatalog,
  designSystemId: string,
): OperationOf<"SET_DESIGN_SYSTEM"> | null {
  const system = catalog.design_systems.find((candidate) => candidate.id === designSystemId);
  if (!system) return null;
  const tokens = themePatchSchema.safeParse(stripEmpty(system.tokens));
  if (!tokens.success) return null;
  return { type: "SET_DESIGN_SYSTEM", design_system: system.id, tokens: tokens.data };
}

export function frameworkOperation(frameworkId: string): OperationOf<"SET_FRAMEWORK"> {
  return { type: "SET_FRAMEWORK", framework: frameworkId };
}

function stripEmpty(tokens: object): ThemePatch {
  return JSON.parse(JSON.stringify(tokens, (_key, value) => (value === null ? undefined : value)));
}
