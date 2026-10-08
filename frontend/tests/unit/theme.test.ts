import { themeToCssVariables, TONE_VARIABLE } from "@/generative-ui/theme/themeTokens";
import { contrastRatio, mix, readableOn } from "@/generative-ui/theme/themeUtils";

import { fixtures } from "../fixtures";

describe("theme utilities", () => {
  it("computes WCAG contrast", () => {
    expect(contrastRatio("#000000", "#FFFFFF")).toBeCloseTo(21, 5);
    expect(contrastRatio("#FFFFFF", "#FFFFFF")).toBe(1);
    expect(contrastRatio("#0F172A", "#FFFFFF")).toBeGreaterThan(4.5);
  });

  it("picks readable text for a background", () => {
    expect(readableOn("#18181B")).toBe("#FFFFFF");
    expect(readableOn("#FBBF24")).toBe("#0A0A0A");
  });

  it("mixes colours", () => {
    expect(mix("#000000", "#FFFFFF", 0.5)).toBe("#808080");
    expect(mix("#2563EB", "#FFFFFF", 0)).toBe("#2563EB");
  });
});

describe("theme tokens", () => {
  it("turns tokens into CSS variables", () => {
    const variables = themeToCssVariables(fixtures.default_theme);

    expect(variables["--g-primary"]).toBe("#2563EB");
    expect(variables["--g-primary-fg"]).toBe("#FFFFFF");
    expect(variables["--g-radius"]).toBe("8px");
    expect(variables["--g-shadow"]).toBe("none");
    expect(variables["--g-font-size"]).toBe("14px");
  });

  it.each(fixtures.theme_presets)("keeps derived text readable in $name", ({ theme }) => {
    const variables = themeToCssVariables({ ...fixtures.default_theme, ...theme });

    expect(contrastRatio(variables["--g-primary-fg"]!, variables["--g-primary"]!)).toBeGreaterThanOrEqual(4.5);
    expect(contrastRatio(variables["--g-muted-fg"]!, variables["--g-surface"]!)).toBeGreaterThanOrEqual(3);
  });

  it("only ever emits values from fixed tables or validated colours", () => {
    const values = Object.values(themeToCssVariables(fixtures.default_theme));

    for (const value of values) {
      expect(value).not.toMatch(/url\(|expression|javascript|;|\{|\}/i);
    }
  });

  it("maps every style tone to a theme variable", () => {
    expect(Object.values(TONE_VARIABLE).every((value) => /^var\(--g-[a-z-]+\)$/.test(value))).toBe(true);
  });
});
