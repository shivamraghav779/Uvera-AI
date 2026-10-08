import { LayoutDashboard, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router";

import { Skeleton } from "@/components/feedback/Skeleton";
import { StateMessage } from "@/components/feedback/StateMessage";
import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { Dialog } from "@/components/ui/Dialog";
import type { WorkspaceRead } from "@/services/api/types";
import { toast } from "@/stores/toastStore";
import { formatRelativeTime } from "@/utils/format";

import { useCreateWorkspace, useDeleteWorkspace, useWorkspaces } from "./queries";
import { WorkspaceThumbnail } from "./WorkspaceThumbnail";

export function WorkspaceListPage() {
  const navigate = useNavigate();
  const workspaces = useWorkspaces();
  const create = useCreateWorkspace();
  const remove = useDeleteWorkspace();
  const [deleting, setDeleting] = useState<WorkspaceRead | null>(null);

  const createWorkspace = () =>
    create.mutate(undefined, {
      onSuccess: (workspace) => navigate(`/workspaces/${workspace.id}`),
      onError: () => toast.error("The workspace could not be created."),
    });

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-5xl px-6 py-10">
        <header className="mb-8 flex items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Workspaces</h1>
            <p className="mt-1 text-sm text-app-muted">
              Each workspace is one interface you build by describing it, with its full version history.
            </p>
          </div>
          <Button variant="primary" icon={<Plus size={15} />} onClick={createWorkspace} busy={create.isPending}>
            New workspace
          </Button>
        </header>

        {workspaces.isPending && (
          <div role="status" aria-label="Loading workspaces" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((index) => (
              <Skeleton key={index} className="h-60" />
            ))}
          </div>
        )}

        {workspaces.isError && (
          <StateMessage
            tone="error"
            title="Workspaces could not be loaded"
            description={workspaces.error.message}
            action={
              <Button variant="primary" onClick={() => void workspaces.refetch()}>
                Try again
              </Button>
            }
          />
        )}

        {workspaces.data?.length === 0 && (
          <div className="rounded-xl border border-dashed border-app-border-strong py-16">
            <StateMessage
              icon={<LayoutDashboard size={18} />}
              title="No workspaces yet"
              description="Create one and describe the interface you need."
              action={
                <Button variant="primary" icon={<Plus size={15} />} onClick={createWorkspace} busy={create.isPending}>
                  New workspace
                </Button>
              }
            />
          </div>
        )}

        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {workspaces.data?.map((workspace) => (
            <li
              key={workspace.id}
              className="group relative rounded-xl border border-app-border bg-app-panel transition-[border-color,box-shadow] hover:border-app-border-strong hover:shadow-app-float"
            >
              <Link to={`/workspaces/${workspace.id}`} className="block rounded-xl">
                <WorkspaceThumbnail workspace={workspace} />
                <h2 className="truncate px-4 pt-3 font-semibold">{workspace.title ?? "Untitled workspace"}</h2>
                <p className="flex px-4 pt-2 pb-4 items-center gap-2 text-xs text-app-muted">
                  {workspace.current_version_number ? (
                    <Badge>v{workspace.current_version_number}</Badge>
                  ) : (
                    <Badge tone="warning">Empty</Badge>
                  )}
                  <span>Updated {formatRelativeTime(workspace.updated_at)}</span>
                </p>
              </Link>
              <IconButton
                label={`Delete ${workspace.title ?? "workspace"}`}
                onClick={() => setDeleting(workspace)}
                className="absolute top-2 right-2 bg-app-panel shadow-app-float opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
              >
                <Trash2 size={15} />
              </IconButton>
            </li>
          ))}
        </ul>
      </div>

      <Dialog
        open={deleting !== null}
        onOpenChange={(open) => !open && setDeleting(null)}
        title={`Delete “${deleting?.title ?? "Untitled workspace"}”?`}
        description="The workspace, its conversation and every version are deleted permanently."
        footer={
          <>
            <Button onClick={() => setDeleting(null)}>Cancel</Button>
            <Button
              variant="danger"
              busy={remove.isPending}
              onClick={() =>
                deleting &&
                remove.mutate(deleting.id, {
                  onSettled: () => setDeleting(null),
                  onError: () => toast.error("The workspace could not be deleted."),
                })
              }
            >
              Delete
            </Button>
          </>
        }
      />
    </div>
  );
}
