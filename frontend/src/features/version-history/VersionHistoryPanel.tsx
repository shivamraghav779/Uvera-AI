/**
 * Version history of the workspace. Versions are immutable: previewing looks at
 * one without changing anything, and restoring appends a copy as the newest
 * version rather than rewinding.
 */
import { useQueryClient } from "@tanstack/react-query";
import { Eye, GitCompareArrows, RotateCcw, X } from "lucide-react";
import { useState } from "react";

import { Skeleton } from "@/components/feedback/Skeleton";
import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { sourceLabel } from "@/generative-ui/history/versionUtils";
import { parseDocument } from "@/generative-ui/schema/normalization";
import { dataMapSchema } from "@/generative-ui/schema/validators";
import { queryKeys } from "@/services/api/queryKeys";
import type { VersionSummary } from "@/services/api/types";
import { versionsApi } from "@/services/api/versions";
import { useEditorStore } from "@/stores/editorStore";
import { toast } from "@/stores/toastStore";
import { selectIsDirty, useWorkspaceStore } from "@/stores/workspaceStore";
import { cn } from "@/utils/cn";
import { formatDateTime, formatRelativeTime } from "@/utils/format";

import { useRestoreVersion } from "../workspace/usePersistence";

import { useVersions } from "./queries";

interface VersionHistoryPanelProps {
  workspaceId: string;
  onClose: () => void;
}

export function VersionHistoryPanel({ workspaceId, onClose }: VersionHistoryPanelProps) {
  const queryClient = useQueryClient();
  const versions = useVersions(workspaceId);
  const restore = useRestoreVersion(workspaceId);
  const previewVersionId = useWorkspaceStore((state) => state.preview?.versionId);
  const dirty = useWorkspaceStore(selectIsDirty);
  const [confirming, setConfirming] = useState<VersionSummary | null>(null);
  const [loadingPreview, setLoadingPreview] = useState<string | null>(null);

  const preview = async (version: VersionSummary) => {
    setLoadingPreview(version.id);
    try {
      const detail = await queryClient.fetchQuery({
        queryKey: queryKeys.version(workspaceId, version.id),
        queryFn: () => versionsApi.get(workspaceId, version.id),
        staleTime: Infinity,
      });
      const document = parseDocument(detail.document);
      if (!document.ok) {
        toast.error(`Version ${version.version_number} cannot be displayed by this build.`);
        return;
      }
      const data = dataMapSchema.safeParse(detail.data);
      useWorkspaceStore.getState().setPreview({
        kind: "version",
        label: `Version ${version.version_number}`,
        document: document.value,
        data: data.success ? data.data : {},
        highlightIds: [],
        versionId: version.id,
      });
    } catch {
      toast.error("That version could not be loaded.");
    } finally {
      setLoadingPreview(null);
    }
  };

  return (
    <aside aria-label="Version history" className="flex h-full flex-col">
      <header className="flex h-10 shrink-0 items-center justify-between border-b border-app-border px-3">
        <h2 className="text-sm font-semibold">Version history</h2>
        <IconButton label="Close version history" onClick={onClose} className="size-7">
          <X size={15} />
        </IconButton>
      </header>

      <div className="flex-1 overflow-y-auto">
        {versions.isPending && (
          <div role="status" aria-label="Loading versions" className="flex flex-col gap-2 p-3">
            {[0, 1, 2].map((index) => (
              <Skeleton key={index} className="h-20" />
            ))}
          </div>
        )}
        {versions.isError && (
          <div className="p-4 text-sm">
            <p className="text-app-danger">The history could not be loaded.</p>
            <Button size="sm" className="mt-2" onClick={() => void versions.refetch()}>
              Try again
            </Button>
          </div>
        )}
        {versions.data?.length === 0 && (
          <p className="p-4 text-sm text-app-muted">
            No versions yet. A version is created each time you apply a proposal or save your edits.
          </p>
        )}
        <ol aria-label="Versions, newest first">
          {versions.data?.map((version) => {
            const previewing = previewVersionId === version.id;
            return (
              <li
                key={version.id}
                aria-current={version.is_current ? "true" : undefined}
                className={cn(
                  "border-b border-app-border p-3",
                  previewing && "bg-app-accent-soft",
                  version.is_current && "border-l-2 border-l-app-accent",
                )}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">Version {version.version_number}</span>
                  {version.is_current && <Badge tone="accent">Current</Badge>}
                  {previewing && <Badge>Previewing</Badge>}
                </div>
                <p className="mt-0.5 text-sm">{version.description}</p>
                <p className="mt-0.5 text-xs text-app-muted">
                  {sourceLabel(version.source)} ·{" "}
                  <time dateTime={version.created_at} title={formatDateTime(version.created_at)}>
                    {formatRelativeTime(version.created_at)}
                  </time>
                </p>
                {!version.is_current && (
                  <div className="mt-2 flex gap-1.5">
                    <Button
                      size="sm"
                      icon={<Eye size={13} />}
                      busy={loadingPreview === version.id}
                      onClick={() =>
                        previewing ? useWorkspaceStore.getState().setPreview(null) : void preview(version)
                      }
                    >
                      {previewing ? "Stop preview" : "Preview"}
                    </Button>
                    <Button
                      size="sm"
                      icon={<GitCompareArrows size={13} />}
                      onClick={() => useEditorStore.getState().setCompareVersionId(version.id)}
                    >
                      Compare
                    </Button>
                    <Button size="sm" icon={<RotateCcw size={13} />} onClick={() => setConfirming(version)}>
                      Restore
                    </Button>
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      </div>

      <Dialog
        open={confirming !== null}
        onOpenChange={(open) => !open && setConfirming(null)}
        title={`Restore version ${confirming?.version_number}?`}
        description={
          "A copy of that version becomes the newest version and the current one. " +
          "Nothing in the history is changed or removed." +
          (dirty ? " Your unsaved edits will be discarded." : "")
        }
        footer={
          <>
            <Button onClick={() => setConfirming(null)}>Cancel</Button>
            <Button
              variant="accent"
              busy={restore.isPending}
              onClick={() =>
                confirming &&
                restore.mutate({ versionId: confirming.id }, { onSettled: () => setConfirming(null) })
              }
            >
              Restore
            </Button>
          </>
        }
      />
    </aside>
  );
}
