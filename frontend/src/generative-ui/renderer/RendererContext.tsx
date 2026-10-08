/**
 * Everything a semantic component needs at render time, in one context:
 * the active adapter, the data rows, per-canvas runtime state, the action
 * dispatcher and the wrappers the editor uses to make cells interactive.
 */
import { createContext, useContext, useMemo, type ComponentType, type ReactNode } from "react";
import { useStore, type StoreApi } from "zustand";
import { createStore } from "zustand/vanilla";

import { assetSource } from "../assets/assetRegistry";

import type { AdapterComponents } from "../components/adapters/types";
import type { RouteParams } from "../runtime/router";
import { selectRows } from "../runtime/rows";
import type {
  ActionSpec,
  ApplicationSpec,
  Asset,
  DataBinding,
  DataMap,
  DataRow,
  Scalar,
  ScreenComponent,
  UIComponent,
} from "../schema/types";

/** `view` is the live UI, `edit` the editor, `preview` a read-only look at another state. */
export type RenderMode = "view" | "edit" | "preview";

/** State that exists only while a canvas is on screen: control values and fetched rows. */
export interface RuntimeState {
  values: Record<string, Scalar>;
  /** Rows returned by an action for a target component (e.g. a filter result). */
  rows: Record<string, DataRow[]>;
  /** Whole datasets replaced by an action (a record was created, changed or removed). */
  datasets: Record<string, DataRow[]>;
  /** The application around the canvas as of the last render, for actions fired later. */
  app: AppRuntime | null;
  setValue: (name: string, value: Scalar) => void;
  setRows: (componentId: string, rows: DataRow[]) => void;
  clearRows: (componentId: string) => void;
  setDataset: (dataset: string, rows: DataRow[]) => void;
}

export function createRuntimeStore(): StoreApi<RuntimeState> {
  return createStore<RuntimeState>((set) => ({
    values: {},
    rows: {},
    datasets: {},
    app: null,
    setDataset: (dataset, rows) =>
      set((state) => ({
        datasets: { ...state.datasets, [dataset]: rows },
        // Per-component results (a filter) were computed from the old rows.
        rows: {},
      })),
    setValue: (name, value) => set((state) => ({ values: { ...state.values, [name]: value } })),
    setRows: (componentId, rows) => set((state) => ({ rows: { ...state.rows, [componentId]: rows } })),
    clearRows: (componentId) =>
      set((state) => {
        const { [componentId]: _removed, ...rest } = state.rows;
        return { rows: rest };
      }),
  }));
}

export interface SlotProps {
  slotId: string;
  items: readonly UIComponent[];
  children: ReactNode;
}

export interface ElementProps {
  node: UIComponent;
  slotId: string;
  index: number;
  children: ReactNode;
}

/** Extra values the UI supplies when an action fires (e.g. the option a user picked). */
export type ActionInput = Record<string, Scalar | Record<string, Scalar>>;
/** The record an action was triggered from (a table row, a card), if any. */
export interface ActionContext {
  row?: DataRow;
}
export type ActionDispatcher = (
  action: ActionSpec,
  input?: ActionInput,
  context?: ActionContext,
) => Promise<void>;

/** Where the user is inside a generated application. */
export interface AppRoute {
  path: string;
  screen: ScreenComponent;
  params: RouteParams;
}

/** The application around the screen being rendered; `null` for a single view. */
export interface AppRuntime {
  application: ApplicationSpec;
  screens: readonly ScreenComponent[];
  route: AppRoute;
  /** Go to an in-app path. Unknown paths are ignored. */
  navigate: (path: string) => void;
}

export interface RendererContextValue {
  mode: RenderMode;
  adapter: AdapterComponents;
  data: DataMap;
  runtime: StoreApi<RuntimeState>;
  dispatchAction: ActionDispatcher;
  highlightIds: ReadonlySet<string>;
  app: AppRuntime | null;
  /** Stored images by asset id. A component can only show an image listed here. */
  assets: ReadonlyMap<string, Asset>;
  /** Wraps the children of a container. The editor makes it a sortable list. */
  Slot: ComponentType<SlotProps>;
  /** Wraps one grid cell. The editor adds selection, drag and resize. */
  Element: ComponentType<ElementProps>;
}

export const RendererContext = createContext<RendererContextValue | null>(null);

export function useRenderer(): RendererContextValue {
  const value = useContext(RendererContext);
  if (!value) throw new Error("Generative UI components must be rendered inside a RendererProvider.");
  return value;
}

export function useAdapter(): AdapterComponents {
  return useRenderer().adapter;
}

/** Current value of a form control, by its `name`. */
export function useRuntimeValue(name: string): Scalar | undefined {
  return useStore(useRenderer().runtime, (state) => state.values[name]);
}

type Bindable = { id: string; data_source?: DataBinding };

const EMPTY_ROWS: readonly DataRow[] = [];
const NO_PARAMS: RouteParams = {};

/** Current rows of a dataset: what an action last returned for it, else what was loaded. */
export function useDataset(dataset: string | undefined): readonly DataRow[] {
  const { runtime, data } = useRenderer();
  const replaced = useStore(runtime, (state) => (dataset ? state.datasets[dataset] : undefined));
  if (!dataset) return EMPTY_ROWS;
  return replaced ?? data[dataset] ?? EMPTY_ROWS;
}

/** Parameters of the current route (`{}` outside an application). */
export function useRouteParams(): RouteParams {
  return useRenderer().app?.route.params ?? NO_PARAMS;
}

/**
 * Rows a data-driven component should show: an action result for it if there
 * is one, else what its binding selects from its dataset, else its inline rows.
 */
export function useRows(node: Bindable, inlineRows: readonly DataRow[] = EMPTY_ROWS): readonly DataRow[] {
  const { runtime } = useRenderer();
  const override = useStore(runtime, (state) => state.rows[node.id]);
  const binding = node.data_source;
  const dataset = useDataset(binding?.dataset);
  const params = useRouteParams();
  const selected = useMemo(
    () => (binding ? selectRows(dataset, binding, params) : EMPTY_ROWS),
    [binding, dataset, params],
  );
  if (override) return override;
  return binding ? selected : inlineRows;
}

/** URL of a stored image, or `undefined` when the id is not an asset of this document. */
export function useAsset(assetId: string | undefined): (Asset & { src: string }) | undefined {
  const { assets } = useRenderer();
  const asset = assetId ? assets.get(assetId) : undefined;
  return asset ? { ...asset, src: assetSource(asset) } : undefined;
}
