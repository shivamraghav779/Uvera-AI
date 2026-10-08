/**
 * What this frontend build can render, and how that compares with what the
 * backend may generate. A mismatch means the two were deployed out of step;
 * the renderer still degrades gracefully (see UnsupportedComponent).
 */
import type { Capabilities, FrameworkCatalog } from "@/services/api/types";

import { CHART_TYPES } from "../schema/validators";

import { supportedComponentTypes } from "./componentRegistry";
import { registeredFrameworkIds } from "./frameworkRegistry";

export interface FrontendCapabilities {
  components: string[];
  chartTypes: string[];
  frameworks: string[];
}

export function frontendCapabilities(): FrontendCapabilities {
  return {
    components: supportedComponentTypes(),
    chartTypes: [...CHART_TYPES],
    frameworks: registeredFrameworkIds(),
  };
}

export interface CapabilityGaps {
  /** Component types the backend can generate that this build cannot render. */
  components: string[];
  chartTypes: string[];
  /** Frameworks the backend marks available that have no adapter here. */
  frameworks: string[];
}

export function findCapabilityGaps(
  backend: Capabilities,
  frameworks: FrameworkCatalog | undefined,
  frontend: FrontendCapabilities = frontendCapabilities(),
): CapabilityGaps {
  const missing = (required: readonly string[], available: readonly string[]) =>
    required.filter((item) => !available.includes(item));
  const backendFrameworks = (frameworks?.frameworks ?? [])
    .filter((framework) => framework.status === "available")
    .map((framework) => framework.id);
  return {
    components: missing(backend.components, frontend.components),
    chartTypes: missing(backend.chart_types, frontend.chartTypes),
    frameworks: missing(backendFrameworks, frontend.frameworks),
  };
}

export function hasGaps(gaps: CapabilityGaps): boolean {
  return gaps.components.length + gaps.chartTypes.length + gaps.frameworks.length > 0;
}

/** Framework ids that are both offered by the backend and implemented here. */
export function usableFrameworkIds(catalog: FrameworkCatalog | undefined): string[] {
  const registered = registeredFrameworkIds();
  if (!catalog) return registered;
  return catalog.frameworks
    .filter((framework) => framework.status === "available" && registered.includes(framework.id))
    .map((framework) => framework.id);
}
