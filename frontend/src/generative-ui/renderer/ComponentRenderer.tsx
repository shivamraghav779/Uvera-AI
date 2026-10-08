import { Component, memo, type ReactNode } from "react";
import { useStore } from "zustand";

import { getComponentDefinition } from "../registry/componentRegistry";
import type { Scalar, UIComponent, UINode } from "../schema/types";

import { useRenderer } from "./RendererContext";

/**
 * Shown for a component type this build has no renderer for. The rest of the UI
 * keeps working; nothing from the unknown node is interpreted.
 */
export function UnsupportedComponent({ type, id }: { type: string; id: string }) {
  return (
    <div
      role="note"
      className="rounded-g border border-dashed border-g-border p-[var(--g-pad)] text-[0.9em] text-g-muted-fg"
    >
      This build cannot display “{type}” components ({id}).
    </div>
  );
}

interface BoundaryProps {
  componentId: string;
  children: ReactNode;
}

/** Contains a rendering failure to the one component that caused it. */
class ComponentBoundary extends Component<BoundaryProps, { failed: boolean }> {
  override state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  override componentDidUpdate(previous: BoundaryProps) {
    // A changed node gets another chance to render.
    if (this.state.failed && previous.children !== this.props.children) {
      this.setState({ failed: false });
    }
  }

  override render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div role="alert" className="rounded-g border border-g-destructive p-[var(--g-pad)] text-[0.9em]">
        “{this.props.componentId}” could not be displayed.
      </div>
    );
  }
}

type Condition = NonNullable<UIComponent["visible_when"]>;

function isEmpty(value: Scalar | undefined): boolean {
  return value === undefined || value === null || value === "" || value === false;
}

/** Evaluate a declarative visibility condition. There is no expression language. */
export function evaluateCondition(condition: Condition, actual: Scalar | undefined): boolean {
  const expected = condition.value;
  switch (condition.operator) {
    case "equals":
      return actual === expected;
    case "not_equals":
      return actual !== expected;
    case "in":
      return Array.isArray(expected) && expected.includes(actual ?? null);
    case "not_in":
      return Array.isArray(expected) && !expected.includes(actual ?? null);
    case "gt":
      return typeof actual === "number" && typeof expected === "number" && actual > expected;
    case "lt":
      return typeof actual === "number" && typeof expected === "number" && actual < expected;
    case "is_set":
      return !isEmpty(actual);
    case "is_empty":
      return isEmpty(actual);
  }
}

function useIsVisible(node: UINode): boolean {
  const { runtime, mode } = useRenderer();
  const condition = "visible_when" in node ? node.visible_when : undefined;
  const actual = useStore(runtime, (state) => (condition ? state.values[condition.field] : undefined));
  // The editor shows everything so hidden components stay reachable.
  if (!condition || mode === "edit") return true;
  return evaluateCondition(condition, actual);
}

/**
 * Renders one node through the component registry. Memoised on the node, and
 * the workspace store shares unchanged nodes by reference, so an edit
 * re-renders only the components it touched.
 */
export const ComponentRenderer = memo(function ComponentRenderer({ node }: { node: UINode }) {
  const visible = useIsVisible(node);
  const definition = getComponentDefinition(node.type);
  if (!definition) return <UnsupportedComponent type={node.type} id={node.id} />;
  if (!visible) return null;
  const Semantic = definition.Component;
  return (
    <ComponentBoundary componentId={node.id}>
      <Semantic node={node} />
    </ComponentBoundary>
  );
});
