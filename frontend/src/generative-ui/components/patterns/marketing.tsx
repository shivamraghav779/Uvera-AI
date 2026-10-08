/**
 * Marketing and content patterns: the sections a landing page, a pricing page
 * or an editorial site is composed of. Each renders one schema node in one of
 * its variants. Content, images (by asset id) and actions come from the node;
 * the look comes from the theme.
 */
import { Check, Minus, Quote, Star } from "lucide-react";
import type { CSSProperties } from "react";

import { cn } from "@/utils/cn";

import { hasEffect } from "../../registry/effectRegistry";
import type { ComponentOf } from "../../schema/types";

import {
  ActionButtons,
  AssetImage,
  Avatar,
  Band,
  Icon,
  IconTile,
  reveal,
  SectionHeader,
  surfaceProps,
  useAction,
} from "./shared";

const cols = (count: number): CSSProperties => ({ "--cols": count }) as CSSProperties;

// --- Hero ------------------------------------------------------------------------

function HeroStats({ stats, inverse = false }: { stats: ComponentOf<"hero">["stats"]; inverse?: boolean }) {
  if (stats.length === 0) return null;
  return (
    <dl className={cn("mt-2 flex flex-wrap gap-x-10 gap-y-4", inverse && "text-white")}>
      {stats.map((stat) => (
        <div key={stat.label}>
          <dd className="g-heading text-[1.7em] leading-none tabular-nums">{stat.value}</dd>
          <dt className={cn("mt-1 text-[0.85em]", inverse ? "text-white/75" : "text-g-muted-fg")}>{stat.label}</dt>
        </div>
      ))}
    </dl>
  );
}

function HeroBadges({ badges }: { badges: readonly string[] }) {
  if (badges.length === 0) return null;
  return (
    <ul className="flex flex-wrap gap-x-5 gap-y-1.5 text-[0.88em] text-g-muted-fg">
      {badges.map((badge) => (
        <li key={badge} className="flex items-center gap-1.5">
          <Check size={14} aria-hidden className="text-g-success" />
          {badge}
        </li>
      ))}
    </ul>
  );
}

/** A screenshot-like frame: the image inside a window with three dots. */
function WindowFrame({ assetId, alt, className }: { assetId?: string; alt: string; className?: string }) {
  return (
    <div className={cn("g-card g-glow-target overflow-hidden p-0", className)}>
      <div className="flex h-9 items-center gap-1.5 border-b border-g-border bg-g-muted px-3">
        {[0, 1, 2].map((dot) => (
          <span key={dot} aria-hidden className="size-2.5 rounded-full bg-[color-mix(in_srgb,var(--g-fg)_18%,transparent)]" />
        ))}
      </div>
      <AssetImage assetId={assetId} alt={alt} aspect="video" eager />
    </div>
  );
}

export function Hero({ node }: { node: ComponentOf<"hero"> }) {
  const { variant, eyebrow, title, subtitle, actions, image, stats, badges, style } = node;
  const parallax = hasEffect(style?.effects, "parallax");

  if (variant === "immersive") {
    return (
      <Band
        style={style}
        className="grid min-h-[clamp(440px,58cqw,760px)] items-end overflow-hidden !py-0 text-white"
        backdrop={
          <div aria-hidden={false} className="absolute inset-0 -z-10">
            <AssetImage assetId={image} alt={title} className="!absolute inset-0 h-full" parallax={parallax} eager />
            <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/30 to-black/10" />
          </div>
        }
      >
        <div className="flex max-w-3xl flex-col gap-5 py-[clamp(40px,7cqw,96px)]">
          {eyebrow && <p {...reveal(0)} className="g-eyebrow !text-white/85">{eyebrow}</p>}
          <h1 {...reveal(1)} className="g-display">{title}</h1>
          {subtitle && <p {...reveal(2)} className="g-lead !text-white/85">{subtitle}</p>}
          <div {...reveal(3)}>
            <ActionButtons actions={actions} large />
          </div>
          <HeroStats stats={stats} inverse />
        </div>
      </Band>
    );
  }

  if (variant === "editorial") {
    return (
      <Band style={style}>
        <div className="flex flex-col gap-[clamp(28px,4cqw,64px)]">
          <div className="g-split items-end" data-ratio="8-4">
            <div className="flex flex-col gap-5">
              {eyebrow && <p {...reveal(0)} className="g-eyebrow !text-g-muted-fg">{eyebrow}</p>}
              <h1 {...reveal(1)} className="g-display !text-[calc(clamp(2.4rem,5.4cqw+1rem,5rem)*var(--g-heading-scale)*0.72)]">
                {title}
              </h1>
            </div>
            <div {...reveal(2)} className="flex flex-col gap-5 pb-2">
              {subtitle && <p className="g-lead">{subtitle}</p>}
              <ActionButtons actions={actions} />
            </div>
          </div>
          <div {...reveal(3)}>
            <AssetImage assetId={image} alt={title} aspect="ultrawide" className="rounded-g" parallax={parallax} eager />
          </div>
          <HeroStats stats={stats} />
        </div>
      </Band>
    );
  }

  if (variant === "centered" || variant === "product") {
    return (
      <Band style={style}>
        <div className="mx-auto flex max-w-4xl flex-col items-center gap-6 text-center">
          {eyebrow && (
            <p {...reveal(0)} className="g-eyebrow rounded-full border border-g-border bg-g-surface px-3 py-1 !tracking-[0.08em]">
              {eyebrow}
            </p>
          )}
          <h1 {...reveal(1)} className="g-display">{title}</h1>
          {subtitle && <p {...reveal(2)} className="g-lead max-w-2xl">{subtitle}</p>}
          <div {...reveal(3)}>
            <ActionButtons actions={actions} large className="justify-center" />
          </div>
          <HeroBadges badges={badges} />
        </div>
        {(variant === "product" || image) && (
          <div {...reveal(4)} className="mx-auto mt-[clamp(32px,5cqw,72px)] max-w-5xl">
            {variant === "product" ? (
              <WindowFrame assetId={image} alt={title} />
            ) : (
              <AssetImage assetId={image} alt={title} aspect="video" className="g-card g-glow-target rounded-g" eager />
            )}
          </div>
        )}
        {stats.length > 0 && (
          <div className="mt-10 flex justify-center">
            <HeroStats stats={stats} />
          </div>
        )}
      </Band>
    );
  }

  return (
    <Band style={style}>
      <div className="g-split">
        <div className="flex flex-col gap-6">
          {eyebrow && <p {...reveal(0)} className="g-eyebrow">{eyebrow}</p>}
          <h1 {...reveal(1)} className="g-display">{title}</h1>
          {subtitle && <p {...reveal(2)} className="g-lead">{subtitle}</p>}
          <div {...reveal(3)}>
            <ActionButtons actions={actions} large />
          </div>
          <HeroBadges badges={badges} />
          <HeroStats stats={stats} />
        </div>
        <div {...reveal(2)} data-order-narrow="last">
          <AssetImage assetId={image} alt={title} aspect="photo" className="g-card g-glow-target rounded-g" eager />
        </div>
      </div>
    </Band>
  );
}

// --- Feature grid ------------------------------------------------------------------

export function FeatureGrid({ node }: { node: ComponentOf<"feature_grid"> }) {
  const { variant, eyebrow, title, subtitle, columns, items, style } = node;
  const align = style?.align ?? (variant === "alternating" ? "left" : "center");
  const header = <SectionHeader eyebrow={eyebrow} title={title} subtitle={subtitle} align={align} />;

  if (variant === "alternating") {
    return (
      <Band style={style}>
        {header}
        <div className="flex flex-col gap-[clamp(40px,6cqw,96px)]">
          {items.map((item, index) => (
            <article key={index} {...reveal(index + 1)} className="g-split" data-ratio="even">
              <div className={cn("flex flex-col gap-4", index % 2 === 1 && "lg:order-2")} style={{ order: index % 2 }}>
                <span className="g-heading text-[0.95em] text-g-primary tabular-nums">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <h3 className="g-h2 !text-[calc(1.55em*var(--g-heading-scale))]">{item.title}</h3>
                {item.description && <p className="g-lead">{item.description}</p>}
              </div>
              <AssetImage assetId={item.image} alt={item.title} aspect="photo" className="g-card rounded-g" />
            </article>
          ))}
        </div>
      </Band>
    );
  }

  if (variant === "list") {
    return (
      <Band style={style}>
        {header}
        <dl className="g-cols gap-x-12 gap-y-7" style={cols(Math.min(columns, 2))}>
          {items.map((item, index) => (
            <div key={index} {...reveal(index + 1)} className="flex gap-3.5">
              {item.icon ? (
                <Icon name={item.icon} size={20} className="mt-0.5 shrink-0 text-g-primary" />
              ) : (
                <Check size={18} aria-hidden className="mt-1 shrink-0 text-g-primary" />
              )}
              <div>
                <dt className="font-semibold">{item.title}</dt>
                {item.description && <dd className="mt-1 text-g-muted-fg">{item.description}</dd>}
              </div>
            </div>
          ))}
        </dl>
      </Band>
    );
  }

  const bento = variant === "bento";
  return (
    <Band style={style}>
      {header}
      <div className={cn("g-cols", bento && "g-bento")} style={cols(columns)}>
        {items.map((item, index) => {
          const wide = bento && item.span === 2;
          return (
            <article
              key={index}
              {...reveal(index + 1)}
              data-wide={wide || undefined}
              {...surfaceProps(style)}
              className={cn(
                "g-card g-lift flex flex-col gap-3 overflow-hidden p-[calc(var(--g-pad)*1.35)] text-left",
                wide && item.image && "gap-5",
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <IconTile name={item.icon} />
                {item.badge && (
                  <span className="rounded-full bg-g-muted px-2 py-0.5 text-[0.76em] font-medium text-g-muted-fg">
                    {item.badge}
                  </span>
                )}
              </div>
              <h3 className={cn("g-h3 font-semibold", wide && "!text-[1.35em]")}>{item.title}</h3>
              {item.description && <p className="text-g-muted-fg">{item.description}</p>}
              {item.image && (
                <AssetImage
                  assetId={item.image}
                  alt={item.title}
                  aspect={wide ? "wide" : "photo"}
                  className="-mx-[calc(var(--g-pad)*1.35)] mt-auto -mb-[calc(var(--g-pad)*1.35)]"
                />
              )}
            </article>
          );
        })}
      </div>
    </Band>
  );
}

// --- Social proof ------------------------------------------------------------------

function Wordmark({ name }: { name: string }) {
  return (
    <span className="g-heading text-[1.25em] whitespace-nowrap opacity-55 grayscale transition-opacity duration-[var(--g-duration-fast)] hover:opacity-90">
      {name}
    </span>
  );
}

export function LogoCloud({ node }: { node: ComponentOf<"logo_cloud"> }) {
  const marquee = node.variant === "marquee" || hasEffect(node.style?.effects, "marquee");
  return (
    <Band style={{ ...node.style, density: node.style?.density ?? "compact" }}>
      {node.title && (
        <p className="mb-6 text-center text-[0.86em] font-medium tracking-wide text-g-muted-fg uppercase">{node.title}</p>
      )}
      {marquee ? (
        <div className="g-marquee" aria-label={node.title ?? "Customers"}>
          <ul className="g-marquee-track items-center">
            {[...node.logos, ...node.logos].map((logo, index) => (
              <li key={index} aria-hidden={index >= node.logos.length || undefined}>
                <Wordmark name={logo} />
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <ul className="flex flex-wrap items-center justify-center gap-x-12 gap-y-5">
          {node.logos.map((logo) => (
            <li key={logo}>
              <Wordmark name={logo} />
            </li>
          ))}
        </ul>
      )}
    </Band>
  );
}

function Rating({ value }: { value?: number }) {
  if (!value) return null;
  return (
    <p className="flex gap-0.5 text-g-warning" role="img" aria-label={`${value} out of 5`}>
      {[1, 2, 3, 4, 5].map((star) => (
        <Star key={star} size={14} aria-hidden fill={star <= value ? "currentColor" : "none"} />
      ))}
    </p>
  );
}

type TestimonialItem = ComponentOf<"testimonials">["items"][number];

function Attribution({ item }: { item: TestimonialItem }) {
  const detail = [item.role, item.company].filter(Boolean).join(", ");
  return (
    <footer className="flex items-center gap-3">
      {item.avatar ? (
        <AssetImage assetId={item.avatar} alt={item.author} aspect="square" className="size-10 rounded-full" />
      ) : (
        <Avatar name={item.author} />
      )}
      <div className="text-left">
        <p className="font-semibold">{item.author}</p>
        {detail && <p className="text-[0.88em] text-g-muted-fg">{detail}</p>}
      </div>
    </footer>
  );
}

function QuoteCard({ item, className }: { item: TestimonialItem; className?: string }) {
  return (
    <figure className={cn("g-card flex flex-col gap-4 p-[calc(var(--g-pad)*1.35)]", className)}>
      <Rating value={item.rating} />
      <blockquote className="flex-1 text-[1.02em] leading-relaxed">“{item.quote}”</blockquote>
      <figcaption>
        <Attribution item={item} />
      </figcaption>
    </figure>
  );
}

export function Testimonials({ node }: { node: ComponentOf<"testimonials"> }) {
  const { variant, eyebrow, title, items, style } = node;
  if (variant === "spotlight") {
    const [first] = items;
    return (
      <Band style={style} tone="muted">
        <figure {...reveal(0)} className="mx-auto flex max-w-4xl flex-col items-center gap-7 text-center">
          <Quote size={34} aria-hidden className="text-g-primary" />
          <blockquote className="g-heading text-[calc(clamp(1.3rem,1.6cqw+1rem,2rem)*var(--g-heading-scale))] leading-snug">
            “{first!.quote}”
          </blockquote>
          <figcaption>
            <Attribution item={first!} />
          </figcaption>
        </figure>
      </Band>
    );
  }
  const header = <SectionHeader eyebrow={eyebrow} title={title} align={style?.align ?? "center"} />;
  if (variant === "marquee") {
    return (
      <Band style={style}>
        {header}
        <div className="g-marquee" style={{ "--marquee-gap": "var(--g-gap)", "--marquee-duration": "60s" } as CSSProperties}>
          <div className="g-marquee-track">
            {[...items, ...items].map((item, index) => (
              <div key={index} aria-hidden={index >= items.length || undefined} className="w-[340px]">
                <QuoteCard item={item} className="h-full" />
              </div>
            ))}
          </div>
        </div>
      </Band>
    );
  }
  return (
    <Band style={style}>
      {header}
      <div className="g-cols" style={cols(Math.min(items.length, 3))}>
        {items.map((item, index) => (
          <div key={index} {...reveal(index + 1)}>
            <QuoteCard item={item} className="h-full" />
          </div>
        ))}
      </div>
    </Band>
  );
}

// --- Stats (marketing presentation; the data-bound variants are in records.tsx) ------

// --- Pricing -----------------------------------------------------------------------

export function Pricing({ node }: { node: ComponentOf<"pricing"> }) {
  const { eyebrow, title, subtitle, plans, style } = node;
  return (
    <Band style={style}>
      <SectionHeader eyebrow={eyebrow} title={title} subtitle={subtitle} align={style?.align ?? "center"} />
      <div className="g-cols items-stretch" style={cols(plans.length)}>
        {plans.map((plan, index) => (
          <article
            key={plan.name}
            {...reveal(index + 1)}
            data-surface={plan.highlighted ? "featured" : undefined}
            className={cn(
              "g-card g-lift relative flex flex-col gap-5 p-[calc(var(--g-pad)*1.5)]",
              plan.highlighted && "border-g-primary shadow-[0_18px_50px_-18px_color-mix(in_srgb,var(--g-primary)_60%,transparent)]",
            )}
          >
            {plan.badge && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-g-primary px-3 py-0.5 text-[0.76em] font-semibold whitespace-nowrap text-g-primary-fg">
                {plan.badge}
              </span>
            )}
            <div>
              <h3 className="g-h3 font-semibold">{plan.name}</h3>
              {plan.description && <p className="mt-1 text-[0.92em] text-g-muted-fg">{plan.description}</p>}
            </div>
            <p className="flex items-baseline gap-2">
              <span className="g-heading text-[2.6em] leading-none tabular-nums">{plan.price}</span>
              {plan.period && <span className="text-[0.9em] text-g-muted-fg">{plan.period}</span>}
            </p>
            <ul className="flex flex-1 flex-col gap-2.5">
              {plan.features.map((feature) => (
                <li key={feature} className="flex items-start gap-2.5 text-[0.95em]">
                  <Check size={16} aria-hidden className="mt-0.5 shrink-0 text-g-primary" />
                  {feature}
                </li>
              ))}
            </ul>
            {plan.action && (
              <ActionButtons
                actions={[{ ...plan.action, variant: plan.highlighted ? plan.action.variant : "secondary" }]}
                className="[&>button]:w-full"
              />
            )}
          </article>
        ))}
      </div>
    </Band>
  );
}

export function Comparison({ node }: { node: ComponentOf<"comparison"> }) {
  const highlighted = node.highlight_column;
  return (
    <Band style={node.style}>
      <SectionHeader title={node.title} align={node.style?.align ?? "center"} />
      <div className="g-card overflow-x-auto">
        <table className="w-full min-w-[520px] border-collapse text-[0.95em]">
          <thead>
            <tr>
              <th scope="col" className="p-[var(--g-pad)] text-left font-medium text-g-muted-fg">
                <span className="sr-only">Feature</span>
              </th>
              {node.columns.map((column, index) => (
                <th
                  key={column}
                  scope="col"
                  className={cn("g-heading p-[var(--g-pad)] text-center", index === highlighted && "bg-[var(--g-primary-soft)] text-g-primary")}
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {node.rows.map((row) => (
              <tr key={row.label} className="border-t border-g-border">
                <th scope="row" className="p-[var(--g-pad)] text-left font-medium">
                  {row.label}
                </th>
                {node.columns.map((column, index) => {
                  const value = row.values[index];
                  return (
                    <td key={column} className={cn("p-[var(--g-pad)] text-center", index === highlighted && "bg-[var(--g-primary-soft)]")}>
                      {value === true ? (
                        <Check size={17} role="img" aria-label="Included" className="mx-auto text-g-success" />
                      ) : value === false || value === undefined ? (
                        <Minus size={17} role="img" aria-label="Not included" className="mx-auto text-g-muted-fg" />
                      ) : (
                        value
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Band>
  );
}

// --- Call to action ----------------------------------------------------------------

export function Cta({ node }: { node: ComponentOf<"cta"> }) {
  const { variant, eyebrow, title, subtitle, actions, image, style } = node;
  const inverse = actions.map((action, index) => ({
    ...action,
    variant: index === 0 ? ("secondary" as const) : ("glass" as const),
  }));

  if (variant === "split") {
    return (
      <Band style={style}>
        <div {...reveal(0)} className="g-card g-split overflow-hidden !p-0" data-ratio="even">
          <div className="flex flex-col gap-5 p-[clamp(24px,4cqw,56px)]">
            {eyebrow && <p className="g-eyebrow">{eyebrow}</p>}
            <h2 className="g-h2">{title}</h2>
            {subtitle && <p className="g-lead">{subtitle}</p>}
            <ActionButtons actions={actions} large />
          </div>
          <AssetImage assetId={image} alt={title} aspect="photo" className="h-full min-h-[240px]" />
        </div>
      </Band>
    );
  }

  const banner = variant === "banner";
  return (
    <Band style={style}>
      <div
        {...reveal(0)}
        className={cn(
          "relative isolate overflow-hidden rounded-[calc(var(--g-radius)*1.6)] bg-[image:var(--g-accent-fill)] bg-g-primary text-g-primary-fg",
          banner
            ? "flex flex-wrap items-center justify-between gap-5 px-[clamp(20px,3cqw,40px)] py-[clamp(18px,2.4cqw,30px)]"
            : "flex flex-col items-center gap-5 px-[clamp(24px,5cqw,80px)] py-[clamp(40px,6cqw,88px)] text-center",
        )}
      >
        <div className={cn("flex flex-col gap-2", !banner && "items-center gap-4")}>
          {eyebrow && <p className="g-eyebrow !text-current opacity-80">{eyebrow}</p>}
          <h2 className={banner ? "g-h3 font-semibold !text-[1.3em]" : "g-h2 max-w-3xl"}>{title}</h2>
          {subtitle && <p className={cn("max-w-2xl opacity-85", !banner && "text-[1.08em]")}>{subtitle}</p>}
        </div>
        <ActionButtons actions={inverse} large={!banner} className={banner ? undefined : "justify-center"} />
      </div>
    </Band>
  );
}

// --- Media, images and galleries ---------------------------------------------------

export function Image({ node }: { node: ComponentOf<"image"> }) {
  return (
    <figure className="flex flex-col gap-2">
      <AssetImage
        assetId={node.image}
        alt={node.caption}
        aspect={node.aspect}
        fit={node.fit}
        className={node.rounded ? "rounded-g" : undefined}
        parallax={hasEffect(node.style?.effects, "parallax")}
      />
      {node.caption && <figcaption className="text-[0.86em] text-g-muted-fg">{node.caption}</figcaption>}
    </figure>
  );
}

export function Media({ node }: { node: ComponentOf<"media"> }) {
  const { variant, eyebrow, title, body, bullets, image, actions, style } = node;
  const copy = (
    <div {...reveal(0)} className="flex flex-col gap-5">
      {eyebrow && <p className="g-eyebrow">{eyebrow}</p>}
      <h2 className="g-h2">{title}</h2>
      {body && <p className="g-lead whitespace-pre-line">{body}</p>}
      {bullets.length > 0 && (
        <ul className="flex flex-col gap-2.5">
          {bullets.map((bullet) => (
            <li key={bullet} className="flex items-start gap-2.5">
              <Check size={17} aria-hidden className="mt-0.5 shrink-0 text-g-primary" />
              {bullet}
            </li>
          ))}
        </ul>
      )}
      <ActionButtons actions={actions} />
    </div>
  );

  if (variant === "overlay") {
    return (
      <Band
        style={style}
        className="grid min-h-[clamp(320px,40cqw,560px)] items-center overflow-hidden text-white"
        backdrop={
          <div className="absolute inset-0 -z-10">
            <AssetImage assetId={image} alt={title} className="!absolute inset-0 h-full" parallax={hasEffect(style?.effects, "parallax")} />
            <div className="absolute inset-0 bg-black/50" />
          </div>
        }
      >
        <div className="max-w-2xl [&_.g-eyebrow]:!text-white/85 [&_.g-lead]:!text-white/85">{copy}</div>
      </Band>
    );
  }

  const visual =
    variant === "framed" ? (
      <WindowFrame assetId={image} alt={title} />
    ) : (
      <AssetImage assetId={image} alt={title} aspect="photo" className="g-card g-glow-target rounded-g" />
    );
  const imageFirst = variant === "image_left";
  return (
    <Band style={style}>
      <div className="g-split" data-ratio={imageFirst ? "5-7" : variant === "framed" ? "even" : undefined}>
        {imageFirst && <div {...reveal(1)}>{visual}</div>}
        {copy}
        {!imageFirst && <div {...reveal(1)}>{visual}</div>}
      </div>
    </Band>
  );
}

type GalleryItem = ComponentOf<"gallery">["items"][number];

function GalleryTile({ item, aspect, large = false }: { item: GalleryItem; aspect: "photo" | "portrait" | "video" | "square"; large?: boolean }) {
  const run = useAction();
  const body = (
    <>
      <div className="relative overflow-hidden rounded-g">
        <AssetImage
          assetId={item.image}
          alt={item.title}
          aspect={aspect}
          className="transition-transform duration-[var(--g-duration-slow)] ease-[var(--g-ease-standard)] group-hover/tile:scale-[1.03]"
        />
        {item.badge && (
          <span className="absolute top-3 left-3 rounded-full bg-g-surface/90 px-2.5 py-0.5 text-[0.76em] font-medium text-g-fg backdrop-blur">
            {item.badge}
          </span>
        )}
      </div>
      <div className="mt-3 flex flex-col gap-1 text-left">
        <h3 className={cn("g-h3 font-semibold", large && "!text-[1.5em]")}>{item.title}</h3>
        {item.subtitle && <p className="text-g-muted-fg">{item.subtitle}</p>}
        {item.description && <p className="text-[0.95em] text-g-muted-fg">{item.description}</p>}
        {item.meta.length > 0 && (
          <dl className="mt-1 flex flex-wrap gap-x-6 gap-y-1 text-[0.8em]">
            {item.meta.map((entry) => (
              <div key={entry.label} className="flex gap-1.5">
                <dt className="tracking-wide text-g-muted-fg uppercase">{entry.label}</dt>
                <dd className="font-medium">{entry.value}</dd>
              </div>
            ))}
          </dl>
        )}
      </div>
    </>
  );
  if (!item.action) return <article className="group/tile">{body}</article>;
  return (
    <button type="button" onClick={() => void run(item.action)} className="group/tile block w-full text-left">
      {body}
    </button>
  );
}

export function Gallery({ node }: { node: ComponentOf<"gallery"> }) {
  const { variant, eyebrow, title, subtitle, columns, items, style } = node;
  const header = <SectionHeader eyebrow={eyebrow} title={title} subtitle={subtitle} align={style?.align} />;
  if (variant === "editorial") {
    return (
      <Band style={style}>
        {header}
        <div className="g-editorial">
          {items.map((item, index) => (
            <div key={index} {...reveal(index + 1)}>
              <GalleryTile item={item} aspect={index % 3 === 0 ? "video" : "photo"} large={index % 3 === 0} />
            </div>
          ))}
        </div>
      </Band>
    );
  }
  if (variant === "masonry") {
    return (
      <Band style={style}>
        {header}
        <div className="g-masonry" style={cols(columns)}>
          {items.map((item, index) => (
            <div key={index}>
              <GalleryTile item={item} aspect={(["portrait", "photo", "square"] as const)[index % 3]!} />
            </div>
          ))}
        </div>
      </Band>
    );
  }
  if (variant === "carousel") {
    return (
      <Band style={style}>
        {header}
        <div className="g-scroll-x" tabIndex={0} role="group" aria-label={title ?? "Gallery"}>
          {items.map((item, index) => (
            <div key={index} className="w-[min(78cqw,340px)]">
              <GalleryTile item={item} aspect="portrait" />
            </div>
          ))}
        </div>
      </Band>
    );
  }
  return (
    <Band style={style}>
      {header}
      <div className="g-cols gap-y-[calc(var(--g-gap)*1.6)]" style={cols(columns)}>
        {items.map((item, index) => (
          <div key={index} {...reveal(index + 1)}>
            <GalleryTile item={item} aspect="photo" />
          </div>
        ))}
      </div>
    </Band>
  );
}

// --- Explaining --------------------------------------------------------------------

export function Steps({ node }: { node: ComponentOf<"steps"> }) {
  const { variant, eyebrow, title, items, style } = node;
  const header = <SectionHeader eyebrow={eyebrow} title={title} align={style?.align ?? (variant === "timeline" ? "left" : "center")} />;
  if (variant === "timeline") {
    return (
      <Band style={style}>
        {header}
        <ol className="relative ml-4 flex max-w-3xl flex-col gap-9 border-l border-g-border pl-9">
          {items.map((item, index) => (
            <li key={index} {...reveal(index + 1)} className="relative">
              <span className="g-heading absolute top-0 -left-[52px] grid size-8 place-items-center rounded-full border border-g-border bg-g-surface text-[0.85em] text-g-primary">
                {index + 1}
              </span>
              <h3 className="g-h3 font-semibold">{item.title}</h3>
              {item.description && <p className="mt-1.5 text-g-muted-fg">{item.description}</p>}
            </li>
          ))}
        </ol>
      </Band>
    );
  }
  const cards = variant === "cards";
  return (
    <Band style={style}>
      {header}
      <ol className="g-cols gap-y-10" style={cols(Math.min(items.length, 4))}>
        {items.map((item, index) => (
          <li
            key={index}
            {...reveal(index + 1)}
            className={cn("flex flex-col gap-3 text-left", cards && "g-card g-lift p-[calc(var(--g-pad)*1.35)]")}
          >
            {item.icon && cards ? (
              <IconTile name={item.icon} />
            ) : (
              <span className="g-heading text-[2.1em] leading-none text-g-primary tabular-nums">
                {String(index + 1).padStart(2, "0")}
              </span>
            )}
            <h3 className="g-h3 font-semibold">{item.title}</h3>
            {item.description && <p className="text-g-muted-fg">{item.description}</p>}
          </li>
        ))}
      </ol>
    </Band>
  );
}

export function Faq({ node }: { node: ComponentOf<"faq"> }) {
  return (
    <Band style={node.style}>
      <SectionHeader title={node.title} align={node.style?.align ?? "center"} />
      <div className="mx-auto flex max-w-3xl flex-col divide-y divide-g-border border-y border-g-border">
        {node.items.map((item) => (
          <details key={item.question} className="group/faq">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-4 font-semibold [&::-webkit-details-marker]:hidden">
              {item.question}
              <span aria-hidden className="text-[1.3em] leading-none text-g-muted-fg transition-transform duration-[var(--g-duration-fast)] group-open/faq:rotate-45">
                +
              </span>
            </summary>
            <p className="pb-5 whitespace-pre-line text-g-muted-fg">{item.answer}</p>
          </details>
        ))}
      </div>
    </Band>
  );
}

export function Footer({ node }: { node: ComponentOf<"footer"> }) {
  const run = useAction();
  return (
    <Band style={{ ...node.style, density: node.style?.density ?? "compact" }} className="border-t border-g-border">
      <div className="flex flex-wrap justify-between gap-x-16 gap-y-10">
        <div className="max-w-xs">
          {node.brand && <p className="g-heading text-[1.25em]">{node.brand}</p>}
          {node.tagline && <p className="mt-2 text-g-muted-fg">{node.tagline}</p>}
        </div>
        <nav aria-label="Footer" className="flex flex-wrap gap-x-16 gap-y-8">
          {node.columns.map((column) => (
            <div key={column.title}>
              <p className="mb-3 text-[0.82em] font-semibold tracking-wide text-g-muted-fg uppercase">{column.title}</p>
              <ul className="flex flex-col gap-2">
                {column.links.map((link) => (
                  <li key={link.label}>
                    {link.action ? (
                      <button type="button" onClick={() => void run(link.action)} className="text-left hover:text-g-primary hover:underline">
                        {link.label}
                      </button>
                    ) : (
                      <span className="text-g-muted-fg">{link.label}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </div>
      {node.note && <p className="mt-10 border-t border-g-border pt-5 text-[0.85em] text-g-muted-fg">{node.note}</p>}
    </Band>
  );
}
