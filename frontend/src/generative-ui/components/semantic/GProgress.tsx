import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GProgress({ node }: { node: ComponentOf<"progress"> }) {
  const { Progress } = useAdapter();
  return <Progress label={node.label} value={node.value} max={node.max} tone={node.tone} />;
}
