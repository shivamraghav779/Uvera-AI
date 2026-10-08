import { LayoutRenderer } from "../../renderer/LayoutRenderer";
import { useAdapter } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";
import { AssetImage } from "../patterns/shared";

export function GSection({ node }: { node: ComponentOf<"section"> }) {
  const { Section } = useAdapter();
  const backdrop = node.image ? (
    <div className="absolute inset-0 -z-10">
      <AssetImage assetId={node.image} alt={node.title} className="!absolute inset-0 h-full" />
      <div className="absolute inset-0 bg-black/55" />
    </div>
  ) : undefined;
  return (
    <Section
      variant={node.variant}
      eyebrow={node.eyebrow}
      title={node.title}
      description={node.description}
      backdrop={backdrop}
      {...node.style}
    >
      <LayoutRenderer slotId={node.id} items={node.children} />
    </Section>
  );
}
