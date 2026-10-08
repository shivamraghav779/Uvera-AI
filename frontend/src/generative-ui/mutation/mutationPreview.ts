/** Human-readable descriptions of operations, for previews and change summaries. */
import { findComponent, kindLabel, nodeLabel } from "../schema/tree";
import type { UIDocument } from "../schema/types";

import type { Operation } from "./mutationTypes";

function quoted(document: UIDocument, componentId: string): string {
  if (componentId === document.page.id) return `“${document.page.title}”`;
  const node = findComponent(document.page, componentId);
  return `“${node ? nodeLabel(node) : componentId}”`;
}

/** One sentence describing `operation` against the document it applies to. */
export function describeOperation(operation: Operation, document: UIDocument): string {
  switch (operation.type) {
    case "CREATE":
      return `Add ${kindLabel(operation.component)} “${nodeLabel(operation.component)}”`;
    case "DELETE":
      return `Remove ${quoted(document, operation.target)}`;
    case "MOVE": {
      const target = quoted(document, operation.target);
      if (operation.before) return `Move ${target} before ${quoted(document, operation.before)}`;
      if (operation.after) return `Move ${target} after ${quoted(document, operation.after)}`;
      if (operation.parent_id) return `Move ${target} into ${quoted(document, operation.parent_id)}`;
      return `Move ${target}`;
    }
    case "RESIZE": {
      const parts = [
        ...(operation.span !== undefined ? [`${operation.span} of 12 columns wide`] : []),
        ...(operation.height !== undefined ? [`height ${operation.height}`] : []),
      ];
      return `Resize ${quoted(document, operation.target)} to ${parts.join(" and ")}`;
    }
    case "STYLE":
      return `Restyle ${quoted(document, operation.target)}`;
    case "UPDATE":
      return `Update ${Object.keys(operation.props).sort().join(", ")} of ${quoted(document, operation.target)}`;
    case "REORDER":
      return `Reorder the contents of ${quoted(document, operation.parent_id)}`;
    case "GROUP":
      return `Group ${operation.targets.length} components into “${nodeLabel(operation.group)}”`;
    case "UNGROUP":
      return `Ungroup ${quoted(document, operation.target)}`;
    case "REPLACE":
      return `Replace ${quoted(document, operation.target)} with a ${kindLabel(operation.component)}`;
    case "SET_THEME":
      return operation.preset ? `Change theme to ${operation.preset}` : "Adjust theme tokens";
    case "SET_FRAMEWORK":
      return `Render with the ${operation.framework} framework`;
    case "SET_DESIGN_SYSTEM":
      return `Switch visual style to ${operation.design_system}`;
    case "SET_NAVIGATION":
      return operation.style ? `Change navigation to ${operation.style}` : "Update the navigation";
    case "UPDATE_APPLICATION":
      return `Update the application's ${Object.keys(operation.props).sort().join(", ")}`;
    case "ADD_ASSETS":
      return `Add ${operation.assets.length} image${operation.assets.length === 1 ? "" : "s"}`;
    case "UPSERT_ENTITIES":
      return `Update data: ${operation.entities.map((entity) => entity.label).join(", ")}`;
  }
}

/** Ids worth highlighting on the canvas for `operation`. */
export function affectedComponentIds(operation: Operation): string[] {
  const ids: string[] = [];
  if ("target" in operation) ids.push(operation.target);
  if (operation.type === "GROUP") ids.push(...operation.targets, operation.group.id);
  if (operation.type === "CREATE" || operation.type === "REPLACE") ids.push(operation.component.id);
  if (operation.type === "REORDER") ids.push(operation.parent_id);
  return [...new Set(ids)];
}

/** A short description of several operations, used for a version's description. */
export function summariseOperations(operations: readonly Operation[], document: UIDocument): string {
  const summaries = operations.map((operation) => describeOperation(operation, document));
  const listed = summaries.slice(0, 3).join("; ");
  return summaries.length > 3 ? `${listed} (+${summaries.length - 3} more)` : listed;
}
