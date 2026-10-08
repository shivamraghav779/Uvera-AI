import { versionForProposal, sourceLabel, currentVersion } from "@/generative-ui/history/versionUtils";
import {
  cellStyle,
  flowRows,
  heightFromPixels,
  spanFromWidth,
  tabletSpan,
} from "@/generative-ui/workspace/LayoutEngine";
import {
  keyboardOperation,
  nudgeOperation,
  selectionAfterDelete,
  selectionPath,
} from "@/generative-ui/workspace/SelectionManager";
import { toDatasetName } from "@/features/settings/DataSourcesCard";
import type { VersionSummary } from "@/services/api/types";
import { aggregate } from "@/utils/aggregate";
import { formatRelativeTime, formatValue } from "@/utils/format";

import { sampleDocument } from "../fixtures";

describe("layout engine", () => {
  it("expresses placement as spans and presets, never positions", () => {
    expect(cellStyle({ span: 4, height: "md" })).toEqual({ "--span": 4, "--span-md": 6, minHeight: 300 });
    expect(cellStyle({ span: 12, height: "auto" })).toEqual({ "--span": 12, "--span-md": 12, minHeight: undefined });
  });

  it("collapses small spans to half width and large ones to full width on tablets", () => {
    expect([1, 3, 6, 7, 12].map(tabletSpan)).toEqual([6, 6, 6, 12, 12]);
  });

  it("snaps a dragged width to the nearest span", () => {
    const grid = 1200;
    const gap = 16;
    const column = (grid - 11 * gap) / 12;
    const widthOf = (span: number) => span * column + (span - 1) * gap;

    expect(spanFromWidth(widthOf(6), grid, gap)).toBe(6);
    expect(spanFromWidth(widthOf(6) + 30, grid, gap)).toBe(6);
    expect(spanFromWidth(widthOf(6) + 70, grid, gap)).toBe(7);
    expect(spanFromWidth(5, grid, gap)).toBe(1);
    expect(spanFromWidth(5000, grid, gap)).toBe(12);
  });

  it("snaps a dragged height to a preset", () => {
    expect([60, 190, 310, 400, 900].map(heightFromPixels)).toEqual(["auto", "sm", "md", "lg", "xl"]);
  });

  it("computes the rows the flow grid produces", () => {
    const rows = flowRows(sampleDocument().page.components).map((row) => row.map((item) => item.id));

    expect(rows).toEqual([
      ["revenue_metric", "orders_metric", "aov_metric", "top_region_metric"],
      ["monthly_revenue_chart", "product_share_chart"],
      ["region_filter"],
      ["regional_table"],
    ]);
  });
});

describe("selection", () => {
  const page = sampleDocument().page;

  it("describes the path to the selected component", () => {
    expect(selectionPath(page, "regional_table")).toEqual([
      { id: "regional_table", label: "Sales by region", type: "table" },
    ]);
    expect(selectionPath(page, "missing")).toEqual([]);
  });

  it("nudges within the parent and stops at the edges", () => {
    expect(nudgeOperation(page, "orders_metric", 1)).toEqual({ type: "MOVE", target: "orders_metric", index: 2 });
    expect(nudgeOperation(page, "revenue_metric", -1)).toBeNull();
    expect(nudgeOperation(page, "regional_table", 1)).toBeNull();
  });

  it("maps keys to operations", () => {
    expect(keyboardOperation(page, "aov_metric", { key: "Delete", altKey: false })).toEqual({
      type: "DELETE",
      target: "aov_metric",
    });
    expect(keyboardOperation(page, "aov_metric", { key: "ArrowLeft", altKey: true })).toEqual({
      type: "MOVE",
      target: "aov_metric",
      index: 1,
    });
    expect(keyboardOperation(page, "aov_metric", { key: "ArrowLeft", altKey: false })).toBeNull();
  });

  it("moves the selection to a neighbour when a component is deleted", () => {
    expect(selectionAfterDelete(page, "revenue_metric")).toBe("orders_metric");
    expect(selectionAfterDelete(page, "regional_table")).toBe("region_filter");
  });
});

describe("versions", () => {
  const version = (overrides: Partial<VersionSummary>): VersionSummary => ({
    id: "v",
    workspace_id: "w",
    version_number: 1,
    parent_version_id: null,
    description: "",
    source: "ai_mutation",
    metadata: {},
    created_at: "2026-10-05T10:00:00Z",
    created_by: null,
    is_current: false,
    ...overrides,
  });

  it("finds the version a proposal became", () => {
    const versions = [
      version({ id: "v2", version_number: 2, metadata: { proposal_id: "p-2" }, is_current: true }),
      version({ id: "v1", metadata: { proposal_id: "p-1" } }),
    ];

    expect(versionForProposal(versions, "p-1")?.id).toBe("v1");
    expect(versionForProposal(versions, "p-9")).toBeUndefined();
    expect(versionForProposal(versions, undefined)).toBeUndefined();
    expect(currentVersion(versions)?.id).toBe("v2");
  });

  it("labels every source", () => {
    expect((["ai_generation", "ai_mutation", "manual_edit", "restore"] as const).map(sourceLabel)).toEqual([
      "AI generated",
      "AI edit",
      "Manual edit",
      "Restore",
    ]);
  });
});

describe("data helpers", () => {
  const rows = [
    { region: "North", revenue: 10 },
    { region: "South", revenue: 30 },
  ];

  it("aggregates a field", () => {
    expect(aggregate(rows, "revenue", "sum")).toBe(40);
    expect(aggregate(rows, "revenue", "avg")).toBe(20);
    expect(aggregate(rows, "revenue", "max")).toBe(30);
    expect(aggregate(rows, "region", "first")).toBe("North");
    expect(aggregate(rows, "region", "count")).toBe(2);
    expect(aggregate(rows, "region", "sum")).toBeUndefined();
    expect(aggregate([], "revenue", "sum")).toBeUndefined();
  });

  it("formats values for display", () => {
    expect(formatValue(undefined)).toBe("—");
    expect(formatValue(null, "number")).toBe("—");
    expect(formatValue(12.5, "percent")).toBe("12.5%");
    expect(formatValue(1234, "text")).toBe("1234");
    expect(formatValue(1234, "number")).toBe(new Intl.NumberFormat().format(1234));
    expect(formatValue("North", "number")).toBe("North");
    expect(formatValue(true)).toBe("Yes");
  });

  it("formats relative time", () => {
    const now = new Date("2026-10-05T12:00:00Z");

    expect(formatRelativeTime("2026-10-05T11:59:40Z", now)).toBe("just now");
    expect(formatRelativeTime("2026-10-05T09:00:00Z", now)).toMatch(/3 hours ago/);
    expect(formatRelativeTime("2026-10-04T12:00:00Z", now)).toMatch(/yesterday|1 day ago/);
  });
});

describe("dataset names", () => {
  it.each([
    ["Support tickets", "support_tickets"],
    ["Q3 Sales (final).csv", "q3_sales_final"],
    ["2026 orders", "data_2026_orders"],
    ["  --weird--  ", "weird"],
  ])("derives a valid identifier from %s", (input, expected) => {
    expect(toDatasetName(input)).toBe(expected);
    expect(toDatasetName(input)).toMatch(/^[a-z][a-z0-9_]{0,63}$/);
  });
});
