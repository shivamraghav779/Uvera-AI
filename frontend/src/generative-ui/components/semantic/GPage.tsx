import { LayoutRenderer } from "../../renderer/LayoutRenderer";
import { useAdapter, useRenderer } from "../../renderer/RendererContext";
import type { PageNode } from "../../schema/types";
import { AppShell } from "../application/AppShell";

import { GScreen } from "./GScreen";

export function GPage({ node }: { node: PageNode }) {
  const { Page } = useAdapter();
  const { app } = useRenderer();
  // An application shows one screen at a time inside its shell; the route decides which.
  if (app) {
    return (
      <AppShell app={app}>
        <GScreen key={app.route.screen.id} node={app.route.screen} />
      </AppShell>
    );
  }
  return (
    <Page title={node.title} description={node.description}>
      <LayoutRenderer slotId={node.id} items={node.components} />
    </Page>
  );
}
