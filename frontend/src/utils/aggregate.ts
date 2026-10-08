import type { DataRow, Scalar } from "@/generative-ui/schema/types";

export type Aggregate = "sum" | "avg" | "min" | "max" | "count" | "first";

/** Reduce one field of `rows` to a single value. Returns `undefined` when there is no data. */
export function aggregate(rows: readonly DataRow[], field: string, kind: Aggregate): Scalar | undefined {
  if (rows.length === 0) return undefined;
  if (kind === "count") return rows.length;
  if (kind === "first") return rows[0]?.[field];
  const numbers = rows.map((row) => row[field]).filter((value): value is number => typeof value === "number");
  if (numbers.length === 0) return undefined;
  switch (kind) {
    case "sum":
      return numbers.reduce((total, value) => total + value, 0);
    case "avg":
      return numbers.reduce((total, value) => total + value, 0) / numbers.length;
    case "min":
      return Math.min(...numbers);
    case "max":
      return Math.max(...numbers);
  }
}
