import type { GenerationJobRead, JobStage } from "@/services/api/types";

/** The stages a build goes through, in order, as the pipeline reports them. */
export const BUILD_STAGES: readonly { stage: JobStage; label: string }[] = [
  { stage: "understanding", label: "Understanding the product" },
  { stage: "planning", label: "Planning screens and data" },
  { stage: "designing", label: "Setting the design direction" },
  { stage: "generating_assets", label: "Preparing images" },
  { stage: "generating_screens", label: "Designing screens" },
  { stage: "assembling", label: "Assembling the application" },
  { stage: "validating", label: "Checking the result" },
];

export type StageState = "done" | "current" | "upcoming";

/** Where each stage stands for a job. An unknown or queued stage leaves everything upcoming. */
export function stageStates(job: Pick<GenerationJobRead, "stage" | "status"> | null): StageState[] {
  if (job?.status === "ready") return BUILD_STAGES.map(() => "done");
  const position = BUILD_STAGES.findIndex((entry) => entry.stage === job?.stage);
  return BUILD_STAGES.map((_, index) => (index < position ? "done" : index === position ? "current" : "upcoming"));
}

/** One line for the job: what the server says it is doing right now. */
export function jobText(job: GenerationJobRead | null): string {
  if (!job) return "Sending your request…";
  if (job.status === "queued") return "Waiting to start…";
  const label = BUILD_STAGES.find((entry) => entry.stage === job.stage)?.label ?? "Working";
  return `${job.detail ?? label} · ${job.progress}%`;
}
