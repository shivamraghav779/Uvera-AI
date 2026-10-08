/**
 * Declarative row selection: what a data binding does to a dataset.
 *
 * A binding can filter (`where`), order (`sort`), summarise (`group_by` with an
 * aggregate) and truncate (`limit`). It is data, evaluated here; there is no
 * expression language and nothing from a document is ever executed.
 */
import { aggregate } from "@/utils/aggregate";

import type { DataBinding, DataRow, Scalar } from "../schema/types";

import type { RouteParams } from "./router";

type Condition = NonNullable<DataBinding["where"]>[number];

function isEmpty(value: Scalar | undefined): boolean {
  return value === undefined || value === null || value === "";
}

/** Loose equality for cells: a route parameter is always text, a cell may be a number. */
function same(cell: Scalar | undefined, expected: Scalar | undefined): boolean {
  if (cell === expected) return true;
  if (cell === null || cell === undefined || expected === null || expected === undefined) return false;
  return String(cell) === String(expected);
}

export function matches(row: DataRow, condition: Condition, params: RouteParams): boolean {
  const cell = row[condition.field];
  // A condition on a parameter the route does not have matches nothing: a detail
  // component never shows somebody else's record by accident.
  if (condition.param !== undefined && params[condition.param] === undefined) return false;
  const expected = condition.param !== undefined ? params[condition.param] : condition.value;
  switch (condition.operator) {
    case "equals":
      return same(cell, expected as Scalar | undefined);
    case "not_equals":
      return !same(cell, expected as Scalar | undefined);
    case "in":
      return Array.isArray(expected) && expected.some((item) => same(cell, item));
    case "not_in":
      return Array.isArray(expected) && !expected.some((item) => same(cell, item));
    case "gt":
      return typeof cell === "number" && Number(expected) < cell;
    case "lt":
      return typeof cell === "number" && Number(expected) > cell;
    case "is_set":
      return !isEmpty(cell);
    case "is_empty":
      return isEmpty(cell);
  }
}

export function filterRows(
  rows: readonly DataRow[],
  where: readonly Condition[] | undefined,
  params: RouteParams,
): readonly DataRow[] {
  if (!where || where.length === 0) return rows;
  return rows.filter((row) => where.every((condition) => matches(row, condition, params)));
}

function compare(a: Scalar | undefined, b: Scalar | undefined): number {
  if (isEmpty(a) && isEmpty(b)) return 0;
  if (isEmpty(a)) return 1; // blanks last, whatever the direction
  if (isEmpty(b)) return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), undefined, { numeric: true });
}

/** One row per value of `groupBy`, holding that value and the aggregated field (or `count`). */
export function groupRows(rows: readonly DataRow[], binding: DataBinding): DataRow[] {
  const key = binding.group_by!;
  const groups = new Map<string, DataRow[]>();
  for (const row of rows) {
    const value = String(row[key] ?? "—");
    groups.set(value, [...(groups.get(value) ?? []), row]);
  }
  const field = binding.field;
  const kind = binding.aggregate ?? (field ? "sum" : "count");
  return [...groups.entries()].map(([value, members]) => ({
    [key]: value,
    [field ?? "count"]: (field ? aggregate(members, field, kind) : members.length) ?? null,
  }));
}

/** The rows a binding selects from its dataset. */
export function selectRows(
  rows: readonly DataRow[],
  binding: DataBinding,
  params: RouteParams = {},
): readonly DataRow[] {
  let selected = filterRows(rows, binding.where, params);
  if (binding.group_by) selected = groupRows(selected, binding);
  const sort = binding.sort;
  if (sort) {
    const direction = sort.direction === "desc" ? -1 : 1;
    selected = [...selected].sort((a, b) => {
      const order = compare(a[sort.field], b[sort.field]);
      const blank = isEmpty(a[sort.field]) || isEmpty(b[sort.field]);
      return blank ? order : order * direction;
    });
  }
  return binding.limit ? selected.slice(0, binding.limit) : selected;
}

/** Initials for an avatar drawn from a name: "Amara Okafor" -> "AO". */
export function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  const letters = words.length > 1 ? [words[0]![0], words.at(-1)![0]] : [words[0]?.[0], words[0]?.[1]];
  return letters.filter(Boolean).join("").toUpperCase();
}
