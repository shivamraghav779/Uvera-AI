import { Sparkles } from "lucide-react";

import { STARTER_PROMPTS } from "./suggestions";

interface EmptyWorkspaceProps {
  busy: boolean;
  onPick: (prompt: string) => void;
}

/** The first thing a new workspace shows: a prompt to describe what to build. */
export function EmptyWorkspace({ busy, onPick }: EmptyWorkspaceProps) {
  return (
    <div className="grid h-full place-items-center p-8">
      <div className="flex max-w-xl flex-col items-center gap-5 text-center">
        <div className="grid size-12 place-items-center rounded-xl bg-app-accent-soft text-app-accent">
          <Sparkles size={22} aria-hidden />
        </div>
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">What do you want to build?</h2>
          <p className="mt-2 text-sm text-app-muted">
            Describe a product in a sentence. The assistant plans its screens, data and look, and
            builds a working application you can click through. You review it before anything is
            saved, then keep shaping it by talking or by editing it directly.
          </p>
        </div>
        <ul aria-label="Example prompts" className="grid w-full gap-2 sm:grid-cols-2">
          {STARTER_PROMPTS.map((prompt) => (
            <li key={prompt}>
              <button
                type="button"
                disabled={busy}
                onClick={() => onPick(prompt)}
                className="h-full w-full rounded-lg border border-app-border bg-app-panel p-3 text-left text-sm transition-colors hover:border-app-accent disabled:opacity-50"
              >
                {prompt}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
