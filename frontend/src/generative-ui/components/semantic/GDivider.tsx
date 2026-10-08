import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GDivider({ node }: { node: ComponentOf<"divider"> }) {
  const { Divider } = useAdapter();
  return <Divider label={node.label} />;
}
