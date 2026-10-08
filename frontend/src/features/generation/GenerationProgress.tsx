/**
 * What the canvas shows while the first version is being built. Every line
 * here is reported by the server's pipeline: the stage, the percentage and the
 * sentence underneath. Nothing is animated on a timer to look busy.
 */
import { Check, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { useChatStore } from "@/stores/chatStore";
import { cn } from "@/utils/cn";

import { useAssistant } from "../chat/useAssistant";

import { BUILD_STAGES, stageStates } from "./stages";

export function GenerationProgress({ workspaceId }: { workspaceId: string }) {
  const job = useChatStore((state) => state.job);
  const instruction = useChatStore((state) => state.pendingMessage);
  const assistant = useAssistant(workspaceId);
  const states = stageStates(job);
  const percent = job?.progress ?? 0;

  return (
    <div className="grid h-full place-items-center overflow-auto p-8">
      <div role="status" aria-live="polite" className="flex w-full max-w-md flex-col gap-5">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">Building your application</h2>
          {instruction && <p className="mt-1 line-clamp-2 text-sm text-app-muted">“{instruction}”</p>}
        </div>

        <div>
          <div
            role="progressbar"
            aria-label="Generation progress"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={percent}
            className="h-1.5 overflow-hidden rounded-full bg-app-subtle"
          >
            <div
              className="h-full rounded-full bg-app-accent transition-[width] duration-500"
              style={{ width: `${percent}%` }}
            />
          </div>
          <p className="mt-2 flex justify-between gap-3 text-sm">
            <span className="min-w-0 truncate">{job?.detail ?? "Starting…"}</span>
            <span className="shrink-0 text-app-muted tabular-nums">{percent}%</span>
          </p>
        </div>

        <ol className="flex flex-col gap-2">
          {BUILD_STAGES.map((entry, index) => {
            const state = states[index]!;
            return (
              <li
                key={entry.stage}
                aria-current={state === "current" ? "step" : undefined}
                className={cn("flex items-center gap-2.5 text-sm", state === "upcoming" && "text-app-muted")}
              >
                <span
                  className={cn(
                    "grid size-5 shrink-0 place-items-center rounded-full border",
                    state === "done" && "border-app-accent bg-app-accent text-app-accent-fg",
                    state === "current" && "border-app-accent text-app-accent",
                    state === "upcoming" && "border-app-border",
                  )}
                >
                  {state === "done" && <Check size={12} strokeWidth={3} aria-hidden />}
                  {state === "current" && <Loader2 size={12} aria-hidden className="animate-spin" />}
                </span>
                <span className={cn(state === "current" && "font-medium")}>{entry.label}</span>
              </li>
            );
          })}
        </ol>

        <div className="flex items-center justify-between gap-3 border-t border-app-border pt-4">
          <p className="text-xs text-app-muted">
            This keeps running if you close the tab. Nothing is saved until you apply the result.
          </p>
          <Button size="sm" variant="ghost" onClick={() => void assistant.cancel()} disabled={!job}>
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}
