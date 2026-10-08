import { useAdapter, useRows } from "../../renderer/RendererContext";
import { DEFAULT_CHART_HEIGHT } from "../../schema/defaults";
import type { ComponentOf } from "../../schema/types";
import { heightInPixels } from "../../workspace/LayoutEngine";

export function GChart({ node }: { node: ComponentOf<"chart"> }) {
  const { Chart } = useAdapter();
  const rows = useRows(node, node.data);
  return (
    <Chart
      title={node.title}
      chartType={node.chart_type}
      rows={rows as Record<string, string | number | boolean | null>[]}
      xKey={node.x_key}
      yKeys={node.y_keys}
      height={heightInPixels(node.layout.height) ?? DEFAULT_CHART_HEIGHT}
      {...node.style}
    />
  );
}
