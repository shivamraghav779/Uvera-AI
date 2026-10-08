/**
 * Client-side gate for operations: schema -> engine -> resulting document.
 *
 * Nothing is applied to the workspace unless the *result* is a valid document.
 * The backend repeats all of this (and more: datasets, registries) before a
 * version is persisted; this layer exists so the editor can never show or
 * build on a corrupted state.
 */
import { parseDocument, zodIssues } from "../schema/normalization";
import { imageRefs, routeExists, routeParams } from "../runtime/router";
import { allComponents, screensOf } from "../schema/tree";
import type { UIDocument, ValidationIssue, ValidationResult } from "../schema/types";
import { contrastRatio } from "../theme/themeUtils";

import { applyOperations, MutationError } from "./mutationEngine";
import { OPERATION_TYPES, operationSchema, type Operation } from "./mutationTypes";

const MIN_TEXT_CONTRAST = 4.5;
const MAX_COMPONENTS = 200;
const MAX_APPLICATION_COMPONENTS = 1500;

export interface ValidationEnvironment {
  /** Framework ids this frontend can render. */
  frameworks?: readonly string[];
  designSystems?: readonly string[];
}

function issue(stage: ValidationIssue["stage"], path: string, message: string): ValidationIssue {
  return { stage, path, message };
}

/** Parse untrusted JSON into operations. Unknown types and fields are rejected. */
export function parseOperations(input: unknown): ValidationResult<Operation[]> {
  if (!Array.isArray(input)) {
    return { ok: false, issues: [issue("schema", "operations", "Operations must be a list.")] };
  }
  const issues: ValidationIssue[] = [];
  input.forEach((raw, index) => {
    const type = (raw as { type?: unknown } | null)?.type;
    if (typeof type !== "string" || !(OPERATION_TYPES as readonly string[]).includes(type)) {
      issues.push(issue("schema", `operations.${index}.type`, `Unknown operation type '${String(type)}'.`));
      return;
    }
    const parsed = operationSchema.safeParse(raw);
    if (!parsed.success) issues.push(...zodIssues(parsed.error, `operations.${index}`));
  });
  // The original JSON is kept (not Zod's output): `null` means "remove" in STYLE/UPDATE.
  return issues.length > 0 ? { ok: false, issues } : { ok: true, value: input as Operation[] };
}

/** Cross-component rules the schema cannot express. A subset of the backend's rules. */
export function semanticIssues(
  document: UIDocument,
  environment: ValidationEnvironment = {},
): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const components = allComponents(document.page);

  const screens = screensOf(document.page);
  const limit = screens.length > 0 ? MAX_APPLICATION_COMPONENTS : MAX_COMPONENTS;
  if (components.length > limit) {
    issues.push(issue("semantic", "page", `UI has more than ${limit} components.`));
  }
  issues.push(...applicationIssues(document));

  const seen = new Set<string>([document.page.id]);
  const ids: string[] = components.flatMap((component) =>
    component.type === "tabs" ? [component.id, ...component.tabs.map((tab) => tab.id)] : [component.id],
  );
  for (const id of ids) {
    if (seen.has(id)) issues.push(issue("semantic", id, `Duplicate id '${id}'; ids must be unique.`));
    seen.add(id);
  }

  for (const component of components) {
    const actions =
      component.type === "button"
        ? [component.action]
        : component.type === "form"
          ? [component.submit_action]
          : "on_change" in component && component.on_change
            ? [component.on_change]
            : [];
    for (const action of actions) {
      const target = action.payload.target;
      if (typeof target === "string" && !seen.has(target)) {
        issues.push(issue("semantic", component.id, `Action target '${target}' is not a component id.`));
      }
    }
  }
  issues.push(...navigationTargetIssues(document));

  const { colors } = document.theme;
  for (const backdrop of ["background", "surface"] as const) {
    if (contrastRatio(colors.foreground, colors[backdrop]) < MIN_TEXT_CONTRAST) {
      issues.push(
        issue("semantic", "theme.colors.foreground", `Text would be hard to read against '${backdrop}'.`),
      );
    }
  }

  const { framework, design_system: designSystem } = document.design;
  if (environment.frameworks && !environment.frameworks.includes(framework)) {
    issues.push(issue("registry", "design.framework", `Framework '${framework}' is not available.`));
  }
  if (environment.designSystems && !environment.designSystems.includes(designSystem)) {
    issues.push(
      issue("registry", "design.design_system", `Design system '${designSystem}' is not registered.`),
    );
  }
  return issues;
}

/** Structure of an application: screens under the page, a consistent shell, real assets. */
function applicationIssues(document: UIDocument): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  const { page, application } = document;
  const screens = screensOf(page);
  const nested = allComponents(page).filter(
    (component) => component.type === "screen" && !screens.includes(component),
  );
  for (const screen of nested) {
    issues.push(issue("semantic", screen.id, "A screen can only be placed directly under the page."));
  }
  if (screens.length > 0 && screens.length !== page.components.length) {
    issues.push(issue("semantic", "page", "A page holds either screens only, or no screens at all."));
  }
  if (!application) {
    if (screens.length > 0) {
      issues.push(issue("semantic", "page", "Screens need an 'application' section."));
    }
    return issues;
  }
  if (screens.length === 0) {
    return [...issues, issue("semantic", "page", "An application needs at least one screen.")];
  }

  const shapes = new Map<string, string>();
  for (const screen of screens) {
    const shape = screen.route.replace(/:[^/]+/g, ":");
    const other = shapes.get(shape);
    if (other) {
      issues.push(
        issue("semantic", screen.id, `Route '${screen.route}' clashes with screen '${other}'.`),
      );
    }
    shapes.set(shape, screen.id);
  }

  const byId = new Map(screens.map((screen) => [screen.id, screen]));
  const { navigation } = application;
  const linked = [...navigation.items, ...(navigation.action ? [navigation.action] : [])];
  for (const screenId of [navigation.home, ...linked.map((item) => item.screen_id)]) {
    const screen = byId.get(screenId);
    if (!screen) {
      issues.push(issue("semantic", "application.navigation", `'${screenId}' is not a screen.`));
    } else if (routeParams(screen.route).length > 0) {
      issues.push(
        issue("semantic", "application.navigation", `'${screenId}' needs a record and cannot be linked.`),
      );
    }
  }

  const assetIds = new Set(application.assets.map((asset) => asset.id));
  for (const component of allComponents(page)) {
    for (const assetId of imageRefs(component)) {
      if (!assetIds.has(assetId)) {
        issues.push(issue("semantic", component.id, `'${assetId}' is not an asset of this UI.`));
      }
    }
  }
  return issues;
}

/** Inside an application an in-app path must lead to one of its screens. */
function navigationTargetIssues(document: UIDocument): ValidationIssue[] {
  const screens = screensOf(document.page);
  if (screens.length === 0) return [];
  const issues: ValidationIssue[] = [];
  const visit = (node: unknown, owner: string) => {
    if (Array.isArray(node)) {
      node.forEach((item) => visit(item, owner));
      return;
    }
    if (node === null || typeof node !== "object") return;
    const record = node as Record<string, unknown>;
    const id = typeof record.id === "string" && typeof record.type === "string" ? record.id : owner;
    const payload = record.payload as Record<string, unknown> | undefined;
    if (typeof record.type === "string" && payload && typeof payload === "object") {
      for (const key of ["to", "navigate_to"]) {
        const destination = payload[key];
        if (typeof destination === "string" && destination.startsWith("/") && !routeExists(screens, destination)) {
          issues.push(issue("semantic", id, `'${destination}' is not a screen of this application.`));
        }
      }
    }
    Object.values(record).forEach((value) => visit(value, id));
  };
  visit(document.page, document.page.id);
  return issues;
}

export function validateDocument(
  input: unknown,
  environment?: ValidationEnvironment,
): ValidationResult<UIDocument> {
  const parsed = parseDocument(input);
  if (!parsed.ok) return parsed;
  const issues = semanticIssues(parsed.value, environment);
  return issues.length > 0 ? { ok: false, issues } : parsed;
}

/**
 * Apply `operations` to `document` and return the validated result, or the
 * reasons it was rejected. `document` is never modified.
 */
export function applyValidated(
  document: UIDocument,
  operations: unknown,
  environment?: ValidationEnvironment,
): ValidationResult<UIDocument> {
  const parsed = parseOperations(operations);
  if (!parsed.ok) return parsed;
  let result: UIDocument;
  try {
    result = applyOperations(document, parsed.value);
  } catch (error) {
    if (error instanceof MutationError) {
      return { ok: false, issues: [issue("operation", `operations.${error.index}`, error.message)] };
    }
    throw error;
  }
  return validateDocument(result, environment);
}
