import { useEffect, useMemo, useState, type ComponentType, type ReactNode } from "react";
import type { StoreApi } from "zustand";

import { resolveAdapter } from "../registry/frameworkRegistry";
import type { Asset, DataMap } from "../schema/types";

import { StaticElement, StaticSlot } from "./LayoutRenderer";
import {
  createRuntimeStore,
  RendererContext,
  type ActionDispatcher,
  type AppRuntime,
  type ElementProps,
  type RenderMode,
  type RendererContextValue,
  type RuntimeState,
  type SlotProps,
} from "./RendererContext";

/** What a dispatcher may read about the canvas at the moment an action fires. */
export interface DispatcherEnvironment {
  runtime: StoreApi<RuntimeState>;
  /** The application runtime as it is now (route parameters change as the user moves). */
  getApp: () => AppRuntime | null;
}

interface RendererProviderProps {
  mode: RenderMode;
  /** `design.framework` of the document being rendered. */
  framework: string;
  data: DataMap;
  highlightIds?: readonly string[];
  /** The application around the screen on display; omit for a single view. */
  app?: AppRuntime | null;
  assets?: ReadonlyMap<string, Asset>;
  /** Builds the dispatcher once the runtime store exists. Omit for inert rendering. */
  createDispatcher?: (environment: DispatcherEnvironment) => ActionDispatcher;
  Slot?: ComponentType<SlotProps>;
  Element?: ComponentType<ElementProps>;
  children: ReactNode;
}

const inertDispatcher: ActionDispatcher = async () => {};
const NO_ASSETS: ReadonlyMap<string, Asset> = new Map();

export function RendererProvider({
  mode,
  framework,
  data,
  highlightIds,
  app = null,
  assets = NO_ASSETS,
  createDispatcher,
  Slot = StaticSlot,
  Element = StaticElement,
  children,
}: RendererProviderProps) {
  const [runtime] = useState(createRuntimeStore);
  // Kept in the runtime store and read at dispatch time, so an action always sees the
  // route it was fired from without the dispatcher being rebuilt on every navigation.
  useEffect(() => runtime.setState({ app }), [runtime, app]);
  const dispatchAction = useMemo(
    () => createDispatcher?.({ runtime, getApp: () => runtime.getState().app }) ?? inertDispatcher,
    [createDispatcher, runtime],
  );
  const highlighted = useMemo(() => new Set(highlightIds ?? []), [highlightIds]);
  const value = useMemo<RendererContextValue>(
    () => ({
      mode,
      // The framework is resolved here, at render time, from the document's design config.
      adapter: resolveAdapter(framework),
      data,
      runtime,
      dispatchAction,
      highlightIds: highlighted,
      app,
      assets,
      Slot,
      Element,
    }),
    [mode, framework, data, runtime, dispatchAction, highlighted, app, assets, Slot, Element],
  );
  return <RendererContext.Provider value={value}>{children}</RendererContext.Provider>;
}
