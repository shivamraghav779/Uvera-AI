/**
 * A live miniature of a workspace's current UI for its card.
 *
 * It is the saved document rendered by the real renderer at desktop width and
 * scaled down, so the picture is always what the workspace actually contains.
 * It is decorative: inert, hidden from assistive technology, never interactive.
 */
import { useQuery } from "@tanstack/react-query";
import { LayoutDashboard, PenLine } from "lucide-react";
import { useLayoutEffect, useMemo, useRef, useState } from "react";

import { parseDocument } from "@/generative-ui/schema/normalization";
import { dataMapSchema } from "@/generative-ui/schema/validators";
import { WorkspaceCanvas } from "@/generative-ui/workspace/WorkspaceCanvas";
import { queryKeys } from "@/services/api/queryKeys";
import { versionsApi } from "@/services/api/versions";
import type { WorkspaceRead } from "@/services/api/types";

/** Width the UI is laid out at before scaling: a desktop canvas. */
const RENDER_WIDTH = 1200;

function Placeholder({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 text-app-muted">
      <span className="grid size-9 place-items-center rounded-full bg-app-panel">{icon}</span>
      <span className="font-mono text-[11px]">{label}</span>
    </div>
  );
}

export function WorkspaceThumbnail({ workspace }: { workspace: WorkspaceRead }) {
  const versionId = workspace.current_version_id ?? null;
  const frame = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0);

  const version = useQuery({
    queryKey: queryKeys.version(workspace.id, versionId ?? "none"),
    queryFn: ({ signal }) => versionsApi.get(workspace.id, versionId!, signal),
    enabled: versionId !== null,
    // A version never changes once saved.
    staleTime: Infinity,
  });

  const preview = useMemo(() => {
    if (!version.data) return null;
    const document = parseDocument(version.data.document);
    if (!document.ok) return null;
    const data = dataMapSchema.safeParse(version.data.data ?? {});
    return { document: document.value, data: data.success ? data.data : {} };
  }, [version.data]);

  useLayoutEffect(() => {
    const element = frame.current;
    if (!element) return;
    const measure = () => setScale(element.clientWidth / RENDER_WIDTH);
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    return () => observer.disconnect();
  }, [preview]);

  return (
    <div aria-hidden className="h-40 overflow-hidden rounded-t-xl border-b border-app-border bg-app-canvas px-5 pt-5">
      {versionId === null ? (
        <Placeholder icon={<PenLine size={16} />} label="Awaiting first prompt" />
      ) : version.isPending ? (
        <div className="app-skeleton h-full rounded-t-lg rounded-b-none" />
      ) : preview === null ? (
        <Placeholder icon={<LayoutDashboard size={16} />} label="Preview unavailable" />
      ) : (
        // The floating window: rounded top, cropped by the card at the bottom.
        <div
          ref={frame}
          inert
          className="pointer-events-none h-full overflow-hidden rounded-t-lg border border-b-0 border-app-border shadow-app-modal select-none"
        >
          {scale > 0 && (
            <div
              // Taller than the frame before scaling, so a short page still fills it.
              style={{
                width: RENDER_WIDTH,
                height: `${100 / scale}%`,
                transform: `scale(${scale})`,
                transformOrigin: "top left",
              }}
            >
              <WorkspaceCanvas document={preview.document} data={preview.data} mode="view" workspaceId={workspace.id} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}
