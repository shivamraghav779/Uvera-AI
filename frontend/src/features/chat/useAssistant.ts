/**
 * The assistant's control flow: instruction -> proposal -> (preview) -> apply or reject.
 *
 * A proposal is never saved by receiving it. Applying it goes through the
 * versions API, which re-validates everything and creates the next version.
 */
import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";

import type { CanvasPreview } from "@/generative-ui/history/versionTypes";
import type { Operation } from "@/generative-ui/mutation/mutationTypes";
import { applyValidated } from "@/generative-ui/mutation/mutationValidator";
import { parseDocument } from "@/generative-ui/schema/normalization";
import type { UIDocument } from "@/generative-ui/schema/types";
import { dataMapSchema } from "@/generative-ui/schema/validators";
import { activeScreenId } from "@/generative-ui/runtime/appRuntime";
import { AI_TIMEOUT_MS, isApiError } from "@/services/api/client";
import { generationApi } from "@/services/api/generation";
import { queryKeys } from "@/services/api/queryKeys";
import type { GenerationJobRead, ProposalRead, VersionCreate } from "@/services/api/types";
import { uiApi } from "@/services/api/ui";
import { versionsApi } from "@/services/api/versions";
import { workspacesApi } from "@/services/api/workspaces";
import { useChatStore } from "@/stores/chatStore";
import { useEditorStore } from "@/stores/editorStore";
import { usePreferencesStore } from "@/stores/preferencesStore";
import { selectIsDirty, useWorkspaceStore } from "@/stores/workspaceStore";

import { followJob, isFinished, stopFollowing } from "../generation/followJob";
import { useValidationEnvironment } from "../workspace/queries";
import { reportWriteError, useCreateVersion, useRestoreVersion } from "../workspace/usePersistence";

const FAILURE_MESSAGES: Record<string, string> = {
  PROVIDER_NOT_CONFIGURED: "No language model is configured on the server yet.",
  LLM_ALL_PROVIDERS_FAILED: "The language model is not responding right now. Please try again.",
  UI_SCHEMA_INVALID: "The assistant could not produce a valid change for that request. Try rephrasing it.",
  TIMEOUT: "The assistant took too long to answer. Please try again.",
  RATE_LIMIT_EXCEEDED: "You are sending requests too quickly. Wait a moment and try again.",
  DATABASE_UNAVAILABLE: "The server is temporarily unavailable. Please try again in a moment.",
  DATA_SOURCE_ERROR: "One of your data sources could not be read.",
};

function failureMessage(error: unknown): string {
  if (isApiError(error)) return FAILURE_MESSAGES[error.code] ?? error.message;
  return "Something went wrong while contacting the assistant.";
}

/** Why a job failed, from the standard error body the server stored with it. */
function jobFailureMessage(job: GenerationJobRead): string {
  const code = typeof job.error?.code === "string" ? job.error.code : "";
  const message = typeof job.error?.message === "string" ? job.error.message : "";
  return FAILURE_MESSAGES[code] ?? (message || "The application could not be generated. Please try again.");
}

/**
 * Editing an application can mean generating a screen again, which takes
 * several model calls. A single view is edited in one.
 */
const APPLICATION_EDIT_TIMEOUT_MS = Math.max(AI_TIMEOUT_MS, 300_000);

/** Operations of the steps the user kept. */
export function acceptedOperations(proposal: ProposalRead, accepted: readonly boolean[]): Operation[] {
  return proposal.steps
    .filter((_, index) => accepted[index])
    .map((step) => step.operation as unknown as Operation);
}

export function useAssistant(workspaceId: string) {
  const queryClient = useQueryClient();
  const environment = useValidationEnvironment();
  const createVersion = useCreateVersion(workspaceId);
  const restoreVersion = useRestoreVersion(workspaceId);

  /** The document a proposal would produce, honouring per-step choices. */
  const resolveDocument = useCallback(
    (proposal: ProposalRead, accepted: readonly boolean[]): UIDocument | string => {
      const base = useWorkspaceStore.getState().base;
      const partial = proposal.kind === "mutate" && accepted.some((kept) => !kept);
      if (partial && base) {
        const result = applyValidated(base.document, acceptedOperations(proposal, accepted), environment);
        return result.ok ? result.value : (result.issues[0]?.message ?? "These changes do not work on their own.");
      }
      const parsed = parseDocument(proposal.document);
      return parsed.ok ? parsed.value : "The proposed UI could not be displayed.";
    },
    [environment],
  );

  const preview = useCallback(() => {
    const { proposal, acceptedSteps } = useChatStore.getState();
    if (!proposal) return;
    const document = resolveDocument(proposal, acceptedSteps);
    if (typeof document === "string") {
      useChatStore.getState().fail(document);
      return;
    }
    const data = dataMapSchema.safeParse(proposal.data);
    const next: CanvasPreview = {
      kind: "proposal",
      label:
        proposal.kind === "restore"
          ? `Version ${proposal.target_version?.version_number}`
          : proposal.kind === "generate" && proposal.application
            ? `${proposal.application.name} — proposed application`
            : "Proposed changes",
      document,
      data: data.success ? data.data : {},
      highlightIds: proposal.steps
        .filter((_, index) => acceptedSteps[index])
        .flatMap((step) => step.affected_component_ids),
    };
    useWorkspaceStore.getState().setPreview(next);
  }, [resolveDocument]);

  const stopPreview = useCallback(() => useWorkspaceStore.getState().setPreview(null), []);

  /** Put a finished proposal in front of the user. Returns false if it had to be discarded. */
  const receive = useCallback(
    (proposal: ProposalRead, showDraft: boolean): boolean => {
      if (proposal.document && !parseDocument(proposal.document).ok) {
        // Malformed backend response: never put it on screen.
        useChatStore.getState().fail("The assistant's proposal could not be displayed, so it was discarded.");
        return false;
      }
      useChatStore.getState().receiveProposal(proposal);
      useEditorStore.getState().setPreviewPath(null);
      if (proposal.kind === "compare" && proposal.target_version) {
        useEditorStore.getState().setCompareVersionId(proposal.target_version.id);
      }
      // With nothing on the canvas yet, show the draft straight away.
      if (showDraft && proposal.kind === "generate") preview();
      return true;
    },
    [preview],
  );

  /** Follow a job to its end and deal with whatever it produced. */
  const follow = useCallback(
    async (job: GenerationJobRead) => {
      const finished = await followJob(job, (state) => {
        // A late answer must not land in another workspace.
        if (useWorkspaceStore.getState().workspaceId === workspaceId) useChatStore.getState().setJob(state);
      });
      if (!finished || useWorkspaceStore.getState().workspaceId !== workspaceId) return;
      if (finished.status === "ready" && finished.proposal) {
        receive(finished.proposal as unknown as ProposalRead, useWorkspaceStore.getState().base === null);
      } else if (finished.status === "cancelled") {
        useChatStore.getState().settle();
      } else {
        useChatStore.getState().fail(jobFailureMessage(finished));
      }
    },
    [workspaceId, receive],
  );

  const reportFailure = useCallback((error: unknown) => {
    if (isApiError(error, "VERSION_CONFLICT")) {
      useChatStore.getState().fail("The workspace changed before the assistant could answer.");
      reportWriteError(error);
    } else {
      useChatStore.getState().fail(failureMessage(error));
    }
  }, []);

  /** Start a job; if one is already running for this workspace, follow that one. */
  const startJob = useCallback(
    async (body: Parameters<typeof generationApi.start>[0]) => {
      try {
        await follow(await generationApi.start(body));
      } catch (error) {
        const running = isApiError(error, "CONFLICT") ? await generationApi.latest(workspaceId).catch(() => null) : null;
        if (running && !isFinished(running)) await follow(running);
        else throw error;
      }
    },
    [workspaceId, follow],
  );

  const send = useCallback(
    async (instruction: string) => {
      const workspace = useWorkspaceStore.getState();
      if (selectIsDirty(workspace)) return;
      const chat = useChatStore.getState();
      workspace.setPreview(null);
      chat.startRequest(instruction);
      try {
        if (workspace.base) {
          const editor = useEditorStore.getState();
          const application = workspace.base.document.application !== undefined;
          const proposal = await uiApi.mutateStream(
            {
              workspace_id: workspaceId,
              base_version_id: workspace.base.id,
              instruction,
              selected_component_id: editor.selectedId,
              // "This screen" means the one on show.
              active_screen_id: activeScreenId(workspace.base.document, workspace.base.data, editor.appPath),
            },
            chat.setProgress,
            application ? APPLICATION_EDIT_TIMEOUT_MS : undefined,
          );
          receive(proposal, false);
        } else {
          // Building from nothing is a background job: an application takes minutes,
          // and the job survives a reload.
          const preferences = usePreferencesStore.getState();
          await startJob({
            workspace_id: workspaceId,
            instruction,
            kind: "build",
            theme_preset: preferences.newWorkspaceThemePreset || undefined,
            design_system: preferences.newWorkspaceDesignSystem || undefined,
            framework: preferences.newWorkspaceFramework || undefined,
          });
        }
      } catch (error) {
        reportFailure(error);
      } finally {
        void queryClient.invalidateQueries({ queryKey: queryKeys.messages(workspaceId), exact: true });
      }
    },
    [workspaceId, queryClient, receive, startJob, reportFailure],
  );

  /** Generate one screen of the current application again (e.g. one that failed). */
  const regenerateScreen = useCallback(
    async (screenId: string, title: string) => {
      const workspace = useWorkspaceStore.getState();
      if (!workspace.base || selectIsDirty(workspace)) return;
      const instruction = `Regenerate the “${title}” screen.`;
      workspace.setPreview(null);
      useChatStore.getState().startRequest(instruction);
      try {
        await startJob({ workspace_id: workspaceId, instruction, kind: "screen", screen_id: screenId });
      } catch (error) {
        reportFailure(error);
      } finally {
        void queryClient.invalidateQueries({ queryKey: queryKeys.messages(workspaceId), exact: true });
      }
    },
    [workspaceId, queryClient, startJob, reportFailure],
  );

  /** Stop the running generation. Nothing was saved, so nothing has to be undone. */
  const cancel = useCallback(async () => {
    const job = useChatStore.getState().job;
    if (!job) return;
    stopFollowing(workspaceId);
    useChatStore.getState().settle();
    try {
      await generationApi.cancel(job.id);
    } catch (error) {
      useChatStore.getState().fail(failureMessage(error));
    }
  }, [workspaceId]);

  /**
   * Pick up where the workspace was left: a generation still running is followed
   * again, and a finished one whose proposal was never decided is offered again.
   */
  const resume = useCallback(async () => {
    let latest: GenerationJobRead | null;
    try {
      latest = await generationApi.latest(workspaceId);
    } catch {
      return; // Resuming is a convenience; the workspace itself reports real outages.
    }
    const chat = useChatStore.getState();
    if (!latest || chat.status !== "idle" || chat.proposal) return;
    if (useWorkspaceStore.getState().workspaceId !== workspaceId) return;
    if (!isFinished(latest)) {
      chat.startRequest(latest.instruction);
      try {
        await follow(latest);
      } catch (error) {
        reportFailure(error);
      }
      return;
    }
    if (latest.status !== "ready" || !latest.proposal) return;
    try {
      const [workspace, versions] = await Promise.all([
        queryClient.fetchQuery({
          queryKey: queryKeys.workspace(workspaceId),
          queryFn: () => workspacesApi.get(workspaceId),
        }),
        queryClient.fetchQuery({
          queryKey: queryKeys.versions(workspaceId),
          queryFn: () => versionsApi.list(workspaceId),
        }),
      ]);
      const proposal = latest.proposal as unknown as ProposalRead;
      const current = (workspace.current_version_id ?? null) === (latest.base_version_id ?? null);
      const applied = versions.some((version) => version.metadata?.proposal_id === proposal.proposal_id);
      const state = useChatStore.getState();
      if (!current || applied || state.status !== "idle" || state.proposal) return;
      useChatStore.setState({ instruction: latest.instruction });
      receive(proposal, workspace.current_version_id === null);
    } catch {
      // Nothing to resume if the workspace cannot be read; its own loader shows why.
    }
  }, [workspaceId, queryClient, follow, receive, reportFailure]);

  const apply = useCallback(() => {
    const { proposal, acceptedSteps, instruction } = useChatStore.getState();
    const base = useWorkspaceStore.getState().base;
    if (!proposal) return;
    const finish = { onSuccess: () => useChatStore.getState().clearProposal() };
    const common = {
      base_version_id: base?.id ?? null,
      proposal_id: proposal.proposal_id,
      instruction: instruction ?? undefined,
    };
    if (proposal.kind === "generate" && proposal.document) {
      const body: VersionCreate = {
        ...common,
        source: "ai_generation",
        document: proposal.document as unknown as VersionCreate["document"],
      };
      createVersion.mutate(body, finish);
    } else if (proposal.kind === "mutate") {
      const operations = acceptedOperations(proposal, acceptedSteps);
      if (operations.length === 0) return;
      const body: VersionCreate = {
        ...common,
        source: "ai_mutation",
        operations: operations as VersionCreate["operations"],
      };
      createVersion.mutate(body, finish);
    } else if (proposal.kind === "restore" && proposal.target_version) {
      restoreVersion.mutate({ versionId: proposal.target_version.id, proposalId: proposal.proposal_id });
    }
  }, [createVersion, restoreVersion]);

  const reject = useCallback(() => {
    useWorkspaceStore.getState().setPreview(null);
    useChatStore.getState().clearProposal();
  }, []);

  /** Throw the proposal away and build again from the same instruction. */
  const regenerate = useCallback(() => {
    const instruction = useChatStore.getState().instruction;
    if (!instruction || useWorkspaceStore.getState().base) return;
    reject();
    void send(instruction);
  }, [reject, send]);

  return {
    send,
    regenerate,
    regenerateScreen,
    cancel,
    resume,
    preview,
    stopPreview,
    apply,
    reject,
    isApplying: createVersion.isPending || restoreVersion.isPending,
  };
}
