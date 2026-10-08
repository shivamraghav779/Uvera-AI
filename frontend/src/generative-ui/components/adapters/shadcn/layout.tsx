import * as Dialog from "@radix-ui/react-dialog";
import * as RadixTabs from "@radix-ui/react-tabs";
import { X } from "lucide-react";

import { cn } from "@/utils/cn";

import { usePortalContainer } from "../../../theme/ThemeProvider";
import { Band, SectionHeader } from "../../patterns/shared";
import { toneStyle, TONE_WASH } from "../shared";
import type {
  CardViewProps,
  DividerViewProps,
  ModalViewProps,
  PageViewProps,
  SectionViewProps,
  TabsViewProps,
} from "../types";

/** Every card-like surface; the theme (or `style.surface`) picks its treatment. */
export const SURFACE = "g-card";

export function Page({ title, description, children }: PageViewProps) {
  return (
    <div className="flex flex-col gap-[var(--g-gap)]">
      <header>
        <h1 className="g-h2 !text-[calc(1.7em*var(--g-heading-scale))]">{title}</h1>
        {description && <p className="mt-1 text-g-muted-fg">{description}</p>}
      </header>
      {children}
    </div>
  );
}

const BAND_TONE = { immersive: "inverse", band: "muted", full_bleed: "default" } as const;

export function Section(props: SectionViewProps) {
  const { variant = "default", eyebrow, backdrop, title, description, tone, emphasis, children } = props;
  const style = { density: props.density, align: props.align, effects: props.effects };

  if (variant === "immersive" || variant === "band" || variant === "full_bleed") {
    const pictured = variant === "immersive" && Boolean(backdrop);
    return (
      <Band
        style={style}
        tone={BAND_TONE[variant]}
        backdrop={pictured ? backdrop : undefined}
        className={cn("g-band-boxed overflow-hidden", pictured && "text-white [&_.g-eyebrow]:!text-white/85 [&_.g-lead]:!text-white/85")}
      >
        <SectionHeader eyebrow={eyebrow} title={title} subtitle={description} align={props.align} />
        {children}
      </Band>
    );
  }
  if (variant === "split") {
    return (
      <Band style={style}>
        <div className="g-split items-start" data-ratio="4-8">
          <SectionHeader eyebrow={eyebrow} title={title} subtitle={description} className="!mb-0 lg:sticky lg:top-24" />
          <div className="min-w-0">{children}</div>
        </div>
      </Band>
    );
  }
  if (variant === "editorial") {
    return (
      <Band style={style} className="border-t border-g-fg pt-[calc(var(--g-gap)*1.25)]">
        <SectionHeader eyebrow={eyebrow} title={title} subtitle={description} className="max-w-4xl" />
        {children}
      </Band>
    );
  }
  return (
    <section
      style={toneStyle(tone)}
      className={cn(
        "flex h-full flex-col gap-[calc(var(--g-gap)*0.75)]",
        emphasis === "strong" && cn("rounded-g p-[var(--g-pad)]", TONE_WASH),
      )}
    >
      {(eyebrow || title || description) && (
        <header>
          {eyebrow && <p className="g-eyebrow mb-1">{eyebrow}</p>}
          {title && <h2 className="g-h3 !text-[1.2em] font-semibold">{title}</h2>}
          {description && <p className="text-[0.92em] text-g-muted-fg">{description}</p>}
        </header>
      )}
      {children}
    </section>
  );
}

export function Card({ title, subtitle, tone, emphasis, surface, children }: CardViewProps) {
  return (
    <article
      style={toneStyle(tone)}
      data-surface={surface}
      className={cn(
        SURFACE,
        "flex h-full flex-col gap-[calc(var(--g-gap)*0.75)] p-[var(--g-pad)]",
        tone && "border-t-2 border-t-g-tone",
        emphasis === "strong" && TONE_WASH,
      )}
    >
      {(title || subtitle) && (
        <header>
          {title && <h3 className="g-h3 font-semibold">{title}</h3>}
          {subtitle && <p className="text-[0.92em] text-g-muted-fg">{subtitle}</p>}
        </header>
      )}
      {children}
    </article>
  );
}

export function Tabs({ tabs, defaultTab }: TabsViewProps) {
  return (
    <RadixTabs.Root defaultValue={defaultTab ?? tabs[0]?.id} className="flex flex-col gap-[var(--g-gap)]">
      <RadixTabs.List className="inline-flex w-fit gap-1 rounded-g bg-g-muted p-1">
        {tabs.map((tab) => (
          <RadixTabs.Trigger
            key={tab.id}
            value={tab.id}
            className={cn(
              "rounded-[calc(var(--g-radius)*0.75)] px-3 py-1.5 text-[0.92em] font-medium text-g-muted-fg",
              "data-[state=active]:bg-g-surface data-[state=active]:text-g-fg data-[state=active]:shadow-sm",
            )}
          >
            {tab.label}
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
      {tabs.map((tab) => (
        <RadixTabs.Content key={tab.id} value={tab.id}>
          {tab.content}
        </RadixTabs.Content>
      ))}
    </RadixTabs.Root>
  );
}

export function Modal({ title, triggerLabel, children }: ModalViewProps) {
  // Rendered inside the themed root so the dialog inherits the document's tokens.
  const container = usePortalContainer();
  return (
    <Dialog.Root>
      <Dialog.Trigger
        className={cn(
          "inline-flex h-[var(--g-control-h)] items-center rounded-g border border-g-border",
          "bg-g-surface px-4 font-medium hover:bg-g-muted",
        )}
      >
        {triggerLabel}
      </Dialog.Trigger>
      <Dialog.Portal container={container}>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/45" />
        <Dialog.Content
          aria-describedby={undefined}
          className={cn(
            SURFACE,
            "fixed top-1/2 left-1/2 z-50 max-h-[85vh] w-[min(92vw,640px)] -translate-x-1/2",
            "-translate-y-1/2 overflow-auto p-[calc(var(--g-pad)*1.25)] text-g-fg shadow-2xl",
          )}
        >
          <div className="mb-4 flex items-start justify-between gap-4">
            <Dialog.Title className="text-[1.15em] font-semibold">{title}</Dialog.Title>
            <Dialog.Close aria-label="Close" className="rounded p-1 text-g-muted-fg hover:bg-g-muted">
              <X size={16} />
            </Dialog.Close>
          </div>
          {children}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

export function Divider({ label }: DividerViewProps) {
  if (!label) return <hr className="my-1 border-g-border" />;
  return (
    <div role="separator" className="flex items-center gap-3 text-[0.85em] text-g-muted-fg">
      <span className="h-px flex-1 bg-g-border" />
      {label}
      <span className="h-px flex-1 bg-g-border" />
    </div>
  );
}
