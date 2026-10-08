import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { shadcnComponents } from "@/generative-ui/components/adapters/shadcn";
import type { Operation } from "@/generative-ui/mutation/mutationTypes";
import { applyValidated } from "@/generative-ui/mutation/mutationValidator";
import { findCapabilityGaps, frontendCapabilities } from "@/generative-ui/registry/capabilityRegistry";
import { getComponentDefinition, supportedComponentTypes } from "@/generative-ui/registry/componentRegistry";
import {
  implementedComponents,
  registeredFrameworkIds,
  resolveAdapter,
} from "@/generative-ui/registry/frameworkRegistry";
import { evaluateCondition } from "@/generative-ui/renderer/ComponentRenderer";
import { isSafeDestination } from "@/generative-ui/renderer/actionRuntime";
import { parseDocument } from "@/generative-ui/schema/normalization";
import type { UIDocument } from "@/generative-ui/schema/types";
import { WorkspaceCanvas, type WorkspaceCanvasProps } from "@/generative-ui/workspace/WorkspaceCanvas";
import { actionsApi } from "@/services/api/actions";

import { documentWith, fixtures, sampleDocument } from "../fixtures";

vi.mock("@/services/api/actions", () => ({ actionsApi: { execute: vi.fn() } }));

function renderCanvas(document: UIDocument, props: Partial<WorkspaceCanvasProps> = {}) {
  return render(
    <WorkspaceCanvas document={document} data={fixtures.sample_data} mode="view" workspaceId="w1" {...props} />,
  );
}

function parsed(input: unknown): UIDocument {
  const result = parseDocument(input);
  if (!result.ok) throw new Error(JSON.stringify(result.issues));
  return result.value;
}

function switchFramework(framework: string): UIDocument {
  const result = applyValidated(sampleDocument(), [{ type: "SET_FRAMEWORK", framework }]);
  if (!result.ok) throw new Error(JSON.stringify(result.issues));
  return result.value;
}

describe("registries", () => {
  it("has a renderer for every component type the backend can generate", () => {
    expect(supportedComponentTypes().sort()).toEqual(Object.keys(fixtures.component_examples).sort());
  });

  it("has an adapter for every framework the backend marks available", () => {
    const available = fixtures.frameworks.filter((f) => f.status === "available").map((f) => f.id);

    expect(registeredFrameworkIds().sort()).toEqual(available.sort());
  });

  it("completes a partial adapter with the default one", () => {
    const material = resolveAdapter("material");

    expect(implementedComponents("material")).toContain("Button");
    expect(material.Button).not.toBe(shadcnComponents.Button);
    expect(material.Table).toBe(shadcnComponents.Table);
    expect(Object.keys(material).sort()).toEqual(Object.keys(shadcnComponents).sort());
  });

  it("falls back to the default adapter for an unknown framework", () => {
    expect(resolveAdapter("not-a-framework")).toBe(resolveAdapter("shadcn"));
  });

  it("reports what the backend can produce that this build cannot render", () => {
    const backend = {
      components: [...frontendCapabilities().components, "hologram"],
      chart_types: ["bar", "radar"],
    } as Parameters<typeof findCapabilityGaps>[0];

    expect(findCapabilityGaps(backend, undefined)).toEqual({
      components: ["hologram"],
      chartTypes: ["radar"],
      frameworks: [],
    });
  });

  it("describes editable properties for the inspector", () => {
    expect(getComponentDefinition("chart")?.fields.map((field) => field.key)).toEqual(["title", "chart_type"]);
    expect(getComponentDefinition("section")?.container).toBe(true);
  });
});

describe("rendering a document", () => {
  it("renders every component with data resolved from bindings", () => {
    renderCanvas(sampleDocument());

    expect(screen.getByRole("heading", { level: 1, name: "Sales Dashboard" })).toBeInTheDocument();
    for (const id of ["revenue_metric", "monthly_revenue_chart", "regional_table", "region_filter"]) {
      expect(document.querySelector(`[data-component-id="${id}"]`)).not.toBeNull();
    }
    // The metric is computed from the bound dataset, not written by the model.
    const total = fixtures.sample_data.sales_summary![0]!.total_revenue as number;
    const compact = new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 2 });
    expect(screen.getByText(compact.format(total))).toBeInTheDocument();
    expect(screen.getByText("North", { selector: "p" })).toBeInTheDocument();

    const table = screen.getByRole("table", { name: "Sales by region" });
    expect(within(table).getAllByRole("row")).toHaveLength(1 + fixtures.sample_data.sales_by_region!.length);
    expect(screen.getByRole("combobox", { name: "Region" })).toBeInTheDocument();
  });

  it("applies the theme as scoped CSS variables", () => {
    const { container } = renderCanvas(sampleDocument());
    const root = container.querySelector<HTMLElement>(".g-root")!;

    expect(root.style.getPropertyValue("--g-primary")).toBe("#2563EB");
    expect(root.dataset.themeMode).toBe("light");
    expect(document.documentElement.style.getPropertyValue("--g-primary")).toBe("");
  });

  it("renders the same document through another framework without changing it", () => {
    const material = switchFramework("material");
    const { container } = renderCanvas(material);

    expect(material.page).toEqual(sampleDocument().page);
    expect(container.querySelector(".g-root")).toHaveAttribute("data-framework", "material");
    expect(screen.getByRole("heading", { level: 1, name: "Sales Dashboard" })).toBeInTheDocument();
    // The material metric labels its title in uppercase tracking; shadcn does not.
    expect(screen.getByText("Avg. order value").className).toContain("uppercase");
  });

  it("renders text as text, never as markup", () => {
    const hostile = '<img src=x onerror="window.pwned = true"><b>bold</b>';
    // Bypasses validation on purpose: even a document that slipped through must be inert.
    const document_ = parsed(documentWith({ type: "text", id: "note", content: "placeholder" }));
    (document_.page.components[0] as { content: string }).content = hostile;

    const { container } = renderCanvas(document_);

    expect(screen.getByText(hostile)).toBeInTheDocument();
    expect(container.querySelector("img")).toBeNull();
    expect(container.querySelector("b")).toBeNull();
    expect((window as unknown as { pwned?: boolean }).pwned).toBeUndefined();
  });

  it("shows a placeholder for a component type it does not know", () => {
    const document_ = parsed(documentWith({ type: "divider", id: "line" }));
    (document_.page.components as unknown[]).push({
      type: "hologram",
      id: "future",
      layout: { span: 12, height: "auto" },
      script: "alert(1)",
    });

    renderCanvas(document_);

    expect(screen.getByRole("note")).toHaveTextContent("cannot display “hologram” components (future)");
  });

  it("hides and shows components from declarative conditions", async () => {
    const document_ = parsed(
      documentWith(
        { type: "checkbox", id: "toggle", name: "show_details", label: "Show details" },
        {
          type: "text",
          id: "details",
          content: "The details",
          visible_when: { field: "show_details", operator: "equals", value: true },
        },
      ),
    );
    renderCanvas(document_);

    expect(screen.queryByText("The details")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("checkbox", { name: "Show details" }));
    expect(screen.getByText("The details")).toBeInTheDocument();
  });

  it("evaluates conditions without an expression language", () => {
    expect(evaluateCondition({ field: "x", operator: "in", value: ["a", "b"] }, "a")).toBe(true);
    expect(evaluateCondition({ field: "x", operator: "gt", value: 3 }, 5)).toBe(true);
    expect(evaluateCondition({ field: "x", operator: "is_empty" }, "")).toBe(true);
    expect(evaluateCondition({ field: "x", operator: "equals", value: "1 == 1" }, "1")).toBe(false);
  });
});

describe("actions", () => {
  beforeEach(() => vi.mocked(actionsApi.execute).mockReset());

  it("sends the allowlisted action with the chosen value and shows the returned rows", async () => {
    vi.mocked(actionsApi.execute).mockResolvedValue({
      action_id: "a1",
      workspace_id: "w1",
      action_type: "filter",
      result: { target: "regional_table", rows: [{ region: "South", revenue: 5, orders: 1 }] },
    });
    renderCanvas(sampleDocument());

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Region" }), "South");

    expect(actionsApi.execute).toHaveBeenCalledWith("w1", "filter", {
      dataset: "sales_by_region",
      field: "region",
      target: "regional_table",
      value: "South",
    });
    const table = screen.getByRole("table", { name: "Sales by region" });
    await waitFor(() => expect(within(table).getAllByRole("row")).toHaveLength(2));
  });

  it.each(["edit", "preview"] as const)("never runs actions in %s mode", async (mode) => {
    renderCanvas(sampleDocument(), { mode });

    fireEvent.change(screen.getByRole("combobox", { name: "Region" }), { target: { value: "South" } });

    expect(actionsApi.execute).not.toHaveBeenCalled();
  });

  it.each([
    ["/reports", true],
    ["https://example.com/a", true],
    ["javascript:alert(1)", false],
    ["//evil.example", false],
    ["http://insecure.example", false],
    ["data:text/html,<script>1</script>", false],
    [42, false],
  ])("treats %s as a safe destination: %s", (destination, safe) => {
    expect(isSafeDestination(destination)).toBe(safe);
  });
});

describe("edit mode", () => {
  function renderEditor(props: Partial<WorkspaceCanvasProps> = {}) {
    const onSelect = vi.fn();
    const onOperations = vi.fn<(operations: Operation[]) => void>();
    renderCanvas(sampleDocument(), { mode: "edit", onSelect, onOperations, ...props });
    return { onSelect, onOperations };
  }

  it("selects the component that was clicked, by its stable id", async () => {
    const { onSelect } = renderEditor();

    await userEvent.click(screen.getByText("Monthly revenue"));

    expect(onSelect).toHaveBeenLastCalledWith("monthly_revenue_chart");
  });

  it("shows handles only for the selected component", () => {
    renderEditor({ selectedId: "regional_table" });

    const selected = document.querySelector('[data-component-id="regional_table"]')!;
    expect(selected).toHaveAttribute("data-selected", "true");
    expect(within(selected as HTMLElement).getByText("Table · regional_table")).toBeInTheDocument();
    expect(screen.getAllByRole("separator", { name: "Resize width" })).toHaveLength(1);
  });

  it("turns keyboard intent into the same operations the assistant would produce", () => {
    const { onOperations, onSelect } = renderEditor({ selectedId: "orders_metric" });
    const element = document.querySelector<HTMLElement>('[data-component-id="orders_metric"]')!;

    fireEvent.keyDown(element, { key: "ArrowRight", altKey: true });
    fireEvent.keyDown(element, { key: "Delete" });

    expect(onOperations.mock.calls).toEqual([
      [[{ type: "MOVE", target: "orders_metric", index: 2 }]],
      [[{ type: "DELETE", target: "orders_metric" }]],
    ]);
    expect(onSelect).toHaveBeenLastCalledWith("aov_metric");
  });

  it("does not offer editing affordances in view mode", () => {
    renderCanvas(sampleDocument(), { selectedId: "regional_table" });

    expect(screen.queryByRole("separator", { name: "Resize width" })).not.toBeInTheDocument();
    expect(document.querySelector("[data-selected]")).toBeNull();
  });
});
