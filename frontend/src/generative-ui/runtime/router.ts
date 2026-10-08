/**
 * The dynamic router of a generated application.
 *
 * Screens declare routes (`/jobs`, `/jobs/:jobId`) in the document. Nothing is
 * compiled into React Router: a path is matched against the document's screens
 * at run time, so every generated application is routable the moment it exists.
 * Mirrors `app/domains/generative_ui/application.py`.
 */
import type { ScreenComponent } from "../schema/types";

export type RouteParams = Record<string, string>;

export interface RouteMatch {
  screen: ScreenComponent;
  params: RouteParams;
}

function segments(path: string): string[] {
  return (path.split("?")[0] ?? "").split("/").filter(Boolean);
}

/** Parameter names of a route: `/jobs/:jobId` -> `["jobId"]`. */
export function routeParams(route: string): string[] {
  return segments(route)
    .filter((segment) => segment.startsWith(":"))
    .map((segment) => segment.slice(1));
}

/** Parameters if `path` is an instance of `route`, else `null`. */
export function matchRoute(route: string, path: string): RouteParams | null {
  const pattern = segments(route);
  const actual = segments(path);
  if (pattern.length !== actual.length) return null;
  const params: RouteParams = {};
  for (const [index, expected] of pattern.entries()) {
    const value = actual[index]!;
    if (expected.startsWith(":")) params[expected.slice(1)] = decodeURIComponent(value);
    else if (expected !== value) return null;
  }
  return params;
}

/**
 * The screen a path leads to. Static routes win over parameterised ones, so
 * `/jobs/new` is the create form even though `/jobs/:jobId` also matches.
 */
export function resolveRoute(screens: readonly ScreenComponent[], path: string): RouteMatch | null {
  const wanted = segments(path).join("/");
  for (const screen of screens) {
    if (segments(screen.route).join("/") === wanted) return { screen, params: {} };
  }
  for (const screen of screens) {
    const params = matchRoute(screen.route, path);
    if (params) return { screen, params };
  }
  return null;
}

/** Whether an in-app path (a route or an instance of one) leads to a screen. */
export function routeExists(screens: readonly ScreenComponent[], path: string): boolean {
  return resolveRoute(screens, path) !== null;
}

/**
 * A concrete path for a route. Parameters come from `params`; any that are
 * missing make the route unfillable (`null`), so navigation never lands on a
 * path with a literal `:param` in it.
 */
export function fillRoute(route: string, params: RouteParams): string | null {
  const filled: string[] = [];
  for (const segment of segments(route)) {
    if (!segment.startsWith(":")) {
      filled.push(segment);
      continue;
    }
    const value = params[segment.slice(1)];
    if (value === undefined || value === "") return null;
    filled.push(encodeURIComponent(value));
  }
  return `/${filled.join("/")}`;
}

/** Fields that hold an asset id, wherever they appear inside a component. */
const IMAGE_KEYS = new Set(["image", "avatar"]);

/**
 * Asset ids referenced inside a component (not its child components).
 * `fields.image` / `fields.avatar` of record components name fields, not assets.
 */
export function imageRefs(value: unknown): string[] {
  const found: string[] = [];
  const visit = (node: unknown) => {
    if (Array.isArray(node)) {
      node.forEach(visit);
    } else if (node !== null && typeof node === "object") {
      for (const [key, nested] of Object.entries(node)) {
        if (key === "fields" && nested !== null && typeof nested === "object" && !Array.isArray(nested)) {
          continue;
        }
        if (key === "children" || key === "tabs" || key === "components") continue;
        if (IMAGE_KEYS.has(key) && typeof nested === "string") found.push(nested);
        else visit(nested);
      }
    }
  };
  visit(value);
  return found;
}
