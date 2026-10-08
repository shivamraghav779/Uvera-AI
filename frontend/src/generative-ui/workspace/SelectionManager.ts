/**
 * Selection helpers for the editor. Pure functions over the document: they
 * answer "what is selected" questions and turn keyboard intent into operations.
 * Selection is always by stable component id, never by position.
 */
import { getComponentDefinition } from "../registry/componentRegistry";
import type { Operation } from "../mutation/mutationTypes";
import { findLocation, nodeLabel } from "../schema/tree";
import type { PageNode, UIComponent } from "../schema/types";

export interface Crumb {
  id: string;
  label: string;
  type: string;
}

/** The selected component and its ancestors, outermost first. */
export function selectionPath(page: PageNode, componentId: string): Crumb[] {
  const location = findLocation(page, componentId);
  if (!location) return [];
  const crumb = (node: UIComponent): Crumb => ({ id: node.id, label: nodeLabel(node), type: node.type });
  const ancestors = location.ancestors
    .map((id) => findLocation(page, id)?.node)
    .filter((node): node is UIComponent => node !== undefined);
  return [...ancestors, location.node].map(crumb);
}

export function typeLabel(type: string): string {
  return getComponentDefinition(type)?.label ?? type;
}

/** Move a component one place among its siblings, or `null` at the edge. */
export function nudgeOperation(page: PageNode, componentId: string, direction: -1 | 1): Operation | null {
  const location = findLocation(page, componentId);
  if (!location) return null;
  const index = location.index + direction;
  if (index < 0 || index >= location.siblings.length) return null;
  return { type: "MOVE", target: componentId, index };
}

/** What to select after a component is removed: a neighbour, else its parent. */
export function selectionAfterDelete(page: PageNode, componentId: string): string | null {
  const location = findLocation(page, componentId);
  if (!location) return null;
  const neighbour = location.siblings[location.index + 1] ?? location.siblings[location.index - 1];
  return neighbour?.id ?? location.ancestors.at(-1) ?? null;
}

/** Operation for a key pressed while a component is selected, if the key means one. */
export function keyboardOperation(
  page: PageNode,
  componentId: string,
  event: { key: string; altKey: boolean },
): Operation | null {
  if (event.key === "Delete" || event.key === "Backspace") {
    return { type: "DELETE", target: componentId };
  }
  if (!event.altKey) return null;
  if (event.key === "ArrowLeft" || event.key === "ArrowUp") return nudgeOperation(page, componentId, -1);
  if (event.key === "ArrowRight" || event.key === "ArrowDown") return nudgeOperation(page, componentId, 1);
  return null;
}
