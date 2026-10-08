/**
 * Applies operations to a UI document.
 *
 * This is a line-for-line counterpart of the backend engine
 * (app/domains/generative_ui/mutation_engine.py). Both work on plain JSON and
 * must produce identical results; `tests/unit/mutationEngine.test.ts` runs the
 * backend-computed cases from the contract fixtures against this file.
 *
 * The engine only restructures data. Its output must still pass validation
 * (see mutationValidator.ts) before it is shown or saved.
 */
import { deepClone, type Json, type JsonObject } from "../schema/normalization";
import { iterNodes, iterSlots } from "../schema/tree";

import type { Operation } from "./mutationTypes";

const UNGROUPABLE = new Set(["section", "card"]);
/** UPDATE may not touch identity, placement, styling or structure. */
export const PROTECTED_PROPS = new Set([
  "id", "type", "layout", "style", "children", "components", "fields", "tabs",
]); // prettier-ignore
const THEME_IDENTITY_TOKENS = ["mode", "colors"];
const NAVIGATION_FIELDS = ["style", "brand", "tagline", "home", "items", "action"];
/** UPDATE_APPLICATION may only touch descriptive fields; the rest have their own operations. */
export const APPLICATION_PROPS = new Set([
  "name", "category", "description", "target_users", "goals", "features", "interactions",
  "design_direction",
]); // prettier-ignore

export class MutationError extends Error {
  constructor(
    readonly index: number,
    message: string,
  ) {
    super(message);
    this.name = "MutationError";
  }
}

class Reject extends Error {}

interface Location {
  node: JsonObject;
  siblings: JsonObject[];
  index: number;
  slotId: string;
}

type RawOperation = JsonObject & { type: string };
type RawDocument = {
  page: JsonObject;
  theme: JsonObject;
  design: JsonObject;
  application?: JsonObject;
} & JsonObject;

function applicationOf(document: RawDocument): JsonObject {
  const application = document.application;
  if (!application || typeof application !== "object") {
    throw new Reject("This UI is not an application.");
  }
  return application;
}

/** Keep the shell consistent with the screens that exist. */
function pruneNavigation(document: RawDocument): void {
  const application = document.application;
  if (!application || typeof application !== "object") return;
  const screenIds = (document.page.components as JsonObject[])
    .filter((child) => child.type === "screen")
    .map((child) => child.id);
  const navigation = application.navigation as JsonObject;
  navigation.items = ((navigation.items ?? []) as JsonObject[]).filter((item) =>
    screenIds.includes(item.screen_id!),
  );
  const action = navigation.action as JsonObject | undefined;
  if (action && !screenIds.includes(action.screen_id!)) delete navigation.action;
  if (!screenIds.includes(navigation.home!) && screenIds.length > 0) navigation.home = screenIds[0]!;
}

/** `existing` with each incoming item replacing the one of the same key, or appended. */
function upsert(existing: JsonObject[], incoming: JsonObject[], key: string): JsonObject[] {
  const merged = [...existing];
  const positions = new Map(merged.map((item, index) => [item[key], index]));
  for (const item of incoming) {
    const position = positions.get(item[key]);
    if (position !== undefined) {
      merged[position] = item;
    } else {
      positions.set(item[key], merged.length);
      merged.push(item);
    }
  }
  return merged;
}

function locate(page: JsonObject, target: string): Location {
  for (const slot of iterSlots(page)) {
    const index = slot.children.findIndex((child) => child.id === target);
    if (index !== -1) {
      return { node: slot.children[index]!, siblings: slot.children, index, slotId: slot.id };
    }
  }
  throw new Reject(`Component '${target}' does not exist.`);
}

function slotChildren(page: JsonObject, slotId: string): JsonObject[] {
  for (const slot of iterSlots(page)) {
    if (slot.id === slotId) return slot.children;
  }
  throw new Reject(`'${slotId}' is not a container that can hold components.`);
}

function insertionIndex(siblings: JsonObject[], operation: RawOperation): number {
  for (const [anchor, offset] of [["before", 0], ["after", 1]] as const) {
    const anchorId = operation[anchor];
    if (anchorId === undefined || anchorId === null) continue;
    const index = siblings.findIndex((sibling) => sibling.id === anchorId);
    if (index === -1) throw new Reject(`'${String(anchorId)}' is not in the destination container.`);
    return index + offset;
  }
  const position = operation.index;
  return typeof position === "number" ? Math.min(position, siblings.length) : siblings.length;
}

/** Overlay `patch` on `base`; nested token groups merge, `null` is ignored. */
export function mergeTheme(base: JsonObject, patch: JsonObject): JsonObject {
  const merged: JsonObject = { ...base };
  for (const [key, value] of Object.entries(patch)) {
    if (value === null || value === undefined) continue;
    if (typeof value === "object" && !Array.isArray(value)) {
      merged[key] = mergeTheme((merged[key] as JsonObject | undefined) ?? {}, value);
    } else {
      merged[key] = value;
    }
  }
  return merged;
}

function findTab(page: JsonObject, tabId: string): JsonObject | null {
  for (const node of iterNodes(page)) {
    if (node.type !== "tabs") continue;
    const tab = ((node.tabs ?? []) as JsonObject[]).find((candidate) => candidate.id === tabId);
    if (tab) return tab;
  }
  return null;
}

const handlers: Record<string, (document: RawDocument, operation: RawOperation) => void> = {
  CREATE(document, operation) {
    const page = document.page;
    const siblings = slotChildren(page, String(operation.parent_id ?? page.id));
    siblings.splice(insertionIndex(siblings, operation), 0, operation.component as JsonObject);
  },

  DELETE(document, operation) {
    const location = locate(document.page, String(operation.target));
    const [removed] = location.siblings.splice(location.index, 1);
    if (removed?.type === "screen") pruneNavigation(document);
  },

  MOVE(document, operation) {
    const page = document.page;
    const location = locate(page, String(operation.target));
    const destinationId = String(operation.parent_id ?? location.slotId);
    for (const slot of iterSlots(location.node)) {
      if (slot.id === destinationId) throw new Reject("A component cannot be moved into itself.");
    }
    const destination = slotChildren(page, destinationId);
    location.siblings.splice(location.index, 1);
    destination.splice(insertionIndex(destination, operation), 0, location.node);
  },

  RESIZE(document, operation) {
    const node = locate(document.page, String(operation.target)).node;
    const layout: JsonObject = { ...((node.layout as JsonObject | undefined) ?? {}) };
    for (const key of ["span", "height"]) {
      const value = operation[key];
      if (value !== undefined && value !== null) layout[key] = value;
    }
    node.layout = layout;
  },

  STYLE(document, operation) {
    const node = locate(document.page, String(operation.target)).node;
    const style: JsonObject = { ...((node.style as JsonObject | undefined) ?? {}) };
    for (const [key, value] of Object.entries(operation.style as JsonObject)) {
      if (value === null) delete style[key];
      else style[key] = value;
    }
    if (Object.keys(style).length > 0) node.style = style;
    else delete node.style;
  },

  UPDATE(document, operation) {
    const page = document.page;
    const target = String(operation.target);
    const node = target === page.id ? page : (findTab(page, target) ?? locate(page, target).node);
    for (const [key, value] of Object.entries(operation.props as JsonObject)) {
      if (PROTECTED_PROPS.has(key)) throw new Reject(`UPDATE cannot change '${key}'.`);
      if (value === null) delete node[key];
      else node[key] = value;
    }
  },

  REORDER(document, operation) {
    const siblings = slotChildren(document.page, String(operation.parent_id));
    const byId = new Map(siblings.map((child) => [String(child.id), child]));
    const order = operation.order as string[];
    const complete = order.length === byId.size && new Set(order).size === byId.size;
    if (!complete || !order.every((id) => byId.has(id))) {
      throw new Reject("REORDER must list every child of the container exactly once.");
    }
    siblings.splice(0, siblings.length, ...order.map((id) => byId.get(id)!));
  },

  GROUP(document, operation) {
    const page = document.page;
    const targets = [...new Set(operation.targets as string[])];
    const locations = targets.map((target) => locate(page, target));
    if (new Set(locations.map((location) => location.slotId)).size !== 1) {
      throw new Reject("GROUP targets must share the same parent.");
    }
    const siblings = locations[0]!.siblings;
    const members = [...locations].sort((a, b) => a.index - b.index);
    const spec = operation.group as JsonObject;
    const container: JsonObject = { type: spec.type ?? "section", id: spec.id! };
    if (spec.title) container.title = spec.title;
    container.children = members.map((member) => member.node);
    const position = members[0]!.index;
    const memberIds = new Set(members.map((member) => member.node.id));
    const remaining = siblings.filter((child) => !memberIds.has(child.id));
    remaining.splice(position, 0, container);
    siblings.splice(0, siblings.length, ...remaining);
  },

  UNGROUP(document, operation) {
    const location = locate(document.page, String(operation.target));
    if (!UNGROUPABLE.has(String(location.node.type))) {
      throw new Reject("Only a section or card can be ungrouped.");
    }
    location.siblings.splice(location.index, 1, ...(location.node.children as JsonObject[]));
  },

  REPLACE(document, operation) {
    const location = locate(document.page, String(operation.target));
    const replaced = location.siblings[location.index]!;
    const component = operation.component as JsonObject;
    location.siblings[location.index] = component;
    if (replaced.type === "screen" && component.id !== replaced.id) pruneNavigation(document);
  },

  SET_THEME(document, operation) {
    const tokens = (operation.tokens as JsonObject | undefined) ?? {};
    const theme = mergeTheme(document.theme, tokens);
    if (operation.preset !== undefined && operation.preset !== null) {
      theme.preset = operation.preset;
    } else if (THEME_IDENTITY_TOKENS.some((token) => token in tokens)) {
      // Colours no longer match the preset they came from.
      delete theme.preset;
    }
    document.theme = theme;
  },

  SET_FRAMEWORK(document, operation) {
    document.design = { ...document.design, framework: operation.framework as Json };
  },

  SET_DESIGN_SYSTEM(document, operation) {
    document.design = { ...document.design, design_system: operation.design_system as Json };
    document.theme = mergeTheme(document.theme, (operation.tokens as JsonObject | undefined) ?? {});
  },

  SET_NAVIGATION(document, operation) {
    const application = applicationOf(document);
    const navigation: JsonObject = { ...(application.navigation as JsonObject) };
    for (const key of NAVIGATION_FIELDS) {
      if (!(key in operation)) continue;
      if (operation[key] === null) delete navigation[key];
      else navigation[key] = operation[key]!;
    }
    document.application = { ...application, navigation };
  },

  UPDATE_APPLICATION(document, operation) {
    const application: JsonObject = { ...applicationOf(document) };
    for (const [key, value] of Object.entries(operation.props as JsonObject)) {
      if (!APPLICATION_PROPS.has(key)) throw new Reject(`UPDATE_APPLICATION cannot change '${key}'.`);
      if (value === null) delete application[key];
      else application[key] = value;
    }
    document.application = application;
  },

  ADD_ASSETS(document, operation) {
    const application = applicationOf(document);
    const assets = upsert(
      (application.assets ?? []) as JsonObject[],
      operation.assets as JsonObject[],
      "id",
    );
    document.application = { ...application, assets };
  },

  UPSERT_ENTITIES(document, operation) {
    const application = applicationOf(document);
    const entities = upsert(
      (application.entities ?? []) as JsonObject[],
      operation.entities as JsonObject[],
      "name",
    );
    document.application = { ...application, entities };
  },
};

/**
 * Return a new document with `operations` applied in order. The input is never
 * modified. Throws `MutationError` (carrying the operation's index) on the
 * first operation that cannot be applied.
 */
export function applyOperations<T extends object>(document: T, operations: readonly Operation[]): T {
  const result = deepClone(document) as unknown as RawDocument;
  operations.forEach((operation, index) => {
    const raw = deepClone(operation) as unknown as RawOperation;
    const handler = handlers[raw.type];
    if (!handler) throw new MutationError(index, `Unknown operation type '${raw.type}'.`);
    try {
      handler(result, raw);
    } catch (error) {
      if (error instanceof Reject) throw new MutationError(index, error.message);
      throw error;
    }
  });
  return result as unknown as T;
}
