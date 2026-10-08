import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GTimeline({ node }: { node: ComponentOf<"timeline"> }) {
  const { Timeline } = useAdapter();
  return <Timeline title={node.title} items={node.items} />;
}
