/**
 * Runtime schema of the UI document.
 *
 * This mirrors the backend's Pydantic models (app/domains/generative_ui). The
 * vocabulary is checked two ways so it cannot drift silently:
 *   - compile time: `contract.ts` asserts these types against the types
 *     generated from the backend's OpenAPI document;
 *   - test time: every fixture exported by the backend must parse here.
 *
 * Every object is strict: an unknown component type or an unknown field is a
 * validation error, so there is no place for markup, script or CSS to hide.
 */
import { z } from "zod";

export const SCHEMA_VERSION = "3.0";
export const GRID_COLUMNS = 12;
const MAX_CHILDREN = 50;
const MAX_DATA_ROWS = 500;
const MAX_ITEMS = 100;

// --- Primitives ----------------------------------------------------------------

export const componentIdSchema = z.string().regex(/^[A-Za-z][A-Za-z0-9_-]{0,63}$/);
const fieldKey = z.string().min(1).max(64);
const shortText = z.string().min(1).max(200);
const mediumText = z.string().min(1).max(600);
const longText = z.string().min(1).max(4000);
/** Id of an entry in the application's asset list. Never a URL. */
export const assetIdSchema = z.string().regex(/^[A-Za-z][A-Za-z0-9_-]{0,63}$/);
const iconName = z.string().regex(/^[a-z][a-z0-9-]{0,39}$/);
export const routePathSchema = z
  .string()
  .max(120)
  .regex(/^\/(?:[A-Za-z0-9_-]+|:[A-Za-z][A-Za-z0-9_]*)?(?:\/(?:[A-Za-z0-9_-]+|:[A-Za-z][A-Za-z0-9_]*))*$/);
export const scalarSchema = z.union([z.string(), z.number(), z.boolean(), z.null()]);
export const dataRowSchema = z.record(z.string(), scalarSchema);

export const COMPONENT_TYPES = [
  "page", "section", "card", "metric", "text", "table", "chart", "form", "input", "select",
  "checkbox", "button", "badge", "alert", "list", "timeline", "progress", "tabs", "divider",
  "modal",
  // application structure and patterns
  "screen", "hero", "feature_grid", "logo_cloud", "testimonials", "pricing", "cta", "stats",
  "gallery", "collection", "kanban", "detail", "profile_header", "image", "media", "steps",
  "faq", "footer", "calendar", "comparison", "command",
] as const; // prettier-ignore
export const HEIGHT_PRESETS = ["auto", "sm", "md", "lg", "xl"] as const;
export const COLOR_ROLES = [
  "primary", "secondary", "success", "warning", "destructive", "neutral",
] as const; // prettier-ignore
export const EMPHASIS_LEVELS = ["subtle", "default", "strong"] as const;
export const CHART_TYPES = ["bar", "line", "area", "pie", "donut", "scatter"] as const;
export const ACTION_TYPES = [
  "filter", "sort", "refresh", "navigate", "submit", "search", "generate", "export",
  "record_create", "record_update", "record_delete",
] as const; // prettier-ignore
export const BUTTON_VARIANTS = [
  "primary", "secondary", "danger", "ghost", "outline", "gradient", "glass",
] as const; // prettier-ignore
export const SURFACE_VARIANTS = [
  "flat", "bordered", "elevated", "glass", "minimal", "featured", "interactive",
] as const; // prettier-ignore
export const VISUAL_PRIORITIES = ["primary", "secondary", "tertiary"] as const;
export const COMPONENT_DENSITIES = ["compact", "comfortable", "spacious"] as const;
export const EFFECTS = [
  "gradient_mesh", "animated_gradient", "glow", "glass", "noise", "grid", "spotlight", "reveal",
  "hover_lift", "parallax", "marquee", "counter",
] as const; // prettier-ignore
export const SCREEN_TYPES = [
  "landing", "dashboard", "listing", "detail", "form", "settings", "analytics", "profile",
  "calendar", "onboarding", "authentication", "pricing", "content", "custom",
] as const; // prettier-ignore
export const SCREEN_WIDTHS = ["narrow", "contained", "wide", "full"] as const;
export const SECTION_VARIANTS = [
  "default", "split", "immersive", "full_bleed", "editorial", "band",
] as const; // prettier-ignore
const ALIGNMENTS = ["left", "center", "right"] as const;
const CONDITION_OPERATORS = [
  "equals", "not_equals", "in", "not_in", "gt", "lt", "is_set", "is_empty",
] as const; // prettier-ignore
const TONES = ["neutral", "info", "success", "warning", "danger"] as const;
const COLUMN_FORMATS = ["text", "number", "currency", "percent", "date"] as const;
const AGGREGATES = ["sum", "avg", "min", "max", "count", "first"] as const;

// --- Building blocks -------------------------------------------------------------

export const actionSpecSchema = z.strictObject({
  type: z.enum(ACTION_TYPES),
  payload: z.record(z.string(), z.union([scalarSchema, z.array(scalarSchema)])).default({}),
});

const visibilitySchema = z.strictObject({
  field: fieldKey,
  operator: z.enum(CONDITION_OPERATORS).default("equals"),
  value: z.union([scalarSchema, z.array(scalarSchema)]).optional(),
});

/** Keep rows whose field matches a fixed value or a parameter of the screen's route. */
const rowConditionSchema = z
  .strictObject({
    field: fieldKey,
    operator: z.enum(CONDITION_OPERATORS).default("equals"),
    value: z.union([scalarSchema, z.array(scalarSchema)]).optional(),
    param: fieldKey.optional(),
  })
  .refine((condition) => condition.param === undefined || condition.value === undefined, {
    message: "Use either 'value' or 'param', not both.",
  });

export const dataBindingSchema = z
  .strictObject({
    dataset: fieldKey,
    limit: z.number().int().min(1).max(MAX_DATA_ROWS).optional(),
    where: z.array(rowConditionSchema).max(4).optional(),
    sort: z
      .strictObject({ field: fieldKey, direction: z.enum(["asc", "desc"]).default("asc") })
      .optional(),
    group_by: fieldKey.optional(),
    aggregate: z.enum(AGGREGATES).optional(),
    field: fieldKey.optional(),
  })
  .refine(
    (binding) =>
      binding.group_by !== undefined || (binding.aggregate === undefined && binding.field === undefined),
    { message: "'aggregate' and 'field' need 'group_by'." },
  );

const metricBindingSchema = z.strictObject({
  dataset: fieldKey,
  field: fieldKey,
  aggregate: z.enum(AGGREGATES).default("sum"),
  where: z.array(rowConditionSchema).max(4).optional(),
});

export const layoutSchema = z.strictObject({
  span: z.number().int().min(1).max(GRID_COLUMNS).default(GRID_COLUMNS),
  height: z.enum(HEIGHT_PRESETS).default("auto"),
});

export const styleSchema = z.strictObject({
  tone: z.enum(COLOR_ROLES).optional(),
  emphasis: z.enum(EMPHASIS_LEVELS).optional(),
  surface: z.enum(SURFACE_VARIANTS).optional(),
  priority: z.enum(VISUAL_PRIORITIES).optional(),
  density: z.enum(COMPONENT_DENSITIES).optional(),
  align: z.enum(ALIGNMENTS).optional(),
  effects: z.array(z.enum(EFFECTS)).max(3).optional(),
});

const base = {
  id: componentIdSchema,
  layout: layoutSchema.default({ span: GRID_COLUMNS, height: "auto" }),
  style: styleSchema.optional(),
  visible_when: visibilitySchema.optional(),
  metadata: z.record(z.string(), scalarSchema).optional(),
};

// --- Leaf components -------------------------------------------------------------

const metricSchema = z.strictObject({
  type: z.literal("metric"),
  ...base,
  title: shortText,
  value: z.union([z.string(), z.number()]).optional(),
  data_source: metricBindingSchema.optional(),
  format: z.enum(COLUMN_FORMATS).default("text"),
  unit: shortText.optional(),
  trend: z
    .strictObject({
      direction: z.enum(["up", "down", "flat"]),
      value: shortText,
      label: shortText.optional(),
    })
    .optional(),
  description: shortText.optional(),
});

const textSchema = z.strictObject({
  type: z.literal("text"),
  ...base,
  content: longText,
  variant: z.enum(["heading", "subheading", "body", "caption"]).default("body"),
});

const tableSchema = z.strictObject({
  type: z.literal("table"),
  ...base,
  title: shortText.optional(),
  columns: z
    .array(
      z.strictObject({
        key: fieldKey,
        label: shortText,
        format: z.enum(COLUMN_FORMATS).default("text"),
        align: z.enum(ALIGNMENTS).default("left"),
      }),
    )
    .min(1)
    .max(20),
  rows: z.array(dataRowSchema).max(MAX_DATA_ROWS).default([]),
  data_source: dataBindingSchema.optional(),
  page_size: z.number().int().min(1).max(100).optional(),
  row_action: actionSpecSchema.optional(),
});

const chartSchema = z.strictObject({
  type: z.literal("chart"),
  ...base,
  title: shortText.optional(),
  chart_type: z.enum(CHART_TYPES),
  x_key: fieldKey,
  y_keys: z.array(fieldKey).min(1).max(8),
  data: z.array(dataRowSchema).max(MAX_DATA_ROWS).default([]),
  data_source: dataBindingSchema.optional(),
});

const inputSchema = z.strictObject({
  type: z.literal("input"),
  ...base,
  name: fieldKey,
  label: shortText,
  input_type: z.enum(["text", "number", "email", "date", "search", "textarea"]).default("text"),
  placeholder: shortText.optional(),
  default_value: z.union([z.string(), z.number()]).optional(),
  required: z.boolean().default(false),
  on_change: actionSpecSchema.optional(),
});

const selectSchema = z.strictObject({
  type: z.literal("select"),
  ...base,
  name: fieldKey,
  label: shortText,
  options: z
    .array(z.strictObject({ label: shortText, value: shortText }))
    .min(1)
    .max(MAX_ITEMS),
  default_value: shortText.optional(),
  multiple: z.boolean().default(false),
  required: z.boolean().default(false),
  on_change: actionSpecSchema.optional(),
});

const checkboxSchema = z.strictObject({
  type: z.literal("checkbox"),
  ...base,
  name: fieldKey,
  label: shortText,
  checked: z.boolean().default(false),
  on_change: actionSpecSchema.optional(),
});

const buttonSchema = z.strictObject({
  type: z.literal("button"),
  ...base,
  label: shortText,
  action: actionSpecSchema,
  variant: z.enum(BUTTON_VARIANTS).default("primary"),
  disabled: z.boolean().default(false),
});

const badgeSchema = z.strictObject({
  type: z.literal("badge"),
  ...base,
  label: shortText,
  tone: z.enum(TONES).default("neutral"),
});

const alertSchema = z.strictObject({
  type: z.literal("alert"),
  ...base,
  title: shortText.optional(),
  message: longText,
  tone: z.enum(TONES).default("info"),
});

const listSchema = z.strictObject({
  type: z.literal("list"),
  ...base,
  title: shortText.optional(),
  items: z
    .array(
      z.strictObject({
        title: shortText,
        description: longText.optional(),
        badge: shortText.optional(),
      }),
    )
    .min(1)
    .max(MAX_ITEMS),
  ordered: z.boolean().default(false),
});

const timelineSchema = z.strictObject({
  type: z.literal("timeline"),
  ...base,
  title: shortText.optional(),
  items: z
    .array(
      z.strictObject({
        title: shortText,
        description: longText.optional(),
        timestamp: shortText.optional(),
        status: z.enum(["completed", "current", "upcoming"]).optional(),
      }),
    )
    .min(1)
    .max(MAX_ITEMS),
});

const progressSchema = z.strictObject({
  type: z.literal("progress"),
  ...base,
  label: shortText,
  value: z.number().min(0),
  max: z.number().positive().default(100),
  tone: z.enum(TONES).default("info"),
});

const dividerSchema = z.strictObject({
  type: z.literal("divider"),
  ...base,
  label: shortText.optional(),
});

const formFieldSchema = z.discriminatedUnion("type", [inputSchema, selectSchema, checkboxSchema]);

const formSchema = z.strictObject({
  type: z.literal("form"),
  ...base,
  title: shortText.optional(),
  fields: z.array(formFieldSchema).min(1).max(MAX_CHILDREN),
  submit_action: actionSpecSchema,
  submit_label: shortText.default("Submit"),
});

// --- Patterns ----------------------------------------------------------------------
//
// A pattern is a designed composition described by content, a variant and
// optional bindings. How it looks belongs to the pattern registry and the theme.

const actionButtonSchema = z.strictObject({
  label: shortText,
  action: actionSpecSchema,
  variant: z.enum(BUTTON_VARIANTS).default("primary"),
  icon: iconName.optional(),
});
const labelValueSchema = z.strictObject({ label: shortText, value: shortText });
const fieldDisplaySchema = z.strictObject({
  key: fieldKey,
  label: shortText,
  format: z.enum(COLUMN_FORMATS).default("text"),
});
const trendSchema = z.strictObject({
  direction: z.enum(["up", "down", "flat"]),
  value: shortText,
  label: shortText.optional(),
});
/** Which fields of a record a card shows. Every value names a field. */
const recordCardFieldsSchema = z.strictObject({
  title: fieldKey,
  subtitle: fieldKey.optional(),
  description: fieldKey.optional(),
  image: fieldKey.optional(),
  badge: fieldKey.optional(),
  timestamp: fieldKey.optional(),
  avatar: z.boolean().default(false),
  meta: z.array(fieldDisplaySchema).max(5).default([]),
});

const heroSchema = z.strictObject({
  type: z.literal("hero"),
  ...base,
  variant: z.enum(["split", "centered", "immersive", "editorial", "product"]).default("split"),
  eyebrow: shortText.optional(),
  title: shortText,
  subtitle: mediumText.optional(),
  actions: z.array(actionButtonSchema).max(3).default([]),
  image: assetIdSchema.optional(),
  stats: z.array(labelValueSchema).max(4).default([]),
  badges: z.array(shortText).max(5).default([]),
});

const featureGridSchema = z.strictObject({
  type: z.literal("feature_grid"),
  ...base,
  variant: z.enum(["grid", "bento", "list", "alternating"]).default("grid"),
  eyebrow: shortText.optional(),
  title: shortText.optional(),
  subtitle: mediumText.optional(),
  columns: z.number().int().min(2).max(4).default(3),
  items: z
    .array(
      z.strictObject({
        title: shortText,
        description: mediumText.optional(),
        icon: iconName.optional(),
        image: assetIdSchema.optional(),
        badge: shortText.optional(),
        span: z.number().int().min(1).max(2).default(1),
      }),
    )
    .min(1)
    .max(12),
});

const logoCloudSchema = z.strictObject({
  type: z.literal("logo_cloud"),
  ...base,
  variant: z.enum(["static", "marquee"]).default("static"),
  title: shortText.optional(),
  logos: z.array(shortText).min(2).max(14),
});

const testimonialsSchema = z.strictObject({
  type: z.literal("testimonials"),
  ...base,
  variant: z.enum(["cards", "spotlight", "marquee"]).default("cards"),
  eyebrow: shortText.optional(),
  title: shortText.optional(),
  items: z
    .array(
      z.strictObject({
        quote: mediumText,
        author: shortText,
        role: shortText.optional(),
        company: shortText.optional(),
        avatar: assetIdSchema.optional(),
        rating: z.number().int().min(1).max(5).optional(),
      }),
    )
    .min(1)
    .max(9),
});

const pricingSchema = z.strictObject({
  type: z.literal("pricing"),
  ...base,
  eyebrow: shortText.optional(),
  title: shortText.optional(),
  subtitle: mediumText.optional(),
  plans: z
    .array(
      z.strictObject({
        name: shortText,
        price: shortText,
        period: shortText.optional(),
        description: shortText.optional(),
        features: z.array(shortText).max(12).default([]),
        action: actionButtonSchema.optional(),
        highlighted: z.boolean().default(false),
        badge: shortText.optional(),
      }),
    )
    .min(1)
    .max(4),
});

const ctaSchema = z.strictObject({
  type: z.literal("cta"),
  ...base,
  variant: z.enum(["banner", "centered", "split"]).default("centered"),
  eyebrow: shortText.optional(),
  title: shortText,
  subtitle: mediumText.optional(),
  actions: z.array(actionButtonSchema).min(1).max(2),
  image: assetIdSchema.optional(),
});

const statsSchema = z.strictObject({
  type: z.literal("stats"),
  ...base,
  variant: z.enum(["strip", "cards", "inline"]).default("strip"),
  title: shortText.optional(),
  items: z
    .array(
      z.strictObject({
        label: shortText,
        value: z.union([z.string(), z.number()]).optional(),
        data_source: metricBindingSchema.optional(),
        format: z.enum(COLUMN_FORMATS).default("text"),
        unit: shortText.optional(),
        trend: trendSchema.optional(),
        icon: iconName.optional(),
        description: shortText.optional(),
      }),
    )
    .min(1)
    .max(8),
});

const gallerySchema = z.strictObject({
  type: z.literal("gallery"),
  ...base,
  variant: z.enum(["grid", "masonry", "editorial", "carousel"]).default("grid"),
  eyebrow: shortText.optional(),
  title: shortText.optional(),
  subtitle: mediumText.optional(),
  columns: z.number().int().min(1).max(4).default(3),
  items: z
    .array(
      z.strictObject({
        title: shortText,
        subtitle: shortText.optional(),
        description: mediumText.optional(),
        image: assetIdSchema.optional(),
        badge: shortText.optional(),
        meta: z.array(labelValueSchema).max(4).default([]),
        action: actionSpecSchema.optional(),
      }),
    )
    .min(1)
    .max(24),
});

const collectionSchema = z.strictObject({
  type: z.literal("collection"),
  ...base,
  variant: z.enum(["cards", "list", "compact", "media", "feed"]).default("cards"),
  title: shortText.optional(),
  subtitle: shortText.optional(),
  data_source: dataBindingSchema,
  fields: recordCardFieldsSchema,
  columns: z.number().int().min(1).max(4).default(3),
  item_action: actionSpecSchema.optional(),
  empty_text: shortText.optional(),
});

const kanbanSchema = z.strictObject({
  type: z.literal("kanban"),
  ...base,
  title: shortText.optional(),
  data_source: dataBindingSchema,
  group_by: fieldKey,
  columns: z
    .array(z.strictObject({ value: shortText, label: shortText, tone: z.enum(TONES).default("neutral") }))
    .min(2)
    .max(8),
  fields: recordCardFieldsSchema,
  item_action: actionSpecSchema.optional(),
  move_action: actionSpecSchema.optional(),
});

const detailSchema = z.strictObject({
  type: z.literal("detail"),
  ...base,
  variant: z.enum(["list", "grid"]).default("grid"),
  title: shortText.optional(),
  data_source: dataBindingSchema,
  fields: z.array(fieldDisplaySchema).min(1).max(24),
  columns: z.number().int().min(1).max(3).default(2),
});

const profileHeaderSchema = z.strictObject({
  type: z.literal("profile_header"),
  ...base,
  variant: z.enum(["banner", "compact"]).default("banner"),
  data_source: dataBindingSchema,
  fields: recordCardFieldsSchema,
  actions: z.array(actionButtonSchema).max(4).default([]),
});

const imageSchema = z.strictObject({
  type: z.literal("image"),
  ...base,
  image: assetIdSchema,
  caption: shortText.optional(),
  aspect: z.enum(["auto", "square", "video", "wide", "ultrawide", "portrait"]).default("auto"),
  fit: z.enum(["cover", "contain"]).default("cover"),
  rounded: z.boolean().default(true),
});

const mediaSchema = z.strictObject({
  type: z.literal("media"),
  ...base,
  variant: z.enum(["image_left", "image_right", "overlay", "framed"]).default("image_right"),
  eyebrow: shortText.optional(),
  title: shortText,
  body: longText.optional(),
  bullets: z.array(shortText).max(6).default([]),
  image: assetIdSchema.optional(),
  actions: z.array(actionButtonSchema).max(2).default([]),
});

const stepsSchema = z.strictObject({
  type: z.literal("steps"),
  ...base,
  variant: z.enum(["numbered", "cards", "timeline"]).default("numbered"),
  eyebrow: shortText.optional(),
  title: shortText.optional(),
  items: z
    .array(z.strictObject({ title: shortText, description: mediumText.optional(), icon: iconName.optional() }))
    .min(2)
    .max(8),
});

const faqSchema = z.strictObject({
  type: z.literal("faq"),
  ...base,
  title: shortText.optional(),
  items: z.array(z.strictObject({ question: shortText, answer: longText })).min(1).max(12),
});

const footerSchema = z.strictObject({
  type: z.literal("footer"),
  ...base,
  brand: shortText.optional(),
  tagline: shortText.optional(),
  columns: z
    .array(
      z.strictObject({
        title: shortText,
        links: z
          .array(z.strictObject({ label: shortText, action: actionSpecSchema.optional() }))
          .min(1)
          .max(8),
      }),
    )
    .max(5)
    .default([]),
  note: shortText.optional(),
});

const calendarSchema = z.strictObject({
  type: z.literal("calendar"),
  ...base,
  title: shortText.optional(),
  data_source: dataBindingSchema,
  date_field: fieldKey,
  time_field: fieldKey.optional(),
  title_field: fieldKey,
  subtitle_field: fieldKey.optional(),
  badge_field: fieldKey.optional(),
  item_action: actionSpecSchema.optional(),
});

const comparisonSchema = z.strictObject({
  type: z.literal("comparison"),
  ...base,
  title: shortText.optional(),
  columns: z.array(shortText).min(2).max(5),
  rows: z
    .array(
      z.strictObject({
        label: shortText,
        values: z.array(z.union([shortText, z.boolean()])).min(1).max(5),
      }),
    )
    .min(1)
    .max(24),
  highlight_column: z.number().int().min(0).max(4).optional(),
});

const commandSchema = z.strictObject({
  type: z.literal("command"),
  ...base,
  placeholder: shortText.default("Search or jump to…"),
  items: z
    .array(
      z.strictObject({
        label: shortText,
        hint: shortText.optional(),
        icon: iconName.optional(),
        action: actionSpecSchema,
      }),
    )
    .min(1)
    .max(12),
});

// --- Containers (recursive) ------------------------------------------------------
//
// TypeScript cannot infer a type that refers to itself through a union, so the
// container types are written out and the schemas are checked against them.

const leafSchema = z.discriminatedUnion("type", [
  metricSchema,
  textSchema,
  tableSchema,
  chartSchema,
  formSchema,
  inputSchema,
  selectSchema,
  checkboxSchema,
  buttonSchema,
  badgeSchema,
  alertSchema,
  listSchema,
  timelineSchema,
  progressSchema,
  dividerSchema,
  heroSchema,
  featureGridSchema,
  logoCloudSchema,
  testimonialsSchema,
  pricingSchema,
  ctaSchema,
  statsSchema,
  gallerySchema,
  collectionSchema,
  kanbanSchema,
  detailSchema,
  profileHeaderSchema,
  imageSchema,
  mediaSchema,
  stepsSchema,
  faqSchema,
  footerSchema,
  calendarSchema,
  comparisonSchema,
  commandSchema,
]);

type BaseFields = z.infer<z.ZodObject<typeof base>>;
export type LeafComponent = z.infer<typeof leafSchema>;

export interface SectionComponent extends BaseFields {
  type: "section";
  variant: (typeof SECTION_VARIANTS)[number];
  eyebrow?: string;
  title?: string;
  description?: string;
  /** Backdrop asset for immersive sections. */
  image?: string;
  children: UIComponent[];
}

/** One routed screen of an application. Only valid directly under the page. */
export interface ScreenComponent extends BaseFields {
  type: "screen";
  title: string;
  route: string;
  screen_type: (typeof SCREEN_TYPES)[number];
  purpose?: string;
  width: (typeof SCREEN_WIDTHS)[number];
  show_title: boolean;
  children: UIComponent[];
}

export interface CardComponent extends BaseFields {
  type: "card";
  title?: string;
  subtitle?: string;
  children: UIComponent[];
}

export interface ModalComponent extends BaseFields {
  type: "modal";
  title: string;
  trigger_label: string;
  children: UIComponent[];
}

export interface TabDefinition {
  id: string;
  label: string;
  children: UIComponent[];
}

export interface TabsComponent extends BaseFields {
  type: "tabs";
  tabs: TabDefinition[];
  default_tab?: string;
}

/** Any component that can appear inside a page. A page itself can never be nested. */
export type UIComponent =
  | LeafComponent
  | ScreenComponent
  | SectionComponent
  | CardComponent
  | ModalComponent
  | TabsComponent;

const children = z.lazy(() => z.array(componentSchema).min(1).max(MAX_CHILDREN));

const sectionSchema = z.strictObject({
  type: z.literal("section"),
  ...base,
  variant: z.enum(SECTION_VARIANTS).default("default"),
  eyebrow: shortText.optional(),
  title: shortText.optional(),
  description: mediumText.optional(),
  image: assetIdSchema.optional(),
  children,
});

const screenSchema = z.strictObject({
  type: z.literal("screen"),
  ...base,
  title: shortText,
  route: routePathSchema,
  screen_type: z.enum(SCREEN_TYPES).default("custom"),
  purpose: shortText.optional(),
  width: z.enum(SCREEN_WIDTHS).default("contained"),
  show_title: z.boolean().default(true),
  children,
});

const cardSchema = z.strictObject({
  type: z.literal("card"),
  ...base,
  title: shortText.optional(),
  subtitle: shortText.optional(),
  children,
});

const modalSchema = z.strictObject({
  type: z.literal("modal"),
  ...base,
  title: shortText,
  trigger_label: shortText,
  children,
});

const tabsSchema = z.strictObject({
  type: z.literal("tabs"),
  ...base,
  tabs: z
    .array(z.strictObject({ id: componentIdSchema, label: shortText, children }))
    .min(1)
    .max(10),
  default_tab: componentIdSchema.optional(),
});

export const componentSchema: z.ZodType<UIComponent> = z.lazy(() =>
  z.discriminatedUnion("type", [
    ...leafSchema.options,
    screenSchema,
    sectionSchema,
    cardSchema,
    modalSchema,
    tabsSchema,
  ]),
);

export const pageSchema = z.strictObject({
  type: z.literal("page"),
  id: componentIdSchema.default("page"),
  title: shortText,
  description: shortText.optional(),
  components: z.array(componentSchema).min(1).max(MAX_CHILDREN),
  metadata: z.record(z.string(), scalarSchema).optional(),
});

// --- Theme and design ------------------------------------------------------------

/** Six-digit hex only: a colour token can never carry CSS. */
export const hexColorSchema = z.string().regex(/^#[0-9A-Fa-f]{6}$/);

export const THEME_COLOR_KEYS = [
  "primary", "secondary", "background", "surface", "foreground", "muted", "border",
  "destructive", "success", "warning",
] as const; // prettier-ignore

const themeColorsShape = Object.fromEntries(
  THEME_COLOR_KEYS.map((key) => [key, hexColorSchema]),
) as Record<(typeof THEME_COLOR_KEYS)[number], typeof hexColorSchema>;
/** Second accent for gradients and highlights; derived from the primary when absent. */
const themeColorsSchema = z.strictObject({ ...themeColorsShape, accent: hexColorSchema.optional() });

export const RADII = ["none", "sm", "md", "lg", "full"] as const;
export const DENSITIES = ["compact", "comfortable", "spacious"] as const;
export const SPACINGS = ["tight", "normal", "relaxed"] as const;
export const SHADOWS = ["none", "subtle", "medium"] as const;
export const FONTS = ["sans", "serif", "mono", "rounded", "grotesk", "geometric"] as const;
export const TYPE_SCALES = ["sm", "md", "lg"] as const;
export const HEADING_SCALES = ["sm", "md", "lg", "xl"] as const;
export const HEADING_WEIGHTS = ["regular", "medium", "semibold", "bold", "black"] as const;
export const SURFACE_STYLES = ["flat", "bordered", "elevated", "glass", "brutal"] as const;
export const MOTION_LEVELS = ["none", "subtle", "expressive"] as const;
export const GRADIENT_LEVELS = ["none", "subtle", "vivid"] as const;

const typographySchema = z.strictObject({
  font: z.enum(FONTS).default("sans"),
  scale: z.enum(TYPE_SCALES).default("md"),
  heading_font: z.enum(FONTS).optional(),
  heading_scale: z.enum(HEADING_SCALES).default("md"),
  heading_weight: z.enum(HEADING_WEIGHTS).default("semibold"),
});
const DEFAULT_TYPOGRAPHY = {
  font: "sans",
  scale: "md",
  heading_scale: "md",
  heading_weight: "semibold",
} as const;

export const themeSchema = z.strictObject({
  preset: fieldKey.optional(),
  mode: z.enum(["light", "dark"]),
  colors: themeColorsSchema,
  radius: z.enum(RADII).default("md"),
  density: z.enum(DENSITIES).default("comfortable"),
  spacing: z.enum(SPACINGS).default("normal"),
  shadows: z.enum(SHADOWS).default("subtle"),
  typography: typographySchema.default(DEFAULT_TYPOGRAPHY),
  surface: z.enum(SURFACE_STYLES).default("bordered"),
  motion: z.enum(MOTION_LEVELS).default("subtle"),
  gradient: z.enum(GRADIENT_LEVELS).default("none"),
});

export const themePatchSchema = z.strictObject({
  mode: z.enum(["light", "dark"]).optional(),
  // `accent: null` is how a palette without a second accent is written; it changes nothing.
  colors: themeColorsSchema.partial().extend({ accent: hexColorSchema.nullish() }).optional(),
  radius: z.enum(RADII).optional(),
  density: z.enum(DENSITIES).optional(),
  spacing: z.enum(SPACINGS).optional(),
  shadows: z.enum(SHADOWS).optional(),
  typography: z
    .strictObject({
      font: z.enum(FONTS).optional(),
      scale: z.enum(TYPE_SCALES).optional(),
      heading_font: z.enum(FONTS).optional(),
      heading_scale: z.enum(HEADING_SCALES).optional(),
      heading_weight: z.enum(HEADING_WEIGHTS).optional(),
    })
    .optional(),
  surface: z.enum(SURFACE_STYLES).optional(),
  motion: z.enum(MOTION_LEVELS).optional(),
  gradient: z.enum(GRADIENT_LEVELS).optional(),
});

export const designSchema = z.strictObject({
  framework: fieldKey,
  design_system: fieldKey,
});

// --- Application -------------------------------------------------------------------
//
// The product around the screens: navigation, data entities with sample records,
// assets, interactions and the design direction. Absent for a single view.

export const NAVIGATION_STYLES = ["sidebar", "topbar", "bottom", "minimal", "none"] as const;
export const ENTITY_FIELD_TYPES = [
  "text", "long_text", "number", "currency", "percent", "date", "time", "boolean", "status",
  "email", "image", "reference",
] as const; // prettier-ignore
const entityName = z.string().regex(/^[a-z][a-z0-9_]{0,63}$/);

export const navigationItemSchema = z.strictObject({
  screen_id: componentIdSchema,
  label: shortText,
  icon: iconName.optional(),
  group: shortText.optional(),
});

export const navigationSchema = z.strictObject({
  style: z.enum(NAVIGATION_STYLES).default("sidebar"),
  brand: shortText.optional(),
  tagline: shortText.optional(),
  home: componentIdSchema,
  items: z.array(navigationItemSchema).max(20).default([]),
  action: navigationItemSchema.optional(),
});

export const entitySchema = z.strictObject({
  name: entityName,
  label: shortText,
  description: shortText.optional(),
  title_field: fieldKey,
  fields: z
    .array(
      z.strictObject({
        key: fieldKey,
        label: shortText,
        type: z.enum(ENTITY_FIELD_TYPES).default("text"),
        options: z.array(shortText).max(12).default([]),
        references: entityName.optional(),
      }),
    )
    .min(1)
    .max(24),
  records: z.array(dataRowSchema).max(60).default([]),
});

/** Assets are served by this application only; a document can never point elsewhere. */
export const assetSchema = z.strictObject({
  id: assetIdSchema,
  kind: z.enum(["photo", "illustration", "abstract", "product", "avatar"]).default("photo"),
  source: z.enum(["generated", "search", "internal"]),
  provider: fieldKey,
  url: z.string().regex(/^\/api\/v1\/assets\/[0-9a-f-]{36}\/content$/),
  alt: shortText,
  prompt: longText.optional(),
  width: z.number().int().min(16).max(4096),
  height: z.number().int().min(16).max(4096),
  usage: shortText.optional(),
  screen_id: componentIdSchema.optional(),
  attribution: shortText.optional(),
  created_at: z.string().max(40).optional(),
});

const interactionSchema = z.strictObject({
  id: componentIdSchema,
  label: shortText,
  type: z.enum(ACTION_TYPES),
  description: shortText.optional(),
  screen_id: componentIdSchema.optional(),
  entity: entityName.optional(),
  result: shortText.optional(),
});

const designDirectionSchema = z.strictObject({
  style: fieldKey,
  summary: shortText,
  mood: z.array(shortText).max(6).default([]),
  rationale: mediumText.optional(),
  imagery: z.enum(["photography", "illustration", "abstract", "product", "none"]).default("none"),
  visual_language: mediumText.optional(),
  layout: shortText.optional(),
  effects: z.array(z.enum(EFFECTS)).max(6).default([]),
});

export const applicationSchema = z.strictObject({
  name: shortText,
  category: shortText,
  description: mediumText,
  target_users: z.array(shortText).max(8).default([]),
  goals: z.array(shortText).max(8).default([]),
  features: z.array(shortText).max(16).default([]),
  navigation: navigationSchema,
  entities: z.array(entitySchema).max(20).default([]),
  interactions: z.array(interactionSchema).max(60).default([]),
  assets: z.array(assetSchema).max(60).default([]),
  design_direction: designDirectionSchema.optional(),
});

export const documentSchema = z.strictObject({
  schema_version: z.literal(SCHEMA_VERSION).default(SCHEMA_VERSION),
  page: pageSchema,
  theme: themeSchema,
  design: designSchema,
  application: applicationSchema.optional(),
});

export const dataMapSchema = z.record(z.string(), z.array(dataRowSchema));
