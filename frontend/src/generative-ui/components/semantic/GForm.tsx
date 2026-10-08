import { useState } from "react";

import { LayoutRenderer } from "../../renderer/LayoutRenderer";
import { useAdapter, useRenderer } from "../../renderer/RendererContext";
import type { ComponentOf, Scalar } from "../../schema/types";

export function GForm({ node }: { node: ComponentOf<"form"> }) {
  const { Form } = useAdapter();
  const { runtime, dispatchAction } = useRenderer();
  const [submitting, setSubmitting] = useState(false);

  const submit = async () => {
    const all = runtime.getState().values;
    const values: Record<string, Scalar> = {};
    for (const field of node.fields) {
      values[field.name] = all[field.name] ?? defaultValue(field);
    }
    setSubmitting(true);
    try {
      await dispatchAction(node.submit_action, { form_id: node.id, values });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Form title={node.title} submitLabel={node.submit_label} submitting={submitting} onSubmit={submit}>
      <LayoutRenderer slotId={node.id} items={node.fields} />
    </Form>
  );
}

function defaultValue(field: ComponentOf<"form">["fields"][number]): Scalar {
  if (field.type === "checkbox") return field.checked;
  return field.default_value ?? "";
}
