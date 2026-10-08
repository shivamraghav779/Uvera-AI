import { ArrowLeft } from "lucide-react";
import { Link } from "react-router";

import { useSyncedDraft } from "@/hooks/useSyncedDraft";
import { toast } from "@/stores/toastStore";

import { useRenameWorkspace } from "./queries";

/** The workspace name in the toolbar. Click to rename; Enter or blur saves. */
export function WorkspaceTitle({ workspaceId, title }: { workspaceId: string; title: string | null }) {
  const rename = useRenameWorkspace(workspaceId);
  const [draft, setDraft] = useSyncedDraft(title ?? "");

  const commit = () => {
    const next = draft.trim();
    if (!next || next === title) {
      setDraft(title ?? "");
      return;
    }
    rename.mutate(next, { onError: () => toast.error("The workspace could not be renamed.") });
  };

  return (
    <>
      <Link
        to="/workspaces"
        aria-label="All workspaces"
        title="All workspaces"
        className="grid size-8 shrink-0 place-items-center rounded-md text-app-muted hover:bg-app-subtle hover:text-app-fg"
      >
        <ArrowLeft size={16} />
      </Link>
      <input
        aria-label="Workspace name"
        value={draft}
        placeholder="Untitled workspace"
        onChange={(event) => setDraft(event.target.value)}
        onBlur={commit}
        onKeyDown={(event) => {
          if (event.key === "Enter") event.currentTarget.blur();
          if (event.key === "Escape") setDraft(title ?? "");
        }}
        size={Math.min(Math.max(draft.length, 12), 40)}
        className="h-8 min-w-0 rounded-md bg-transparent px-1.5 text-sm font-semibold hover:bg-app-subtle focus-visible:bg-app-subtle"
      />
    </>
  );
}
