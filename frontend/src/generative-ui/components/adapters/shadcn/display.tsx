import {
  AlertTriangle,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Info,
  XCircle,
} from "lucide-react";
import { lazy, Suspense, useState } from "react";

import { cn } from "@/utils/cn";

import { feedbackStyle, toneStyle, TONE_WASH } from "../shared";
import type {
  AlertViewProps,
  BadgeViewProps,
  ChartViewProps,
  FeedbackTone,
  ListViewProps,
  MetricViewProps,
  ProgressViewProps,
  TableViewProps,
  TextViewProps,
  TimelineViewProps,
} from "../types";

import { SURFACE } from "./layout";

// Recharts is the heaviest dependency; it loads only when a chart is on screen.
const ChartCanvas = lazy(() => import("../ChartCanvas"));

const TREND = {
  up: { Icon: ArrowUpRight, className: "text-g-success" },
  down: { Icon: ArrowDownRight, className: "text-g-destructive" },
  flat: { Icon: ArrowRight, className: "text-g-muted-fg" },
} as const;

export function Metric({ title, value, unit, trend, description, tone, emphasis, surface }: MetricViewProps) {
  const Trend = trend ? TREND[trend.direction] : null;
  return (
    <div
      style={toneStyle(tone)}
      data-surface={surface}
      className={cn(
        SURFACE,
        "flex h-full flex-col gap-1 p-[var(--g-pad)]",
        emphasis === "strong" && TONE_WASH,
      )}
    >
      <p className="text-[0.88em] font-medium text-g-muted-fg">{title}</p>
      <p className={cn("g-heading text-[1.9em] leading-tight tabular-nums", tone && "text-g-tone")}>
        {unit && <span className="mr-0.5 text-[0.7em] font-medium text-g-muted-fg">{unit}</span>}
        {value}
      </p>
      {trend && Trend && (
        <p className={cn("flex items-center gap-1 text-[0.88em] font-medium", Trend.className)}>
          <Trend.Icon size={14} aria-hidden />
          <span>{trend.value}</span>
          {trend.label && <span className="font-normal text-g-muted-fg">{trend.label}</span>}
        </p>
      )}
      {description && <p className="text-[0.85em] text-g-muted-fg">{description}</p>}
    </div>
  );
}

const TEXT_VARIANT = {
  heading: "g-h2 !text-[calc(1.45em*var(--g-heading-scale))]",
  subheading: "g-h3 font-semibold",
  body: "",
  caption: "text-[0.85em] text-g-muted-fg",
} as const;

export function Text({ content, variant, tone }: TextViewProps) {
  const Tag = variant === "heading" ? "h2" : variant === "subheading" ? "h3" : "p";
  return (
    <Tag
      style={toneStyle(tone)}
      className={cn("whitespace-pre-line", TEXT_VARIANT[variant], tone && "text-g-tone")}
    >
      {content}
    </Tag>
  );
}

const ALIGN = { left: "text-left", center: "text-center", right: "text-right" } as const;

export function Table({ title, columns, rows, pageSize, height, onRowClick }: TableViewProps) {
  const [page, setPage] = useState(0);
  const pageCount = pageSize ? Math.max(Math.ceil(rows.length / pageSize), 1) : 1;
  const current = Math.min(page, pageCount - 1);
  const visible = pageSize ? rows.slice(current * pageSize, (current + 1) * pageSize) : rows;

  return (
    <div className={cn(SURFACE, "flex h-full flex-col overflow-hidden")}>
      {title && <h3 className="px-[var(--g-pad)] pt-[var(--g-pad)] pb-2 font-semibold">{title}</h3>}
      <div className="overflow-auto" style={height ? { maxHeight: height } : undefined}>
        <table className="w-full border-collapse text-[0.95em]">
          {title && <caption className="sr-only">{title}</caption>}
          <thead className="sticky top-0 bg-g-muted text-[0.88em] text-g-muted-fg">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={cn("px-[var(--g-pad)] py-2 font-medium", ALIGN[column.align])}
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((row, index) => (
              <tr
                key={index}
                tabIndex={onRowClick ? 0 : undefined}
                onClick={onRowClick ? () => onRowClick(current * (pageSize ?? 0) + index) : undefined}
                onKeyDown={
                  onRowClick
                    ? (event) => {
                        if (event.key === "Enter") onRowClick(current * (pageSize ?? 0) + index);
                      }
                    : undefined
                }
                className={cn(
                  "border-t border-g-border",
                  onRowClick && "cursor-pointer transition-colors duration-[var(--g-duration-fast)] hover:bg-g-muted",
                )}
              >
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={cn("px-[var(--g-pad)] py-2 tabular-nums", ALIGN[column.align])}
                  >
                    {row[column.key]}
                  </td>
                ))}
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-[var(--g-pad)] py-6 text-center text-g-muted-fg">
                  No data
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {pageSize && pageCount > 1 && (
        <div className="flex items-center justify-end gap-2 border-t border-g-border px-[var(--g-pad)] py-2 text-[0.88em] text-g-muted-fg">
          <span>
            Page {current + 1} of {pageCount}
          </span>
          <button
            type="button"
            aria-label="Previous page"
            disabled={current === 0}
            onClick={() => setPage(current - 1)}
            className="rounded p-1 hover:bg-g-muted disabled:opacity-40"
          >
            <ChevronLeft size={16} />
          </button>
          <button
            type="button"
            aria-label="Next page"
            disabled={current >= pageCount - 1}
            onClick={() => setPage(current + 1)}
            className="rounded p-1 hover:bg-g-muted disabled:opacity-40"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}

export function Chart(props: ChartViewProps) {
  const { title, rows, height, chartType } = props;
  return (
    <figure className={cn(SURFACE, "flex h-full flex-col gap-2 p-[var(--g-pad)]")} style={toneStyle(props.tone)}>
      {title && <figcaption className="font-semibold">{title}</figcaption>}
      <div
        role="img"
        aria-label={`${title ?? "Chart"}: ${chartType} chart with ${rows.length} data points`}
        style={{ height }}
      >
        {rows.length === 0 ? (
          <div className="grid h-full place-items-center text-g-muted-fg">No data</div>
        ) : (
          <Suspense fallback={<div className="h-full animate-pulse rounded-g bg-g-muted" />}>
            <ChartCanvas {...props} />
          </Suspense>
        )}
      </div>
    </figure>
  );
}

export function List({ title, ordered, items }: ListViewProps) {
  const Tag = ordered ? "ol" : "ul";
  return (
    <div className={cn(SURFACE, "h-full p-[var(--g-pad)]")}>
      {title && <h3 className="mb-2 font-semibold">{title}</h3>}
      <Tag className="flex flex-col divide-y divide-g-border">
        {items.map((item, index) => (
          <li key={index} className="flex items-start gap-3 py-2 first:pt-0 last:pb-0">
            {ordered && (
              <span className="mt-0.5 w-5 shrink-0 text-[0.85em] text-g-muted-fg tabular-nums">
                {index + 1}.
              </span>
            )}
            <div className="min-w-0 flex-1">
              <p className="font-medium">{item.title}</p>
              {item.description && <p className="text-[0.9em] text-g-muted-fg">{item.description}</p>}
            </div>
            {item.badge && (
              <span className="shrink-0 rounded-full bg-g-muted px-2 py-0.5 text-[0.8em] text-g-muted-fg">
                {item.badge}
              </span>
            )}
          </li>
        ))}
      </Tag>
    </div>
  );
}

const TIMELINE_DOT = {
  completed: "bg-g-success border-g-success",
  current: "bg-g-primary border-g-primary ring-4 ring-[color-mix(in_srgb,var(--g-primary)_20%,transparent)]",
  upcoming: "bg-g-surface border-g-border",
} as const;

export function Timeline({ title, items }: TimelineViewProps) {
  return (
    <div className={cn(SURFACE, "h-full p-[var(--g-pad)]")}>
      {title && <h3 className="mb-3 font-semibold">{title}</h3>}
      <ol className="relative ml-1.5 flex flex-col gap-4 border-l border-g-border pl-5">
        {items.map((item, index) => (
          <li key={index} className="relative">
            <span
              aria-hidden
              className={cn(
                "absolute top-1.5 -left-[26px] size-2.5 rounded-full border-2",
                TIMELINE_DOT[item.status ?? "upcoming"],
              )}
            />
            <div className="flex flex-wrap items-baseline justify-between gap-x-3">
              <p className="font-medium">
                {item.title}
                {item.status && <span className="sr-only"> ({item.status})</span>}
              </p>
              {item.timestamp && <time className="text-[0.85em] text-g-muted-fg">{item.timestamp}</time>}
            </div>
            {item.description && <p className="text-[0.9em] text-g-muted-fg">{item.description}</p>}
          </li>
        ))}
      </ol>
    </div>
  );
}

export function Badge({ label, tone }: BadgeViewProps) {
  return (
    <span
      style={feedbackStyle(tone)}
      className={cn(
        "inline-flex w-fit items-center rounded-full px-2.5 py-0.5 text-[0.85em] font-medium text-g-tone",
        TONE_WASH,
      )}
    >
      {label}
    </span>
  );
}

export function Progress({ label, value, max, tone }: ProgressViewProps) {
  const percent = Math.min(Math.max((value / max) * 100, 0), 100);
  return (
    <div style={feedbackStyle(tone)} className="flex flex-col gap-1.5">
      <div className="flex justify-between text-[0.92em]">
        <span className="font-medium">{label}</span>
        <span className="text-g-muted-fg tabular-nums">{Math.round(percent)}%</span>
      </div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={max}
        aria-valuenow={value}
        className="h-2 overflow-hidden rounded-full bg-g-muted"
      >
        <div className="h-full rounded-full bg-g-tone transition-[width]" style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}

const ALERT_ICON: Record<FeedbackTone, typeof Info> = {
  neutral: Info,
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: XCircle,
};

export function Alert({ title, message, tone }: AlertViewProps) {
  const Icon = ALERT_ICON[tone];
  return (
    <div
      role={tone === "danger" || tone === "warning" ? "alert" : "status"}
      style={feedbackStyle(tone)}
      className={cn(
        "flex gap-3 rounded-g border border-[color-mix(in_srgb,var(--tone)_35%,transparent)] p-[var(--g-pad)]",
        TONE_WASH,
      )}
    >
      <Icon size={18} aria-hidden className="mt-0.5 shrink-0 text-g-tone" />
      <div>
        {title && <p className="font-semibold">{title}</p>}
        <p className="whitespace-pre-line">{message}</p>
      </div>
    </div>
  );
}
