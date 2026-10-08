import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";

interface StateMessageProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  /** Technical details, e.g. validation issues. */
  details?: string[];
  action?: ReactNode;
  tone?: "neutral" | "error";
}

/** Centered message for empty and error states. */
export function StateMessage({ icon, title, description, details, action, tone = "neutral" }: StateMessageProps) {
  return (
    <div role={tone === "error" ? "alert" : undefined} className="grid h-full place-items-center p-8">
      <div className="flex max-w-md flex-col items-center gap-3 text-center">
        <div
          className={
            tone === "error"
              ? "grid size-10 place-items-center rounded-full bg-[color-mix(in_srgb,var(--app-danger)_12%,transparent)] text-app-danger"
              : "grid size-10 place-items-center rounded-full bg-app-subtle text-app-muted"
          }
        >
          {icon ?? <AlertTriangle size={18} />}
        </div>
        <h2 className="text-base font-semibold">{title}</h2>
        {description && <p className="text-sm text-app-muted">{description}</p>}
        {details && details.length > 0 && (
          <ul className="w-full rounded-md bg-app-subtle p-3 text-left font-mono text-xs text-app-muted">
            {details.slice(0, 6).map((detail) => (
              <li key={detail}>{detail}</li>
            ))}
          </ul>
        )}
        {action}
      </div>
    </div>
  );
}
