/**
 * Decides what the canvas shows: a loading skeleton, the empty state, an error,
 * a read-only preview, or the working copy in view or edit mode.
 */
import { Eye } from "lucide-react";
import { useCallback } from "react";
import { useNavigate } from "react-router";

import { CanvasSkeleton } from "@/components/feedback/Skeleton";
import { StateMessage } from "@/components/feedback/StateMessage";
import { Button } from "@/components/ui/Button";
import type { Operation } from "@/generative-ui/mutation/mutationTypes";
import { WorkspaceCanvas } from "@/generative-ui/workspace/WorkspaceCanvas";
import { useChatStore } from "@/stores/chatStore";
import { useEditorStore, type Device } from "@/stores/editorStore";
import { selectDraft, useWorkspaceStore } from "@/stores/workspaceStore";
import { cn } from "@/utils/cn";

import { useAssistant } from "../chat/useAssistant";
import { EmptyWorkspace } from "../generation/EmptyWorkspace";
import { GenerationProgress } from "../generation/GenerationProgress";

import type { SessionStatus } from "./useWorkspaceSession";

const DEVICE_WIDTH: Record<Device, string> = {
  desktop: "max-w-[1280px]",
  tablet: "max-w-[700px]",
  mobile: "max-w-[400px]",
};

interface CanvasAreaProps {
  workspaceId: string;
  status: SessionStatus;
  errorMessage?: string;
  issues?: string[];
  onRetry: () => void;
  onOperations: (operations: Operation[]) => void;
  onRestoreVersion: (versionId: string) => void;
  /** Where the user is inside a generated application; kept by the page (in the URL). */
  appPath: string | null;
  onAppPathChange: (path: string) => void;
}

export function CanvasArea({
  workspaceId,
  status,
  errorMessage,
  issues,
  onRetry,
  onOperations,
  onRestoreVersion,
  appPath,
  onAppPathChange,
}: CanvasAreaProps) {
  const navigate = useNavigate();
  const assistant = useAssistant(workspaceId);
  const draft = useWorkspaceStore(selectDraft);
  const baseData = useWorkspaceStore((state) => state.base?.data);
  const preview = useWorkspaceStore((state) => state.preview);
  const mode = useEditorStore((state) => state.mode);
  const device = useEditorStore((state) => state.device);
  const selectedId = useEditorStore((state) => state.selectedId);
  const select = useEditorStore((state) => state.select);
  const previewPath = useEditorStore((state) => state.previewPath);
  const setPreviewPath = useEditorStore((state) => state.setPreviewPath);
  const thinking = useChatStore((state) => state.status === "thinking");

  // A "generate" action in the UI is a request to the assistant: it produces a proposal
  // the user still has to approve, exactly like typing the instruction.
  const requestGeneration = useCallback(
    (instruction: string) => void assistant.send(instruction),
    [assistant],
  );
  const stopPreview = () => useWorkspaceStore.getState().setPreview(null);


  if (preview) {
    return (
      <div className="flex h-full flex-col">
        <div
          role="status"
          className="flex shrink-0 items-center gap-3 border-b border-app-border bg-app-accent-soft px-4 py-2 text-sm"
        >
          <Eye size={15} aria-hidden className="text-app-accent" />
          <span className="flex-1">
            <strong className="font-semibold">{preview.label}</strong>
            {preview.kind === "proposal"
              ? " — a preview. Nothing is saved until you apply it."
              : " — read-only. Your current version is unchanged."}
          </span>
          {preview.kind === "proposal" ? (
            <>
              <Button size="sm" variant="accent" onClick={assistant.apply} busy={assistant.isApplying}>
                Apply
              </Button>
              <Button size="sm" onClick={stopPreview}>
                Exit preview
              </Button>
            </>
          ) : (
            <>
              <Button
                size="sm"
                onClick={() => useEditorStore.getState().setCompareVersionId(preview.versionId ?? null)}
              >
                Compare with current
              </Button>
              <Button
                size="sm"
                variant="accent"
                onClick={() => preview.versionId && onRestoreVersion(preview.versionId)}
              >
                Restore this version
              </Button>
              <Button size="sm" onClick={stopPreview}>
                Back to current
              </Button>
            </>
          )}
        </div>
        <Frame device={device}>
          <WorkspaceCanvas
            key={preview.versionId ?? "proposal"}
            document={preview.document}
            data={preview.data}
            mode="preview"
            workspaceId={workspaceId}
            highlightIds={preview.highlightIds}
            path={previewPath}
            onPathChange={setPreviewPath}
          />
        </Frame>
      </div>
    );
  }

  if (status === "loading") return <CanvasSkeleton label="Loading workspace" />;
  if (status === "error") {
    return (
      <StateMessage
        tone="error"
        title="This workspace could not be loaded"
        description={errorMessage ?? "Check your connection and try again."}
        action={
          <Button variant="primary" onClick={onRetry}>
            Try again
          </Button>
        }
      />
    );
  }
  if (status === "invalid") {
    return (
      <StateMessage
        tone="error"
        title="This version cannot be displayed"
        description="The saved UI does not match the schema this build understands, so it was not rendered. Open the version history to restore an earlier version."
        details={issues}
      />
    );
  }
  if (status === "empty" || !draft) {
    if (thinking) return <GenerationProgress workspaceId={workspaceId} />;
    return <EmptyWorkspace busy={thinking} onPick={(prompt) => void assistant.send(prompt)} />;
  }

  return (
    <Frame device={device}>
      <WorkspaceCanvas
        document={draft}
        data={baseData ?? {}}
        mode={mode}
        workspaceId={workspaceId}
        selectedId={selectedId}
        onSelect={select}
        onOperations={onOperations}
        onNavigate={navigate}
        onRequestGeneration={requestGeneration}
        path={appPath}
        onPathChange={onAppPathChange}
      />
    </Frame>
  );
}

/** The surface the generated UI sits on, at the chosen preview width. */
function Frame({ device, children }: { device: Device; children: React.ReactNode }) {
  return (
    <div className="h-full overflow-auto bg-app-canvas p-4">
      <div
        className={cn(
          // `clip`, not `hidden`: sticky navigation inside the UI must keep working.
          "mx-auto min-h-full overflow-clip rounded-xl border border-app-border shadow-sm transition-[max-width]",
          DEVICE_WIDTH[device],
        )}
      >
        {children}
      </div>
    </div>
  );
}
