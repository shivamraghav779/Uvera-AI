/**
 * Patterns that show an application's records: figures, collections, a board,
 * one record's details, an agenda, and a command bar. They bind to datasets
 * (the application's entities) and never hold business data themselves.
 */
import { ArrowDownRight, ArrowRight, ArrowUpRight, ChevronRight, Search } from "lucide-react";
import { useId, useMemo, useRef, useState, type CSSProperties, type DragEvent } from "react";
import { useStore } from "zustand";

import { cn } from "@/utils/cn";
import { aggregate } from "@/utils/aggregate";
import { formatValue, type ValueFormat } from "@/utils/format";

import { useCountUp, useInView } from "../../effects/useEffects";
import { hasEffect } from "../../registry/effectRegistry";
import { useRenderer, useRouteParams, useRows, type ActionContext } from "../../renderer/RendererContext";
import { filterRows } from "../../runtime/rows";
import type { ActionSpec, ComponentOf, DataRow, Scalar } from "../../schema/types";

import {
  ActionButtons,
  AssetImage,
  Avatar,
  Band,
  BlockTitle,
  Icon,
  StatusPill,
  surfaceProps,
  useAction,
} from "./shared";

const cols = (count: number): CSSProperties => ({ "--cols": count }) as CSSProperties;
const PRIMARY_KEY = "id";

function cell(row: DataRow, key: string | undefined): string | undefined {
  if (!key) return undefined;
  const value = row[key];
  return value === null || value === undefined || value === "" ? undefined : String(value);
}

function rowKey(row: DataRow, index: number): string {
  return String(row[PRIMARY_KEY] ?? index);
}

// --- Stats -------------------------------------------------------------------------

type StatItem = ComponentOf<"stats">["items"][number];

const TREND = {
  up: { Glyph: ArrowUpRight, className: "text-g-success" },
  down: { Glyph: ArrowDownRight, className: "text-g-destructive" },
  flat: { Glyph: ArrowRight, className: "text-g-muted-fg" },
} as const;

/** A stat's value: computed from its binding, never taken from model text when bound. */
function useStatValue(item: StatItem): Scalar | undefined {
  const { data, runtime } = useRenderer();
  const params = useRouteParams();
  const binding = item.data_source;
  const replaced = useStore(runtime, (state) => (binding ? state.datasets[binding.dataset] : undefined));
  return useMemo(() => {
    if (!binding) return item.value;
    const rows = filterRows(replaced ?? data[binding.dataset] ?? [], binding.where, params);
    return aggregate(rows, binding.field, binding.aggregate);
  }, [binding, item.value, replaced, data, params]);
}

function Stat({ item, counting, started, large }: { item: StatItem; counting: boolean; started: boolean; large: boolean }) {
  const raw = useStatValue(item);
  const numeric = typeof raw === "number" ? raw : null;
  const counted = useCountUp(numeric, started, counting && numeric !== null);
  const format: ValueFormat = item.format === "text" && numeric !== null ? "number" : item.format;
  const shown = numeric !== null && counted !== null ? (Number.isInteger(numeric) ? Math.round(counted) : counted) : raw;
  const trend = item.trend ? TREND[item.trend.direction] : null;
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <dt className="flex items-center gap-2 text-[0.86em] font-medium text-g-muted-fg">
        <Icon name={item.icon} size={15} />
        <span className="truncate">{item.label}</span>
      </dt>
      <dd className={cn("g-heading leading-none tabular-nums", large ? "text-[calc(2.6em*var(--g-heading-scale))]" : "text-[1.85em]")}>
        {item.unit && <span className="mr-0.5 text-[0.6em] font-medium text-g-muted-fg">{item.unit}</span>}
        {formatValue(shown, format, { compactNumbers: true })}
      </dd>
      {item.trend && trend && (
        <dd className={cn("flex items-center gap-1 text-[0.85em] font-medium", trend.className)}>
          <trend.Glyph size={14} aria-hidden />
          {item.trend.value}
          {item.trend.label && <span className="font-normal text-g-muted-fg">{item.trend.label}</span>}
        </dd>
      )}
      {item.description && <dd className="text-[0.84em] text-g-muted-fg">{item.description}</dd>}
    </div>
  );
}

export function Stats({ node }: { node: ComponentOf<"stats"> }) {
  const { variant, title, items, style } = node;
  const counting = hasEffect(style?.effects, "counter");
  const ref = useRef<HTMLDListElement | null>(null);
  const seen = useInView(ref, counting);
  const count = Math.min(items.length, 4);

  if (variant === "inline") {
    return (
      <Band style={style}>
        {title && <h2 className="g-h2 mb-8 text-center">{title}</h2>}
        <dl ref={ref} className="g-cols gap-y-10 text-center" data-keep="2" style={cols(count)}>
          {items.map((item) => (
            <div key={item.label} className="flex flex-col items-center [&>dt]:order-2 [&>dt]:mt-2">
              <Stat item={item} counting={counting} started={seen} large />
            </div>
          ))}
        </dl>
      </Band>
    );
  }
  if (variant === "cards") {
    return (
      <section>
        <BlockTitle title={title} />
        <dl ref={ref} className="g-cols" data-keep="2" style={cols(count)}>
          {items.map((item) => (
            <div key={item.label} {...surfaceProps(style)} className="g-card g-lift p-[var(--g-pad)]">
              <Stat item={item} counting={counting} started={seen} large={false} />
            </div>
          ))}
        </dl>
      </section>
    );
  }
  return (
    <section>
      <BlockTitle title={title} />
      {/* Hairlines between cells whatever the number of rows: each cell draws its top and
          left edge and the grid is shifted so the outer ones fall outside the card. */}
      <div {...surfaceProps(style)} className="g-card overflow-hidden">
        <dl
          ref={ref}
          data-keep="2"
          style={cols(items.length > 5 ? 4 : items.length)}
          className="g-cols -mt-px -ml-px w-[calc(100%+1px)] gap-0"
        >
          {items.map((item) => (
            <div key={item.label} className="border-t border-l border-g-border p-[calc(var(--g-pad)*1.1)]">
              <Stat item={item} counting={counting} started={seen} large={false} />
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

// --- Record cards ------------------------------------------------------------------

type CardFields = ComponentOf<"collection">["fields"];

function Meta({ row, fields }: { row: DataRow; fields: CardFields }) {
  if (fields.meta.length === 0) return null;
  return (
    <dl className="flex flex-wrap gap-x-5 gap-y-1 text-[0.86em]">
      {fields.meta.map((entry) => (
        <div key={entry.key} className="flex gap-1.5">
          <dt className="text-g-muted-fg">{entry.label}</dt>
          <dd className="font-medium tabular-nums">{formatValue(row[entry.key], entry.format)}</dd>
        </div>
      ))}
    </dl>
  );
}

/** A record's card or row becomes a button when it has an action. */
function Clickable({
  action,
  row,
  label,
  className,
  children,
}: {
  action?: ActionSpec;
  row: DataRow;
  label: string;
  className?: string;
  children: React.ReactNode;
}) {
  const run = useAction();
  if (!action) return <div className={className}>{children}</div>;
  return (
    <button type="button" aria-label={`Open ${label}`} onClick={() => void run(action, { row })} className={cn("w-full text-left", className)}>
      {children}
    </button>
  );
}

function shortDate(value: string | undefined): string | undefined {
  if (!value) return undefined;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

export function Collection({ node }: { node: ComponentOf<"collection"> }) {
  const { variant, title, subtitle, fields, columns, item_action: action, style } = node;
  const rows = useRows(node);
  const count = <span className="text-[0.86em] text-g-muted-fg tabular-nums">{rows.length}</span>;
  const empty = (
    <p className="g-card p-[calc(var(--g-pad)*1.5)] text-center text-g-muted-fg">{node.empty_text ?? "Nothing here yet."}</p>
  );
  const heading = <BlockTitle title={title} subtitle={subtitle} aside={title ? count : undefined} />;
  if (rows.length === 0) {
    return (
      <section>
        {heading}
        {empty}
      </section>
    );
  }

  if (variant === "cards" || variant === "media") {
    const media = variant === "media";
    return (
      <section>
        {heading}
        <div className="g-cols" style={cols(columns)}>
          {rows.map((row, index) => {
            const name = cell(row, fields.title) ?? "—";
            return (
              <Clickable
                key={rowKey(row, index)}
                action={action}
                row={row}
                label={name}
                className={cn("g-card g-lift flex h-full flex-col overflow-hidden", !media && "gap-3 p-[var(--g-pad)]")}
              >
                {(media || fields.image) && (
                  <AssetImage assetId={cell(row, fields.image)} alt={name} aspect="photo" className={media ? undefined : "-m-[var(--g-pad)] mb-0"} />
                )}
                <div className={cn("flex flex-1 flex-col gap-2", media && "p-[var(--g-pad)]")}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-2.5">
                      {fields.avatar && <Avatar name={name} />}
                      <div className="min-w-0">
                        <p className="truncate font-semibold">{name}</p>
                        {cell(row, fields.subtitle) && (
                          <p className="truncate text-[0.9em] text-g-muted-fg">{cell(row, fields.subtitle)}</p>
                        )}
                      </div>
                    </div>
                    {cell(row, fields.badge) && <StatusPill label={cell(row, fields.badge)!} />}
                  </div>
                  {cell(row, fields.description) && (
                    <p className="line-clamp-2 text-[0.93em] text-g-muted-fg">{cell(row, fields.description)}</p>
                  )}
                  <div className="mt-auto">
                    <Meta row={row} fields={fields} />
                  </div>
                </div>
              </Clickable>
            );
          })}
        </div>
      </section>
    );
  }

  if (variant === "feed") {
    return (
      <section {...surfaceProps(style)} className="g-card p-[var(--g-pad)]">
        {heading}
        <ol className="relative ml-1.5 flex flex-col gap-4 border-l border-g-border pl-5">
          {rows.map((row, index) => {
            const name = cell(row, fields.title) ?? "—";
            return (
              <li key={rowKey(row, index)} className="relative">
                <span aria-hidden className="absolute top-1.5 -left-[25px] size-2 rounded-full bg-g-primary ring-4 ring-[var(--g-card-bg)]" />
                <Clickable action={action} row={row} label={name} className="flex flex-col gap-0.5">
                  <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                    <p className="font-medium">{name}</p>
                    {cell(row, fields.timestamp) && (
                      <time className="text-[0.82em] text-g-muted-fg">{shortDate(cell(row, fields.timestamp))}</time>
                    )}
                  </div>
                  {(cell(row, fields.subtitle) || cell(row, fields.description)) && (
                    <p className="text-[0.9em] text-g-muted-fg">{cell(row, fields.subtitle) ?? cell(row, fields.description)}</p>
                  )}
                  {cell(row, fields.badge) && <StatusPill label={cell(row, fields.badge)!} />}
                </Clickable>
              </li>
            );
          })}
        </ol>
      </section>
    );
  }

  const compact = variant === "compact";
  return (
    // A container of its own: in a narrow column the secondary figures give way to the names.
    <section {...surfaceProps(style)} className="g-card @container overflow-hidden">
      {(title || subtitle) && <div className="px-[var(--g-pad)] pt-[var(--g-pad)]">{heading}</div>}
      <ul className="divide-y divide-g-border">
        {rows.map((row, index) => {
          const name = cell(row, fields.title) ?? "—";
          const first = fields.meta[0];
          return (
            <li key={rowKey(row, index)}>
              <Clickable
                action={action}
                row={row}
                label={name}
                className={cn(
                  "flex items-center gap-3 px-[var(--g-pad)] transition-colors duration-[var(--g-duration-fast)]",
                  compact ? "py-2.5" : "py-3.5",
                  action && "hover:bg-g-muted",
                )}
              >
                {fields.avatar && <Avatar name={name} size={compact ? "sm" : "md"} />}
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">{name}</p>
                  {cell(row, fields.subtitle) && (
                    <p className="truncate text-[0.88em] text-g-muted-fg">{cell(row, fields.subtitle)}</p>
                  )}
                </div>
                {compact ? (
                  first && <span className="shrink-0 text-[0.88em] text-g-muted-fg tabular-nums @max-[340px]:hidden">{formatValue(row[first.key], first.format)}</span>
                ) : (
                  <div className="shrink-0 @max-[460px]:hidden">
                    <Meta row={row} fields={fields} />
                  </div>
                )}
                {cell(row, fields.badge) && <StatusPill label={cell(row, fields.badge)!} />}
                {action && <ChevronRight size={16} aria-hidden className="shrink-0 text-g-muted-fg" />}
              </Clickable>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

// --- Kanban ------------------------------------------------------------------------

const TONE_VAR = {
  neutral: "var(--g-muted-fg)",
  info: "var(--g-primary)",
  success: "var(--g-success)",
  warning: "var(--g-warning)",
  danger: "var(--g-destructive)",
} as const;

export function Kanban({ node }: { node: ComponentOf<"kanban"> }) {
  const { title, columns, group_by: groupBy, fields, item_action: action, move_action: move } = node;
  const rows = useRows(node);
  const { dispatchAction, mode } = useRenderer();
  const run = useAction();
  const [dragging, setDragging] = useState<string | null>(null);
  const [over, setOver] = useState<string | null>(null);
  const canMove = Boolean(move) && mode !== "edit";

  const moveTo = async (row: DataRow, value: string) => {
    if (!move || String(row[groupBy]) === value) return;
    // The static payload names the entity and field; the destination column is the value.
    await dispatchAction(move, { value }, { row } satisfies ActionContext);
  };
  const onDrop = (event: DragEvent, value: string) => {
    event.preventDefault();
    const id = event.dataTransfer.getData("text/plain") || dragging;
    const row = rows.find((candidate) => String(candidate[PRIMARY_KEY]) === id);
    setDragging(null);
    setOver(null);
    if (row) void moveTo(row, value);
  };

  return (
    <section>
      <BlockTitle title={title} />
      <div className="g-scroll-x items-start">
        {columns.map((column, position) => {
          const members = rows.filter((row) => String(row[groupBy]) === column.value);
          const next = columns[position + 1];
          return (
            <div
              key={column.value}
              role="group"
              aria-label={`${column.label}, ${members.length}`}
              onDragOver={canMove ? (event) => (event.preventDefault(), setOver(column.value)) : undefined}
              onDragLeave={() => setOver((current) => (current === column.value ? null : current))}
              onDrop={canMove ? (event) => onDrop(event, column.value) : undefined}
              style={{ "--tone": TONE_VAR[column.tone] } as CSSProperties}
              className={cn(
                "flex w-[272px] flex-col gap-2.5 rounded-g bg-g-muted p-2.5 transition-shadow duration-[var(--g-duration-fast)]",
                over === column.value && "shadow-[inset_0_0_0_2px_var(--g-primary)]",
              )}
            >
              <header className="flex items-center gap-2 px-1.5 pt-1">
                <span aria-hidden className="size-2 rounded-full bg-[var(--tone)]" />
                <h3 className="flex-1 text-[0.9em] font-semibold">{column.label}</h3>
                <span className="rounded-full bg-g-surface px-2 text-[0.8em] text-g-muted-fg tabular-nums">{members.length}</span>
              </header>
              {members.map((row, index) => {
                const name = cell(row, fields.title) ?? "—";
                const id = rowKey(row, index);
                const badge = fields.badge !== groupBy ? cell(row, fields.badge) : undefined;
                return (
                  <article
                    key={id}
                    draggable={canMove}
                    onDragStart={(event) => {
                      event.dataTransfer.setData("text/plain", id);
                      event.dataTransfer.effectAllowed = "move";
                      setDragging(id);
                    }}
                    onDragEnd={() => setDragging(null)}
                    className={cn("g-card flex flex-col gap-2 p-3", canMove && "cursor-grab active:cursor-grabbing", dragging === id && "opacity-50")}
                  >
                    <button
                      type="button"
                      disabled={!action}
                      aria-label={`Open ${name}`}
                      onClick={() => void run(action, { row })}
                      className="flex items-center gap-2.5 text-left enabled:hover:text-g-primary"
                    >
                      {fields.avatar && <Avatar name={name} size="sm" />}
                      <span className="min-w-0">
                        <span className="block truncate font-medium">{name}</span>
                        {cell(row, fields.subtitle) && (
                          <span className="block truncate text-[0.86em] text-g-muted-fg">{cell(row, fields.subtitle)}</span>
                        )}
                      </span>
                    </button>
                    {badge && <StatusPill label={badge} />}
                    <Meta row={row} fields={fields} />
                    {/* Dragging has a keyboard and touch equivalent: one step forward. */}
                    {canMove && next && (
                      <button
                        type="button"
                        onClick={() => void moveTo(row, next.value)}
                        className="mt-0.5 inline-flex w-fit items-center gap-1 rounded text-[0.8em] font-medium text-g-muted-fg hover:text-g-primary"
                      >
                        Move to {next.label}
                        <ArrowRight size={12} aria-hidden />
                      </button>
                    )}
                  </article>
                );
              })}
              {members.length === 0 && <p className="px-1.5 py-3 text-[0.86em] text-g-muted-fg">Nothing here.</p>}
            </div>
          );
        })}
      </div>
    </section>
  );
}

// --- One record --------------------------------------------------------------------

export function Detail({ node }: { node: ComponentOf<"detail"> }) {
  const [row] = useRows(node);
  const narrow = node.variant === "list";
  return (
    <section {...surfaceProps(node.style)} className="g-card p-[var(--g-pad)]">
      <BlockTitle title={node.title} />
      {row ? (
        <dl className={narrow ? "flex flex-col divide-y divide-g-border" : "g-cols gap-x-8 gap-y-5"} style={narrow ? undefined : cols(node.columns)}>
          {node.fields.map((field) => (
            <div key={field.key} className={narrow ? "flex items-baseline justify-between gap-4 py-2.5 first:pt-0 last:pb-0" : "min-w-0"}>
              <dt className="text-[0.84em] text-g-muted-fg">{field.label}</dt>
              <dd className={cn("font-medium break-words", !narrow && "mt-0.5")}>{formatValue(row[field.key], field.format)}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="text-g-muted-fg">No record selected.</p>
      )}
    </section>
  );
}

export function ProfileHeader({ node }: { node: ComponentOf<"profile_header"> }) {
  const { fields, actions, variant, style } = node;
  const [row] = useRows(node);
  if (!row) {
    return <p className="g-card p-[calc(var(--g-pad)*1.5)] text-g-muted-fg">This record could not be found.</p>;
  }
  const name = cell(row, fields.title) ?? "—";
  const compact = variant === "compact";
  return (
    <header
      {...surfaceProps(style)}
      className={cn("g-card flex flex-wrap items-center gap-x-6 gap-y-4", compact ? "p-[var(--g-pad)]" : "p-[calc(var(--g-pad)*1.5)]")}
    >
      {fields.image && cell(row, fields.image) ? (
        <AssetImage assetId={cell(row, fields.image)} alt={name} aspect="square" className={cn("rounded-g", compact ? "size-12" : "size-20")} />
      ) : (
        <Avatar name={name} size={compact ? "md" : "lg"} />
      )}
      <div className="min-w-[200px] flex-1">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className={compact ? "g-h3 font-semibold" : "g-h2 !text-[calc(1.6em*var(--g-heading-scale))]"}>{name}</h2>
          {cell(row, fields.badge) && <StatusPill label={cell(row, fields.badge)!} />}
        </div>
        {cell(row, fields.subtitle) && <p className="mt-0.5 text-g-muted-fg">{cell(row, fields.subtitle)}</p>}
        {!compact && cell(row, fields.description) && <p className="mt-2 max-w-2xl">{cell(row, fields.description)}</p>}
        {fields.meta.length > 0 && (
          <div className="mt-3">
            <Meta row={row} fields={fields} />
          </div>
        )}
      </div>
      <ActionButtons actions={actions} context={{ row }} />
    </header>
  );
}

// --- Agenda ------------------------------------------------------------------------

function dayLabel(value: string): { weekday: string; day: string } {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return { weekday: "", day: value };
  return {
    weekday: date.toLocaleDateString(undefined, { weekday: "short" }),
    day: date.toLocaleDateString(undefined, { day: "numeric", month: "short" }),
  };
}

export function Calendar({ node }: { node: ComponentOf<"calendar"> }) {
  const rows = useRows(node);
  const action = node.item_action;
  const days = useMemo(() => {
    const grouped = new Map<string, DataRow[]>();
    for (const row of rows) {
      const day = String(row[node.date_field] ?? "—");
      grouped.set(day, [...(grouped.get(day) ?? []), row]);
    }
    return [...grouped.entries()];
  }, [rows, node.date_field]);

  return (
    <section {...surfaceProps(node.style)} className="g-card p-[var(--g-pad)]">
      <BlockTitle title={node.title} />
      {days.length === 0 ? (
        <p className="text-g-muted-fg">Nothing scheduled.</p>
      ) : (
        <ol className="flex flex-col gap-5">
          {days.map(([day, items]) => {
            const label = dayLabel(day);
            return (
              <li key={day} className="grid grid-cols-[64px_minmax(0,1fr)] gap-4">
                <p className="pt-2 leading-tight">
                  <span className="block text-[0.76em] tracking-wide text-g-muted-fg uppercase">{label.weekday}</span>
                  <span className="font-semibold">{label.day}</span>
                </p>
                <ul className="flex flex-col gap-2 border-l border-g-border pl-4">
                  {items.map((row, index) => {
                    const name = cell(row, node.title_field) ?? "—";
                    return (
                      <li key={rowKey(row, index)}>
                        <Clickable
                          action={action}
                          row={row}
                          label={name}
                          className={cn("flex items-center gap-3 rounded-g px-2.5 py-2", action && "hover:bg-g-muted")}
                        >
                          {node.time_field && (
                            <time className="w-12 shrink-0 text-[0.88em] text-g-muted-fg tabular-nums">{cell(row, node.time_field) ?? ""}</time>
                          )}
                          <span className="min-w-0 flex-1">
                            <span className="block truncate font-medium">{name}</span>
                            {cell(row, node.subtitle_field) && (
                              <span className="block truncate text-[0.88em] text-g-muted-fg">{cell(row, node.subtitle_field)}</span>
                            )}
                          </span>
                          {cell(row, node.badge_field) && <StatusPill label={cell(row, node.badge_field)!} />}
                        </Clickable>
                      </li>
                    );
                  })}
                </ul>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}

// --- Command bar -------------------------------------------------------------------

export function Command({ node }: { node: ComponentOf<"command"> }) {
  const run = useAction();
  const [query, setQuery] = useState("");
  const listId = useId();
  const matching = node.items.filter((item) => item.label.toLowerCase().includes(query.trim().toLowerCase()));
  return (
    <section {...surfaceProps(node.style)} className="g-card overflow-hidden">
      <form
        role="search"
        className="flex items-center gap-3 border-b border-g-border px-[var(--g-pad)]"
        onSubmit={(event) => {
          event.preventDefault();
          void run(matching[0]?.action);
        }}
      >
        <Search size={17} aria-hidden className="shrink-0 text-g-muted-fg" />
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={node.placeholder}
          aria-label={node.placeholder}
          aria-controls={listId}
          className="h-[calc(var(--g-control-h)*1.25)] w-full bg-transparent outline-none placeholder:text-g-muted-fg"
        />
        <kbd className="g-hide-narrow rounded border border-g-border px-1.5 py-0.5 font-mono text-[0.72em] text-g-muted-fg">Enter</kbd>
      </form>
      <ul id={listId} className="max-h-72 overflow-auto p-1.5">
        {matching.map((item) => (
          <li key={item.label}>
            <button
              type="button"
              onClick={() => void run(item.action)}
              className="flex w-full items-center gap-3 rounded-[calc(var(--g-radius)*0.7)] px-2.5 py-2 text-left hover:bg-g-muted"
            >
              <Icon name={item.icon ?? "arrow-right"} size={16} className="shrink-0 text-g-muted-fg" />
              <span className="flex-1">{item.label}</span>
              {item.hint && <span className="text-[0.82em] text-g-muted-fg">{item.hint}</span>}
            </button>
          </li>
        ))}
        {matching.length === 0 && <li className="px-2.5 py-3 text-g-muted-fg">No matching command.</li>}
      </ul>
    </section>
  );
}
