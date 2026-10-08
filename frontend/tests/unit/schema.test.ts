import { parseDocument, stripNulls } from "@/generative-ui/schema/normalization";
import { allComponents, findLocation } from "@/generative-ui/schema/tree";
import { COMPONENT_TYPES, componentSchema, pageSchema } from "@/generative-ui/schema/validators";

import { documentWith, fixtures, sampleDocument } from "../fixtures";

describe("document schema", () => {
  it("accepts the backend's sample document unchanged", () => {
    const parsed = parseDocument(fixtures.sample_document);

    expect(parsed.ok).toBe(true);
    // The backend sends canonical JSON; parsing must not alter it.
    expect(parsed.ok && parsed.value).toEqual(fixtures.sample_document);
  });

  it("knows exactly the component types the backend registers", () => {
    expect([...COMPONENT_TYPES].sort()).toEqual(Object.keys(fixtures.component_examples).sort());
  });

  it.each(Object.entries(fixtures.component_examples))("accepts the backend example for %s", (type, example) => {
    const schema = type === "page" ? pageSchema : componentSchema;

    expect(schema.safeParse(example).success).toBe(true);
  });

  it("fills in defaults", () => {
    const parsed = parseDocument(documentWith({ type: "divider", id: "line" }));

    expect(parsed.ok && parsed.value.page.components[0]).toEqual({
      type: "divider",
      id: "line",
      layout: { span: 12, height: "auto" },
    });
  });

  it.each([
    ["unknown component", { type: "iframe", id: "frame", src: "https://evil.example" }],
    ["unknown field", { type: "text", id: "t", content: "hi", onClick: "alert(1)" }],
    ["raw html field", { type: "text", id: "t", content: "hi", dangerouslySetInnerHTML: { __html: "<b>x</b>" } }],
    ["css in style", { type: "text", id: "t", content: "hi", style: { css: "position:fixed" } }],
    ["colour in style", { type: "text", id: "t", content: "hi", style: { tone: "#ff0000" } }],
    ["pixel layout", { type: "divider", id: "d", layout: { x: 10, y: 20, width: 300 } }],
    ["span out of range", { type: "divider", id: "d", layout: { span: 13 } }],
    ["unknown action", { type: "button", id: "b", label: "Run", action: { type: "eval", payload: {} } }],
    ["nested page", { type: "page", id: "inner", title: "x", components: [] }],
    ["bad id", { type: "divider", id: "1 bad id" }],
    ["chart without series", { type: "chart", id: "c", chart_type: "bar", x_key: "a", y_keys: [] }],
  ])("rejects %s", (_name, component) => {
    expect(parseDocument(documentWith(component)).ok).toBe(false);
  });

  it.each([
    ["named colour", "red"],
    ["short hex", "#FFF"],
    ["css function", "rgb(0,0,0)"],
    ["css injection", "#000000; background: url(javascript:alert(1))"],
  ])("rejects a theme colour that is a %s", (_name, color) => {
    const document = documentWith({ type: "divider", id: "d" }) as { theme: { colors: Record<string, string> } };
    document.theme = { ...fixtures.default_theme, colors: { ...fixtures.default_theme.colors, primary: color } };

    const parsed = parseDocument(document);

    expect(parsed.ok).toBe(false);
    expect(!parsed.ok && parsed.issues[0]?.path).toBe("theme.colors.primary");
  });

  it("reports where a problem is", () => {
    const parsed = parseDocument(documentWith({ type: "metric", id: "m" }));

    expect(!parsed.ok && parsed.issues.map((issue) => issue.path)).toEqual(["page.components.0.title"]);
  });

  it("treats null members as absent", () => {
    expect(stripNulls({ a: null, b: [{ c: null, d: 1 }], e: { f: undefined, g: "x" } })).toEqual({
      b: [{ d: 1 }],
      e: { g: "x" },
    });
  });
});

describe("tree helpers", () => {
  it("lists every component with a stable id", () => {
    const ids = allComponents(sampleDocument().page).map((component) => component.id);

    expect(ids).toEqual([
      "revenue_metric", "orders_metric", "aov_metric", "top_region_metric",
      "monthly_revenue_chart", "product_share_chart", "region_filter", "regional_table",
    ]); // prettier-ignore
    expect(new Set(ids).size).toBe(ids.length);
  });

  it("locates a component by id, not by position", () => {
    const location = findLocation(sampleDocument().page, "regional_table");

    expect(location).toMatchObject({ slotId: "page", index: 7, ancestors: [] });
    expect(findLocation(sampleDocument().page, "missing")).toBeNull();
  });
});
