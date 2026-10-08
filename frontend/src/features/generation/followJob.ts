/**
 * Follows a generation job until it finishes.
 *
 * One follower per workspace, kept outside React so that every part of the
 * screen sees the same job and leaving the workspace stops the polling. The
 * job itself keeps running on the server; opening the workspace again picks it
 * up where it is.
 */
import { ApiError } from "@/services/api/client";
import { generationApi } from "@/services/api/generation";
import type { GenerationJobRead } from "@/services/api/types";

const POLL_MS = 1200;
/** Consecutive polls that may fail (a blip, a restart) before giving up. */
const MAX_MISSES = 8;

const followers = new Map<string, AbortController>();

export function isFinished(job: Pick<GenerationJobRead, "status">): boolean {
  return job.status === "ready" || job.status === "failed" || job.status === "cancelled";
}

function wait(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, ms);
    signal.addEventListener("abort", () => (clearTimeout(timer), resolve()), { once: true });
  });
}

/** Stop following the workspace's job (the job is not cancelled). */
export function stopFollowing(workspaceId: string): void {
  followers.get(workspaceId)?.abort();
  followers.delete(workspaceId);
}

/**
 * Poll `job` until it is finished, reporting every state. Resolves with the
 * finished job, or `null` when following was stopped first.
 */
export async function followJob(
  job: GenerationJobRead,
  onUpdate: (job: GenerationJobRead) => void,
  pollMs: number = POLL_MS,
): Promise<GenerationJobRead | null> {
  stopFollowing(job.workspace_id);
  const controller = new AbortController();
  followers.set(job.workspace_id, controller);
  let current = job;
  let misses = 0;
  onUpdate(current);
  try {
    while (!isFinished(current)) {
      await wait(pollMs, controller.signal);
      if (controller.signal.aborted) return null;
      try {
        current = await generationApi.get(job.id, controller.signal);
        misses = 0;
        onUpdate(current);
      } catch (error) {
        if (controller.signal.aborted) return null;
        // The job is unaffected by a failed poll; only a persistent failure is reported.
        const fatal = error instanceof ApiError && error.status !== null && error.status < 500 && error.code !== "TIMEOUT";
        if (fatal || ++misses >= MAX_MISSES) throw error;
      }
    }
    return current;
  } finally {
    if (followers.get(job.workspace_id) === controller) followers.delete(job.workspace_id);
  }
}
