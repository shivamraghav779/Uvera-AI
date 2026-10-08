import { Sparkles } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/Badge";
import type { ProposalProgress } from "@/services/api/stream";
import { cn } from "@/utils/cn";

interface ChatMessageProps {
  role: "user" | "assistant" | "system";
  content: string;
  /** Outcome of the proposal this message described, if any. */
  status?: ReactNode;
  pending?: boolean;
}

export function ChatMessage({ role, content, status, pending }: ChatMessageProps) {
  if (role === "user") {
    return (
      <li className="flex justify-end">
        <p
          className={cn(
            "max-w-[80%] rounded-2xl rounded-br-md bg-app-accent-soft px-3 py-1.5 text-sm whitespace-pre-wrap",
            pending && "opacity-70",
          )}
        >
          <span className="sr-only">You: </span>
          {content}
        </p>
      </li>
    );
  }
  return (
    <li className="flex items-start gap-2">
      <Sparkles size={14} aria-hidden className="mt-1 shrink-0 text-app-accent" />
      <div className="max-w-[85%]">
        <p className="text-sm whitespace-pre-wrap">
          <span className="sr-only">Assistant: </span>
          {content}
        </p>
        {status && <div className="mt-1">{status}</div>}
      </div>
    </li>
  );
}

const STAGE_TEXT: Record<ProposalProgress["stage"], string> = {
  understanding: "Understanding your request…",
  planning: "Planning the interface…",
  generating: "Writing the changes…",
  validating: "Checking the result against the schema…",
  repairing: "Fixing a problem the validator found…",
  finishing: "Preparing the preview…",
};

/** What the assistant is doing right now, as reported by the server. */
export function progressText(progress: ProposalProgress | null): string {
  if (!progress) return "Sending your request…";
  const written =
    progress.stage === "generating" && progress.characters
      ? ` (${progress.characters.toLocaleString()} characters)`
      : "";
  return STAGE_TEXT[progress.stage] + written;
}

export function ThinkingMessage({ text }: { text: string }) {
  return (
    <li role="status" className="flex items-center gap-2 text-sm text-app-muted">
      <Sparkles size={14} aria-hidden className="animate-pulse text-app-accent" />
      {text}
    </li>
  );
}

/** Marks how a past proposal ended. */
export function OutcomeBadge({ versionNumber, awaiting }: { versionNumber?: number; awaiting: boolean }) {
  if (versionNumber !== undefined) return <Badge tone="success">Applied · v{versionNumber}</Badge>;
  if (awaiting) return <Badge tone="accent">Awaiting your decision</Badge>;
  return <Badge>Not applied</Badge>;
}
