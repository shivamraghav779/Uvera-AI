/**
 * The single place HTTP happens.
 *
 * Every backend response is one of two envelopes ({success, data} or
 * {success: false, error}). This module unwraps the first and turns everything
 * else — error envelopes, timeouts, network failures, malformed bodies — into
 * an `ApiError` with a stable `code`, so callers handle failures uniformly.
 */
import { z } from "zod";

import { currentToken, useAuthStore } from "@/stores/authStore";

const environment = z
  .object({
    VITE_API_BASE_URL: z.url().default("http://localhost:8000"),
    VITE_API_TIMEOUT_MS: z.coerce.number().int().positive().default(20_000),
    VITE_AI_TIMEOUT_MS: z.coerce.number().int().positive().default(90_000),
  })
  .parse(import.meta.env);

export const API_BASE_URL = environment.VITE_API_BASE_URL.replace(/\/$/, "");
export const DEFAULT_TIMEOUT_MS = environment.VITE_API_TIMEOUT_MS;
/** Model calls take longer than CRUD. */
export const AI_TIMEOUT_MS = environment.VITE_AI_TIMEOUT_MS;

const API_PREFIX = "/api/v1";

export type ApiErrorCode =
  | "AUTHENTICATION_REQUIRED"
  | "INVALID_TOKEN"
  | "TOKEN_EXPIRED"
  | "INVALID_CREDENTIALS"
  | "EMAIL_ALREADY_REGISTERED"
  | "RATE_LIMIT_EXCEEDED"
  | "DATABASE_UNAVAILABLE"
  | "DATA_SOURCE_ERROR"
  | "CONFLICT"
  | "NETWORK_ERROR"
  | "TIMEOUT"
  | "MALFORMED_RESPONSE"
  | "VERSION_CONFLICT"
  | "UI_SCHEMA_INVALID"
  | "PROVIDER_NOT_CONFIGURED"
  | "LLM_ALL_PROVIDERS_FAILED"
  | "RESOURCE_NOT_FOUND"
  | "VALIDATION_ERROR"
  | (string & {});

export class ApiError extends Error {
  constructor(
    readonly code: ApiErrorCode,
    message: string,
    readonly status: number | null = null,
    readonly details: Record<string, unknown>[] = [],
    readonly requestId: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function isApiError(error: unknown, code?: ApiErrorCode): error is ApiError {
  return error instanceof ApiError && (code === undefined || error.code === code);
}

const errorEnvelope = z.object({
  success: z.literal(false),
  error: z.object({
    code: z.string(),
    message: z.string(),
    request_id: z.string().nullish(),
    details: z.array(z.record(z.string(), z.unknown())).nullish(),
  }),
});

const successEnvelope = z.object({ success: z.literal(true), data: z.unknown() });

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | undefined>;
  timeoutMs?: number;
  signal?: AbortSignal;
}

/** Codes meaning "this session is no longer valid": the user has to sign in again. */
const SESSION_ENDED = new Set(["AUTHENTICATION_REQUIRED", "INVALID_TOKEN", "TOKEN_EXPIRED"]);

export function requestHeaders(hasBody: boolean): Record<string, string> {
  const headers: Record<string, string> = {};
  if (hasBody) headers["Content-Type"] = "application/json";
  const token = currentToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

/** Build the error for a failed response, ending the session if the server says it is over. */
export function errorFromEnvelope(payload: unknown, status: number): ApiError | null {
  const failure = errorEnvelope.safeParse(payload);
  if (!failure.success) return null;
  const { code, message, details, request_id: requestId } = failure.data.error;
  if (SESSION_ENDED.has(code) && currentToken()) useAuthStore.getState().signOut();
  return new ApiError(code, message, status, details ?? [], requestId ?? null);
}

export function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(`${API_BASE_URL}${API_PREFIX}${path}`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }
  return url.toString();
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    throw new ApiError("MALFORMED_RESPONSE", "The server sent a response that is not JSON.", response.status);
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, query, timeoutMs = DEFAULT_TIMEOUT_MS, signal } = options;
  const timeout = AbortSignal.timeout(timeoutMs);

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), {
      method,
      headers: requestHeaders(body !== undefined),
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: signal ? AbortSignal.any([signal, timeout]) : timeout,
    });
  } catch (error) {
    if (timeout.aborted) {
      throw new ApiError("TIMEOUT", "The request took too long. Please try again.");
    }
    if (signal?.aborted) throw error;
    throw new ApiError("NETWORK_ERROR", "Could not reach the server. Check that the backend is running.");
  }

  if (response.status === 204) return undefined as T;

  const payload = await readJson(response);
  const failure = errorFromEnvelope(payload, response.status);
  if (failure) throw failure;
  const success = successEnvelope.safeParse(payload);
  if (!response.ok || !success.success) {
    throw new ApiError(
      "MALFORMED_RESPONSE",
      "The server sent a response in an unexpected format.",
      response.status,
    );
  }
  return success.data.data as T;
}
