/**
 * Effects this build implements, by token name.
 *
 * `style.effects` in a document is a list of these names. The registry says
 * which a component may show: only implemented ones, and none at all when the
 * theme's motion is off for effects that are pure motion.
 */
import type { EFFECTS } from "../schema/validators";

export type EffectName = (typeof EFFECTS)[number];

interface EffectDefinition {
  /** Drawn with CSS alone (a class on the band), or needs a hook as well. */
  kind: "decor" | "motion";
  label: string;
}

const REGISTRY: Record<EffectName, EffectDefinition> = {
  gradient_mesh: { kind: "decor", label: "Gradient mesh" },
  animated_gradient: { kind: "motion", label: "Animated gradient" },
  glow: { kind: "decor", label: "Glow" },
  glass: { kind: "decor", label: "Glass" },
  noise: { kind: "decor", label: "Noise" },
  grid: { kind: "decor", label: "Grid" },
  spotlight: { kind: "motion", label: "Spotlight" },
  reveal: { kind: "motion", label: "Reveal" },
  hover_lift: { kind: "motion", label: "Hover lift" },
  parallax: { kind: "motion", label: "Parallax" },
  marquee: { kind: "motion", label: "Marquee" },
  counter: { kind: "motion", label: "Animated counter" },
};

export function supportedEffects(): EffectName[] {
  return Object.keys(REGISTRY) as EffectName[];
}

export function effectLabel(effect: EffectName): string {
  return REGISTRY[effect].label;
}

/** CSS classes for the effects a component requested. Unknown names are ignored. */
export function effectClasses(effects: readonly string[] | undefined): string {
  return (effects ?? [])
    .filter((effect): effect is EffectName => effect in REGISTRY)
    .map((effect) => `g-fx-${effect}`)
    .join(" ");
}

export function hasEffect(effects: readonly string[] | undefined, effect: EffectName): boolean {
  return effects?.includes(effect) ?? false;
}
