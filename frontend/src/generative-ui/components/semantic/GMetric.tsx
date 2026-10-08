import { useMemo } from "react";

import { aggregate } from "@/utils/aggregate";
import { formatValue } from "@/utils/format";

import { useAdapter, useDataset, useRouteParams } from "../../renderer/RendererContext";
import { filterRows } from "../../runtime/rows";
import type { ComponentOf } from "../../schema/types";

export function GMetric({ node }: { node: ComponentOf<"metric"> }) {
  const { Metric } = useAdapter();
  // A bound metric is computed from the dataset; the figure never comes from model text.
  const binding = node.data_source;
  const rows = useDataset(binding?.dataset);
  const params = useRouteParams();
  const raw = useMemo(
    () => (binding ? aggregate(filterRows(rows, binding.where, params), binding.field, binding.aggregate) : node.value),
    [binding, rows, params, node.value],
  );
  const format = node.format === "text" && typeof raw === "number" ? "number" : node.format;
  return (
    <Metric
      title={node.title}
      value={formatValue(raw, format, { compactNumbers: true })}
      unit={node.unit}
      trend={node.trend}
      description={node.description}
      {...node.style}
    />
  );
}
