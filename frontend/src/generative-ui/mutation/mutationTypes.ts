/**
 * The mutation language: every way a UI document can change.
 *
 * Mirrors app/domains/generative_ui/operations.py. Operations are data. They
 * are produced by the model (via the backend) or by direct manipulation in the
 * editor, validated here before being applied locally, and validated again by
 * the backend before anything is persisted.
 */
import { z } from "zod";

import {
  assetSchema,
  COLOR_ROLES,
  COMPONENT_DENSITIES,
  componentIdSchema,
  componentSchema,
  EFFECTS,
  EMPHASIS_LEVELS,
  entitySchema,
  GRID_COLUMNS,
  HEIGHT_PRESETS,
  NAVIGATION_STYLES,
  navigationItemSchema,
  scalarSchema,
  SURFACE_VARIANTS,
  themePatchSchema,
  VISUAL_PRIORITIES,
} from "../schema/validators";

export const OPERATION_TYPES = [
  "CREATE", "DELETE", "MOVE", "RESIZE", "STYLE", "UPDATE", "REORDER", "GROUP", "UNGROUP",
  "REPLACE", "SET_THEME", "SET_FRAMEWORK", "SET_DESIGN_SYSTEM",
  // application-level
  "SET_NAVIGATION", "UPDATE_APPLICATION", "ADD_ASSETS", "UPSERT_ENTITIES",
] as const; // prettier-ignore

const placement = {
  parent_id: componentIdSchema.optional(),
  before: componentIdSchema.optional(),
  after: componentIdSchema.optional(),
  index: z.number().int().min(0).optional(),
};

function singleAnchor(value: { before?: string; after?: string; index?: number }): boolean {
  return [value.before, value.after, value.index].filter((anchor) => anchor !== undefined).length <= 1;
}
const SINGLE_ANCHOR = { message: "Use at most one of 'before', 'after' and 'index'." };

const jsonValue: z.ZodType<unknown> = z.lazy(() =>
  z.union([scalarSchema, z.array(jsonValue), z.record(z.string(), jsonValue)]),
);

const createSchema = z
  .strictObject({ type: z.literal("CREATE"), component: componentSchema, ...placement })
  .refine(singleAnchor, SINGLE_ANCHOR);

const deleteSchema = z.strictObject({ type: z.literal("DELETE"), target: componentIdSchema });

const moveSchema = z
  .strictObject({ type: z.literal("MOVE"), target: componentIdSchema, ...placement })
  .refine(singleAnchor, SINGLE_ANCHOR);

const resizeSchema = z
  .strictObject({
    type: z.literal("RESIZE"),
    target: componentIdSchema,
    span: z.number().int().min(1).max(GRID_COLUMNS).optional(),
    height: z.enum(HEIGHT_PRESETS).optional(),
  })
  .refine((value) => value.span !== undefined || value.height !== undefined, {
    message: "RESIZE needs 'span' and/or 'height'.",
  });

const styleSchema = z.strictObject({
  type: z.literal("STYLE"),
  target: componentIdSchema,
  // `null` clears a token.
  style: z.strictObject({
    tone: z.enum(COLOR_ROLES).nullable().optional(),
    emphasis: z.enum(EMPHASIS_LEVELS).nullable().optional(),
    surface: z.enum(SURFACE_VARIANTS).nullable().optional(),
    priority: z.enum(VISUAL_PRIORITIES).nullable().optional(),
    density: z.enum(COMPONENT_DENSITIES).nullable().optional(),
    align: z.enum(["left", "center", "right"]).nullable().optional(),
    effects: z.array(z.enum(EFFECTS)).max(3).nullable().optional(),
  }),
});

const updateSchema = z.strictObject({
  type: z.literal("UPDATE"),
  target: componentIdSchema,
  // `null` removes an optional prop.
  props: z.record(z.string(), jsonValue).refine((props) => Object.keys(props).length > 0, {
    message: "UPDATE needs at least one prop.",
  }),
});

const reorderSchema = z.strictObject({
  type: z.literal("REORDER"),
  parent_id: componentIdSchema,
  order: z.array(componentIdSchema).min(1),
});

const groupSchema = z.strictObject({
  type: z.literal("GROUP"),
  targets: z.array(componentIdSchema).min(1),
  group: z.strictObject({
    id: componentIdSchema,
    type: z.enum(["section", "card"]).optional(),
    title: z.string().min(1).max(200).optional(),
  }),
});

const ungroupSchema = z.strictObject({ type: z.literal("UNGROUP"), target: componentIdSchema });

const replaceSchema = z.strictObject({
  type: z.literal("REPLACE"),
  target: componentIdSchema,
  component: componentSchema,
});

const setThemeSchema = z
  .strictObject({
    type: z.literal("SET_THEME"),
    preset: z.string().min(1).max(64).optional(),
    tokens: themePatchSchema.optional(),
  })
  .refine((value) => value.preset !== undefined || value.tokens !== undefined, {
    message: "SET_THEME needs 'preset' and/or 'tokens'.",
  });

const setFrameworkSchema = z.strictObject({
  type: z.literal("SET_FRAMEWORK"),
  framework: z.string().min(1).max(64),
});

const setDesignSystemSchema = z.strictObject({
  type: z.literal("SET_DESIGN_SYSTEM"),
  design_system: z.string().min(1).max(64),
  tokens: themePatchSchema.optional(),
});

/** Change the application shell. Omitted fields keep their value; `null` clears one. */
const setNavigationSchema = z
  .strictObject({
    type: z.literal("SET_NAVIGATION"),
    style: z.enum(NAVIGATION_STYLES).optional(),
    brand: z.string().min(1).max(200).nullable().optional(),
    tagline: z.string().min(1).max(200).nullable().optional(),
    home: componentIdSchema.optional(),
    items: z.array(navigationItemSchema).max(20).optional(),
    action: navigationItemSchema.nullable().optional(),
  })
  .refine((value) => Object.keys(value).length > 1, {
    message: "SET_NAVIGATION needs at least one field to change.",
  });

const updateApplicationSchema = z.strictObject({
  type: z.literal("UPDATE_APPLICATION"),
  props: z.record(z.string(), jsonValue).refine((props) => Object.keys(props).length > 0, {
    message: "UPDATE_APPLICATION needs at least one prop.",
  }),
});

const addAssetsSchema = z.strictObject({
  type: z.literal("ADD_ASSETS"),
  assets: z.array(assetSchema).min(1).max(20),
});

const upsertEntitiesSchema = z.strictObject({
  type: z.literal("UPSERT_ENTITIES"),
  entities: z.array(entitySchema).min(1).max(10),
});

export const operationSchema = z.union([
  createSchema,
  deleteSchema,
  moveSchema,
  resizeSchema,
  styleSchema,
  updateSchema,
  reorderSchema,
  groupSchema,
  ungroupSchema,
  replaceSchema,
  setThemeSchema,
  setFrameworkSchema,
  setDesignSystemSchema,
  setNavigationSchema,
  updateApplicationSchema,
  addAssetsSchema,
  upsertEntitiesSchema,
]);

export type Operation = z.infer<typeof operationSchema>;
export type OperationType = (typeof OPERATION_TYPES)[number];
export type OperationOf<T extends OperationType> = Extract<Operation, { type: T }>;
