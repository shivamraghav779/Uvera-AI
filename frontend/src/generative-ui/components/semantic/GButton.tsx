import { useState } from "react";

import { useAdapter, useRenderer } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GButton({ node }: { node: ComponentOf<"button"> }) {
  const { Button } = useAdapter();
  const { dispatchAction } = useRenderer();
  const [busy, setBusy] = useState(false);

  // The button can only request an allowlisted action; it never runs code from the schema.
  const click = async () => {
    setBusy(true);
    try {
      await dispatchAction(node.action);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Button label={node.label} variant={node.variant} disabled={node.disabled} busy={busy} onClick={click} />
  );
}
