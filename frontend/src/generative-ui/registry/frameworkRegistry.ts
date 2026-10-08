/**
 * Maps a document's `design.framework` id to the components that render it.
 *
 * A partial adapter is completed with the default adapter's components, so
 * switching framework can never leave a component without an implementation.
 */
import { materialAdapter } from "../components/adapters/material";
import { shadcnAdapter, shadcnComponents } from "../components/adapters/shadcn";
import type { AdapterComponents, FrameworkAdapter } from "../components/adapters/types";
import { DEFAULT_FRAMEWORK } from "../schema/defaults";

const adapters = new Map<string, FrameworkAdapter>();
const resolved = new Map<string, AdapterComponents>();

export function registerFramework(adapter: FrameworkAdapter): void {
  adapters.set(adapter.id, adapter);
  resolved.delete(adapter.id);
}

registerFramework(shadcnAdapter);
registerFramework(materialAdapter);

export function registeredFrameworkIds(): string[] {
  return [...adapters.keys()];
}

export function getFramework(frameworkId: string): FrameworkAdapter | undefined {
  return adapters.get(frameworkId);
}

/**
 * Components for a framework id. Unknown ids resolve to the default adapter:
 * a document must stay viewable even if it names a framework this build lacks.
 */
export function resolveAdapter(frameworkId: string): AdapterComponents {
  const id = adapters.has(frameworkId) ? frameworkId : DEFAULT_FRAMEWORK;
  let components = resolved.get(id);
  if (!components) {
    components = { ...shadcnComponents, ...adapters.get(id)?.components };
    resolved.set(id, components);
  }
  return components;
}

/** Names of the semantic components a framework implements itself. */
export function implementedComponents(frameworkId: string): string[] {
  return Object.keys(adapters.get(frameworkId)?.components ?? {});
}
