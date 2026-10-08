/**
 * The screens of the open application. Picking one shows it on the canvas, which
 * is also how screens that are not in the navigation (a record's page, a form)
 * are reached while designing.
 */
import { Check, ChevronDown, Layers } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Popover } from "@/components/ui/Popover";
import type { ScreenComponent } from "@/generative-ui/schema/types";
import { cn } from "@/utils/cn";

interface ScreenMenuProps {
  screens: readonly ScreenComponent[];
  activeId: string | null;
  onPick: (screen: ScreenComponent) => void;
}

export function ScreenMenu({ screens, activeId, onPick }: ScreenMenuProps) {
  const active = screens.find((screen) => screen.id === activeId);
  return (
    <Popover
      className="w-72"
      trigger={(props) => (
        <Button size="sm" icon={<Layers size={14} />} {...props}>
          <span className="max-w-32 truncate">{active?.title ?? "Screens"}</span>
          <ChevronDown size={13} aria-hidden className="text-app-muted" />
        </Button>
      )}
    >
      {(close) => (
        <div role="listbox" aria-label="Screens" className="flex max-h-[60vh] flex-col overflow-y-auto">
          <p className="mb-1.5 px-2 text-xs font-semibold tracking-wide text-app-muted uppercase">
            {screens.length} screens
          </p>
          {screens.map((screen) => (
            <button
              key={screen.id}
              type="button"
              role="option"
              aria-selected={screen.id === activeId}
              onClick={() => {
                onPick(screen);
                close();
              }}
              className={cn(
                "flex items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-app-subtle",
                screen.id === activeId && "bg-app-accent-soft",
              )}
            >
              <span className="min-w-0 flex-1">
                <span className="block truncate font-medium">{screen.title}</span>
                <span className="block truncate font-mono text-[11px] text-app-muted">{screen.route}</span>
              </span>
              {screen.id === activeId && <Check size={14} aria-hidden className="shrink-0 text-app-accent" />}
            </button>
          ))}
        </div>
      )}
    </Popover>
  );
}
