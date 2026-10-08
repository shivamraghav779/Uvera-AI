import { CheckCircle2, Info, X, XCircle } from "lucide-react";

import { useToastStore, type ToastTone } from "@/stores/toastStore";
import { cn } from "@/utils/cn";

const ICON: Record<ToastTone, typeof Info> = { info: Info, success: CheckCircle2, error: XCircle };
const TONE: Record<ToastTone, string> = {
  info: "text-app-accent",
  success: "text-app-success",
  error: "text-app-danger",
};

/** Transient notifications, announced to assistive technology. */
export function Toaster() {
  const toasts = useToastStore((state) => state.toasts);
  const dismiss = useToastStore((state) => state.dismiss);
  return (
    <div aria-live="polite" className="pointer-events-none fixed top-14 right-4 z-[60] flex w-80 flex-col gap-2">
      {toasts.map((toast) => {
        const Icon = ICON[toast.tone];
        return (
          <div
            key={toast.id}
            role={toast.tone === "error" ? "alert" : "status"}
            className="pointer-events-auto flex items-start gap-2.5 rounded-lg border border-app-border bg-app-raised p-3 text-sm shadow-app-float"
          >
            <Icon size={16} aria-hidden className={cn("mt-0.5 shrink-0", TONE[toast.tone])} />
            <p className="flex-1">{toast.message}</p>
            <button
              type="button"
              aria-label="Dismiss"
              onClick={() => dismiss(toast.id)}
              className="rounded p-0.5 text-app-muted hover:text-app-fg"
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
