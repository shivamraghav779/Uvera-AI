/**
 * The frame around an application's screens: brand, navigation and the primary
 * action, in the arrangement the document's navigation style names. Links move
 * between screens of the document; they can lead nowhere else.
 */
import { useEffect, useRef, type ReactNode } from "react";

import { cn } from "@/utils/cn";

import type { AppRuntime } from "../../renderer/RendererContext";
import type { NavigationItem, ScreenComponent } from "../../schema/types";
import { BUTTON_BASE, BUTTON_VARIANT_CLASS, Icon } from "../patterns/shared";

interface ShellLink {
  item: NavigationItem;
  screen: ScreenComponent;
}

function staticPrefix(route: string): string {
  return route.split("/:")[0] ?? route;
}

/**
 * The navigation entry to mark as current: the screen itself, else the entry
 * the screen sits under (`/jobs/:jobId` belongs to `/jobs`).
 */
export function currentItem(links: readonly ShellLink[], screen: ScreenComponent): string | null {
  if (links.some((link) => link.screen.id === screen.id)) return screen.id;
  const best = links
    .filter((link) => link.screen.route !== "/" && `${staticPrefix(screen.route)}/`.startsWith(`${link.screen.route}/`))
    .sort((a, b) => b.screen.route.length - a.screen.route.length)[0];
  return best?.screen.id ?? null;
}

function Brand({ name, tagline, onClick }: { name: string; tagline?: string; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className="flex min-w-0 shrink-0 items-center gap-2.5 text-left">
      <span
        aria-hidden
        className="grid size-8 shrink-0 place-items-center rounded-[calc(var(--g-radius)*0.8)] bg-g-primary bg-[image:var(--g-accent-fill)] font-bold text-g-primary-fg"
      >
        {name.trim().charAt(0).toUpperCase()}
      </span>
      <span className="min-w-0">
        <span className="g-heading block truncate text-[1.05em] leading-tight">{name}</span>
        {tagline && <span className="g-nav-footer block truncate text-[0.76em] text-g-muted-fg">{tagline}</span>}
      </span>
    </button>
  );
}

export function AppShell({ app, children }: { app: AppRuntime; children: ReactNode }) {
  const { navigation, name } = app.application;
  const { screen, path } = app.route;
  const byId = new Map(app.screens.map((candidate) => [candidate.id, candidate]));
  const links: ShellLink[] = navigation.items.flatMap((item) => {
    const target = byId.get(item.screen_id);
    return target ? [{ item, screen: target }] : [];
  });
  const current = currentItem(links, screen);
  const home = byId.get(navigation.home) ?? app.screens[0]!;
  const actionScreen = navigation.action ? byId.get(navigation.action.screen_id) : undefined;
  const style = navigation.style;

  // A new screen starts at its top, like a page would.
  const main = useRef<HTMLElement | null>(null);
  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    main.current?.scrollIntoView?.({ block: "start" });
  }, [path]);

  const link = ({ item, screen: target }: ShellLink, compact = false) => (
    <button
      key={item.screen_id}
      type="button"
      aria-current={current === target.id ? "page" : undefined}
      onClick={() => app.navigate(target.route)}
      className={cn("g-nav-link", compact && "flex-1 flex-col gap-1 px-1 py-1.5 text-[0.72em]")}
    >
      <Icon name={item.icon} size={compact ? 19 : 17} className="shrink-0" />
      <span className="truncate">{item.label}</span>
    </button>
  );
  const brand = <Brand name={navigation.brand ?? name} tagline={navigation.tagline} onClick={() => app.navigate(home.route)} />;
  const action = navigation.action && actionScreen && (
    <button
      type="button"
      onClick={() => app.navigate(actionScreen.route)}
      className={cn(BUTTON_BASE, BUTTON_VARIANT_CLASS.primary, "h-[calc(var(--g-control-h)*0.9)] whitespace-nowrap")}
    >
      <Icon name={navigation.action.icon} size={16} />
      {navigation.action.label}
    </button>
  );
  const content = (
    <main ref={main} className="min-w-0 scroll-mt-16" data-route={path}>
      {children}
    </main>
  );

  if (style === "none") {
    return (
      <div className="g-app" data-nav="none">
        {content}
      </div>
    );
  }

  if (style === "sidebar") {
    return (
      <div className="g-app" data-nav="sidebar">
        <aside className="g-app-sidebar">
          <div className="mb-4 px-1.5">{brand}</div>
          <nav aria-label={name} className="contents">
            {links.map((entry, index) => {
              // Entries keep their order; a group heading appears when the group changes.
              const group = entry.item.group;
              const heading = group !== links[index - 1]?.item.group ? group : undefined;
              return (
                <div key={entry.item.screen_id} className="contents">
                  {heading && (
                    <p className="g-nav-group mt-4 mb-1 px-2.5 text-[0.72em] font-semibold tracking-wider text-g-muted-fg uppercase">
                      {heading}
                    </p>
                  )}
                  {link(entry)}
                </div>
              );
            })}
          </nav>
          {action && <div className="g-nav-footer mt-auto pt-4 [&>button]:w-full">{action}</div>}
        </aside>
        {content}
      </div>
    );
  }

  if (style === "bottom") {
    return (
      <div className="g-app grid-rows-[auto_minmax(0,1fr)_auto]" data-nav="bottom">
        <header className="g-app-topbar justify-between">
          {brand}
          {action}
        </header>
        {content}
        <nav aria-label={name} className="g-app-bottombar">
          {links.slice(0, 5).map((entry) => link(entry, true))}
        </nav>
      </div>
    );
  }

  return (
    <div className="g-app grid-rows-[auto_minmax(0,1fr)]" data-nav={style}>
      <header className="g-app-topbar">
        {brand}
        <nav
          aria-label={name}
          className={cn("flex min-w-0 flex-1 items-center gap-1 overflow-x-auto", style === "minimal" && "justify-end")}
        >
          {links.map((entry) => link(entry))}
        </nav>
        {action}
      </header>
      {content}
    </div>
  );
}
