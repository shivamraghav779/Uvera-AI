import type { ProposalStep } from "@/services/api/types";
import { cn } from "@/utils/cn";

interface OperationPreviewProps {
  steps: readonly ProposalStep[];
  accepted: readonly boolean[];
  onToggle: (index: number) => void;
  disabled?: boolean;
}

/** The operations of a proposal, each of which can be kept or left out. */
export function OperationPreview({ steps, accepted, onToggle, disabled }: OperationPreviewProps) {
  return (
    <fieldset disabled={disabled}>
      <legend className="mb-1.5 text-xs font-medium text-app-muted">
        {steps.length} proposed change{steps.length === 1 ? "" : "s"}
      </legend>
      <ol className="flex flex-col gap-0.5">
        {steps.map((step, index) => {
          const kept = accepted[index] ?? false;
          return (
            <li key={index}>
              <label
                className={cn(
                  "flex cursor-pointer items-start gap-2 rounded-md px-1.5 py-1 text-sm hover:bg-app-subtle",
                  !kept && "text-app-muted line-through",
                )}
              >
                <input
                  type="checkbox"
                  checked={kept}
                  onChange={() => onToggle(index)}
                  className="mt-0.5 size-3.5 accent-[var(--app-accent)]"
                />
                <span className="w-4 shrink-0 text-app-muted tabular-nums">{index + 1}.</span>
                <span>{step.summary}</span>
              </label>
            </li>
          );
        })}
      </ol>
    </fieldset>
  );
}
