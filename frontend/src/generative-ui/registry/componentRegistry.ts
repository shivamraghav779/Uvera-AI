/**
 * The frontend's component registry: UI schema `type` -> semantic component.
 *
 * This is the only path from data to React. A type that is not registered here
 * cannot render (the renderer shows a placeholder), no matter what a document
 * says. The registry also describes each component to the editor.
 */
import type { ComponentType as ReactComponentType } from "react";

import { GAlert } from "../components/semantic/GAlert";
import { GBadge } from "../components/semantic/GBadge";
import { GButton } from "../components/semantic/GButton";
import { GCard } from "../components/semantic/GCard";
import { GChart } from "../components/semantic/GChart";
import { GCheckbox } from "../components/semantic/GCheckbox";
import { GDivider } from "../components/semantic/GDivider";
import { GForm } from "../components/semantic/GForm";
import { GInput } from "../components/semantic/GInput";
import { GList } from "../components/semantic/GList";
import { GMetric } from "../components/semantic/GMetric";
import { GModal } from "../components/semantic/GModal";
import { GPage } from "../components/semantic/GPage";
import { GProgress } from "../components/semantic/GProgress";
import { GScreen } from "../components/semantic/GScreen";
import { GSection } from "../components/semantic/GSection";
import { GSelect } from "../components/semantic/GSelect";
import { GTable } from "../components/semantic/GTable";
import { GTabs } from "../components/semantic/GTabs";
import { GText } from "../components/semantic/GText";
import { GTimeline } from "../components/semantic/GTimeline";
import {
  Comparison,
  Cta,
  Faq,
  FeatureGrid,
  Footer,
  Gallery,
  Hero,
  Image,
  LogoCloud,
  Media,
  Pricing,
  Steps,
  Testimonials,
} from "../components/patterns/marketing";
import { Calendar, Collection, Command, Detail, Kanban, ProfileHeader, Stats } from "../components/patterns/records";
import type { UINode } from "../schema/types";
import { BUTTON_VARIANTS, CHART_TYPES, SCREEN_WIDTHS, SECTION_VARIANTS } from "../schema/validators";

/** A property the inspector can edit. Edits become UPDATE operations. */
export interface EditableField {
  key: string;
  label: string;
  kind: "text" | "textarea" | "number" | "boolean" | "select";
  options?: readonly string[];
}

export interface ComponentDefinition {
  type: UINode["type"];
  label: string;
  /** Whether other components can be moved into it. */
  container: boolean;
  fields: readonly EditableField[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any -- narrowed by `define`
  Component: ReactComponentType<{ node: any }>;
}

const registry = new Map<string, ComponentDefinition>();

function define<T extends UINode["type"]>(
  type: T,
  Component: ReactComponentType<{ node: Extract<UINode, { type: T }> }>,
  label: string,
  fields: readonly EditableField[] = [],
  container = false,
): void {
  registry.set(type, { type, label, container, fields, Component });
}

const text = (key: string, label: string): EditableField => ({ key, label, kind: "text" });
const select = (key: string, label: string, options: readonly string[]): EditableField => ({
  key,
  label,
  kind: "select",
  options,
});
const TONES = ["neutral", "info", "success", "warning", "danger"] as const;
const TITLE = text("title", "Title");

define("page", GPage, "Page", [TITLE, text("description", "Description")], true);
define(
  "section",
  GSection,
  "Section",
  [text("eyebrow", "Eyebrow"), TITLE, text("description", "Description"), select("variant", "Layout", SECTION_VARIANTS)],
  true,
);
define(
  "screen",
  GScreen,
  "Screen",
  [TITLE, select("width", "Width", SCREEN_WIDTHS), { key: "show_title", label: "Show title", kind: "boolean" }],
  true,
);
define("card", GCard, "Card", [TITLE, text("subtitle", "Subtitle")], true);
define("tabs", GTabs, "Tabs", [], true);
define("modal", GModal, "Modal", [TITLE, text("trigger_label", "Button label")], true);
define("divider", GDivider, "Divider", [text("label", "Label")]);
define("metric", GMetric, "Metric", [
  TITLE,
  text("unit", "Unit"),
  select("format", "Format", ["text", "number", "currency", "percent"]),
  text("description", "Description"),
]);
define("text", GText, "Text", [
  { key: "content", label: "Content", kind: "textarea" },
  select("variant", "Variant", ["heading", "subheading", "body", "caption"]),
]);
define("table", GTable, "Table", [TITLE, { key: "page_size", label: "Rows per page", kind: "number" }]);
define("chart", GChart, "Chart", [TITLE, select("chart_type", "Chart type", CHART_TYPES)]);
define("list", GList, "List", [TITLE, { key: "ordered", label: "Numbered", kind: "boolean" }]);
define("timeline", GTimeline, "Timeline", [TITLE]);
define("badge", GBadge, "Badge", [text("label", "Label"), select("tone", "Tone", TONES)]);
define("progress", GProgress, "Progress", [
  text("label", "Label"),
  { key: "value", label: "Value", kind: "number" },
  { key: "max", label: "Maximum", kind: "number" },
  select("tone", "Tone", TONES),
]);
define("alert", GAlert, "Alert", [
  TITLE,
  { key: "message", label: "Message", kind: "textarea" },
  select("tone", "Tone", TONES),
]);
define("form", GForm, "Form", [TITLE, text("submit_label", "Submit label")], true);
define("input", GInput, "Input", [
  text("label", "Label"),
  text("placeholder", "Placeholder"),
  select("input_type", "Type", ["text", "number", "email", "date", "search", "textarea"]),
  { key: "required", label: "Required", kind: "boolean" },
]);
define("select", GSelect, "Select", [
  text("label", "Label"),
  { key: "required", label: "Required", kind: "boolean" },
]);
define("checkbox", GCheckbox, "Checkbox", [text("label", "Label")]);
define("button", GButton, "Button", [
  text("label", "Label"),
  select("variant", "Variant", BUTTON_VARIANTS),
]);

// --- Patterns: designed compositions described by content and a variant ---------------

const EYEBROW = text("eyebrow", "Eyebrow");
const SUBTITLE: EditableField = { key: "subtitle", label: "Subtitle", kind: "textarea" };
const COLUMNS: EditableField = { key: "columns", label: "Columns", kind: "number" };
const variant = (...options: string[]) => select("variant", "Layout", options);

define("hero", Hero, "Hero", [
  variant("split", "centered", "immersive", "editorial", "product"),
  EYEBROW,
  TITLE,
  SUBTITLE,
]);
define("feature_grid", FeatureGrid, "Features", [
  variant("grid", "bento", "list", "alternating"),
  EYEBROW,
  TITLE,
  SUBTITLE,
  COLUMNS,
]);
define("logo_cloud", LogoCloud, "Logos", [variant("static", "marquee"), TITLE]);
define("testimonials", Testimonials, "Testimonials", [variant("cards", "spotlight", "marquee"), EYEBROW, TITLE]);
define("pricing", Pricing, "Pricing", [EYEBROW, TITLE, SUBTITLE]);
define("cta", Cta, "Call to action", [variant("banner", "centered", "split"), EYEBROW, TITLE, SUBTITLE]);
define("stats", Stats, "Stats", [variant("strip", "cards", "inline"), TITLE]);
define("gallery", Gallery, "Gallery", [
  variant("grid", "masonry", "editorial", "carousel"),
  EYEBROW,
  TITLE,
  SUBTITLE,
  COLUMNS,
]);
define("collection", Collection, "Collection", [
  variant("cards", "list", "compact", "media", "feed"),
  TITLE,
  text("subtitle", "Subtitle"),
  COLUMNS,
  text("empty_text", "Text when empty"),
]);
define("kanban", Kanban, "Board", [TITLE]);
define("detail", Detail, "Details", [variant("grid", "list"), TITLE, COLUMNS]);
define("profile_header", ProfileHeader, "Record header", [variant("banner", "compact")]);
define("image", Image, "Image", [
  text("caption", "Caption"),
  select("aspect", "Shape", ["auto", "square", "video", "wide", "ultrawide", "portrait"]),
  select("fit", "Fit", ["cover", "contain"]),
  { key: "rounded", label: "Rounded corners", kind: "boolean" },
]);
define("media", Media, "Media block", [
  variant("image_left", "image_right", "overlay", "framed"),
  EYEBROW,
  TITLE,
  { key: "body", label: "Text", kind: "textarea" },
]);
define("steps", Steps, "Steps", [variant("numbered", "cards", "timeline"), EYEBROW, TITLE]);
define("faq", Faq, "Questions", [TITLE]);
define("footer", Footer, "Footer", [text("brand", "Brand"), text("tagline", "Tagline"), text("note", "Note")]);
define("calendar", Calendar, "Agenda", [TITLE]);
define("comparison", Comparison, "Comparison", [TITLE]);
define("command", Command, "Command bar", [text("placeholder", "Placeholder")]);

export function getComponentDefinition(type: string): ComponentDefinition | undefined {
  return registry.get(type);
}

export function supportedComponentTypes(): string[] {
  return [...registry.keys()];
}
