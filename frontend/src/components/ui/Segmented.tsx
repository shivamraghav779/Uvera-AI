import type { ReactNode } from "react";

import { cn } from "@/utils/cn";

interface Option<T extends string> {
  value: T;
  label: string;
  icon?: ReactNode;
}

interface SegmentedProps<T extends string> {
  /** Accessible name of the group. */
  label: string;
  value: T;
  options: readonly Option<T>[];
  onChange: (value: T) => void;
  /** Show only icons (labels stay available to assistive technology). */
  iconOnly?: boolean;
}

/** A two-or-three-way switch. Used where the current choice must be obvious. */
export function Segmented<T extends string>({ label, value, options, onChange, iconOnly }: SegmentedProps<T>) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-md bg-app-subtle p-0.5">
      {options.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={iconOnly ? option.label : undefined}
            title={iconOnly ? option.label : undefined}
            onClick={() => onChange(option.value)}
            className={cn(
              "inline-flex h-7 items-center gap-1.5 rounded px-2.5 text-xs font-medium transition-colors",
              selected ? "bg-app-panel text-app-fg shadow-sm" : "text-app-muted hover:text-app-fg",
            )}
          >
            {option.icon}
            {!iconOnly && option.label}
          </button>
        );
      })}
    </div>
  );
}
