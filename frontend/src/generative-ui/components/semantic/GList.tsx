import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GList({ node }: { node: ComponentOf<"list"> }) {
  const { List } = useAdapter();
  return <List title={node.title} ordered={node.ordered} items={node.items} />;
}
