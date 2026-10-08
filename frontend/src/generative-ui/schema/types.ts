import type { z } from "zod";

import type { UIComponent } from "./validators";
import type {
  applicationSchema,
  assetSchema,
  dataBindingSchema,
  entitySchema,
  navigationItemSchema,
  navigationSchema,
  actionSpecSchema,
  COLOR_ROLES,
  COMPONENT_TYPES,
  dataMapSchema,
  dataRowSchema,
  designSchema,
  documentSchema,
  HEIGHT_PRESETS,
  layoutSchema,
  pageSchema,
  scalarSchema,
  styleSchema,
  themePatchSchema,
  themeSchema,
} from "./validators";

export type Scalar = z.infer<typeof scalarSchema>;
export type DataRow = z.infer<typeof dataRowSchema>;
export type DataMap = z.infer<typeof dataMapSchema>;

export type ComponentType = (typeof COMPONENT_TYPES)[number];
export type HeightPreset = (typeof HEIGHT_PRESETS)[number];
export type ColorRole = (typeof COLOR_ROLES)[number];

export type ActionSpec = z.infer<typeof actionSpecSchema>;
export type LayoutSpec = z.infer<typeof layoutSchema>;
export type ComponentStyle = z.infer<typeof styleSchema>;

export type {
  ScreenComponent,
  CardComponent,
  LeafComponent,
  ModalComponent,
  SectionComponent,
  TabDefinition,
  TabsComponent,
  UIComponent,
} from "./validators";
export type PageNode = z.infer<typeof pageSchema>;
/** Any node of the tree, root included. */
export type UINode = PageNode | UIComponent;

/** A component narrowed by its `type`, e.g. `ComponentOf<"chart">`. */
export type ComponentOf<T extends UIComponent["type"]> = Extract<UIComponent, { type: T }>;

export type Theme = z.infer<typeof themeSchema>;
export type ThemePatch = z.infer<typeof themePatchSchema>;
export type DesignConfig = z.infer<typeof designSchema>;
export type UIDocument = z.infer<typeof documentSchema>;
export type ApplicationSpec = z.infer<typeof applicationSchema>;
export type Navigation = z.infer<typeof navigationSchema>;
export type NavigationItem = z.infer<typeof navigationItemSchema>;
export type Entity = z.infer<typeof entitySchema>;
export type Asset = z.infer<typeof assetSchema>;
export type DataBinding = z.infer<typeof dataBindingSchema>;

export type ValidationStage = "json_parsing" | "schema" | "operation" | "registry" | "semantic";

export interface ValidationIssue {
  stage: ValidationStage;
  path: string;
  message: string;
}

export type ValidationResult<T> =
  | { ok: true; value: T }
  | { ok: false; issues: ValidationIssue[] };
