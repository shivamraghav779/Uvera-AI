/**
 * The workspace screen: toolbar on top, the generated UI dominating the centre,
 * an optional side panel (inspector or history), and the assistant docked below.
 */
import { useCallback, useEffect, useMemo } from "react";
import { useParams, useSearchParams } from "react-router";

import { StateMessage } from "@/components/feedback/StateMessage";
import type { Operation } from "@/generative-ui/mutation/mutationTypes";
import { activeScreenId } from "@/generative-ui/runtime/appRuntime";
import { screensOf } from "@/generative-ui/schema/tree";
import { WorkspaceToolbar } from "@/generative-ui/workspace/WorkspaceToolbar";
import { isApiError } from "@/services/api/client";
import { useChatStore } from "@/stores/chatStore";
import { useEditorStore } from "@/stores/editorStore";
import { toast } from "@/stores/toastStore";
import {
  selectCanRedo,
  selectCanUndo,
  selectDraft,
  selectPendingOperations,
  useWorkspaceStore,
} from "@/stores/workspaceStore";

import { ChatPanel } from "../chat/ChatPanel";
import { VersionCompareDialog } from "../version-history/VersionCompareDialog";
import { VersionHistoryPanel } from "../version-history/VersionHistoryPanel";

import { CanvasArea } from "./CanvasArea";
import { ConflictDialog } from "./ConflictDialog";
import { DesignMenu } from "./DesignMenu";
import { InspectorPanel } from "./InspectorPanel";
import { ScreenMenu } from "./ScreenMenu";
import { useValidationEnvironment } from "./queries";
import { useRestoreVersion, useSaveEdits } from "./usePersistence";
import { useWorkspaceSession } from "./useWorkspaceSession";
import { WorkspaceTitle } from "./WorkspaceTitle";

const APP_PATH_PARAM = "at";

interface WorkspacePageProps {
  /** Open with the version history showing (the /history route). */
  showHistory?: boolean;
}

export function WorkspacePage({ showHistory = false }: WorkspacePageProps) {
  const { workspaceId = "" } = useParams();
  const session = useWorkspaceSession(workspaceId);
  const environment = useValidationEnvironment();
  const { save, isSaving } = useSaveEdits(workspaceId);
  const restore = useRestoreVersion(workspaceId);

  const draft = useWorkspaceStore(selectDraft);
  const versionNumber = useWorkspaceStore((state) => state.base?.number ?? null);
  const pending = useWorkspaceStore(selectPendingOperations);
  const canUndo = useWorkspaceStore(selectCanUndo);
  const canRedo = useWorkspaceStore(selectCanRedo);
  const previewing = useWorkspaceStore((state) => state.preview !== null);
  const { undo, redo, discard } = useWorkspaceStore.getState();

  const mode = useEditorStore((state) => state.mode);
  const panel = useEditorStore((state) => state.panel);
  const device = useEditorStore((state) => state.device);
  const selectedId = useEditorStore((state) => state.selectedId);
  const { setMode, setPanel, togglePanel, setDevice, select } = useEditorStore.getState();

  useEffect(() => {
    if (showHistory) useEditorStore.getState().setPanel("history");
  }, [showHistory, workspaceId]);

  // The place inside a generated application lives in the URL (`?at=/jobs/j-3`), so a
  // reload or a shared link opens the same screen. The store mirrors it for the assistant.
  const [search, setSearch] = useSearchParams();
  const appPath = search.get(APP_PATH_PARAM);
  const setAppPath = useCallback(
    (path: string) => {
      setSearch(
        (current) => {
          const next = new URLSearchParams(current);
          next.set(APP_PATH_PARAM, path);
          return next;
        },
        { replace: false },
      );
    },
    [setSearch],
  );
  useEffect(() => {
    useEditorStore.getState().setAppPath(appPath);
  }, [appPath, workspaceId]);
  const baseData = useWorkspaceStore((state) => state.base?.data);
  const screens = useMemo(() => (draft?.application ? screensOf(draft.page) : []), [draft]);
  const screenId = useMemo(() => activeScreenId(draft, baseData ?? {}, appPath), [draft, baseData, appPath]);

  /** The single entry point for direct manipulation: validated, then applied or refused. */
  const applyOperations = useCallback(
    (operations: Operation[]) => {
      const result = useWorkspaceStore.getState().applyOperations(operations, environment);
      if (!result.ok) toast.error(result.issues[0]?.message ?? "That change is not possible.");
    },
    [environment],
  );

  // Undo/redo shortcuts for unsaved edits (not while typing in a field).
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement;
      if (target.closest("input, textarea, select, [contenteditable]")) return;
      if (!(event.metaKey || event.ctrlKey) || event.key.toLowerCase() !== "z") return;
      event.preventDefault();
      if (event.shiftKey) useWorkspaceStore.getState().redo();
      else useWorkspaceStore.getState().undo();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  if (session.status === "error" && isApiError(session.error, "RESOURCE_NOT_FOUND")) {
    return (
      <StateMessage
        title="Workspace not found"
        description="It may have been deleted, or the link is wrong."
      />
    );
  }

  const canEdit = session.status === "ready" && !previewing;
  const showInspector = panel === "inspector" && mode === "edit" && draft !== null;

  return (
    <div className="flex h-full min-w-0 flex-col">
      <WorkspaceToolbar
        title={<WorkspaceTitle workspaceId={workspaceId} title={session.workspace?.title ?? null} />}
        versionNumber={versionNumber}
        mode={mode}
        onModeChange={setMode}
        canEdit={canEdit}
        device={device}
        onDeviceChange={setDevice}
        canUndo={canUndo}
        canRedo={canRedo}
        onUndo={undo}
        onRedo={redo}
        unsavedCount={pending.length}
        saving={isSaving}
        onSave={save}
        onDiscard={discard}
        historyOpen={panel === "history"}
        onToggleHistory={() => togglePanel("history")}
      >
        {screens.length > 0 && !previewing && (
          <ScreenMenu screens={screens} activeId={screenId} onPick={(screen) => setAppPath(screen.route)} />
        )}
        {draft && <DesignMenu document={draft} disabled={!canEdit} onApply={applyOperations} />}
      </WorkspaceToolbar>

      <div className="flex min-h-0 flex-1">
        <main aria-label="Canvas" className="flex min-w-0 flex-1 flex-col">
          <div className="min-h-0 flex-1">
            <CanvasArea
              workspaceId={workspaceId}
              status={session.status}
              errorMessage={session.error?.message}
              issues={session.loadIssues?.map((issue) => `${issue.path}: ${issue.message}`)}
              onRetry={session.retry}
              onOperations={applyOperations}
              onRestoreVersion={(versionId) => restore.mutate({ versionId })}
              appPath={appPath}
              onAppPathChange={setAppPath}
            />
          </div>
          <ChatPanel workspaceId={workspaceId} />
        </main>

        {(showInspector || panel === "history") && (
          <div className="w-80 shrink-0 border-l border-app-border bg-app-panel">
            {panel === "history" ? (
              <VersionHistoryPanel workspaceId={workspaceId} onClose={() => setPanel("none")} />
            ) : (
              draft && (
                <InspectorPanel
                  page={draft.page}
                  selectedId={selectedId}
                  onApply={applyOperations}
                  onSelect={select}
                  onAsk={() => useChatStore.getState().requestFocus()}
                  onClose={() => setPanel("none")}
                />
              )
            )}
          </div>
        )}
      </div>

      <VersionCompareDialog workspaceId={workspaceId} />
      <ConflictDialog onReload={() => void session.reloadLatest()} />
    </div>
  );
}
