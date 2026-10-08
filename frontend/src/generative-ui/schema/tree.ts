/**
 * Traversal of a UI document's component tree.
 *
 * A *slot* is a list holding child components. Containers have one slot,
 * addressed by the container's id; a `tabs` component has one slot per tab,
 * addressed by the tab's id. The same vocabulary is used by the backend's
 * mutation engine.
 */
import type { JsonObject } from "./normalization";
import type { PageNode, ScreenComponent, UIComponent, UINode } from "./types";

const CHILD_KEY_BY_TYPE: Record<string, string> = {
  page: "components",
  section: "children",
  card: "children",
  modal: "children",
  form: "fields",
  screen: "children",
};

export interface Slot {
  id: string;
  children: JsonObject[];
}

/** Child slots of a node, operating on plain JSON (used by the mutation engine). */
export function slotsOf(node: JsonObject): Slot[] {
  if (node.type === "tabs") {
    const tabs = (node.tabs ?? []) as JsonObject[];
    return tabs.map((tab) => ({ id: String(tab.id), children: tab.children as JsonObject[] }));
  }
  const key = CHILD_KEY_BY_TYPE[String(node.type)];
  return key && key in node ? [{ id: String(node.id), children: node[key] as JsonObject[] }] : [];
}

export function* iterSlots(root: JsonObject): Generator<Slot> {
  for (const slot of slotsOf(root)) {
    yield slot;
    for (const child of slot.children) {
      yield* iterSlots(child);
    }
  }
}

export function* iterNodes(root: JsonObject): Generator<JsonObject> {
  yield root;
  for (const slot of slotsOf(root)) {
    for (const child of slot.children) {
      yield* iterNodes(child);
    }
  }
}

// --- Typed helpers for UI code ----------------------------------------------------

export interface NodeLocation {
  node: UIComponent;
  /** Id of the slot (container or tab) holding the node. */
  slotId: string;
  index: number;
  siblings: UIComponent[];
  /** Ids of the components containing the node, outermost first (page excluded). */
  ancestors: string[];
}

function typedSlots(node: UINode): { id: string; children: UIComponent[] }[] {
  return slotsOf(node as unknown as JsonObject) as unknown as {
    id: string;
    children: UIComponent[];
  }[];
}

export function findLocation(page: PageNode, componentId: string): NodeLocation | null {
  const visit = (node: UINode, ancestors: string[]): NodeLocation | null => {
    for (const slot of typedSlots(node)) {
      for (const [index, child] of slot.children.entries()) {
        if (child.id === componentId) {
          return { node: child, slotId: slot.id, index, siblings: slot.children, ancestors };
        }
        const found = visit(child, [...ancestors, child.id]);
        if (found) return found;
      }
    }
    return null;
  };
  return visit(page, []);
}

export function findComponent(page: PageNode, componentId: string): UIComponent | null {
  return findLocation(page, componentId)?.node ?? null;
}

export function allComponents(page: PageNode): UIComponent[] {
  const result: UIComponent[] = [];
  const visit = (node: UINode) => {
    for (const slot of typedSlots(node)) {
      for (const child of slot.children) {
        result.push(child);
        visit(child);
      }
    }
  };
  visit(page);
  return result;
}

/** How a person would refer to a component. */
export function nodeLabel(node: { id?: unknown; title?: unknown; label?: unknown }): string {
  return String(node.title ?? node.label ?? node.id ?? "");
}

export function kindLabel(node: { type?: unknown; chart_type?: unknown }): string {
  if (node.type === "chart") return `${String(node.chart_type ?? "")} chart`.trim();
  return String(node.type).replaceAll("_", " ");
}

/** The screens of an application document (empty for a single view). */
export function screensOf(page: PageNode): ScreenComponent[] {
  return page.components.filter((child): child is ScreenComponent => child.type === "screen");
}

/** Id of the screen containing `componentId` (or being it). */
export function screenIdOf(page: PageNode, componentId: string): string | null {
  for (const screen of screensOf(page)) {
    if (screen.id === componentId) return screen.id;
    const location = findLocation(page, componentId);
    if (location?.ancestors[0] === screen.id) return screen.id;
  }
  return null;
}
