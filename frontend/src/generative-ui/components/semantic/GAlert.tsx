import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GAlert({ node }: { node: ComponentOf<"alert"> }) {
  const { Alert } = useAdapter();
  return <Alert title={node.title} message={node.message} tone={node.tone} />;
}
