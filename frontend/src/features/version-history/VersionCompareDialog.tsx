import { Skeleton } from "@/components/feedback/Skeleton";
import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { useEditorStore } from "@/stores/editorStore";

import { ChangePreview } from "../chat/ChangePreview";

import { useComparison } from "./queries";

/** Schema-based comparison of an older version with the current one. */
export function VersionCompareDialog({ workspaceId }: { workspaceId: string }) {
  const versionId = useEditorStore((state) => state.compareVersionId);
  const close = () => useEditorStore.getState().setCompareVersionId(null);
  const comparison = useComparison(workspaceId, versionId);
  const data = comparison.data;

  return (
    <Dialog
      open={versionId !== null}
      onOpenChange={(open) => !open && close()}
      size="md"
      title={
        data
          ? `Version ${data.from_version.version_number} → Version ${data.to_version.version_number}`
          : "Comparing versions"
      }
      description={
        data
          ? `What is different in the current version compared with version ${data.from_version.version_number}.`
          : undefined
      }
      footer={<Button onClick={close}>Close</Button>}
    >
      {comparison.isPending && (
        <div role="status" aria-label="Comparing versions" className="flex flex-col gap-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      )}
      {comparison.isError && <p className="text-sm text-app-danger">The comparison could not be loaded.</p>}
      {data && (
        <ChangePreview changes={data.changes} limit={50} emptyText="These two versions are identical." />
      )}
    </Dialog>
  );
}
