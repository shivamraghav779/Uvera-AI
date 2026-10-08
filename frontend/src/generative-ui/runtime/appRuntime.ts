/**
 * Where the user is inside a generated application, and how they move.
 *
 * The path is plain state owned by whoever shows the canvas (the workspace
 * keeps it in the URL; a preview keeps its own). Everything else is derived
 * from the document: which screen the path leads to, and its parameters.
 */
import { useMemo } from "react";

import type { AppRoute, AppRuntime } from "../renderer/RendererContext";
import type { JsonObject } from "../schema/normalization";
import { iterNodes, screensOf } from "../schema/tree";
import type { DataMap, ScreenComponent, UIDocument } from "../schema/types";

import { fillRoute, resolveRoute, routeParams, type RouteParams } from "./router";

interface ParamCondition {
  field?: unknown;
  param?: unknown;
}

/**
 * Values for a screen's route parameters when the path does not carry them
 * (the screen was picked from a list of screens, not reached from a record):
 * the first record of the dataset the screen filters by that parameter.
 */
export function defaultParams(screen: ScreenComponent, data: DataMap): RouteParams {
  const wanted = new Set(routeParams(screen.route));
  const params: RouteParams = {};
  if (wanted.size === 0) return params;
  for (const node of iterNodes(screen as unknown as JsonObject)) {
    const binding = node.data_source as { dataset?: unknown; where?: ParamCondition[] } | undefined;
    if (!binding || typeof binding.dataset !== "string") continue;
    for (const condition of binding.where ?? []) {
      const name = condition.param;
      if (typeof name !== "string" || !wanted.has(name) || name in params) continue;
      const value = data[binding.dataset]?.[0]?.[String(condition.field)];
      if (value !== undefined && value !== null && value !== "") params[name] = String(value);
    }
  }
  return params;
}

function homeScreen(document: UIDocument, screens: readonly ScreenComponent[]): ScreenComponent {
  const home = document.application?.navigation.home;
  return screens.find((screen) => screen.id === home) ?? screens[0]!;
}

/** The route a path leads to; an unknown or missing path leads home. */
export function locate(document: UIDocument, data: DataMap, path: string | null | undefined): AppRoute | null {
  const screens = screensOf(document.page);
  if (screens.length === 0) return null;
  const match = path ? resolveRoute(screens, path) : null;
  const screen = match?.screen ?? homeScreen(document, screens);
  const given = Object.fromEntries(
    Object.entries(match?.params ?? {}).filter(([, value]) => !value.startsWith(":")),
  );
  const params = { ...defaultParams(screen, data), ...given };
  return { screen, params, path: fillRoute(screen.route, params) ?? screen.route };
}

/** Id of the screen a path shows (what the assistant treats as "this screen"). */
export function activeScreenId(document: UIDocument | null, data: DataMap, path: string | null): string | null {
  if (!document?.application) return null;
  return locate(document, data, path)?.screen.id ?? null;
}

/**
 * The application around the canvas, or `null` when the document is a single
 * view. `onPathChange` receives concrete paths only, and only ones that exist.
 */
export function useAppRuntime(
  document: UIDocument,
  data: DataMap,
  path: string | null | undefined,
  onPathChange: (path: string) => void,
): AppRuntime | null {
  return useMemo(() => {
    const application = document.application;
    const route = application ? locate(document, data, path) : null;
    if (!application || !route) return null;
    const screens = screensOf(document.page);
    return {
      application,
      screens,
      route,
      navigate: (to) => {
        if (!resolveRoute(screens, to)) return;
        const next = locate(document, data, to);
        if (next && next.path !== route.path) onPathChange(next.path);
      },
    };
  }, [document, data, path, onPathChange]);
}
