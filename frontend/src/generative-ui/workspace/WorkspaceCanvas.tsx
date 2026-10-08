/**
 * The canvas: renders one UI document through theme -> renderer -> registry ->
 * adapter. The same component serves the live view, the editor and read-only
 * previews; only `mode` and the wrappers around cells differ.
 */
import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { memo, useCallback, useMemo, useState } from "react";

import { buildAssetIndex } from "../assets/assetRegistry";
import type { Operation } from "../mutation/mutationTypes";
import { createActionDispatcher } from "../renderer/actionRuntime";
import { ComponentRenderer } from "../renderer/ComponentRenderer";
import type { RenderMode } from "../renderer/RendererContext";
import { RendererProvider, type DispatcherEnvironment } from "../renderer/RendererProvider";
import { useAppRuntime } from "../runtime/appRuntime";
import type { DataMap, UIDocument } from "../schema/types";
import { ThemeProvider } from "../theme/ThemeProvider";

import { EditorContext, type EditorContextValue } from "./EditorContext";
import { EditableSlot, WorkspaceElement } from "./WorkspaceElement";

export interface WorkspaceCanvasProps {
  document: UIDocument;
  data: DataMap;
  mode: RenderMode;
  workspaceId: string;
  highlightIds?: readonly string[];
  selectedId?: string | null;
  onSelect?: (componentId: string | null) => void;
  /** Called with operations produced by direct manipulation. */
  onOperations?: (operations: Operation[]) => void;
  onNavigate?: (path: string) => void;
  onRequestGeneration?: (instruction: string) => void;
  /**
   * Where the user is inside a generated application. Leave both out and the
   * canvas keeps the path itself (a preview, a thumbnail).
   */
  path?: string | null;
  onPathChange?: (path: string) => void;
}

interface SortableData {
  slotId: string;
  index: number;
}

const noop = () => {};

export const WorkspaceCanvas = memo(function WorkspaceCanvas({
  document,
  data,
  mode,
  workspaceId,
  highlightIds,
  selectedId = null,
  onSelect = noop,
  onOperations = noop,
  onNavigate = noop,
  onRequestGeneration = noop,
  path,
  onPathChange,
}: WorkspaceCanvasProps) {
  const editing = mode === "edit";
  const [ownPath, setOwnPath] = useState<string | null>(null);
  const app = useAppRuntime(document, data, onPathChange ? path : ownPath, onPathChange ?? setOwnPath);
  const assets = useMemo(() => buildAssetIndex(document), [document]);
  const sensors = useSensors(
    // A small drag distance keeps a click a click.
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const createDispatcher = useCallback(
    ({ runtime, getApp }: DispatcherEnvironment) =>
      createActionDispatcher({
        workspaceId,
        mode,
        runtime,
        getApp,
        navigate: onNavigate,
        requestGeneration: onRequestGeneration,
      }),
    [workspaceId, mode, onNavigate, onRequestGeneration],
  );

  const editor = useMemo<EditorContextValue>(
    () => ({ page: document.page, selectedId, select: onSelect, apply: onOperations }),
    [document.page, selectedId, onSelect, onOperations],
  );

  const onDragEnd = ({ active, over }: DragEndEvent) => {
    if (!over || active.id === over.id) return;
    const from = active.data.current as SortableData | undefined;
    const to = over.data.current as SortableData | undefined;
    if (!from || !to) return;
    // Dropping on a sibling reorders; dropping on a component elsewhere moves into its container.
    onOperations([
      from.slotId === to.slotId
        ? { type: "MOVE", target: String(active.id), index: to.index }
        : { type: "MOVE", target: String(active.id), parent_id: to.slotId, index: to.index },
    ]);
  };

  const content = (
    <RendererProvider
      mode={mode}
      framework={document.design.framework}
      data={data}
      highlightIds={highlightIds}
      app={app}
      assets={assets}
      createDispatcher={createDispatcher}
      Slot={editing ? EditableSlot : undefined}
      Element={editing ? WorkspaceElement : undefined}
    >
      <ComponentRenderer node={document.page} />
    </RendererProvider>
  );

  return (
    <ThemeProvider
      theme={document.theme}
      framework={document.design.framework}
      // An application brings its own frame; a single view gets a margin.
      className={app ? "min-h-full" : "min-h-full p-[calc(var(--g-gap)*1.5)]"}
    >
      {editing ? (
        <EditorContext.Provider value={editor}>
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
            {/* Clicking empty canvas clears the selection. */}
            <div onClick={() => onSelect(null)} className={app ? "min-h-full" : "min-h-full pt-5"}>
              {content}
            </div>
          </DndContext>
        </EditorContext.Provider>
      ) : (
        content
      )}
    </ThemeProvider>
  );
});
