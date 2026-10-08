import { LayoutRenderer } from "../../renderer/LayoutRenderer";
import type { ComponentOf } from "../../schema/types";

/** One screen of an application: a column of the chosen width holding its components. */
export function GScreen({ node }: { node: ComponentOf<"screen"> }) {
  // A full-width screen is made of bands that carry their own headings.
  const titled = node.show_title && node.width !== "full";
  return (
    <div className="g-screen" data-width={node.width} data-screen-id={node.id} data-screen-type={node.screen_type}>
      {titled && (
        <header className="mb-[calc(var(--g-gap)*1.25)]">
          <h1 className="g-h2 !text-[calc(1.75em*var(--g-heading-scale))]">{node.title}</h1>
        </header>
      )}
      <div className="g-screen-body">
        <LayoutRenderer slotId={node.id} items={node.children} />
      </div>
    </div>
  );
}
