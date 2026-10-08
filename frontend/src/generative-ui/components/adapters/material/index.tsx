/**
 * Material-style adapter.
 *
 * A second, deliberately partial adapter: it restyles the core controls and
 * surfaces in the spirit of Material Design (elevation, filled fields,
 * uppercase actions, underlined tabs) and lets everything else fall back to the
 * default adapter. It is written in-house; it does not wrap @mui/material.
 * Its job is to prove that the same UI document renders through a different
 * framework without the document changing.
 */
import * as RadixTabs from "@radix-ui/react-tabs";
import { Check, ChevronDown, Loader2 } from "lucide-react";

import { cn } from "@/utils/cn";

import { feedbackStyle, toneStyle, TONE_WASH } from "../shared";
import type {
  AlertViewProps,
  BadgeViewProps,
  ButtonViewProps,
  CardViewProps,
  CheckboxViewProps,
  FrameworkAdapter,
  InputViewProps,
  MetricViewProps,
  SelectViewProps,
  TabsViewProps,
} from "../types";

/** Elevation replaces borders. Falls back to a visible shadow when the theme has none. */
const ELEVATED =
  "rounded-g bg-g-surface shadow-[var(--g-shadow),0_1px_3px_rgb(0_0_0/0.12),0_1px_2px_rgb(0_0_0/0.08)]";

const FILLED = cn(
  "peer w-full rounded-t-[4px] border-b-2 border-g-border bg-g-muted px-3 pt-5 pb-1 text-g-fg",
  "transition-colors focus-visible:border-g-primary focus-visible:outline-none",
);
const FLOATING_LABEL = "pointer-events-none absolute top-1.5 left-3 text-[0.75em] font-medium text-g-muted-fg";

function Card({ title, subtitle, tone, emphasis, children }: CardViewProps) {
  return (
    <article
      style={toneStyle(tone)}
      className={cn(
        ELEVATED,
        "flex h-full flex-col gap-[calc(var(--g-gap)*0.75)] p-[var(--g-pad)]",
        emphasis === "strong" && TONE_WASH,
      )}
    >
      {(title || subtitle) && (
        <header>
          {title && <h3 className="text-[1.1em] font-medium">{title}</h3>}
          {subtitle && <p className="text-[0.9em] text-g-muted-fg">{subtitle}</p>}
        </header>
      )}
      {children}
    </article>
  );
}

function Metric({ title, value, unit, trend, description, tone }: MetricViewProps) {
  return (
    <div style={toneStyle(tone)} className={cn(ELEVATED, "relative h-full overflow-hidden p-[var(--g-pad)]")}>
      <span aria-hidden className="absolute inset-x-0 top-0 h-1 bg-g-tone" />
      <p className="text-[0.75em] font-medium tracking-[0.08em] text-g-muted-fg uppercase">{title}</p>
      <p className="mt-1 text-[2.1em] leading-tight font-normal tabular-nums">
        {unit && <span className="mr-0.5 text-[0.6em] text-g-muted-fg">{unit}</span>}
        {value}
      </p>
      {trend && (
        <p className="mt-1 text-[0.88em] text-g-muted-fg">
          <span
            className={cn(
              "font-medium",
              trend.direction === "up" && "text-g-success",
              trend.direction === "down" && "text-g-destructive",
            )}
          >
            {trend.direction === "up" ? "▲" : trend.direction === "down" ? "▼" : "•"} {trend.value}
          </span>
          {trend.label && ` ${trend.label}`}
        </p>
      )}
      {description && <p className="mt-1 text-[0.85em] text-g-muted-fg">{description}</p>}
    </div>
  );
}

function Tabs({ tabs, defaultTab }: TabsViewProps) {
  return (
    <RadixTabs.Root defaultValue={defaultTab ?? tabs[0]?.id} className="flex flex-col gap-[var(--g-gap)]">
      <RadixTabs.List className="flex border-b border-g-border">
        {tabs.map((tab) => (
          <RadixTabs.Trigger
            key={tab.id}
            value={tab.id}
            className={cn(
              "-mb-px border-b-2 border-transparent px-4 py-2.5 text-[0.85em] font-medium tracking-[0.06em]",
              "text-g-muted-fg uppercase hover:bg-g-muted",
              "data-[state=active]:border-g-primary data-[state=active]:text-g-primary",
            )}
          >
            {tab.label}
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
      {tabs.map((tab) => (
        <RadixTabs.Content key={tab.id} value={tab.id}>
          {tab.content}
        </RadixTabs.Content>
      ))}
    </RadixTabs.Root>
  );
}

function Input({ id, name, label, inputType, placeholder, value, required, onChange }: InputViewProps) {
  const shared = {
    id,
    name,
    value,
    required,
    placeholder,
    onChange: (event: { target: { value: string } }) => onChange(event.target.value),
  };
  return (
    <div className="relative">
      {inputType === "textarea" ? (
        <textarea rows={3} {...shared} className={FILLED} />
      ) : (
        <input type={inputType} {...shared} className={cn(FILLED, "h-[calc(var(--g-control-h)+14px)]")} />
      )}
      <label htmlFor={id} className={FLOATING_LABEL}>
        {label}
        {required && " *"}
      </label>
    </div>
  );
}

function Select({ id, name, label, options, value, required, onChange }: SelectViewProps) {
  return (
    <div className="relative">
      <select
        id={id}
        name={name}
        value={value}
        required={required}
        onChange={(event) => onChange(event.target.value)}
        className={cn(FILLED, "h-[calc(var(--g-control-h)+14px)] appearance-none pr-9")}
      >
        <option value="">All</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <label htmlFor={id} className={FLOATING_LABEL}>
        {label}
        {required && " *"}
      </label>
      <ChevronDown
        size={18}
        aria-hidden
        className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-g-muted-fg"
      />
    </div>
  );
}

function Checkbox({ id, name, label, checked, onChange }: CheckboxViewProps) {
  return (
    <label htmlFor={id} className="flex w-fit cursor-pointer items-center gap-3">
      <span className="relative grid size-5 place-items-center">
        <input
          id={id}
          name={name}
          type="checkbox"
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
          className={cn(
            "peer size-5 appearance-none rounded-[2px] border-2 border-g-muted-fg",
            "checked:border-g-primary checked:bg-g-primary",
          )}
        />
        <Check
          size={14}
          strokeWidth={3.5}
          aria-hidden
          className="pointer-events-none absolute hidden text-g-primary-fg peer-checked:block"
        />
      </span>
      <span>{label}</span>
    </label>
  );
}

const BUTTON_VARIANT = {
  primary: "bg-g-primary text-g-primary-fg shadow-[0_2px_4px_rgb(0_0_0/0.2)] hover:shadow-[0_4px_8px_rgb(0_0_0/0.25)]",
  secondary: "border border-g-primary text-g-primary hover:bg-[color-mix(in_srgb,var(--g-primary)_8%,transparent)]",
  danger: "bg-g-destructive text-g-destructive-fg shadow-[0_2px_4px_rgb(0_0_0/0.2)]",
  ghost: "text-g-primary hover:bg-[color-mix(in_srgb,var(--g-primary)_8%,transparent)]",
  outline: "border border-current text-g-fg hover:bg-[color-mix(in_srgb,currentColor_8%,transparent)]",
  gradient:
    "bg-g-primary bg-[image:var(--g-accent-fill)] text-g-primary-fg shadow-[0_2px_4px_rgb(0_0_0/0.2)] hover:shadow-[0_4px_8px_rgb(0_0_0/0.25)]",
  glass:
    "border border-[color-mix(in_srgb,currentColor_22%,transparent)] bg-[color-mix(in_srgb,var(--g-surface)_45%,transparent)] backdrop-blur-md",
} as const satisfies Record<ButtonViewProps["variant"], string>;

function Button({ label, variant, disabled, busy, onClick }: ButtonViewProps) {
  return (
    <button
      type="button"
      disabled={disabled || busy}
      aria-busy={busy}
      onClick={onClick}
      className={cn(
        "inline-flex h-[var(--g-control-h)] w-fit items-center justify-center gap-2 rounded-g px-4",
        "text-[0.88em] font-medium tracking-[0.06em] uppercase transition-shadow",
        "disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none",
        BUTTON_VARIANT[variant],
      )}
    >
      {busy && <Loader2 size={15} aria-hidden className="animate-spin" />}
      {label}
    </button>
  );
}

function Badge({ label, tone }: BadgeViewProps) {
  return (
    <span
      style={feedbackStyle(tone)}
      className="inline-flex h-6 w-fit items-center rounded-full bg-g-tone px-3 text-[0.8em] font-medium text-g-surface"
    >
      {label}
    </span>
  );
}

function Alert({ title, message, tone }: AlertViewProps) {
  return (
    <div
      role={tone === "danger" || tone === "warning" ? "alert" : "status"}
      style={feedbackStyle(tone)}
      className={cn("rounded-[4px] border-l-4 border-g-tone p-[var(--g-pad)]", TONE_WASH)}
    >
      {title && <p className="font-medium">{title}</p>}
      <p className="whitespace-pre-line">{message}</p>
    </div>
  );
}

export const materialAdapter: FrameworkAdapter = {
  id: "material",
  name: "Material",
  components: { Card, Metric, Tabs, Input, Select, Checkbox, Button, Badge, Alert },
};
