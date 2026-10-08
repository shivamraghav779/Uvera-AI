import {
  AppWindow,
  ArrowLeftRight,
  Database,
  LayoutTemplate,
  Maximize2,
  Minus,
  MoveRight,
  Navigation,
  Paintbrush,
  Palette,
  Pencil,
  Plus,
  Replace,
} from "lucide-react";

import type { ChangeRead } from "@/services/api/types";

const ICON: Record<ChangeRead["kind"], typeof Plus> = {
  theme: Palette,
  framework: LayoutTemplate,
  design_system: Paintbrush,
  added: Plus,
  removed: Minus,
  replaced: Replace,
  moved: MoveRight,
  resized: Maximize2,
  restyled: Paintbrush,
  updated: Pencil,
  application: AppWindow,
  navigation: Navigation,
  data: Database,
};

const MAX_SHOWN = 8;

interface ChangePreviewProps {
  changes: readonly ChangeRead[];
  /** Shown when there is nothing to list. */
  emptyText?: string;
  limit?: number;
}

/** A schema-based list of differences between two UI states. */
export function ChangePreview({ changes, emptyText = "No differences.", limit = MAX_SHOWN }: ChangePreviewProps) {
  if (changes.length === 0) {
    return (
      <p className="flex items-center gap-2 text-sm text-app-muted">
        <ArrowLeftRight size={14} aria-hidden /> {emptyText}
      </p>
    );
  }
  const shown = changes.slice(0, limit);
  return (
    <div>
      <p className="mb-1.5 text-xs font-medium text-app-muted">
        {changes.length} change{changes.length === 1 ? "" : "s"}
      </p>
      <ul className="flex flex-col gap-1">
        {shown.map((change, index) => {
          const Icon = ICON[change.kind];
          return (
            <li key={index} className="flex items-start gap-2 text-sm">
              <Icon size={14} aria-hidden className="mt-0.5 shrink-0 text-app-muted" />
              <span>{change.summary}</span>
            </li>
          );
        })}
      </ul>
      {changes.length > shown.length && (
        <p className="mt-1 text-xs text-app-muted">and {changes.length - shown.length} more</p>
      )}
    </div>
  );
}
