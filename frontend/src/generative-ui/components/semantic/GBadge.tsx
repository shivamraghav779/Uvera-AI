import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GBadge({ node }: { node: ComponentOf<"badge"> }) {
  const { Badge } = useAdapter();
  return <Badge label={node.label} tone={node.tone} />;
}
