import { useAdapter, useRenderer, useRuntimeValue } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GSelect({ node }: { node: ComponentOf<"select"> }) {
  const { Select } = useAdapter();
  const { runtime, dispatchAction } = useRenderer();
  const value = useRuntimeValue(node.name) ?? node.default_value ?? "";

  const change = (next: string) => {
    runtime.getState().setValue(node.name, next);
    // The schema holds the action's static parameters; the chosen value is added here.
    if (node.on_change) void dispatchAction(node.on_change, { value: next });
  };

  return (
    <Select
      id={node.id}
      name={node.name}
      label={node.label}
      options={node.options}
      value={String(value)}
      required={node.required}
      onChange={change}
    />
  );
}
