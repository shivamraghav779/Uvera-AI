import type { Scalar } from "@/generative-ui/schema/types";

export type ValueFormat = "text" | "number" | "currency" | "percent" | "date";

const standard = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 });
const compact = new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 2 });

function asDate(value: string | number): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleDateString();
}

/** Display text for a data value. `compactNumbers` suits headline figures. */
export function formatValue(
  value: Scalar | undefined,
  format: ValueFormat = "text",
  options: { compactNumbers?: boolean } = {},
): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (format === "date") return asDate(value);
  if (typeof value !== "number") return String(value);
  if (format === "percent") return `${standard.format(value)}%`;
  if (format === "text") return String(value);
  return (options.compactNumbers ? compact : standard).format(value);
}

const relative = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });
const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 31_536_000],
  ["month", 2_592_000],
  ["day", 86_400],
  ["hour", 3_600],
  ["minute", 60],
];

/** "3 minutes ago", "yesterday", ... */
export function formatRelativeTime(iso: string, now: Date = new Date()): string {
  const seconds = (new Date(iso).getTime() - now.getTime()) / 1000;
  for (const [unit, size] of UNITS) {
    if (Math.abs(seconds) >= size) return relative.format(Math.round(seconds / size), unit);
  }
  return "just now";
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}
