import { LayoutGrid, LogOut, Settings } from "lucide-react";
import { NavLink, Outlet } from "react-router";

import { Toaster } from "@/components/feedback/Toaster";
import { useSignOut } from "@/features/auth/useAuth";
import { useWorkspaces } from "@/features/workspace/queries";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/utils/cn";

const NAV_LINK = cn(
  "flex h-8 items-center gap-2 rounded-md px-2 text-sm text-app-muted transition-colors",
  "hover:bg-app-subtle hover:text-app-fg aria-[current=page]:bg-app-subtle aria-[current=page]:text-app-fg",
);

const RECENT_COUNT = 8;

/** Application frame: a slim sidebar and the current screen. */
export function AppShell() {
  const workspaces = useWorkspaces();
  const user = useAuthStore((state) => state.user);
  const signOut = useSignOut();
  return (
    <div className="flex h-full">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-app-panel focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <nav
        aria-label="Primary"
        className="hidden w-56 shrink-0 flex-col gap-1 border-r border-app-border bg-app-panel p-3 md:flex"
      >
        <div className="mb-3 flex items-center gap-2 px-1.5 py-1">
          <span aria-hidden className="grid size-6 grid-cols-2 gap-0.5 rounded-md bg-app-fg p-1">
            <span className="rounded-[2px] bg-app-panel" />
            <span className="rounded-[2px] bg-app-muted" />
            <span className="col-span-2 rounded-[2px] bg-app-accent" />
          </span>
          <span className="text-sm font-semibold tracking-tight">Generative UI</span>
        </div>
        <NavLink to="/workspaces" end className={NAV_LINK}>
          <LayoutGrid size={15} aria-hidden /> Workspaces
        </NavLink>
        <NavLink to="/settings" className={NAV_LINK}>
          <Settings size={15} aria-hidden /> Settings
        </NavLink>

        {workspaces.data && workspaces.data.length > 0 && (
          <>
            <h2 className="mt-5 mb-1 px-2 text-[11px] font-semibold tracking-wide text-app-muted uppercase">
              Recent
            </h2>
            <ul className="flex flex-col gap-0.5 overflow-y-auto">
              {workspaces.data.slice(0, RECENT_COUNT).map((workspace) => (
                <li key={workspace.id}>
                  <NavLink to={`/workspaces/${workspace.id}`} className={NAV_LINK}>
                    <span className="truncate">{workspace.title ?? "Untitled workspace"}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </>
        )}

        {user && (
          <div className="mt-auto flex items-center gap-2 border-t border-app-border pt-3">
            <span className="min-w-0 flex-1 truncate px-1 text-xs text-app-muted" title={user.email}>
              {user.email}
            </span>
            <button
              type="button"
              onClick={signOut}
              aria-label="Sign out"
              title="Sign out"
              className="grid size-7 shrink-0 place-items-center rounded-md text-app-muted hover:bg-app-subtle hover:text-app-fg"
            >
              <LogOut size={14} />
            </button>
          </div>
        )}
      </nav>
      <div id="main" className="min-w-0 flex-1">
        <Outlet />
      </div>
      <Toaster />
    </div>
  );
}
