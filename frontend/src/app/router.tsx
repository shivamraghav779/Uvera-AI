import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter, Navigate } from "react-router";

import { CanvasSkeleton } from "@/components/feedback/Skeleton";
import { StateMessage } from "@/components/feedback/StateMessage";
import { LoginPage } from "@/features/auth/LoginPage";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { WorkspaceListPage } from "@/features/workspace/WorkspaceListPage";

// The editor (renderer, drag-and-drop, adapters) loads only when a workspace is opened.
const WorkspacePage = lazy(() =>
  import("@/features/workspace/WorkspacePage").then((module) => ({ default: module.WorkspacePage })),
);
const SettingsPage = lazy(() =>
  import("@/features/settings/SettingsPage").then((module) => ({ default: module.SettingsPage })),
);

function screen(element: ReactNode) {
  return <Suspense fallback={<CanvasSkeleton label="Loading" />}>{element}</Suspense>;
}

import { AppShell } from "./layouts/AppShell";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      // Signed-in users land on their workspaces.
      { path: "/", element: <Navigate to="/workspaces" replace /> },
      { path: "/workspaces", element: <WorkspaceListPage /> },
      { path: "/workspaces/:workspaceId", element: screen(<WorkspacePage />) },
      { path: "/workspaces/:workspaceId/history", element: screen(<WorkspacePage showHistory />) },
      { path: "/settings", element: screen(<SettingsPage />) },
      {
        path: "*",
        element: <StateMessage title="Page not found" description="That address does not exist." />,
      },
    ],
  },
]);
