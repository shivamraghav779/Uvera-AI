/** Contract fixtures exported by the backend (`npm run contract`). */
import raw from "@/generative-ui/schema/generated/contract-fixtures.json";
import type { Operation } from "@/generative-ui/mutation/mutationTypes";
import { parseDocument } from "@/generative-ui/schema/normalization";
import type { DataMap, Theme, ThemePatch, UIDocument } from "@/generative-ui/schema/types";
import type { ApplicationSummary } from "@/services/api/types";

export interface MutationCase {
  name: string;
  operations: Operation[];
  summaries: string[];
  expected: unknown;
}

export const fixtures = raw as unknown as {
  schema_version: string;
  sample_document: unknown;
  sample_data: DataMap;
  component_examples: Record<string, Record<string, unknown>>;
  operation_examples: Record<string, unknown>[];
  version_operation_examples: Record<string, unknown>[];
  allowed_actions: string[];
  theme_presets: { id: string; name: string; theme: Theme }[];
  default_theme: Theme;
  design_systems: { id: string; name: string; tokens: ThemePatch }[];
  frameworks: { id: string; name: string; status: "available" | "planned" }[];
  mutation_cases: MutationCase[];
  rejected_mutation_cases: { name: string; operations: Operation[]; stage: string }[];
  sample_application: unknown;
  sample_application_data: DataMap;
  application_summary: ApplicationSummary;
  application_mutation_cases: MutationCase[];
  rejected_application_mutation_cases: { name: string; operations: Operation[]; stage: string }[];
  application_operation_examples: Record<string, unknown>[];
  patterns: { id: string; component: string; variant: string | null }[];
  effects: string[];
  icons: string[];
  component_variants: Record<string, string[]>;
};

/** The scripted sample application ("Hirewell", a recruitment product). */
export function sampleApplication(): UIDocument {
  const parsed = parseDocument(fixtures.sample_application);
  if (!parsed.ok) throw new Error(`Sample application is invalid: ${JSON.stringify(parsed.issues)}`);
  return parsed.value;
}

export function sampleDocument(): UIDocument {
  const parsed = parseDocument(fixtures.sample_document);
  if (!parsed.ok) throw new Error(`Sample document is invalid: ${JSON.stringify(parsed.issues)}`);
  return parsed.value;
}

/** A minimal valid document around the given components. */
export function documentWith(...components: unknown[]): unknown {
  return {
    schema_version: fixtures.schema_version,
    page: { type: "page", id: "page", title: "Test", components },
    theme: fixtures.default_theme,
    design: { framework: "shadcn", design_system: "modern_minimal" },
  };
}
