import { Button } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import { useEditorStore } from "@/stores/editorStore";

/**
 * Shown when the server's current version is no longer the one this client is
 * working from. Nothing was overwritten; the user chooses when to reload.
 */
export function ConflictDialog({ onReload }: { onReload: () => void }) {
  const conflict = useEditorStore((state) => state.conflict);
  const dismiss = () => useEditorStore.getState().setConflict(null);
  return (
    <Dialog
      open={conflict !== null}
      onOpenChange={(open) => !open && dismiss()}
      title="Workspace changed"
      description={
        (conflict?.currentVersionNumber
          ? `This workspace is now at version ${conflict.currentVersionNumber}, saved from somewhere else. `
          : "This workspace was changed from somewhere else. ") +
        "Your change was not saved, and nothing was overwritten. Reload the latest version to continue; " +
        "unsaved edits and the pending proposal will be discarded."
      }
      footer={
        <>
          <Button onClick={dismiss}>Keep looking</Button>
          <Button variant="primary" onClick={onReload}>
            Reload latest version
          </Button>
        </>
      }
    />
  );
}
