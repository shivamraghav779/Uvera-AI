import { useAdapter, useRenderer, useRuntimeValue } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GInput({ node }: { node: ComponentOf<"input"> }) {
  const { Input } = useAdapter();
  const { runtime, dispatchAction } = useRenderer();
  const value = useRuntimeValue(node.name) ?? node.default_value ?? "";

  const change = (next: string) => {
    runtime.getState().setValue(node.name, next);
    if (node.on_change) void dispatchAction(node.on_change, { value: next });
  };

  return (
    <Input
      id={node.id}
      name={node.name}
      label={node.label}
      inputType={node.input_type}
      placeholder={node.placeholder}
      value={String(value)}
      required={node.required}
      onChange={change}
    />
  );
}
