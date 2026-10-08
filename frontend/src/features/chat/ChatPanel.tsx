/**
 * The assistant dock under the canvas. It is the workspace's command line:
 * one input, the proposal awaiting a decision, and the conversation on demand.
 */
import { useEffect, useMemo, useRef } from "react";

import { Button } from "@/components/ui/Button";
import { versionForProposal } from "@/generative-ui/history/versionUtils";
import { activeScreenId } from "@/generative-ui/runtime/appRuntime";
import { screensOf } from "@/generative-ui/schema/tree";
import type { MessageRead } from "@/services/api/types";
import { useChatStore } from "@/stores/chatStore";
import { useEditorStore } from "@/stores/editorStore";
import { usePreferencesStore } from "@/stores/preferencesStore";
import { selectIsDirty, useWorkspaceStore } from "@/stores/workspaceStore";

import { stopFollowing } from "../generation/followJob";
import { jobText } from "../generation/stages";
import { APPLICATION_PROMPTS, EDIT_PROMPTS, SELECTION_PROMPTS } from "../generation/suggestions";
import { useVersions } from "../version-history/queries";
import { useSaveEdits } from "../workspace/usePersistence";

import { ChatInput } from "./ChatInput";
import { ChatMessage, OutcomeBadge, progressText, ThinkingMessage } from "./ChatMessage";
import { ProposalCard } from "./ProposalCard";
import { useMessages } from "./queries";
import { SuggestionList } from "./SuggestionList";
import { useAssistant } from "./useAssistant";

const DECIDABLE_KINDS = new Set(["generate", "mutate", "restore"]);

export function ChatPanel({ workspaceId }: { workspaceId: string }) {
  const assistant = useAssistant(workspaceId);
  const messages = useMessages(workspaceId);
  const versions = useVersions(workspaceId);
  const { save, isSaving } = useSaveEdits(workspaceId);

  const status = useChatStore((state) => state.status);
  const pendingMessage = useChatStore((state) => state.pendingMessage);
  const progress = useChatStore((state) => state.progress);
  const job = useChatStore((state) => state.job);
  const proposal = useChatStore((state) => state.proposal);
  const acceptedSteps = useChatStore((state) => state.acceptedSteps);
  const error = useChatStore((state) => state.error);
  const draft = useChatStore((state) => state.draft);
  const focusToken = useChatStore((state) => state.focusToken);
  const { setDraft, toggleStep, clearError } = useChatStore.getState();

  const hasUi = useWorkspaceStore((state) => state.base !== null);
  const base = useWorkspaceStore((state) => state.base);
  const appPath = useEditorStore((state) => state.appPath);
  // The screen on show, when the workspace holds an application.
  const screen = useMemo(() => {
    if (!base?.document.application) return null;
    const id = activeScreenId(base.document, base.data, appPath);
    return screensOf(base.document.page).find((candidate) => candidate.id === id) ?? null;
  }, [base, appPath]);
  // The pipeline leaves this marker where a screen could not be generated.
  const screenPending = screen?.children[0]?.id === `${screen?.id}_pending`;

  // Opening a workspace picks up a generation that is still running, or one whose
  // result was never decided. Leaving stops the polling, not the job.
  const { resume } = assistant;
  useEffect(() => {
    void resume();
    return () => stopFollowing(workspaceId);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- once per workspace
  }, [workspaceId]);
  const dirty = useWorkspaceStore(selectIsDirty);
  const previewing = useWorkspaceStore((state) => state.preview?.kind === "proposal");
  const discard = useWorkspaceStore((state) => state.discard);
  const selectedId = useEditorStore((state) => state.selectedId);
  const expanded = usePreferencesStore((state) => state.chatExpanded);
  const setExpanded = usePreferencesStore((state) => state.setChatExpanded);

  const thinking = status === "thinking";
  const thread = useRef<HTMLOListElement>(null);
  const messageCount = messages.data?.length ?? 0;
  useEffect(() => {
    thread.current?.scrollTo({ top: thread.current.scrollHeight });
  }, [messageCount, thinking, expanded]);

  const submit = (text: string = draft) => {
    const instruction = text.trim();
    if (!instruction || thinking || dirty) return;
    setDraft("");
    void assistant.send(instruction);
  };

  // Re-previews when the kept steps change so the canvas always matches the checkboxes.
  const onToggleStep = (index: number) => {
    toggleStep(index);
    if (previewing) assistant.preview();
  };

  const outcome = (message: MessageRead) => {
    const details = message.details as { proposal_id?: string; kind?: string } | null | undefined;
    if (!details?.proposal_id || !details.kind || !DECIDABLE_KINDS.has(details.kind)) return null;
    const version = versionForProposal(versions.data ?? [], details.proposal_id);
    return (
      <OutcomeBadge
        versionNumber={version?.version_number}
        awaiting={proposal?.proposal_id === details.proposal_id}
      />
    );
  };

  return (
    <section aria-label="Assistant" className="border-t border-app-border bg-app-bg">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-2 px-4 py-3">
        {expanded && (
          <ol
            ref={thread}
            aria-label="Conversation"
            className="flex max-h-[32vh] flex-col gap-2.5 overflow-y-auto rounded-lg border border-app-border bg-app-panel p-3"
          >
            {messageCount === 0 && !pendingMessage && (
              <li className="text-sm text-app-muted">
                Nothing yet. Describe what you want and the assistant will propose it.
              </li>
            )}
            {messages.data?.map((message) => (
              <ChatMessage
                key={message.id}
                role={message.role}
                content={message.content}
                status={message.role === "assistant" ? outcome(message) : undefined}
              />
            ))}
            {pendingMessage && !messages.data?.some((m) => m.content === pendingMessage && m.role === "user") && (
              <ChatMessage role="user" content={pendingMessage} pending />
            )}
            {thinking && <ThinkingMessage text={job ? jobText(job) : progressText(progress)} />}
          </ol>
        )}

        {!expanded && thinking && (
          <p role="status" className="px-1 text-sm text-app-muted">
            <span className="mr-2 inline-block size-2 animate-pulse rounded-full bg-app-accent" />
            {job ? jobText(job) : progressText(progress)}
          </p>
        )}

        {proposal && (
          <ProposalCard
            proposal={proposal}
            accepted={acceptedSteps}
            previewing={previewing}
            applying={assistant.isApplying}
            onToggleStep={onToggleStep}
            onPreview={assistant.preview}
            onStopPreview={assistant.stopPreview}
            onApply={assistant.apply}
            onReject={assistant.reject}
            onOpenComparison={() =>
              useEditorStore.getState().setCompareVersionId(proposal.target_version?.id ?? null)
            }
            onRegenerate={hasUi ? undefined : assistant.regenerate}
            onOpenScreen={(route) => {
              if (!previewing) assistant.preview();
              useEditorStore.getState().setPreviewPath(route);
            }}
          />
        )}

        {error && (
          <div
            role="alert"
            className="flex items-center justify-between gap-3 rounded-lg border border-app-danger/40 bg-[color-mix(in_srgb,var(--app-danger)_8%,transparent)] px-3 py-2 text-sm"
          >
            <span>{error}</span>
            <Button size="sm" variant="ghost" onClick={clearError}>
              Dismiss
            </Button>
          </div>
        )}

        {dirty && (
          <div className="flex items-center justify-between gap-3 rounded-lg border border-app-border bg-app-panel px-3 py-2 text-sm">
            <span className="text-app-muted">
              Save or discard your edits before asking the assistant, so it works on what you see.
            </span>
            <span className="flex shrink-0 gap-2">
              <Button size="sm" variant="ghost" onClick={discard} disabled={isSaving}>
                Discard
              </Button>
              <Button size="sm" variant="accent" onClick={save} busy={isSaving}>
                Save version
              </Button>
            </span>
          </div>
        )}

        <ChatInput
          value={draft}
          onChange={setDraft}
          onSubmit={() => submit()}
          placeholder={
            hasUi
              ? selectedId
                ? "Describe a change to the selected component…"
                : screen
                  ? `Change “${screen.title}”, the whole application, or go back to a version…`
                  : "Describe a change, or ask to go back to a version…"
              : "Describe the product you want to build…"
          }
          disabled={dirty}
          busy={thinking}
          selectedId={hasUi ? selectedId : null}
          onClearSelection={() => useEditorStore.getState().select(null)}
          expanded={expanded}
          onToggleExpanded={() => setExpanded(!expanded)}
          focusToken={focusToken}
        />

        {hasUi && !proposal && !thinking && !dirty && (
          <div className="flex flex-wrap items-center gap-1.5">
            {screen && screenPending && (
              <Button
                size="sm"
                variant="accent"
                onClick={() => void assistant.regenerateScreen(screen.id, screen.title)}
              >
                Regenerate “{screen.title}”
              </Button>
            )}
            <SuggestionList
              suggestions={selectedId ? SELECTION_PROMPTS : screen ? APPLICATION_PROMPTS : EDIT_PROMPTS}
              onPick={submit}
            />
          </div>
        )}
      </div>
    </section>
  );
}
