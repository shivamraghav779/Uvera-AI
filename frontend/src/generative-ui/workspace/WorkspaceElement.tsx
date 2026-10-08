/**
 * One component on the canvas in edit mode: selectable, draggable among its
 * siblings (or into another container) and resizable. Every gesture ends as an
 * operation (MOVE, RESIZE, DELETE) handed to the canvas owner — exactly the
 * operations the assistant produces for the same intent.
 */
import { rectSortingStrategy, SortableContext, useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical } from "lucide-react";
import { useCallback, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";

import { cn } from "@/utils/cn";

import type { ElementProps, SlotProps } from "../renderer/RendererContext";
import type { LayoutSpec } from "../schema/types";

import { useEditor } from "./EditorContext";
import { cellStyle, heightFromPixels, spanFromWidth } from "./LayoutEngine";
import { keyboardOperation, selectionAfterDelete, typeLabel } from "./SelectionManager";

/** Makes a container's children a sortable list. */
export function EditableSlot({ slotId, items, children }: SlotProps) {
  return (
    <SortableContext id={slotId} items={items.map((item) => item.id)} strategy={rectSortingStrategy}>
      {children}
    </SortableContext>
  );
}

type Axis = "width" | "height";

export function WorkspaceElement({ node, slotId, index, children }: ElementProps) {
  const { page, selectedId, select, apply } = useEditor();
  const selected = selectedId === node.id;
  const element = useRef<HTMLDivElement | null>(null);
  // Layout shown while a resize handle is being dragged; committed on release.
  const [live, setLive] = useState<LayoutSpec | null>(null);
  const liveRef = useRef<LayoutSpec | null>(null);

  const { attributes, listeners, setNodeRef, setActivatorNodeRef, transform, transition, isDragging } =
    useSortable({ id: node.id, data: { slotId, index } });

  const setRefs = useCallback(
    (value: HTMLDivElement | null) => {
      element.current = value;
      setNodeRef(value);
    },
    [setNodeRef],
  );

  const startResize = (event: PointerEvent, axis: Axis) => {
    event.preventDefault();
    event.stopPropagation();
    const cell = element.current;
    const grid = cell?.parentElement;
    if (!cell || !grid) return;
    const gridWidth = grid.getBoundingClientRect().width;
    const gap = parseFloat(getComputedStyle(grid).columnGap) || 0;
    const start = cell.getBoundingClientRect();
    const origin = { x: event.clientX, y: event.clientY };

    const onMove = (move: globalThis.PointerEvent) => {
      const next: LayoutSpec =
        axis === "width"
          ? { ...node.layout, span: spanFromWidth(start.width + move.clientX - origin.x, gridWidth, gap) }
          : { ...node.layout, height: heightFromPixels(start.height + move.clientY - origin.y) };
      liveRef.current = next;
      setLive(next);
    };
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      const next = liveRef.current;
      liveRef.current = null;
      setLive(null);
      if (!next) return;
      if (axis === "width" && next.span !== node.layout.span) {
        apply([{ type: "RESIZE", target: node.id, span: next.span }]);
      } else if (axis === "height" && next.height !== node.layout.height) {
        apply([{ type: "RESIZE", target: node.id, height: next.height }]);
      }
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp, { once: true });
  };

  const onKeyDown = (event: KeyboardEvent) => {
    // Only keys pressed on the element itself, not inside a field it contains.
    if (event.target !== event.currentTarget) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      select(node.id);
      return;
    }
    if (event.key === "Escape") {
      select(null);
      return;
    }
    if (!selected) return;
    const operation = keyboardOperation(page, node.id, event);
    if (!operation) return;
    event.preventDefault();
    if (operation.type === "DELETE") select(selectionAfterDelete(page, node.id));
    apply([operation]);
  };

  const layout = live ?? node.layout;
  return (
    <div
      ref={setRefs}
      role="group"
      tabIndex={0}
      aria-label={`${typeLabel(node.type)} ${node.id}`}
      aria-selected={selected}
      data-component-id={node.id}
      data-component-type={node.type}
      data-selected={selected || undefined}
      onClick={(event) => {
        // The innermost element under the pointer wins.
        event.stopPropagation();
        select(node.id);
      }}
      onKeyDown={onKeyDown}
      style={{ ...cellStyle(layout), transform: CSS.Translate.toString(transform), transition }}
      className={cn(
        "g-cell group/element relative rounded-[6px] outline-offset-[3px]",
        "outline-1 outline-transparent hover:outline-app-border-strong hover:outline-dashed",
        selected && "z-10 outline-2 outline-app-accent outline-solid hover:outline-app-accent hover:outline-solid",
        isDragging && "z-20 opacity-60",
      )}
    >
      {children}

      {selected && (
        <>
          <div className="absolute -top-[26px] left-0 z-20 flex h-[22px] items-center overflow-hidden rounded-t-md bg-app-accent text-[11px] font-medium whitespace-nowrap text-app-accent-fg">
            <button
              ref={setActivatorNodeRef}
              type="button"
              aria-label={`Drag ${node.id} to move it`}
              title="Drag to move"
              className="grid h-full w-5 cursor-grab place-items-center hover:bg-black/15 active:cursor-grabbing"
              {...attributes}
              {...listeners}
            >
              <GripVertical size={12} aria-hidden />
            </button>
            <span className="pr-2 pl-1">
              {typeLabel(node.type)} · {node.id}
              {live && ` · ${live.span}/12 · ${live.height}`}
            </span>
          </div>
          <div
            role="separator"
            aria-orientation="vertical"
            aria-label="Resize width"
            title="Drag to change width"
            onPointerDown={(event) => startResize(event, "width")}
            className="absolute top-1/2 -right-[7px] z-20 h-10 w-[10px] -translate-y-1/2 cursor-ew-resize rounded-full border-2 border-app-panel bg-app-accent"
          />
          <div
            role="separator"
            aria-orientation="horizontal"
            aria-label="Resize height"
            title="Drag to change height"
            onPointerDown={(event) => startResize(event, "height")}
            className="absolute -bottom-[7px] left-1/2 z-20 h-[10px] w-10 -translate-x-1/2 cursor-ns-resize rounded-full border-2 border-app-panel bg-app-accent"
          />
        </>
      )}
    </div>
  );
}
