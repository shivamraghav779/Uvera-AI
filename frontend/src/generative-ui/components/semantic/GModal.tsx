import { LayoutRenderer } from "../../renderer/LayoutRenderer";
import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";

export function GModal({ node }: { node: ComponentOf<"modal"> }) {
  const { Modal } = useAdapter();
  return (
    <Modal title={node.title} triggerLabel={node.trigger_label}>
      <LayoutRenderer slotId={node.id} items={node.children} />
    </Modal>
  );
}
