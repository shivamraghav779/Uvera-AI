/**
 * Building blocks shared by the pattern components: the band a section sits in
 * (with its effects), headings, action buttons, images, avatars and status
 * pills. Everything is styled through theme tokens.
 */
import { createElement, useRef, useState, type CSSProperties, type ReactNode } from "react";

import { cn } from "@/utils/cn";

import { useInView, useParallax, useSpotlight } from "../../effects/useEffects";
import { effectClasses, hasEffect } from "../../registry/effectRegistry";
import { resolveIcon } from "../../registry/iconRegistry";
import { useAsset, useRenderer, type ActionContext } from "../../renderer/RendererContext";
import { initials } from "../../runtime/rows";
import type { ActionSpec, ComponentStyle } from "../../schema/types";

// --- Band ----------------------------------------------------------------------

interface BandProps {
  style?: ComponentStyle;
  /** Background of the band: the page's, a muted tint, the inverse, or the accent. */
  tone?: "default" | "muted" | "inverse" | "primary";
  className?: string;
  /** Rendered edge to edge behind the content (an immersive image). */
  backdrop?: ReactNode;
  children: ReactNode;
}

/**
 * The strip of page a pattern occupies. On a full-width screen it runs edge to
 * edge and centres its content; inside an application screen it is just a box.
 * It owns the effects requested for the component.
 */
export function Band({ style, tone = "default", className, backdrop, children }: BandProps) {
  const effects = style?.effects;
  const element = useRef<HTMLElement | null>(null);
  const revealed = useInView(element, hasEffect(effects, "reveal"));
  useSpotlight(element, hasEffect(effects, "spotlight"));
  const decorated = (effects ?? []).some((effect) =>
    ["gradient_mesh", "animated_gradient", "grid", "noise", "spotlight"].includes(effect),
  );
  return (
    <section
      ref={element}
      data-tone={tone === "default" ? undefined : tone}
      data-density={style?.density}
      data-revealed={revealed || undefined}
      className={cn("g-band", effectClasses(effects), className)}
    >
      {backdrop}
      {decorated && <div aria-hidden className="g-fx-layer" />}
      <div className={cn("g-container", style?.align === "center" && "text-center")}>{children}</div>
    </section>
  );
}

/** Marks content that rises into view when its band has the `reveal` effect. */
export function reveal(index = 0): { "data-reveal": ""; style: CSSProperties } {
  return { "data-reveal": "", style: { "--reveal-index": index } as CSSProperties };
}

// --- Headings ------------------------------------------------------------------

interface SectionHeaderProps {
  eyebrow?: string;
  title?: string;
  subtitle?: string;
  align?: "left" | "center" | "right";
  className?: string;
}

export function SectionHeader({ eyebrow, title, subtitle, align = "left", className }: SectionHeaderProps) {
  if (!eyebrow && !title && !subtitle) return null;
  return (
    <header
      {...reveal(0)}
      className={cn(
        "mb-[calc(var(--g-gap)*1.75)] flex max-w-3xl flex-col gap-3",
        align === "center" && "mx-auto items-center text-center",
        className,
      )}
    >
      {eyebrow && <p className="g-eyebrow">{eyebrow}</p>}
      {title && <h2 className="g-h2">{title}</h2>}
      {subtitle && <p className="g-lead">{subtitle}</p>}
    </header>
  );
}

/** A small heading inside an application screen (above a list, a board, ...). */
export function BlockTitle({ title, subtitle, aside }: { title?: string; subtitle?: string; aside?: ReactNode }) {
  if (!title && !subtitle && !aside) return null;
  return (
    <header className="mb-3 flex items-end justify-between gap-3">
      <div className="min-w-0">
        {title && <h3 className="g-h3 font-semibold">{title}</h3>}
        {subtitle && <p className="text-[0.9em] text-g-muted-fg">{subtitle}</p>}
      </div>
      {aside}
    </header>
  );
}

// --- Icons ---------------------------------------------------------------------

export function Icon({ name, size = 18, className }: { name?: string; size?: number; className?: string }) {
  // Looked up in the icon registry: an existing component, never one made here.
  const glyph = resolveIcon(name);
  return glyph ? createElement(glyph, { size, className, "aria-hidden": true }) : null;
}

/** An icon on a tinted tile, the usual lead-in of a feature. */
export function IconTile({ name, className }: { name?: string; className?: string }) {
  if (!name) return null;
  return (
    <span
      className={cn(
        "grid size-10 shrink-0 place-items-center rounded-[calc(var(--g-radius)*0.9)] bg-[var(--g-primary-soft)] text-g-primary",
        className,
      )}
    >
      <Icon name={name} size={19} />
    </span>
  );
}

// --- Actions -------------------------------------------------------------------

export const BUTTON_VARIANT_CLASS = {
  primary: "bg-g-primary text-g-primary-fg hover:opacity-90",
  secondary: "border border-g-border bg-g-surface text-g-fg hover:bg-g-muted",
  danger: "bg-g-destructive text-g-destructive-fg hover:opacity-90",
  ghost: "text-g-fg hover:bg-g-muted",
  outline: "border border-current bg-transparent text-g-fg hover:bg-[color-mix(in_srgb,currentColor_8%,transparent)]",
  gradient: "bg-[image:var(--g-accent-fill)] bg-g-primary text-g-primary-fg hover:opacity-90",
  glass:
    "border border-[color-mix(in_srgb,currentColor_22%,transparent)] bg-[color-mix(in_srgb,var(--g-surface)_45%,transparent)] text-current backdrop-blur-md hover:bg-[color-mix(in_srgb,var(--g-surface)_65%,transparent)]",
} as const;

export const BUTTON_BASE = cn(
  "inline-flex h-[var(--g-control-h)] w-fit shrink-0 items-center justify-center gap-2 rounded-g px-4 font-medium",
  "transition-[opacity,background-color,transform] duration-[var(--g-duration-fast)]",
  "disabled:cursor-not-allowed disabled:opacity-50",
);

export interface ActionButtonSpec {
  label: string;
  action: ActionSpec;
  variant: keyof typeof BUTTON_VARIANT_CLASS;
  icon?: string;
}

/** Runs an allowlisted action; shows that it is working. Never evaluates anything. */
export function useAction(): (action: ActionSpec | undefined, context?: ActionContext) => Promise<void> {
  const { dispatchAction } = useRenderer();
  return async (action, context) => {
    if (action) await dispatchAction(action, {}, context);
  };
}

export function ActionButtons({
  actions,
  context,
  large = false,
  className,
}: {
  actions: readonly ActionButtonSpec[];
  context?: ActionContext;
  large?: boolean;
  className?: string;
}) {
  const run = useAction();
  const [busy, setBusy] = useState<number | null>(null);
  if (actions.length === 0) return null;
  return (
    <div className={cn("flex flex-wrap items-center gap-3", className)}>
      {actions.map((button, index) => (
        <button
          key={index}
          type="button"
          disabled={busy !== null}
          aria-busy={busy === index || undefined}
          onClick={async () => {
            setBusy(index);
            try {
              await run(button.action, context);
            } finally {
              setBusy(null);
            }
          }}
          className={cn(BUTTON_BASE, BUTTON_VARIANT_CLASS[button.variant], large && "h-[calc(var(--g-control-h)*1.2)] px-6 text-[1.02em]")}
        >
          <Icon name={button.icon} size={16} />
          {button.label}
        </button>
      ))}
    </div>
  );
}

// --- Images --------------------------------------------------------------------

const ASPECT = {
  auto: undefined,
  square: "1 / 1",
  video: "16 / 9",
  wide: "2 / 1",
  ultrawide: "21 / 9",
  portrait: "4 / 5",
  photo: "4 / 3",
} as const;

export type Aspect = keyof typeof ASPECT;

interface AssetImageProps {
  assetId?: string;
  /** Used when the asset has no description of its own. */
  alt?: string;
  aspect?: Aspect;
  fit?: "cover" | "contain";
  className?: string;
  parallax?: boolean;
  /** Load before the rest (the image at the top of a screen). */
  eager?: boolean;
}

/**
 * An image by asset id. An id that is not an asset of the document, or an
 * image that fails to load, shows a soft colour field instead of a broken icon.
 */
export function AssetImage({ assetId, alt, aspect = "auto", fit = "cover", className, parallax = false, eager = false }: AssetImageProps) {
  const asset = useAsset(assetId);
  const [failed, setFailed] = useState(false);
  const frame = useRef<HTMLDivElement | null>(null);
  useParallax(frame, parallax);
  const ratio = ASPECT[aspect] ?? (asset ? `${asset.width} / ${asset.height}` : ASPECT.photo);
  return (
    <div ref={frame} style={{ aspectRatio: ratio }} className={cn("relative overflow-hidden bg-g-muted", className)}>
      {asset && asset.src && !failed ? (
        <img
          src={asset.src}
          alt={asset.alt || alt || ""}
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          onError={() => setFailed(true)}
          style={{ objectFit: fit, transform: parallax ? "translateY(var(--parallax, 0)) scale(1.12)" : undefined }}
          className="g-image absolute inset-0"
        />
      ) : (
        <div role="img" aria-label={alt ?? "Image"} className="g-image-fallback absolute inset-0" />
      )}
      {asset?.attribution && (
        <span className="absolute right-1.5 bottom-1.5 max-w-[70%] truncate rounded bg-black/55 px-1.5 py-0.5 text-[10px] text-white/90">
          {asset.attribution}
        </span>
      )}
    </div>
  );
}

// --- People and status ---------------------------------------------------------

export function Avatar({ name, size = "md" }: { name: string; size?: "sm" | "md" | "lg" }) {
  const dimension = size === "lg" ? "size-16 text-[1.25em]" : size === "sm" ? "size-7 text-[0.72em]" : "size-9 text-[0.82em]";
  return (
    <span
      aria-hidden
      className={cn(
        "grid shrink-0 place-items-center rounded-full bg-[var(--g-primary-soft)] font-semibold text-g-primary",
        dimension,
      )}
    >
      {initials(name)}
    </span>
  );
}

const POSITIVE = /^(hired|active|open|paid|approved|accepted|done|completed?|confirmed|live|won|published|delivered|healthy|resolved|in stock|available|verified|success)/i;
const CAUTION = /^(pending|paused|offer|review|in review|draft|scheduled|waiting|on hold|trial|low|processing|in progress|screening)/i;
const NEGATIVE = /^(rejected|closed|failed|overdue|declined|cancell?ed|lost|blocked|critical|churned|out of stock|expired|error)/i;

/** Colour of a status value, from what the word usually means. Unknown words stay neutral. */
export function statusTone(value: string): string {
  if (POSITIVE.test(value)) return "var(--g-success)";
  if (CAUTION.test(value)) return "var(--g-warning)";
  if (NEGATIVE.test(value)) return "var(--g-destructive)";
  return "var(--g-primary)";
}

export function StatusPill({ label, tone }: { label: string; tone?: string }) {
  return (
    <span
      style={{ "--tone": tone ?? statusTone(label) } as CSSProperties}
      className="inline-flex w-fit shrink-0 items-center gap-1.5 rounded-full bg-[color-mix(in_srgb,var(--tone)_13%,transparent)] px-2.5 py-0.5 text-[0.8em] font-medium whitespace-nowrap text-[var(--tone)]"
    >
      <span aria-hidden className="size-1.5 rounded-full bg-[var(--tone)]" />
      {label}
    </span>
  );
}

/** Surface class plus the per-component surface override, if one was asked for. */
export function surfaceProps(style: ComponentStyle | undefined): { className: string; "data-surface"?: string } {
  return { className: "g-card", "data-surface": style?.surface };
}
