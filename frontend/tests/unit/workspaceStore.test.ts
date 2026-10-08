import { HISTORY_LIMIT } from "@/generative-ui/history/editHistory";
import {
  designSystemOperation,
  frameworkOperation,
  themePresetOperation,
} from "@/generative-ui/registry/themeRegistry";
import { findComponent } from "@/generative-ui/schema/tree";
import type { FrameworkCatalog, ThemeCatalog } from "@/services/api/types";
import {
  selectCanRedo,
  selectCanUndo,
  selectDraft,
  selectIsDirty,
  selectPendingOperations,
  useWorkspaceStore,
} from "@/stores/workspaceStore";

import { documentWith, fixtures } from "../fixtures";

const store = () => useWorkspaceStore.getState();
const draft = () => selectDraft(store())!;
const version = (id: string, number: number, document: unknown = fixtures.sample_document) => ({
  id,
  version_number: number,
  document,
  data: fixtures.sample_data,
});

beforeEach(() => {
  useWorkspaceStore.setState({ workspaceId: null, base: null, history: null, preview: null, loadIssues: null });
  store().hydrate("w1", version("v1", 1));
});

describe("loading a version", () => {
  it("adopts a valid version as the base and working copy", () => {
    expect(store().base).toMatchObject({ id: "v1", number: 1 });
    expect(draft()).toEqual(fixtures.sample_document);
    expect(store().base!.data).toEqual(fixtures.sample_data);
    expect(selectIsDirty(store())).toBe(false);
  });

  it("refuses an invalid document and keeps the last good state on screen", () => {
    const bad = documentWith({ type: "iframe", id: "x", src: "https://evil.example" });

    const accepted = store().hydrate("w1", version("v2", 2, bad));

    expect(accepted).toBe(false);
    expect(store().base!.id).toBe("v1");
    expect(store().loadIssues?.[0]?.path).toBe("page.components.0.type");
  });

  it("tolerates malformed data rows without rejecting the document", () => {
    store().hydrate("w1", { ...version("v2", 2), data: "not a data map" });

    expect(store().base!.data).toEqual({});
  });

  it("starts clean when another workspace is opened", () => {
    store().applyOperations([{ type: "DELETE", target: "aov_metric" }]);

    store().open("w2");

    expect(store()).toMatchObject({ workspaceId: "w2", base: null, history: null, preview: null });
  });
});

describe("editing", () => {
  it("applies valid operations to the working copy only", () => {
    const result = store().applyOperations([{ type: "RESIZE", target: "regional_table", span: 6 }]);

    expect(result.ok).toBe(true);
    expect(findComponent(draft().page, "regional_table")?.layout.span).toBe(6);
    expect(findComponent(store().base!.document.page, "regional_table")?.layout.span).toBe(12);
    expect(selectPendingOperations(store())).toEqual([{ type: "RESIZE", target: "regional_table", span: 6 }]);
    expect(selectIsDirty(store())).toBe(true);
  });

  it.each([
    ["an unknown target", [{ type: "DELETE", target: "ghost" }]],
    ["an unknown operation", [{ type: "EXECUTE", code: "alert(1)" }]],
    ["a result that breaks the schema", [{ type: "UPDATE", target: "revenue_metric", props: { onClick: "x" } }]],
    ["a dangling action target", [{ type: "DELETE", target: "regional_table" }]],
    ["a partly valid batch", [{ type: "RESIZE", target: "aov_metric", span: 6 }, { type: "DELETE", target: "ghost" }]],
  ])("leaves the state untouched for %s", (_name, operations) => {
    const before = store().history;

    const result = store().applyOperations(operations as never);

    expect(result.ok).toBe(false);
    expect(store().history).toBe(before);
    expect(selectIsDirty(store())).toBe(false);
  });

  it("re-uses unchanged components by reference so only edited ones re-render", () => {
    const before = draft();

    store().applyOperations([{ type: "UPDATE", target: "orders_metric", props: { title: "Total orders" } }]);

    const after = draft();
    expect(after).not.toBe(before);
    expect(findComponent(after.page, "orders_metric")).not.toBe(findComponent(before.page, "orders_metric"));
    expect(findComponent(after.page, "monthly_revenue_chart")).toBe(findComponent(before.page, "monthly_revenue_chart"));
    expect(after.theme).toBe(before.theme);
  });

  it("keeps component references across a reorder", () => {
    const before = draft();

    store().applyOperations([{ type: "MOVE", target: "regional_table", index: 0 }]);

    expect(draft().page.components[0]).toBe(findComponent(before.page, "regional_table"));
  });

  it("undoes and redoes unsaved edits", () => {
    store().applyOperations([{ type: "RESIZE", target: "aov_metric", span: 6 }]);
    store().applyOperations([{ type: "DELETE", target: "product_share_chart" }]);
    expect(selectPendingOperations(store())).toHaveLength(2);

    store().undo();
    expect(findComponent(draft().page, "product_share_chart")).not.toBeNull();
    expect(selectPendingOperations(store())).toHaveLength(1);
    expect(selectCanRedo(store())).toBe(true);

    store().undo();
    expect(draft()).toEqual(fixtures.sample_document);
    expect(selectCanUndo(store())).toBe(false);
    expect(selectIsDirty(store())).toBe(false);

    store().redo();
    store().redo();
    expect(findComponent(draft().page, "product_share_chart")).toBeNull();
    expect(selectPendingOperations(store())).toHaveLength(2);
  });

  it("drops the redo branch when a new edit is made after undo", () => {
    store().applyOperations([{ type: "RESIZE", target: "aov_metric", span: 6 }]);
    store().undo();

    store().applyOperations([{ type: "RESIZE", target: "aov_metric", span: 4 }]);

    expect(selectCanRedo(store())).toBe(false);
    expect(selectPendingOperations(store())).toEqual([{ type: "RESIZE", target: "aov_metric", span: 4 }]);
  });

  it("bounds the undo history", () => {
    for (let index = 0; index < HISTORY_LIMIT + 20; index += 1) {
      store().applyOperations([{ type: "RESIZE", target: "aov_metric", span: (index % 12) + 1 }]);
    }

    expect(store().history!.past).toHaveLength(HISTORY_LIMIT);
  });

  it("discards unsaved edits back to the saved version", () => {
    store().applyOperations([{ type: "DELETE", target: "product_share_chart" }]);

    store().discard();

    expect(draft()).toBe(store().base!.document);
    expect(selectIsDirty(store())).toBe(false);
  });

  it("clears unsaved edits and previews when a new version is adopted", () => {
    store().applyOperations([{ type: "DELETE", target: "product_share_chart" }]);
    store().setPreview({ kind: "proposal", label: "x", document: draft(), data: {}, highlightIds: [] });

    store().hydrate("w1", version("v2", 2));

    expect(store().base!.number).toBe(2);
    expect(store().preview).toBeNull();
    expect(selectIsDirty(store())).toBe(false);
  });

  it("previewing never changes the working copy", () => {
    const before = draft();

    store().setPreview({ kind: "version", label: "Version 1", document: before, data: {}, highlightIds: [], versionId: "v0" });

    expect(draft()).toBe(before);
    expect(selectIsDirty(store())).toBe(false);
  });
});

describe("design choices become explicit operations", () => {
  const themes = { presets: fixtures.theme_presets, default_theme: fixtures.default_theme } as unknown as ThemeCatalog;
  const frameworks = { design_systems: fixtures.design_systems, frameworks: fixtures.frameworks } as unknown as FrameworkCatalog;
  const backendCase = (name: string) => fixtures.mutation_cases.find((item) => item.name === name)!;

  it("a theme picked in the editor produces what the backend produces for the same preset", () => {
    store().applyOperations([themePresetOperation(themes, "slate_dark")!]);

    expect(draft()).toEqual(backendCase("theme preset").expected);
  });

  it("framework and design system picked in the editor match the backend too", () => {
    store().applyOperations([frameworkOperation("material"), designSystemOperation(frameworks, "material")!]);

    expect(draft()).toEqual(backendCase("framework and design system").expected);
    expect(draft().page).toBe(store().base!.document.page);
  });

  it("returns nothing for unknown presets", () => {
    expect(themePresetOperation(themes, "neon")).toBeNull();
    expect(designSystemOperation(frameworks, "brutal")).toBeNull();
  });
});
