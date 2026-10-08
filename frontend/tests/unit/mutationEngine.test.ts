import { applyOperations, type MutationError } from "@/generative-ui/mutation/mutationEngine";
import { affectedComponentIds, describeOperation } from "@/generative-ui/mutation/mutationPreview";
import { OPERATION_TYPES, operationSchema, type Operation } from "@/generative-ui/mutation/mutationTypes";
import { applyValidated, parseOperations } from "@/generative-ui/mutation/mutationValidator";
import { parseDocument } from "@/generative-ui/schema/normalization";

import { fixtures, sampleApplication, sampleDocument } from "../fixtures";

const ENVIRONMENT = {
  frameworks: fixtures.frameworks.filter((f) => f.status === "available").map((f) => f.id),
  designSystems: fixtures.design_systems.map((system) => system.id),
};

describe("parity with the backend engine", () => {
  // Expected results were computed by the Python engine and exported with the fixtures.
  it.each(fixtures.mutation_cases)("$name", ({ operations, expected }) => {
    const result = applyValidated(sampleDocument(), operations, ENVIRONMENT);

    expect(result.ok && result.value).toEqual(expected);
  });

  it.each(fixtures.mutation_cases)("describes '$name' like the backend", ({ operations, summaries }) => {
    let document = sampleDocument();
    const described = operations.map((operation) => {
      const summary = describeOperation(operation, document);
      const next = parseDocument(applyOperations(document, [operation]));
      if (next.ok) document = next.value;
      return summary;
    });

    expect(described).toEqual(summaries);
  });

  it.each(fixtures.rejected_mutation_cases)("rejects: $name", ({ operations }) => {
    expect(applyValidated(sampleDocument(), operations, ENVIRONMENT).ok).toBe(false);
  });
});

describe("parity with the backend engine on an application", () => {
  it.each(fixtures.application_mutation_cases)("$name", ({ operations, expected }) => {
    const result = applyValidated(sampleApplication(), operations, ENVIRONMENT);

    expect(result.ok && result.value).toEqual(expected);
  });

  it.each(fixtures.application_mutation_cases)("describes '$name' like the backend", ({ operations, summaries }) => {
    let document = sampleApplication();
    const described = operations.map((operation) => {
      const summary = describeOperation(operation, document);
      const next = parseDocument(applyOperations(document, [operation]));
      if (next.ok) document = next.value;
      return summary;
    });

    expect(described).toEqual(summaries);
  });

  it.each(fixtures.rejected_application_mutation_cases)("rejects: $name", ({ operations }) => {
    expect(applyValidated(sampleApplication(), operations, ENVIRONMENT).ok).toBe(false);
  });
});

describe("operation contract", () => {
  it("knows exactly the operation types the backend documents", () => {
    const documented = [...fixtures.operation_examples, ...fixtures.application_operation_examples].map(
      (example) => example.type,
    );
    // The pipeline alone adds assets and entities; the model is never shown those two.
    const offered = OPERATION_TYPES.filter((type) => type !== "ADD_ASSETS" && type !== "UPSERT_ENTITIES");

    expect(documented).toEqual(offered);
  });

  it.each([...fixtures.operation_examples, ...fixtures.application_operation_examples])(
    "accepts the backend example for $type",
    (example) => {
      expect(operationSchema.safeParse(example).success).toBe(true);
    },
  );

  it.each(fixtures.version_operation_examples)("does not treat $type as a document operation", (example) => {
    expect(parseOperations([example]).ok).toBe(false);
  });

  it.each([
    ["unknown operation", { type: "EXECUTE", code: "fetch('/steal')" }],
    ["pixel move", { type: "MOVE", target: "revenue_metric", position: { x: 9, y: 0 } }],
    ["two anchors", { type: "MOVE", target: "a", before: "b", after: "c" }],
    ["empty resize", { type: "RESIZE", target: "revenue_metric" }],
    ["css style", { type: "STYLE", target: "revenue_metric", style: { css: "color:red" } }],
    ["css colour", { type: "SET_THEME", tokens: { colors: { primary: "blue" } } }],
    ["script component", { type: "CREATE", component: { type: "script", id: "x", src: "evil.js" } }],
    ["not an object", "DELETE revenue_metric"],
  ])("rejects %s before touching the document", (_name, operation) => {
    const result = parseOperations([operation]);

    expect(result.ok).toBe(false);
    expect(!result.ok && result.issues[0]?.path.startsWith("operations.0")).toBe(true);
  });
});

describe("engine behaviour", () => {
  it("never modifies its input", () => {
    const document = sampleDocument();
    const snapshot = structuredClone(document);

    applyOperations(document, [{ type: "DELETE", target: "product_share_chart" }]);

    expect(document).toEqual(snapshot);
  });

  it("reports which operation failed", () => {
    const operations: Operation[] = [
      { type: "RESIZE", target: "revenue_metric", span: 6 },
      { type: "DELETE", target: "ghost" },
    ];

    expect(() => applyOperations(sampleDocument(), operations)).toThrowError(
      expect.objectContaining({ index: 1, message: "Component 'ghost' does not exist." }) as MutationError,
    );
  });

  it("leaves the page untouched when only theme or framework change", () => {
    const before = sampleDocument();

    const after = applyOperations(before, [
      { type: "SET_THEME", tokens: { mode: "dark", colors: { background: "#000000", foreground: "#FFFFFF" } } },
      { type: "SET_FRAMEWORK", framework: "material" },
    ]);

    expect(after.page).toEqual(before.page);
    expect(after.design.framework).toBe("material");
    expect(after.theme.mode).toBe("dark");
  });

  it("rejects a result that is not a valid document", () => {
    const result = applyValidated(sampleDocument(), [
      { type: "UPDATE", target: "monthly_revenue_chart", props: { onClick: "alert(1)" } },
    ]);

    expect(result.ok).toBe(false);
    expect(!result.ok && result.issues[0]?.stage).toBe("schema");
  });

  it("rejects an unreadable theme and an unavailable framework", () => {
    const unreadable = applyValidated(sampleDocument(), [
      { type: "SET_THEME", tokens: { colors: { foreground: "#FFFFFF" } } },
    ]);
    const unavailable = applyValidated(
      sampleDocument(),
      [{ type: "SET_FRAMEWORK", framework: "mui" }],
      ENVIRONMENT,
    );

    expect(!unreadable.ok && unreadable.issues[0]?.path).toBe("theme.colors.foreground");
    expect(!unavailable.ok && unavailable.issues[0]?.path).toBe("design.framework");
  });

  it("lists the components an operation touches", () => {
    expect(affectedComponentIds({ type: "MOVE", target: "a", after: "b" })).toEqual(["a"]);
    expect(
      affectedComponentIds({ type: "GROUP", targets: ["a", "b"], group: { id: "g" } }),
    ).toEqual(["a", "b", "g"]);
  });
});
