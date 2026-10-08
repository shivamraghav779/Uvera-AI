# Design reference — "Precision Canvas"

The look of the application itself (the editor around the canvas). It comes from the
Stitch design system export of the same name; this file records the parts the frontend
implements and where they live. Generated UIs do not use these tokens: they have their
own themes (see "Palettes for generated UIs" below).

## Principles

- **Quiet chrome.** Surfaces step back so the generated UI is the focal point.
- **Instrument precision.** Hairline borders, tight alignment, dense controls; in the
  spirit of Figma and Linear, not a chat feed.
- **One accent.** Neutral surfaces everywhere; indigo only for selection, focus and
  committing work.

## Tokens (`frontend/src/index.css`, `--app-*`)

| Role | Light | Dark |
| --- | --- | --- |
| Page / shell background | `#F6F6F7` | `#0E0E10` |
| Canvas backdrop | `#ECECEF` | `#0A0A0C` |
| Surfaces (panels, cards, overlays) | `#FFFFFF` | `#17171A` |
| Hairline border | `#E4E4E7` | `#2A2A2F` |
| Text | `#18181B` | `#F4F4F5` |
| Muted text | `#71717A` | `#A1A1AA` |
| Hover surface | `#F4F4F5` | `#212126` |
| Primary action | `#18181B` (hover `#27272A`) | `#F4F4F5` |
| Accent / focus | `#4F46E5` | `#818CF8` |
| Selection tint | `#EEF2FF` | `#23234A` |
| Success / warning / danger | `#15803D` / `#B45309` / `#DC2626` | lighter equivalents |

## Typography

- **Inter** for the interface, 14px base, slight negative tracking.
- **JetBrains Mono** only for ids, dataset names and other literal values.
- Section headers: 11–12px uppercase, wide tracking.
- Both fonts are bundled (`@fontsource-variable/*`); nothing is loaded from a CDN.

## Layout

48px top toolbar, 224px left sidebar, 320px right inspector, fluid canvas between them.
Spacing follows a 4/8px cadence.

## Elevation

- Structural panels: border only, no shadow.
- Floating things (popovers, toasts, the proposal card): `--app-shadow-float`.
- Dialogs: `--app-shadow-modal` over a 20% `#18181B` backdrop, no blur.

## Buttons (`components/ui/Button.tsx`)

| Variant | Look | Used for |
| --- | --- | --- |
| `primary` | Near-black, white text | The main action of a screen: Sign in, New workspace, Add dataset |
| `accent` | Indigo | Committing work only: Apply, Save version, Restore |
| `secondary` | White, hairline border | Everything else |
| `ghost` | Transparent | Low-emphasis and icon actions |
| `danger` | Red | Destructive confirmation |

Controls are 32px high (28px in compact rows), 6px radius; cards and panels 12px.

## Palettes for generated UIs

A generated UI's colours come from a theme preset in
`backend/app/domains/generative_ui/design_registry.py`. There are sixteen: the original
six plus ten modelled on currently popular directions (Indigo Mist, Mocha Mousse, Peach
Fuzz, Digital Lavender, Sage Garden, Coral Sunset, Ocean Depth, Midnight Teal, Graphite
Lime, Aubergine Gold). Every preset is checked for WCAG AA text contrast by tests.

**Automatic palette.** When someone creates a new UI and names no colours or look:

1. a preset chosen in Settings → New workspaces is used, if there is one;
2. otherwise the platform picks one of the presets at random.

If the request does name a look ("dark", "green", "warm"), the assistant picks the closest
preset and that wins. The assistant's reply says which palette was used, and the Design
menu has "Surprise me" to shuffle to another. An existing UI keeps its theme when it is
regenerated.

"Popular" here means a hand-curated list in the registry, not live trend data; add or
retire presets there.
