import { useMemo } from "react";

import { formatValue } from "@/utils/format";

import { useAdapter, useRenderer, useRows } from "../../renderer/RendererContext";
import type { ComponentOf } from "../../schema/types";
import { heightInPixels } from "../../workspace/LayoutEngine";

export function GTable({ node }: { node: ComponentOf<"table"> }) {
  const { Table } = useAdapter();
  const { dispatchAction } = useRenderer();
  const rows = useRows(node, node.rows);
  const cells = useMemo(
    () =>
      rows.map((row) =>
        Object.fromEntries(
          node.columns.map((column) => [column.key, formatValue(row[column.key], column.format)]),
        ),
      ),
    [rows, node.columns],
  );
  const action = node.row_action;
  return (
    <Table
      title={node.title}
      columns={node.columns}
      rows={cells}
      pageSize={node.page_size}
      height={heightInPixels(node.layout.height)}
      // The action receives the record itself, so it can open or change that record.
      onRowClick={action ? (index) => void dispatchAction(action, {}, { row: rows[index] }) : undefined}
    />
  );
}
