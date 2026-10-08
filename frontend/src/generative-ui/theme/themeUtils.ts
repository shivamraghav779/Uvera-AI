/** Colour maths for the theme engine. Inputs are always validated `#RRGGBB` values. */

export type Rgb = readonly [number, number, number];

export function hexToRgb(hex: string): Rgb {
  return [1, 3, 5].map((start) => parseInt(hex.slice(start, start + 2), 16)) as unknown as Rgb;
}

export function rgbToHex([red, green, blue]: Rgb): string {
  return `#${[red, green, blue]
    .map((channel) => Math.round(channel).toString(16).padStart(2, "0"))
    .join("")}`.toUpperCase();
}

function linear(channel: number): number {
  const scaled = channel / 255;
  return scaled <= 0.03928 ? scaled / 12.92 : ((scaled + 0.055) / 1.055) ** 2.4;
}

export function relativeLuminance(hex: string): number {
  const [red, green, blue] = hexToRgb(hex);
  return 0.2126 * linear(red) + 0.7152 * linear(green) + 0.0722 * linear(blue);
}

/** WCAG 2 contrast ratio between two colours (1 to 21). */
export function contrastRatio(first: string, second: string): number {
  const [lighter, darker] = [relativeLuminance(first), relativeLuminance(second)].sort(
    (a, b) => b - a,
  ) as [number, number];
  return (lighter + 0.05) / (darker + 0.05);
}

/** Blend `amount` (0..1) of `other` into `base`. */
export function mix(base: string, other: string, amount: number): string {
  const from = hexToRgb(base);
  const to = hexToRgb(other);
  return rgbToHex(from.map((channel, i) => channel + (to[i]! - channel) * amount) as unknown as Rgb);
}

/** Black or white, whichever is more readable on `background`. */
export function readableOn(background: string): string {
  return contrastRatio("#FFFFFF", background) >= contrastRatio("#0A0A0A", background)
    ? "#FFFFFF"
    : "#0A0A0A";
}
