import { Eye, History, Monitor, PencilRuler, Redo2, Smartphone, Tablet, Undo2 } from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button, IconButton } from "@/components/ui/Button";
import { Segmented } from "@/components/ui/Segmented";

export type ToolbarMode = "view" | "edit";
export type ToolbarDevice = "desktop" | "tablet" | "mobile";

interface WorkspaceToolbarProps {
  /** Title area (the workspace name, editable by its owner). */
  title: ReactNode;
  versionNumber: number | null;
  mode: ToolbarMode;
  onModeChange: (mode: ToolbarMode) => void;
  /** Editing is unavailable while there is nothing to edit or a preview is shown. */
  canEdit: boolean;
  device: ToolbarDevice;
  onDeviceChange: (device: ToolbarDevice) => void;
  canUndo: boolean;
  canRedo: boolean;
  onUndo: () => void;
  onRedo: () => void;
  unsavedCount: number;
  saving: boolean;
  onSave: () => void;
  onDiscard: () => void;
  historyOpen: boolean;
  onToggleHistory: () => void;
  /** Extra controls, e.g. the design menu. */
  children?: ReactNode;
}

/** The workspace's top bar: where you are, which mode you are in, and unsaved work. */
export function WorkspaceToolbar({
  title,
  versionNumber,
  mode,
  onModeChange,
  canEdit,
  device,
  onDeviceChange,
  canUndo,
  canRedo,
  onUndo,
  onRedo,
  unsavedCount,
  saving,
  onSave,
  onDiscard,
  historyOpen,
  onToggleHistory,
  children,
}: WorkspaceToolbarProps) {
  return (
    <header
      role="toolbar"
      aria-label="Workspace"
      className="flex h-12 shrink-0 items-center gap-3 border-b border-app-border bg-app-panel px-3"
    >
      <div className="flex min-w-0 flex-1 items-center gap-2">
        {title}
        {versionNumber !== null && <Badge>v{versionNumber}</Badge>}
        {unsavedCount > 0 && (
          <Badge tone="warning">
            {unsavedCount} unsaved change{unsavedCount === 1 ? "" : "s"}
          </Badge>
        )}
      </div>

      <Segmented
        label="Mode"
        value={mode}
        onChange={(next) => (next === "edit" && !canEdit ? undefined : onModeChange(next))}
        options={[
          { value: "view", label: "View", icon: <Eye size={13} aria-hidden /> },
          { value: "edit", label: "Edit", icon: <PencilRuler size={13} aria-hidden /> },
        ]}
      />

      <div className="flex flex-1 items-center justify-end gap-1.5">
        {mode === "edit" && (
          <>
            <IconButton label="Undo (unsaved edits)" onClick={onUndo} disabled={!canUndo}>
              <Undo2 size={16} />
            </IconButton>
            <IconButton label="Redo" onClick={onRedo} disabled={!canRedo}>
              <Redo2 size={16} />
            </IconButton>
            <span aria-hidden className="mx-1 h-5 w-px bg-app-border" />
          </>
        )}
        {children}
        <Segmented
          label="Preview width"
          value={device}
          onChange={onDeviceChange}
          iconOnly
          options={[
            { value: "desktop", label: "Desktop width", icon: <Monitor size={14} aria-hidden /> },
            { value: "tablet", label: "Tablet width", icon: <Tablet size={14} aria-hidden /> },
            { value: "mobile", label: "Mobile width", icon: <Smartphone size={14} aria-hidden /> },
          ]}
        />
        <IconButton label="Version history" active={historyOpen} onClick={onToggleHistory}>
          <History size={16} />
        </IconButton>
        {unsavedCount > 0 && (
          <>
            <Button size="sm" variant="ghost" onClick={onDiscard} disabled={saving}>
              Discard
            </Button>
            <Button size="sm" variant="accent" onClick={onSave} busy={saving}>
              Save version
            </Button>
          </>
        )}
      </div>
    </header>
  );
}
