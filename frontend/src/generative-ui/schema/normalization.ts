import type { ZodError } from "zod";

import type { UIDocument, ValidationIssue, ValidationResult } from "./types";
import { documentSchema } from "./validators";

/** Plain JSON as it travels over the wire. */
export type Json = string | number | boolean | null | Json[] | { [key: string]: Json };
export type JsonObject = { [key: string]: Json };

export function deepClone<T>(value: T): T {
  return structuredClone(value);
}

/**
 * Remove `null`/`undefined` object members recursively.
 *
 * The canonical form of a document has no nulls (the backend serialises with
 * `exclude_none`), so "absent" has exactly one representation.
 */
export function stripNulls<T>(value: T): T {
  if (Array.isArray(value)) {
    return value.map((item) => stripNulls(item)) as T;
  }
  if (value !== null && typeof value === "object") {
    const result: Record<string, unknown> = {};
    for (const [key, member] of Object.entries(value)) {
      if (member !== null && member !== undefined) {
        result[key] = stripNulls(member);
      }
    }
    return result as T;
  }
  return value;
}

export function zodIssues(error: ZodError, prefix = ""): ValidationIssue[] {
  return error.issues.map((issue) => ({
    stage: "schema",
    path: [...(prefix ? [prefix] : []), ...issue.path.map(String)].join("."),
    message: issue.message,
  }));
}

/**
 * Parse untrusted JSON into a canonical `UIDocument`: nulls stripped, defaults
 * filled in. Returns issues instead of throwing so callers can keep the last
 * good state on screen.
 */
export function parseDocument(input: unknown): ValidationResult<UIDocument> {
  const parsed = documentSchema.safeParse(stripNulls(input));
  if (!parsed.success) {
    return { ok: false, issues: zodIssues(parsed.error) };
  }
  return { ok: true, value: parsed.data };
}

/** Structural equality of two JSON values (object key order is irrelevant). */
export function jsonEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (typeof a !== typeof b || a === null || b === null) return false;
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) return false;
    return a.every((item, index) => jsonEqual(item, b[index]));
  }
  if (typeof a !== "object" || typeof b !== "object") return false;
  const left = a as Record<string, unknown>;
  const right = b as Record<string, unknown>;
  const keys = Object.keys(left);
  if (keys.length !== Object.keys(right).length) return false;
  return keys.every((key) => key in right && jsonEqual(left[key], right[key]));
}

/**
 * Return a value equal to `next` that reuses every unchanged subtree of
 * `previous` by reference. Components memoised on their node then re-render
 * only when that node actually changed.
 */
export function shareStructure<T>(previous: unknown, next: T): T {
  if (previous === next) return next;
  if (typeof next !== "object" || next === null || typeof previous !== "object" || previous === null) {
    return next;
  }
  if (Array.isArray(next)) {
    if (!Array.isArray(previous)) return next;
    const priorById = new Map<unknown, unknown>();
    for (const item of previous) {
      if (item && typeof item === "object" && "id" in item) priorById.set(item.id, item);
    }
    const shared = next.map((item, index) => {
      // Match moved components by id so reordering does not re-render them.
      const hasId = item && typeof item === "object" && "id" in item;
      return shareStructure(hasId ? (priorById.get(item.id) ?? previous[index]) : previous[index], item);
    });
    const unchanged =
      shared.length === previous.length && shared.every((item, index) => item === previous[index]);
    return (unchanged ? previous : shared) as T;
  }
  if (Array.isArray(previous)) return next;
  const prior = previous as Record<string, unknown>;
  const result: Record<string, unknown> = {};
  let unchanged = Object.keys(prior).length === Object.keys(next).length;
  for (const [key, value] of Object.entries(next)) {
    result[key] = shareStructure(prior[key], value);
    if (result[key] !== prior[key] || !(key in prior)) unchanged = false;
  }
  return (unchanged ? previous : result) as T;
}
