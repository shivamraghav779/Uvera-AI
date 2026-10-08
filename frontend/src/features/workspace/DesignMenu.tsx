/**
 * Theme, design system and framework pickers. Each choice becomes an explicit
 * operation applied through the same engine as every other edit, so it can be
 * undone, previewed and saved as a version. The components themselves are
 * never touched by any of these.
 */
import { Check, Palette, Shuffle } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Popover } from "@/components/ui/Popover";
import type { Operation } from "@/generative-ui/mutation/mutationTypes";
import { usableFrameworkIds } from "@/generative-ui/registry/capabilityRegistry";
import {
  designSystemOperation,
  frameworkOperation,
  themePresetOperation,
} from "@/generative-ui/registry/themeRegistry";
import type { UIDocument } from "@/generative-ui/schema/types";
import { NAVIGATION_STYLES } from "@/generative-ui/schema/validators";
import { cn } from "@/utils/cn";

import { useFrameworkCatalog, useThemeCatalog } from "./queries";

interface DesignMenuProps {
  document: UIDocument;
  disabled?: boolean;
  onApply: (operations: Operation[]) => void;
}

function OptionButton({
  selected,
  onClick,
  title,
  description,
}: {
  selected: boolean;
  onClick: () => void;
  title: string;
  description?: string;
}) {
  return (
    <button
      type="button"
      role="radio"
      aria-checked={selected}
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-app-subtle",
        selected && "bg-app-accent-soft",
      )}
    >
      <span className="min-w-0 flex-1">
        <span className="block font-medium">{title}</span>
        {description && <span className="block truncate text-xs text-app-muted">{description}</span>}
      </span>
      {selected && <Check size={14} aria-hidden className="shrink-0 text-app-accent" />}
    </button>
  );
}

const NAVIGATION_LABEL: Record<(typeof NAVIGATION_STYLES)[number], string> = {
  sidebar: "Sidebar",
  topbar: "Top bar",
  bottom: "Bottom bar",
  minimal: "Minimal",
  none: "None",
};

export function DesignMenu({ document, disabled, onApply }: DesignMenuProps) {
  const themes = useThemeCatalog();
  const frameworks = useFrameworkCatalog();
  const usable = usableFrameworkIds(frameworks.data);
  const navigation = document.application?.navigation;

  const applyOne = (operation: Operation | null) => {
    if (operation) onApply([operation]);
  };

  /** A random palette other than the one in use. */
  const shuffle = () => {
    if (!themes.data) return;
    const others = themes.data.presets.filter((preset) => preset.id !== document.theme.preset);
    const pick = others[Math.floor(Math.random() * others.length)];
    if (pick) applyOne(themePresetOperation(themes.data, pick.id));
  };

  return (
    <Popover
      className="w-80"
      trigger={(props) => (
        <Button size="sm" icon={<Palette size={14} />} disabled={disabled} {...props}>
          Design
        </Button>
      )}
    >
      <div className="flex max-h-[70vh] flex-col gap-4 overflow-y-auto">
        <section>
          <div className="mb-1.5 flex items-center justify-between">
            <h3 className="text-xs font-semibold tracking-wide text-app-muted uppercase">Theme</h3>
            <button
              type="button"
              onClick={shuffle}
              disabled={!themes.data}
              className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-medium text-app-muted hover:bg-app-subtle hover:text-app-fg disabled:opacity-50"
            >
              <Shuffle size={12} aria-hidden />
              Surprise me
            </button>
          </div>
          <div role="radiogroup" aria-label="Theme" className="grid grid-cols-2 gap-1.5">
            {themes.data?.presets.map((preset) => {
              const selected = document.theme.preset === preset.id;
              return (
                <button
                  key={preset.id}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  title={preset.description}
                  onClick={() => applyOne(themePresetOperation(themes.data, preset.id))}
                  className={cn(
                    "flex items-center gap-2 rounded-md border px-2 py-1.5 text-left text-xs font-medium",
                    selected ? "border-app-accent bg-app-accent-soft" : "border-app-border hover:bg-app-subtle",
                  )}
                >
                  <span
                    aria-hidden
                    className="flex size-5 shrink-0 overflow-hidden rounded-full border border-app-border"
                  >
                    {/* Swatches use validated preset colours from the backend. */}
                    <span className="flex-1" style={{ background: preset.theme.colors.background }} />
                    <span className="flex-1" style={{ background: preset.theme.colors.primary }} />
                  </span>
                  <span className="truncate">{preset.name}</span>
                </button>
              );
            })}
          </div>
        </section>

        <section>
          <h3 className="mb-1.5 text-xs font-semibold tracking-wide text-app-muted uppercase">
            Visual style
          </h3>
          <div role="radiogroup" aria-label="Visual style">
            {frameworks.data?.design_systems.map((system) => (
              <OptionButton
                key={system.id}
                selected={document.design.design_system === system.id}
                onClick={() => applyOne(designSystemOperation(frameworks.data, system.id))}
                title={system.name}
                description={system.description}
              />
            ))}
          </div>
        </section>

        {navigation && (
          <section>
            <h3 className="mb-1.5 text-xs font-semibold tracking-wide text-app-muted uppercase">Navigation</h3>
            <div role="radiogroup" aria-label="Navigation" className="flex flex-wrap gap-1.5">
              {NAVIGATION_STYLES.map((style) => (
                <button
                  key={style}
                  type="button"
                  role="radio"
                  aria-checked={navigation.style === style}
                  onClick={() => navigation.style !== style && onApply([{ type: "SET_NAVIGATION", style }])}
                  className={cn(
                    "rounded-md border px-2 py-1 text-xs font-medium",
                    navigation.style === style
                      ? "border-app-accent bg-app-accent-soft"
                      : "border-app-border hover:bg-app-subtle",
                  )}
                >
                  {NAVIGATION_LABEL[style]}
                </button>
              ))}
            </div>
          </section>
        )}

        <section>
          <h3 className="mb-1.5 text-xs font-semibold tracking-wide text-app-muted uppercase">
            Component framework
          </h3>
          <div role="radiogroup" aria-label="Component framework">
            {frameworks.data?.frameworks
              .filter((framework) => usable.includes(framework.id))
              .map((framework) => (
                <OptionButton
                  key={framework.id}
                  selected={document.design.framework === framework.id}
                  onClick={() => applyOne(frameworkOperation(framework.id))}
                  title={framework.name}
                  description={framework.description}
                />
              ))}
          </div>
          <p className="mt-1.5 text-xs text-app-muted">
            Switching framework re-renders the same UI. Nothing is regenerated.
          </p>
        </section>
      </div>
    </Popover>
  );
}
