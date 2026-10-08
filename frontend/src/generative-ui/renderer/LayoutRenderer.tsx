import { memo } from "react";

import { cn } from "@/utils/cn";

import type { UIComponent } from "../schema/types";
import { cellStyle } from "../workspace/LayoutEngine";

import { ComponentRenderer } from "./ComponentRenderer";
import { useRenderer, type ElementProps, type SlotProps } from "./RendererContext";

/** Default slot wrapper: nothing to add outside the editor. */
export function StaticSlot({ children }: SlotProps) {
  return <>{children}</>;
}

/** Default cell: placement from the layout engine, plus a highlight ring in previews. */
export function StaticElement({ node, children }: ElementProps) {
  const highlighted = useRenderer().highlightIds.has(node.id);
  return (
    <div
      data-component-id={node.id}
      data-component-type={node.type}
      style={cellStyle(node.layout)}
      className={cn(
        "g-cell",
        highlighted && "rounded-g outline-2 outline-offset-4 outline-g-primary outline-dashed",
      )}
    >
      {children}
    </div>
  );
}

interface LayoutRendererProps {
  /** Id of the container (or tab) these children belong to. */
  slotId: string;
  items: readonly UIComponent[];
}

/** Lays out a container's children in the 12-column flow grid. */
export const LayoutRenderer = memo(function LayoutRenderer({ slotId, items }: LayoutRendererProps) {
  const { Slot, Element } = useRenderer();
  return (
    <Slot slotId={slotId} items={items}>
      <div className="g-grid" data-slot-id={slotId}>
        {items.map((item, index) => (
          <Element key={item.id} node={item} slotId={slotId} index={index}>
            <ComponentRenderer node={item} />
          </Element>
        ))}
      </div>
    </Slot>
  );
});
