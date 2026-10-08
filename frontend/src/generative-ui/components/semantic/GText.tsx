import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GText({ node }: { node: ComponentOf<"text"> }) {
  const { Text } = useAdapter();
  // Content is rendered as text by React; it is never interpreted as markup.
  return <Text content={node.content} variant={node.variant} {...node.style} />;
}
