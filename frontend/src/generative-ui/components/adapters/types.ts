/**
 * The adapter contract.
 *
 * A semantic component (GMetric, GChart, ...) owns behaviour: it reads the
 * schema node, resolves data and wires actions. It then hands *view props* to
 * the active framework adapter, which owns nothing but looks. An adapter is
 * therefore a set of presentational React components with these props.
 *
 * Adding a UI framework = implementing (part of) `AdapterComponents`. The UI
 * schema, the mutation engine and the AI prompts do not change.
 */
import type { ComponentType, ReactNode } from "react";

import type { ColorRole, ComponentStyle } from "../../schema/types";
import type { BUTTON_VARIANTS, SECTION_VARIANTS } from "../../schema/validators";

export type Emphasis = "subtle" | "default" | "strong";
export type FeedbackTone = "neutral" | "info" | "success" | "warning" | "danger";

/** Token-based styling shared by every view. Never CSS. */
export interface StyleProps {
  tone?: ColorRole;
  emphasis?: Emphasis;
  /** Surface treatment for this one component; the theme decides otherwise. */
  surface?: ComponentStyle["surface"];
  density?: ComponentStyle["density"];
  align?: ComponentStyle["align"];
  effects?: ComponentStyle["effects"];
}

export interface PageViewProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export interface SectionViewProps extends StyleProps {
  variant?: (typeof SECTION_VARIANTS)[number];
  eyebrow?: string;
  /** Drawn behind an immersive section (an image chosen by the semantic component). */
  backdrop?: ReactNode;
  title?: string;
  description?: string;
  children: ReactNode;
}

export interface CardViewProps extends StyleProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
}

export interface TabsViewProps {
  tabs: { id: string; label: string; content: ReactNode }[];
  defaultTab?: string;
}

export interface ModalViewProps {
  title: string;
  triggerLabel: string;
  children: ReactNode;
}

export interface DividerViewProps {
  label?: string;
}

export interface MetricViewProps extends StyleProps {
  title: string;
  /** Already formatted for display. */
  value: string;
  unit?: string;
  trend?: { direction: "up" | "down" | "flat"; value: string; label?: string };
  description?: string;
}

export interface TextViewProps extends StyleProps {
  content: string;
  variant: "heading" | "subheading" | "body" | "caption";
}

export interface TableViewProps {
  title?: string;
  columns: { key: string; label: string; align: "left" | "center" | "right" }[];
  /** Cells already formatted for display, one record per row keyed by column key. */
  rows: Record<string, string>[];
  pageSize?: number;
  /** Fixed height in pixels; the body scrolls. */
  height?: number;
  /** Set when rows lead somewhere; called with the row's position in `rows`. */
  onRowClick?: (index: number) => void;
}

export interface ChartViewProps extends StyleProps {
  title?: string;
  chartType: "bar" | "line" | "area" | "pie" | "donut" | "scatter";
  rows: Record<string, string | number | boolean | null>[];
  xKey: string;
  yKeys: string[];
  height: number;
}

export interface ListViewProps {
  title?: string;
  ordered: boolean;
  items: { title: string; description?: string; badge?: string }[];
}

export interface TimelineViewProps {
  title?: string;
  items: {
    title: string;
    description?: string;
    timestamp?: string;
    status?: "completed" | "current" | "upcoming";
  }[];
}

export interface BadgeViewProps {
  label: string;
  tone: FeedbackTone;
}

export interface ProgressViewProps {
  label: string;
  value: number;
  max: number;
  tone: FeedbackTone;
}

export interface AlertViewProps {
  title?: string;
  message: string;
  tone: FeedbackTone;
}

export interface FormViewProps {
  title?: string;
  submitLabel: string;
  submitting: boolean;
  onSubmit: () => void;
  children: ReactNode;
}

export interface InputViewProps {
  id: string;
  name: string;
  label: string;
  inputType: "text" | "number" | "email" | "date" | "search" | "textarea";
  placeholder?: string;
  value: string;
  required: boolean;
  onChange: (value: string) => void;
}

export interface SelectViewProps {
  id: string;
  name: string;
  label: string;
  options: { label: string; value: string }[];
  /** Empty string means "nothing selected". */
  value: string;
  required: boolean;
  onChange: (value: string) => void;
}

export interface CheckboxViewProps {
  id: string;
  name: string;
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export interface ButtonViewProps {
  label: string;
  variant: (typeof BUTTON_VARIANTS)[number];
  disabled: boolean;
  busy: boolean;
  onClick: () => void;
}

export interface AdapterComponents {
  Page: ComponentType<PageViewProps>;
  Section: ComponentType<SectionViewProps>;
  Card: ComponentType<CardViewProps>;
  Tabs: ComponentType<TabsViewProps>;
  Modal: ComponentType<ModalViewProps>;
  Divider: ComponentType<DividerViewProps>;
  Metric: ComponentType<MetricViewProps>;
  Text: ComponentType<TextViewProps>;
  Table: ComponentType<TableViewProps>;
  Chart: ComponentType<ChartViewProps>;
  List: ComponentType<ListViewProps>;
  Timeline: ComponentType<TimelineViewProps>;
  Badge: ComponentType<BadgeViewProps>;
  Progress: ComponentType<ProgressViewProps>;
  Alert: ComponentType<AlertViewProps>;
  Form: ComponentType<FormViewProps>;
  Input: ComponentType<InputViewProps>;
  Select: ComponentType<SelectViewProps>;
  Checkbox: ComponentType<CheckboxViewProps>;
  Button: ComponentType<ButtonViewProps>;
}

export type AdapterComponentName = keyof AdapterComponents;

export interface FrameworkAdapter {
  /** Matches `design.framework` in the UI document and the backend's framework registry. */
  id: string;
  name: string;
  /** A complete adapter implements everything; a partial one falls back to the default. */
  components: Partial<AdapterComponents>;
}
