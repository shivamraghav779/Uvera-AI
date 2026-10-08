import { LayoutRenderer } from "../../renderer/LayoutRenderer";
import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GCard({ node }: { node: ComponentOf<"card"> }) {
  const { Card } = useAdapter();
  return (
    <Card title={node.title} subtitle={node.subtitle} {...node.style}>
      <LayoutRenderer slotId={node.id} items={node.children} />
    </Card>
  );
}
