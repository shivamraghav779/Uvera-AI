/**
 * Runs the actions a generated UI declares.
 *
 * An action in the schema is a name plus static parameters. Running it means
 * asking the backend, which executes it only if it is on the allowlist. What
 * comes back is data (rows, a file's text, a destination); this module decides
 * what to do with it. Nothing from the schema or the response is evaluated.
 *
 * Two kinds of action never leave the browser: moving between the screens of a
 * generated application (the destination must be one of its routes), and
 * anything at all while editing.
 */
import type { StoreApi } from "zustand";

import { actionsApi } from "@/services/api/actions";
import { ApiError } from "@/services/api/client";
import { toast } from "@/stores/toastStore";

import { fillRoute, resolveRoute, routeParams } from "../runtime/router";
import type { ActionSpec, DataRow, Scalar } from "../schema/types";
import { dataRowSchema } from "../schema/validators";

import type {
  ActionContext,
  ActionDispatcher,
  ActionInput,
  AppRuntime,
  RenderMode,
  RuntimeState,
} from "./RendererContext";

export interface ActionEnvironment {
  workspaceId: string;
  mode: RenderMode;
  runtime: StoreApi<RuntimeState>;
  /** The generated application the action runs in, if the UI is one. */
  getApp?: () => AppRuntime | null;
  /** Navigation in the surrounding product (used by single views). */
  navigate: (path: string) => void;
  /** Hand a follow-up instruction to the assistant. */
  requestGeneration: (instruction: string) => void;
}

const PRIMARY_KEY = "id";
const RECORD_ACTIONS = new Set(["record_create", "record_update", "record_delete"]);

/** In-app paths and https links only; mirrors the backend's rule. */
export function isSafeDestination(destination: unknown): destination is string {
  if (typeof destination !== "string") return false;
  if (destination.startsWith("/")) return !destination.startsWith("//");
  return destination.startsWith("https://");
}

function parseRows(value: unknown): DataRow[] {
  const parsed = dataRowSchema.array().safeParse(value);
  return parsed.success ? parsed.data : [];
}

function download(filename: string, mediaType: string, content: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: mediaType }));
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function text(value: unknown): string | undefined {
  return typeof value === "string" || typeof value === "number" ? String(value) : undefined;
}

/**
 * The concrete path a navigate action leads to inside an application, or why
 * it cannot be followed. A route's parameter is filled from the record the
 * action was triggered on, otherwise from the current route.
 */
export function resolveDestination(
  app: AppRuntime,
  payload: Record<string, unknown>,
  context: ActionContext,
): { path: string } | { problem: string } | null {
  const destination = payload.to;
  if (typeof destination !== "string" || !destination.startsWith("/")) return null;
  const match = resolveRoute(app.screens, destination);
  if (!match) return { problem: "That screen does not exist in this application." };
  const fromField = typeof payload.from_field === "string" ? payload.from_field : PRIMARY_KEY;
  const recordId = text(context.row?.[fromField]);
  const params: Record<string, string> = {};
  for (const name of routeParams(match.screen.route)) {
    const given = match.params[name];
    // A concrete path (`/jobs/j-12`) carries its value; a route pattern (`/jobs/:jobId`)
    // is filled from the record acted on, else from where the user already is.
    const value = given && !given.startsWith(":") ? given : (recordId ?? app.route.params[name]);
    if (value !== undefined) params[name] = value;
  }
  const path = fillRoute(match.screen.route, params);
  return path ? { path } : { problem: "Open a record first: that screen shows one record." };
}

/** What a record action sends to the backend: the entity, the record and the new values. */
export function recordPayload(
  action: ActionSpec,
  input: ActionInput,
  context: ActionContext,
  app: AppRuntime | null,
): Record<string, unknown> | { problem: string } {
  const { entity, set_field: setField, set_value: setValue, key_param: keyParam } = action.payload;
  const payload: Record<string, unknown> = { entity };
  if (typeof action.payload.navigate_to === "string") payload.navigate_to = action.payload.navigate_to;

  const formValues = input.values as Record<string, Scalar> | undefined;
  if (action.type !== "record_delete") {
    // A form supplies its fields; a button or a moved card sets one field.
    const single = typeof setField === "string" ? { [setField]: input.value ?? setValue ?? null } : {};
    payload.values = formValues ?? single;
  }
  if (action.type === "record_create") return payload;

  const fromRoute = typeof keyParam === "string" ? app?.route.params[keyParam] : undefined;
  const onlyParam = app ? Object.values(app.route.params) : [];
  const recordId = text(context.row?.[PRIMARY_KEY]) ?? fromRoute ?? (onlyParam.length === 1 ? onlyParam[0] : undefined);
  if (recordId === undefined) return { problem: "There is no record here to change." };
  return { ...payload, record_id: recordId };
}

function handleResult(
  action: ActionSpec,
  result: Record<string, unknown>,
  environment: ActionEnvironment,
): void {
  const target = typeof result.target === "string" ? result.target : undefined;
  const store = environment.runtime.getState();
  switch (action.type) {
    case "filter":
    case "sort":
    case "refresh":
      if (target) store.setRows(target, parseRows(result.rows));
      return;
    case "export":
      download(String(result.filename ?? "export.txt"), String(result.media_type ?? "text/plain"), String(result.content ?? ""));
      return;
    case "navigate": {
      const destination = result.navigate_to;
      if (!isSafeDestination(destination)) {
        toast.error("That link was blocked because it is not a safe destination.");
      } else if (destination.startsWith("/")) {
        environment.navigate(destination);
      } else {
        window.open(destination, "_blank", "noopener,noreferrer");
      }
      return;
    }
    case "record_create":
    case "record_update":
    case "record_delete": {
      // The whole entity comes back: every component bound to it shows the change.
      if (typeof result.dataset === "string") store.setDataset(result.dataset, parseRows(result.rows));
      toast.success(action.type === "record_create" ? "Added." : action.type === "record_delete" ? "Removed." : "Saved.");
      const next = result.navigate_to;
      const app = environment.getApp?.();
      if (app && typeof next === "string" && resolveRoute(app.screens, next)) app.navigate(next);
      return;
    }
    case "submit":
      toast.success("Submitted.");
      return;
    case "search": {
      const results = Array.isArray(result.results) ? result.results.length : 0;
      toast.info(`${results} result${results === 1 ? "" : "s"} found.`);
      return;
    }
    case "generate":
      environment.requestGeneration(String(result.message ?? ""));
      return;
  }
}

export function createActionDispatcher(environment: ActionEnvironment): ActionDispatcher {
  return async (action: ActionSpec, input: ActionInput = {}, context: ActionContext = {}) => {
    // Editing never triggers anything: a click selects.
    if (environment.mode === "edit") return;
    const app = environment.getApp?.() ?? null;

    // Moving between the screens of an application is local, and works while previewing.
    if (action.type === "navigate" && app) {
      const destination = resolveDestination(app, action.payload, context);
      if (destination) {
        if ("problem" in destination) toast.info(destination.problem);
        else app.navigate(destination.path);
        return;
      }
    }
    // A preview is not the saved application: nothing in it reaches the server.
    if (environment.mode !== "view") {
      toast.info("Apply this version to use its actions.");
      return;
    }

    let type: string = action.type;
    let payload: Record<string, unknown> = { ...action.payload, ...input };
    if (action.type === "filter" && (input.value === "" || input.value === undefined)) {
      // Clearing a filter control shows everything again.
      type = "refresh";
      delete payload.field;
      delete payload.value;
      delete payload.operator;
    }
    if (RECORD_ACTIONS.has(action.type)) {
      const record = recordPayload(action, input, context, app);
      if ("problem" in record) {
        toast.info(String(record.problem));
        return;
      }
      payload = record;
    }
    try {
      const response = await actionsApi.execute(environment.workspaceId, type, payload);
      handleResult({ ...action, type: type as ActionSpec["type"] }, response.result, environment);
    } catch (error) {
      toast.error(error instanceof ApiError ? error.message : "The action could not be completed.");
    }
  };
}
