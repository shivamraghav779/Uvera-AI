import type { ReactNode } from "react";

import { cn } from "@/utils/cn";

type Tone = "neutral" | "accent" | "success" | "warning" | "danger";

const TONE: Record<Tone, string> = {
  neutral: "bg-app-subtle text-app-muted",
  accent: "bg-app-accent-soft text-app-accent",
  success: "bg-[color-mix(in_srgb,var(--app-success)_14%,transparent)] text-app-success",
  warning: "bg-[color-mix(in_srgb,var(--app-warning)_14%,transparent)] text-app-warning",
  danger: "bg-[color-mix(in_srgb,var(--app-danger)_14%,transparent)] text-app-danger",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={cn("inline-flex h-5 items-center rounded px-1.5 text-[11px] font-medium", TONE[tone])}>
      {children}
    </span>
  );
}
