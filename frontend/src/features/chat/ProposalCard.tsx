import { Eye, EyeOff, GitCompareArrows, RefreshCw, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import type { ProposalRead } from "@/services/api/types";

import { ApplicationSummary } from "./ApplicationSummary";
import { ChangePreview } from "./ChangePreview";
import { OperationPreview } from "./OperationPreview";

const KIND_LABEL: Record<ProposalRead["kind"], string> = {
  generate: "New UI",
  mutate: "Changes",
  restore: "Restore version",
  compare: "Comparison",
  message: "Note",
};

interface ProposalCardProps {
  proposal: ProposalRead;
  accepted: readonly boolean[];
  previewing: boolean;
  applying: boolean;
  onToggleStep: (index: number) => void;
  onPreview: () => void;
  onStopPreview: () => void;
  onApply: () => void;
  onReject: () => void;
  onOpenComparison: () => void;
  /** Build again from the same instruction (offered for a first build). */
  onRegenerate?: () => void;
  /** Show one screen of a proposed application. */
  onOpenScreen?: (route: string) => void;
}

/**
 * A proposal awaiting a decision. Nothing here has been saved: Apply persists
 * it as a new version, Reject discards it and leaves the workspace untouched.
 */
export function ProposalCard({
  proposal,
  accepted,
  previewing,
  applying,
  onToggleStep,
  onPreview,
  onStopPreview,
  onApply,
  onReject,
  onOpenComparison,
  onRegenerate,
  onOpenScreen,
}: ProposalCardProps) {
  const application = proposal.kind === "generate" ? proposal.application : null;
  const keptCount = accepted.filter(Boolean).length;
  const actionable = proposal.kind === "generate" || proposal.kind === "mutate" || proposal.kind === "restore";
  const partial = proposal.kind === "mutate" && keptCount < proposal.steps.length;
  const applyLabel =
    proposal.kind === "restore"
      ? `Restore version ${proposal.target_version?.version_number}`
      : partial
        ? `Apply ${keptCount} of ${proposal.steps.length}`
        : proposal.kind === "mutate" && proposal.steps.length > 1
          ? "Apply all"
          : application
            ? "Apply application"
            : "Apply";

  return (
    <section
      aria-label="Proposal awaiting your decision"
      className="rounded-lg border border-app-border bg-app-raised p-3 shadow-app-float"
    >
      <header className="mb-2 flex items-start gap-2">
        <Sparkles size={15} aria-hidden className="mt-0.5 shrink-0 text-app-accent" />
        <p className="flex-1 text-sm">{proposal.message}</p>
        <Badge tone="accent">{application ? "New application" : KIND_LABEL[proposal.kind]}</Badge>
      </header>

      {application && (
        <div className="mb-3 max-h-[34vh] overflow-y-auto pl-6">
          <ApplicationSummary summary={application} quality={proposal.quality} onOpenScreen={onOpenScreen} />
        </div>
      )}

      {proposal.kind === "mutate" && (
        <div className="mb-3 pl-6">
          <OperationPreview
            steps={proposal.steps}
            accepted={accepted}
            onToggle={onToggleStep}
            disabled={applying}
          />
        </div>
      )}
      {(proposal.kind === "restore" || proposal.kind === "compare") && (
        <div className="mb-3 pl-6">
          <ChangePreview
            changes={proposal.changes}
            emptyText={
              proposal.kind === "restore"
                ? "That version is identical to the current one."
                : "Nothing differs from that version."
            }
          />
        </div>
      )}
      {proposal.kind === "generate" && !application && proposal.changes.length > 0 && (
        <div className="mb-3 pl-6">
          <ChangePreview changes={proposal.changes} limit={5} />
        </div>
      )}

      <footer className="flex flex-wrap items-center gap-2 pl-6">
        {actionable && (
          <>
            <Button
              size="sm"
              icon={previewing ? <EyeOff size={13} /> : <Eye size={13} />}
              onClick={previewing ? onStopPreview : onPreview}
              disabled={applying}
            >
              {previewing ? "Hide preview" : application ? "Preview application" : "Preview"}
            </Button>
            <Button
              size="sm"
              variant="accent"
              onClick={onApply}
              busy={applying}
              disabled={proposal.kind === "mutate" && keptCount === 0}
            >
              {applyLabel}
            </Button>
            {proposal.kind === "generate" && onRegenerate && (
              <Button size="sm" icon={<RefreshCw size={13} />} onClick={onRegenerate} disabled={applying}>
                Regenerate
              </Button>
            )}
            <Button size="sm" variant="ghost" onClick={onReject} disabled={applying}>
              Reject
            </Button>
            <span className="ml-auto text-xs text-app-muted">Not saved until you apply</span>
          </>
        )}
        {proposal.kind === "compare" && (
          <>
            <Button size="sm" icon={<GitCompareArrows size={13} />} onClick={onOpenComparison}>
              Open comparison
            </Button>
            <Button size="sm" variant="ghost" onClick={onReject}>
              Dismiss
            </Button>
          </>
        )}
        {proposal.kind === "message" && (
          <Button size="sm" variant="ghost" onClick={onReject}>
            Dismiss
          </Button>
        )}
      </footer>
    </section>
  );
}
