import { LayoutRenderer } from "../../renderer/LayoutRenderer";
import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GTabs({ node }: { node: ComponentOf<"tabs"> }) {
  const { Tabs } = useAdapter();
  return (
    <Tabs
      defaultTab={node.default_tab}
      tabs={node.tabs.map((tab) => ({
        id: tab.id,
        label: tab.label,
        // Each tab is its own slot, addressed by the tab's id.
        content: <LayoutRenderer slotId={tab.id} items={tab.children} />,
      }))}
    />
  );
}
