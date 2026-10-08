import { useAdapter, useRenderer, useRuntimeValue } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GCheckbox({ node }: { node: ComponentOf<"checkbox"> }) {
  const { Checkbox } = useAdapter();
  const { runtime, dispatchAction } = useRenderer();
  const checked = useRuntimeValue(node.name) ?? node.checked;

  const change = (next: boolean) => {
    runtime.getState().setValue(node.name, next);
    if (node.on_change) void dispatchAction(node.on_change, { value: next });
  };

  return (
    <Checkbox id={node.id} name={node.name} label={node.label} checked={checked === true} onChange={change} />
  );
}
