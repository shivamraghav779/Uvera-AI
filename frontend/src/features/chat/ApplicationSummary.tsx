/**
 * What a proposed application consists of, so it can be judged as a whole
 * before anything is saved: its screens, look, data, interactions and the
 * result of the design review.
 */
import { AlertTriangle, Database, Image as ImageIcon, LayoutGrid, MousePointerClick, Navigation, Palette } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/Badge";
import type { ApplicationSummary as Summary, QualityRead } from "@/services/api/types";
import { cn } from "@/utils/cn";

interface ApplicationSummaryProps {
  summary: Summary;
  quality?: QualityRead | null;
  /** Show a screen of the proposal on the canvas. */
  onOpenScreen?: (route: string) => void;
}

const NAVIGATION_LABEL: Record<string, string> = {
  sidebar: "Sidebar navigation",
  topbar: "Top navigation",
  bottom: "Bottom navigation",
  minimal: "Minimal navigation",
  none: "No navigation",
};

function words(value: string): string {
  return value.replaceAll("_", " ");
}

function Row({ icon, label, children }: { icon: ReactNode; label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[18px_88px_minmax(0,1fr)] items-start gap-x-2 text-sm">
      <span aria-hidden className="mt-0.5 text-app-muted">
        {icon}
      </span>
      <dt className="text-app-muted">{label}</dt>
      <dd className="min-w-0">{children}</dd>
    </div>
  );
}

export function ApplicationSummary({ summary, quality, onOpenScreen }: ApplicationSummaryProps) {
  const failed = summary.screens.filter((screen) => screen.failed);
  const concerns = (quality?.issues ?? []).filter((issue) => issue.severity === "major").slice(0, 3);
  return (
    <div className="flex flex-col gap-3">
      <div>
        <p className="font-semibold">
          {summary.name} <span className="font-normal text-app-muted">· {summary.category}</span>
        </p>
        <p className="mt-0.5 text-sm text-app-muted">{summary.description}</p>
      </div>

      <dl className="flex flex-col gap-2">
        <Row icon={<LayoutGrid size={14} />} label={`${summary.screens.length} screens`}>
          <ul aria-label="Screens" className="flex flex-wrap gap-1">
            {summary.screens.map((screen) => (
              <li key={screen.id}>
                <button
                  type="button"
                  disabled={!onOpenScreen}
                  title={screen.failed ? "This screen could not be generated" : screen.route}
                  onClick={() => onOpenScreen?.(screen.route)}
                  className={cn(
                    "rounded-md border px-1.5 py-0.5 text-xs enabled:hover:border-app-accent",
                    screen.failed ? "border-app-danger/50 text-app-danger" : "border-app-border",
                  )}
                >
                  {screen.title}
                </button>
              </li>
            ))}
          </ul>
        </Row>
        <Row icon={<Palette size={14} />} label="Design">
          <span className="font-medium">{summary.design.style_name}</span>
          {summary.design.summary && <span className="text-app-muted"> · {summary.design.summary}</span>}
          {summary.design.mood.length > 0 && (
            <span className="mt-1 flex flex-wrap gap-1">
              {summary.design.mood.map((mood) => (
                <Badge key={mood}>{mood}</Badge>
              ))}
            </span>
          )}
        </Row>
        <Row icon={<Navigation size={14} />} label="Navigation">
          {NAVIGATION_LABEL[summary.navigation_style] ?? words(summary.navigation_style)}
        </Row>
        {summary.entities.length > 0 && (
          <Row icon={<Database size={14} />} label="Data">
            {summary.entities.map((entity) => `${entity.label} (${entity.record_count})`).join(", ")}
          </Row>
        )}
        {summary.interactions.length > 0 && (
          <Row icon={<MousePointerClick size={14} />} label="Interactions">
            {summary.interactions.slice(0, 6).join(" · ")}
            {summary.interactions.length > 6 && (
              <span className="text-app-muted"> and {summary.interactions.length - 6} more</span>
            )}
          </Row>
        )}
        <Row icon={<ImageIcon size={14} />} label="Contents">
          {summary.component_count} components of {summary.pattern_count} kinds, {summary.asset_count} image
          {summary.asset_count === 1 ? "" : "s"}
          {quality && <span className="text-app-muted"> · design review {quality.score}/100</span>}
        </Row>
      </dl>

      {(failed.length > 0 || concerns.length > 0) && (
        <ul className="flex flex-col gap-1 rounded-md border border-app-border bg-app-subtle p-2 text-xs">
          {failed.length > 0 && (
            <li className="flex items-start gap-1.5">
              <AlertTriangle size={13} aria-hidden className="mt-px shrink-0 text-app-danger" />
              <span>
                {failed.map((screen) => screen.title).join(", ")} could not be generated. The rest works; apply
                it, then open that screen and regenerate it.
              </span>
            </li>
          )}
          {concerns.map((issue, index) => (
            <li key={index} className="flex items-start gap-1.5 text-app-muted">
              <AlertTriangle size={13} aria-hidden className="mt-px shrink-0" />
              <span>{issue.message}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
