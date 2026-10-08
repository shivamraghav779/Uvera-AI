"""Catalogue of theme presets, visual styles, effects, icons and UI frameworks.

This is metadata only. The backend knows a framework's *id*; the frontend maps
that id to real components. Nothing here contains React or CSS.

A *visual style* (stored as ``design.design_system``) is more than a colour
scheme: it fixes type, shape, surface treatment, motion and density, and carries
the knowledge the Design Director needs to choose it: what it feels like, which
products it suits, which palettes and effects belong to it.
"""

import random
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from typing import Any

from app.domains.generative_ui.document import DesignConfig, Theme, ThemePatch
from app.domains.generative_ui.schemas import Effect


class FrameworkStatus(StrEnum):
    AVAILABLE = "available"
    PLANNED = "planned"


@dataclass(frozen=True, slots=True)
class FrameworkDescriptor:
    id: str
    name: str
    status: FrameworkStatus
    description: str


@dataclass(frozen=True, slots=True)
class ThemePreset:
    id: str
    name: str
    description: str
    theme: Theme


@dataclass(frozen=True, slots=True)
class DesignSystem:
    """A visual style: shape, type, surface and motion tokens plus design knowledge.

    Colours belong to themes; ``palettes`` only names presets that suit the style.
    """

    id: str
    name: str
    description: str
    tokens: ThemePatch
    mood: tuple[str, ...] = ()
    # Product kinds the style suits, as lower-case keywords matched against a brief.
    suited_for: tuple[str, ...] = ()
    imagery: str = "none"
    effects: tuple[Effect, ...] = ()
    palettes: tuple[str, ...] = ()
    navigation: tuple[str, ...] = ("sidebar", "topbar")
    guidance: str = ""


@dataclass(frozen=True, slots=True)
class EffectDescriptor:
    id: Effect
    name: str
    description: str
    # Where the effect belongs; using it elsewhere is a design-quality finding.
    use_for: str


def _theme(preset: str, mode: str, **colors: str) -> Theme:
    return Theme.model_validate({"preset": preset, "mode": mode, "colors": colors})


def _tokens(**tokens: Any) -> ThemePatch:
    return ThemePatch.model_validate(tokens)


_THEME_PRESETS = (
    ThemePreset(
        "blue_white",
        "Blue & White",
        "Crisp light theme with a blue accent.",
        _theme(
            "blue_white", "light",
            primary="#2563EB", secondary="#64748B", background="#F8FAFC", surface="#FFFFFF",
            foreground="#0F172A", muted="#F1F5F9", border="#E2E8F0", destructive="#DC2626",
            success="#16A34A", warning="#D97706",
        ),
    ),
    ThemePreset(
        "slate_dark",
        "Slate Dark",
        "Dark theme with cool blue accents.",
        _theme(
            "slate_dark", "dark",
            primary="#60A5FA", secondary="#94A3B8", background="#0B1120", surface="#111827",
            foreground="#E5E7EB", muted="#1F2937", border="#263244", destructive="#F87171",
            success="#4ADE80", warning="#FBBF24",
        ),
    ),
    ThemePreset(
        "emerald",
        "Emerald",
        "Light theme with a green accent on warm neutrals.",
        _theme(
            "emerald", "light",
            primary="#059669", secondary="#57534E", background="#FAFAF9", surface="#FFFFFF",
            foreground="#1C1917", muted="#F5F5F4", border="#E7E5E4", destructive="#DC2626",
            success="#15803D", warning="#B45309",
        ),
    ),
    ThemePreset(
        "violet_night",
        "Violet Night",
        "Dark, futuristic theme with violet accents.",
        _theme(
            "violet_night", "dark",
            primary="#A78BFA", secondary="#A1A1AA", background="#0C0A14", surface="#16131F",
            foreground="#EDE9FE", muted="#221D30", border="#2E2840", destructive="#FB7185",
            success="#34D399", warning="#FBBF24",
        ),
    ),
    ThemePreset(
        "mono_minimal",
        "Mono Minimal",
        "Black-and-white minimal theme.",
        _theme(
            "mono_minimal", "light",
            primary="#18181B", secondary="#71717A", background="#FFFFFF", surface="#FFFFFF",
            foreground="#18181B", muted="#F4F4F5", border="#E4E4E7", destructive="#B91C1C",
            success="#15803D", warning="#A16207",
        ),
    ),
    ThemePreset(
        "warm_sand",
        "Warm Sand",
        "Soft light theme with terracotta accents.",
        _theme(
            "warm_sand", "light",
            primary="#C2410C", secondary="#78716C", background="#FAF7F2", surface="#FFFDF9",
            foreground="#292524", muted="#F0EBE3", border="#E4DCD0", destructive="#B91C1C",
            success="#3F7D3A", warning="#B45309",
        ),
    ),
    ThemePreset(
        "indigo_mist",
        "Indigo Mist",
        "Calm light theme with an indigo accent on cool grey.",
        _theme(
            "indigo_mist", "light",
            primary="#4F46E5", secondary="#5A5E69", background="#F6F6F7", surface="#FFFFFF",
            foreground="#18181B", muted="#EEF2FF", border="#E4E4E7", destructive="#DC2626",
            success="#15803D", warning="#B45309",
        ),
    ),
    ThemePreset(
        "mocha_mousse",
        "Mocha Mousse",
        "Warm light theme in soft cocoa browns.",
        _theme(
            "mocha_mousse", "light",
            primary="#8A5A44", secondary="#7A6A60", background="#FAF6F2", surface="#FFFFFF",
            foreground="#2B211C", muted="#F1E8E0", border="#E5D8CC", destructive="#B3261E",
            success="#3F7D3A", warning="#A65F00",
        ),
    ),
    ThemePreset(
        "peach_fuzz",
        "Peach Fuzz",
        "Friendly light theme with a peach-coral accent.",
        _theme(
            "peach_fuzz", "light",
            primary="#E0633A", secondary="#7C6F68", background="#FFF8F4", surface="#FFFFFF",
            foreground="#2A1F1A", muted="#FDEBE1", border="#F3D9CB", destructive="#C62828",
            success="#2E7D32", warning="#B26A00",
        ),
    ),
    ThemePreset(
        "digital_lavender",
        "Digital Lavender",
        "Airy light theme with lavender and violet.",
        _theme(
            "digital_lavender", "light",
            primary="#7C3AED", secondary="#6B6880", background="#F8F6FF", surface="#FFFFFF",
            foreground="#1E1B2E", muted="#EFEAFE", border="#E0D9F7", destructive="#DC2626",
            success="#15803D", warning="#B45309",
        ),
    ),
    ThemePreset(
        "sage_garden",
        "Sage Garden",
        "Quiet light theme in muted sage greens.",
        _theme(
            "sage_garden", "light",
            primary="#4F7A5B", secondary="#6B7568", background="#F6F8F4", surface="#FFFFFF",
            foreground="#1D2620", muted="#E9EFE6", border="#D9E2D5", destructive="#B3261E",
            success="#2F7D4F", warning="#A66A00",
        ),
    ),
    ThemePreset(
        "coral_sunset",
        "Coral Sunset",
        "Vivid light theme with a rose-coral accent.",
        _theme(
            "coral_sunset", "light",
            primary="#E11D48", secondary="#78716C", background="#FFF7F7", surface="#FFFFFF",
            foreground="#231518", muted="#FFE4E6", border="#F6D2D6", destructive="#B91C1C",
            success="#15803D", warning="#B45309",
        ),
    ),
    ThemePreset(
        "ocean_depth",
        "Ocean Depth",
        "Deep navy dark theme with a sky-blue accent.",
        _theme(
            "ocean_depth", "dark",
            primary="#38BDF8", secondary="#8AA4B8", background="#071521", surface="#0D2030",
            foreground="#E2EEF6", muted="#14293B", border="#1E3A50", destructive="#F87171",
            success="#34D399", warning="#FBBF24",
        ),
    ),
    ThemePreset(
        "midnight_teal",
        "Midnight Teal",
        "Dark theme with a bright teal accent.",
        _theme(
            "midnight_teal", "dark",
            primary="#2DD4BF", secondary="#8FA6A3", background="#06141B", surface="#0C1F26",
            foreground="#E3F2F0", muted="#132B33", border="#1D3B44", destructive="#FB7185",
            success="#4ADE80", warning="#FACC15",
        ),
    ),
    ThemePreset(
        "graphite_lime",
        "Graphite Lime",
        "Near-black dark theme with an electric lime accent.",
        _theme(
            "graphite_lime", "dark",
            primary="#A3E635", secondary="#A1A1AA", background="#0D0F0E", surface="#161917",
            foreground="#ECEFEA", muted="#1F2421", border="#2B312D", destructive="#F87171",
            success="#4ADE80", warning="#FBBF24",
        ),
    ),
    ThemePreset(
        "aubergine_gold",
        "Aubergine Gold",
        "Rich plum dark theme with a warm gold accent.",
        _theme(
            "aubergine_gold", "dark",
            primary="#E0B252", secondary="#B3A6BA", background="#150F1A", surface="#1E1626",
            foreground="#F1E9F5", muted="#2A2033", border="#3A2D45", destructive="#FB7185",
            success="#4ADE80", warning="#F59E0B",
        ),
    ),
    ThemePreset(
        "citrus_pop",
        "Citrus Pop",
        "High-contrast light theme with a vivid yellow accent on white and black.",
        _theme(
            "citrus_pop", "light",
            primary="#111111", secondary="#52525B", background="#FFFDF5", surface="#FFFFFF",
            foreground="#111111", muted="#FEF3C7", border="#111111", destructive="#DC2626",
            success="#15803D", warning="#B45309", accent="#FACC15",
        ),
    ),
    ThemePreset(
        "noir_gold",
        "Noir Gold",
        "Near-black luxury theme with champagne gold accents.",
        _theme(
            "noir_gold", "dark",
            primary="#D4B483", secondary="#A8A29E", background="#0C0B0A", surface="#151312",
            foreground="#F5F0E8", muted="#1F1C1A", border="#2E2A26", destructive="#F87171",
            success="#86EFAC", warning="#FBBF24", accent="#F3E3C3",
        ),
    ),
    ThemePreset(
        "stone_ink",
        "Stone & Ink",
        "Quiet warm-grey light theme with deep ink text, for editorial work.",
        _theme(
            "stone_ink", "light",
            primary="#1C1917", secondary="#78716C", background="#F5F3EF", surface="#FBFAF8",
            foreground="#1C1917", muted="#EBE7E0", border="#DAD4CA", destructive="#B91C1C",
            success="#3F7D3A", warning="#A16207", accent="#B45309",
        ),
    ),
    ThemePreset(
        "arctic_cyan",
        "Arctic Cyan",
        "Cool light theme with a deep teal-blue accent, precise and technical.",
        _theme(
            "arctic_cyan", "light",
            primary="#0E7490", secondary="#64748B", background="#F4F8FA", surface="#FFFFFF",
            foreground="#0B1F2A", muted="#E6F0F4", border="#D5E3EA", destructive="#DC2626",
            success="#15803D", warning="#B45309", accent="#06B6D4",
        ),
    ),
)  # fmt: skip

_E = Effect

_DESIGN_SYSTEMS = (
    DesignSystem(
        "modern_minimal",
        "Modern Minimal",
        "Flat surfaces, hairline borders, medium radius.",
        _tokens(radius="md", shadows="none", density="comfortable", spacing="normal",
                surface="bordered", motion="subtle", gradient="none",
                typography={"font": "sans", "scale": "md", "heading_font": "sans",
                            "heading_scale": "md", "heading_weight": "semibold"}),
        mood=("clean", "calm", "precise"),
        suited_for=("saas", "dashboard", "internal tool", "productivity", "general"),
        effects=(_E.REVEAL, _E.HOVER_LIFT),
        palettes=("indigo_mist", "blue_white", "mono_minimal", "arctic_cyan"),
        guidance="Let whitespace and alignment carry the design. One accent, used sparingly.",
    ),
    DesignSystem(
        "premium_saas",
        "Premium SaaS",
        "Generous spacing, soft large radius, refined type and restrained gradients.",
        _tokens(radius="lg", shadows="subtle", density="comfortable", spacing="relaxed",
                surface="bordered", motion="subtle", gradient="subtle",
                typography={"font": "sans", "scale": "md", "heading_font": "geometric",
                            "heading_scale": "lg", "heading_weight": "semibold"}),
        mood=("polished", "confident", "trustworthy"),
        suited_for=("saas", "b2b", "platform", "recruitment", "crm", "marketing", "startup"),
        imagery="product",
        effects=(_E.REVEAL, _E.HOVER_LIFT, _E.SPOTLIGHT, _E.GRADIENT_MESH, _E.COUNTER),
        palettes=("indigo_mist", "stone_ink", "digital_lavender", "arctic_cyan", "mono_minimal"),
        guidance="Bento sections, product previews and one confident accent. Effects only on "
        "the landing hero and call to action; application screens stay quiet.",
    ),
    DesignSystem(
        "editorial",
        "Editorial",
        "Square corners, serif display type, airy spacing and full-width imagery.",
        _tokens(radius="none", shadows="none", density="spacious", spacing="relaxed",
                surface="flat", motion="subtle", gradient="none",
                typography={"font": "serif", "scale": "lg", "heading_font": "serif",
                            "heading_scale": "xl", "heading_weight": "regular"}),
        mood=("considered", "cultured", "quiet"),
        suited_for=("architecture", "studio", "magazine", "portfolio", "gallery", "publishing",
                    "interior", "fashion"),
        imagery="photography",
        effects=(_E.REVEAL, _E.PARALLAX),
        palettes=("stone_ink", "warm_sand", "mono_minimal", "mocha_mousse"),
        navigation=("minimal", "topbar"),
        guidance="Large type, asymmetric columns (7/5, 8/4) and big photographs with metadata "
        "set small. No cards with borders, no icons in grids, no gradients.",
    ),
    DesignSystem(
        "neo_brutalist",
        "Neo-Brutalist",
        "Thick outlines, hard offset shadows, heavy grotesk type and flat saturated colour.",
        _tokens(radius="none", shadows="none", density="comfortable", spacing="normal",
                surface="brutal", motion="subtle", gradient="none",
                typography={"font": "grotesk", "scale": "md", "heading_font": "grotesk",
                            "heading_scale": "xl", "heading_weight": "black"}),
        mood=("bold", "raw", "playful"),
        suited_for=("creative", "indie", "community", "event", "zine", "gen z", "web3"),
        imagery="illustration",
        effects=(_E.MARQUEE, _E.HOVER_LIFT),
        palettes=("citrus_pop", "coral_sunset", "mono_minimal"),
        navigation=("topbar", "minimal"),
        guidance="Oversized headings and blunt copy. Colour blocks instead of shadows.",
    ),
    DesignSystem(
        "glass",
        "Glass",
        "Translucent blurred surfaces over rich colour fields.",
        _tokens(radius="lg", shadows="medium", density="comfortable", spacing="relaxed",
                surface="glass", motion="expressive", gradient="vivid",
                typography={"font": "sans", "scale": "md", "heading_font": "geometric",
                            "heading_scale": "lg", "heading_weight": "semibold"}),
        mood=("luminous", "modern", "immersive"),
        suited_for=("consumer", "music", "media", "weather", "crypto", "mobile app"),
        imagery="abstract",
        effects=(_E.GRADIENT_MESH, _E.GLASS, _E.GLOW, _E.SPOTLIGHT, _E.REVEAL),
        palettes=("ocean_depth", "violet_night", "midnight_teal", "digital_lavender"),
        guidance="Needs a colourful backdrop to work: gradient mesh or imagery behind panels.",
    ),
    DesignSystem(
        "dark_futuristic",
        "Dark Futuristic",
        "Dark surfaces, thin luminous lines, grotesk type and controlled glow.",
        _tokens(radius="sm", shadows="none", density="comfortable", spacing="normal",
                surface="bordered", motion="expressive", gradient="subtle",
                typography={"font": "grotesk", "scale": "md", "heading_font": "grotesk",
                            "heading_scale": "lg", "heading_weight": "bold"}),
        mood=("technical", "ambitious", "nocturnal"),
        suited_for=("web3", "gaming", "space", "robotics", "hardware", "infrastructure"),
        imagery="abstract",
        effects=(_E.GLOW, _E.GRID, _E.SPOTLIGHT, _E.ANIMATED_GRADIENT, _E.REVEAL),
        palettes=("violet_night", "graphite_lime", "midnight_teal", "ocean_depth"),
        guidance="Glow marks one focal element per screen, never every card.",
    ),
    DesignSystem(
        "soft",
        "Soft",
        "Rounded corners, gentle shadows, generous spacing.",
        _tokens(radius="lg", shadows="subtle", density="comfortable", spacing="relaxed",
                surface="elevated", motion="subtle", gradient="subtle",
                typography={"font": "rounded", "scale": "md", "heading_font": "rounded",
                            "heading_scale": "md", "heading_weight": "bold"}),
        mood=("friendly", "gentle", "approachable"),
        suited_for=("consumer", "education", "family", "habit", "community", "nonprofit"),
        imagery="illustration",
        effects=(_E.REVEAL, _E.HOVER_LIFT),
        palettes=("peach_fuzz", "digital_lavender", "sage_garden"),
    ),
    DesignSystem(
        "material",
        "Material",
        "Elevated surfaces with small radius, in the spirit of Material Design.",
        _tokens(radius="sm", shadows="medium", density="comfortable", spacing="normal",
                surface="elevated", motion="subtle", gradient="none",
                typography={"font": "sans", "scale": "md", "heading_font": "sans",
                            "heading_scale": "md", "heading_weight": "medium"}),
        mood=("familiar", "structured"),
        suited_for=("android", "utility", "internal tool"),
        effects=(_E.HOVER_LIFT,),
        palettes=("blue_white", "indigo_mist", "emerald"),
    ),
    DesignSystem(
        "enterprise",
        "Enterprise",
        "Restrained, information-first surfaces with clear status and no decoration.",
        _tokens(radius="sm", shadows="none", density="comfortable", spacing="normal",
                surface="bordered", motion="none", gradient="none",
                typography={"font": "sans", "scale": "md", "heading_font": "sans",
                            "heading_scale": "sm", "heading_weight": "semibold"}),
        mood=("dependable", "serious", "high signal"),
        suited_for=("enterprise", "cybersecurity", "security", "compliance", "erp", "logistics",
                    "healthcare", "government", "operations", "admin"),
        effects=(),
        palettes=("blue_white", "slate_dark", "arctic_cyan", "mono_minimal"),
        navigation=("sidebar",),
        guidance="Status colours carry meaning; nothing else is coloured. No effects, no hero "
        "imagery, dense tables and clear filters.",
    ),
    DesignSystem(
        "compact_pro",
        "Data Dense",
        "Dense, information-rich layout for power users.",
        _tokens(radius="sm", shadows="none", density="compact", spacing="tight",
                surface="bordered", motion="none", gradient="none",
                typography={"font": "sans", "scale": "sm", "heading_font": "sans",
                            "heading_scale": "sm", "heading_weight": "semibold"}),
        mood=("efficient", "analytical"),
        suited_for=("analytics", "trading", "monitoring", "observability", "bi", "back office"),
        effects=(),
        palettes=("slate_dark", "blue_white", "mono_minimal", "graphite_lime"),
        navigation=("sidebar",),
        guidance="More rows, less chrome. Charts and tables side by side in 8/4 and 7/5 splits.",
    ),
    DesignSystem(
        "playful",
        "Playful",
        "Pill shapes, bouncy motion, bright colour and rounded bold type.",
        _tokens(radius="full", shadows="subtle", density="comfortable", spacing="relaxed",
                surface="elevated", motion="expressive", gradient="vivid",
                typography={"font": "rounded", "scale": "md", "heading_font": "rounded",
                            "heading_scale": "lg", "heading_weight": "black"}),
        mood=("joyful", "energetic", "warm"),
        suited_for=("kids", "game", "social", "food", "pets", "fitness", "language learning"),
        imagery="illustration",
        effects=(_E.HOVER_LIFT, _E.REVEAL, _E.COUNTER, _E.GRADIENT_MESH),
        palettes=("peach_fuzz", "coral_sunset", "digital_lavender", "citrus_pop"),
        navigation=("bottom", "topbar"),
    ),
    DesignSystem(
        "luxury",
        "Luxury",
        "Serif display type, wide margins, almost no ornament, slow reveals.",
        _tokens(radius="none", shadows="none", density="spacious", spacing="relaxed",
                surface="flat", motion="subtle", gradient="none",
                typography={"font": "sans", "scale": "md", "heading_font": "serif",
                            "heading_scale": "xl", "heading_weight": "regular"}),
        mood=("exclusive", "restrained", "timeless"),
        suited_for=("luxury", "jewellery", "hotel", "real estate", "wine", "private banking",
                    "concierge", "yacht"),
        imagery="photography",
        effects=(_E.REVEAL, _E.PARALLAX),
        palettes=("noir_gold", "stone_ink", "aubergine_gold", "mocha_mousse"),
        navigation=("minimal", "topbar"),
        guidance="Few words, large images, small uppercase labels. Never more than one accent.",
    ),
    DesignSystem(
        "creative_agency",
        "Creative Agency",
        "Oversized grotesk type, asymmetry, marquees and visual storytelling.",
        _tokens(radius="none", shadows="none", density="spacious", spacing="relaxed",
                surface="flat", motion="expressive", gradient="subtle",
                typography={"font": "grotesk", "scale": "lg", "heading_font": "grotesk",
                            "heading_scale": "xl", "heading_weight": "black"}),
        mood=("expressive", "confident", "unconventional"),
        suited_for=("agency", "design studio", "branding", "film", "production", "portfolio"),
        imagery="photography",
        effects=(_E.MARQUEE, _E.REVEAL, _E.PARALLAX, _E.HOVER_LIFT, _E.NOISE),
        palettes=("mono_minimal", "citrus_pop", "coral_sunset", "graphite_lime"),
        navigation=("minimal", "topbar"),
        guidance="Headlines are the layout. Alternate full-bleed work with tight text blocks.",
    ),
    DesignSystem(
        "developer_tool",
        "Developer Tool",
        "Dense, precise and command-oriented, with monospace accents.",
        _tokens(radius="sm", shadows="none", density="compact", spacing="tight",
                surface="bordered", motion="subtle", gradient="none",
                typography={"font": "sans", "scale": "sm", "heading_font": "mono",
                            "heading_scale": "md", "heading_weight": "medium"}),
        mood=("exact", "fast", "no-nonsense"),
        suited_for=("developer", "api", "devops", "cli", "database", "ci", "sdk", "cloud",
                    "infrastructure", "open source"),
        effects=(_E.GRID, _E.GLOW),
        palettes=("graphite_lime", "slate_dark", "mono_minimal", "midnight_teal"),
        navigation=("sidebar", "topbar"),
        guidance="Command bar, status badges, logs and tables. Show the product, not people.",
    ),
    DesignSystem(
        "ai_native",
        "AI Native",
        "Calm, interactive surfaces around a prompt or assistant, without neon clichés.",
        _tokens(radius="lg", shadows="subtle", density="comfortable", spacing="normal",
                surface="bordered", motion="subtle", gradient="subtle",
                typography={"font": "sans", "scale": "md", "heading_font": "geometric",
                            "heading_scale": "lg", "heading_weight": "semibold"}),
        mood=("intelligent", "calm", "assistive"),
        suited_for=("ai", "assistant", "copilot", "automation", "agent", "llm", "productivity"),
        imagery="abstract",
        effects=(_E.SPOTLIGHT, _E.REVEAL, _E.COUNTER, _E.GRADIENT_MESH),
        palettes=("stone_ink", "mono_minimal", "sage_garden", "arctic_cyan", "indigo_mist"),
        guidance="Do not default to purple or glow. Show what the product does: a command bar, "
        "a product preview, concrete before/after results.",
    ),
    DesignSystem(
        "fintech",
        "Fintech",
        "Trustworthy and restrained: strong hierarchy, tabular figures, calm colour.",
        _tokens(radius="md", shadows="subtle", density="comfortable", spacing="normal",
                surface="bordered", motion="subtle", gradient="none",
                typography={"font": "sans", "scale": "md", "heading_font": "sans",
                            "heading_scale": "md", "heading_weight": "semibold"}),
        mood=("trustworthy", "clear", "composed"),
        suited_for=("fintech", "bank", "payments", "invoicing", "accounting", "insurance",
                    "investing", "wealth", "expense"),
        effects=(_E.COUNTER, _E.REVEAL),
        palettes=("emerald", "arctic_cyan", "blue_white", "slate_dark", "ocean_depth"),
        guidance="Numbers first. Green and red only for gains and losses.",
    ),
    DesignSystem(
        "travel",
        "Travel",
        "Immersive photography, spacious editorial layout and serif display headings.",
        _tokens(radius="lg", shadows="subtle", density="spacious", spacing="relaxed",
                surface="elevated", motion="expressive", gradient="subtle",
                typography={"font": "sans", "scale": "md", "heading_font": "serif",
                            "heading_scale": "xl", "heading_weight": "medium"}),
        mood=("inviting", "adventurous", "premium"),
        suited_for=("travel", "tourism", "hospitality", "experiences", "booking", "outdoor",
                    "airline", "trip"),
        imagery="photography",
        effects=(_E.PARALLAX, _E.REVEAL, _E.HOVER_LIFT),
        palettes=("warm_sand", "stone_ink", "ocean_depth", "sage_garden", "peach_fuzz"),
        navigation=("topbar", "minimal"),
        guidance="Lead with a full-bleed photograph and a search or booking action. Destinations "
        "and experiences as large image tiles, not text cards.",
    ),
    DesignSystem(
        "wellness",
        "Wellness",
        "Soft organic shapes, muted natural colour and unhurried spacing.",
        _tokens(radius="full", shadows="subtle", density="spacious", spacing="relaxed",
                surface="flat", motion="subtle", gradient="subtle",
                typography={"font": "sans", "scale": "md", "heading_font": "serif",
                            "heading_scale": "lg", "heading_weight": "regular"}),
        mood=("calm", "caring", "natural"),
        suited_for=("wellness", "health", "meditation", "yoga", "therapy", "spa", "nutrition",
                    "skincare", "clinic"),
        imagery="photography",
        effects=(_E.REVEAL,),
        palettes=("sage_garden", "peach_fuzz", "warm_sand", "mocha_mousse"),
        navigation=("topbar", "bottom"),
    ),
    DesignSystem(
        "ecommerce",
        "E-commerce",
        "Product imagery first, clear prices, filters and confident calls to action.",
        _tokens(radius="md", shadows="subtle", density="comfortable", spacing="normal",
                surface="bordered", motion="subtle", gradient="none",
                typography={"font": "sans", "scale": "md", "heading_font": "sans",
                            "heading_scale": "lg", "heading_weight": "bold"}),
        mood=("clear", "desirable", "conversion-focused"),
        suited_for=("ecommerce", "e-commerce", "shop", "store", "marketplace", "retail",
                    "fashion", "catalog"),
        imagery="product",
        effects=(_E.HOVER_LIFT, _E.REVEAL),
        palettes=("mono_minimal", "stone_ink", "warm_sand", "coral_sunset"),
        navigation=("topbar",),
        guidance="Product grids with large images, price and one action. Comparison and "
        "reviews support the decision.",
    ),
)  # fmt: skip

_EFFECTS = (
    EffectDescriptor(_E.GRADIENT_MESH, "Gradient mesh",
                     "Soft blended colour fields behind a section.", "hero, call to action"),
    EffectDescriptor(_E.ANIMATED_GRADIENT, "Animated gradient",
                     "A slowly shifting gradient backdrop.", "hero"),
    EffectDescriptor(_E.GLOW, "Glow", "A luminous halo around one focal element.",
                     "one featured card or image per screen"),
    EffectDescriptor(_E.GLASS, "Glass", "Translucent, blurred surface.",
                     "panels over imagery or gradients"),
    EffectDescriptor(_E.NOISE, "Noise", "Fine grain texture over a surface.",
                     "hero, editorial sections"),
    EffectDescriptor(_E.GRID, "Grid", "A faint dotted or lined grid backdrop.",
                     "hero and feature sections of technical products"),
    EffectDescriptor(_E.SPOTLIGHT, "Spotlight", "A light that follows the pointer.",
                     "hero, bento feature grids"),
    EffectDescriptor(_E.REVEAL, "Reveal", "Content fades and rises into view on scroll.",
                     "marketing sections"),
    EffectDescriptor(_E.HOVER_LIFT, "Hover lift", "Cards rise slightly under the pointer.",
                     "interactive cards and tiles"),
    EffectDescriptor(_E.PARALLAX, "Parallax", "Imagery drifts slower than the page.",
                     "full-bleed photography"),
    EffectDescriptor(_E.MARQUEE, "Marquee", "A row that scrolls continuously.",
                     "logo clouds, testimonials"),
    EffectDescriptor(_E.COUNTER, "Animated counter", "Numbers count up when first seen.",
                     "statistics"),
)  # fmt: skip

# Icon names the frontend can draw. Anything else renders a neutral glyph.
ICONS: tuple[str, ...] = (
    "home", "dashboard", "users", "user", "briefcase", "calendar", "chart", "bar-chart",
    "line-chart", "pie-chart", "settings", "search", "bell", "mail", "message", "phone",
    "file", "folder", "image", "map", "map-pin", "globe", "compass", "plane", "hotel",
    "star", "heart", "bookmark", "tag", "cart", "bag", "credit-card", "wallet", "dollar",
    "trending-up", "trending-down", "activity", "zap", "sparkles", "bot", "brain", "cpu",
    "code", "terminal", "database", "server", "cloud", "lock", "shield", "key", "check",
    "check-circle", "x-circle", "alert", "info", "clock", "timer", "filter", "list", "grid",
    "layers", "layout", "kanban", "table", "plus", "edit", "trash", "download", "upload",
    "share", "link", "external", "arrow-right", "arrow-up-right", "play", "camera", "video",
    "mic", "music", "book", "graduation", "building", "store", "truck", "package", "leaf",
    "sun", "moon", "flame", "droplet", "target", "award", "trophy", "rocket", "lightbulb",
    "puzzle", "handshake", "megaphone", "pen", "palette", "ruler", "workflow", "git-branch",
)  # fmt: skip

_FRAMEWORKS = (
    FrameworkDescriptor(
        "shadcn",
        "shadcn/ui",
        FrameworkStatus.AVAILABLE,
        "Tailwind-based components in the shadcn/ui style. Implements every semantic component.",
    ),
    FrameworkDescriptor(
        "material",
        "Material",
        FrameworkStatus.AVAILABLE,
        "Material-style adapter. Overrides the core controls; other components fall back "
        "to the default adapter.",
    ),
    FrameworkDescriptor("mui", "MUI", FrameworkStatus.PLANNED, "Adapter over @mui/material."),
    FrameworkDescriptor("mantine", "Mantine", FrameworkStatus.PLANNED, "Adapter over Mantine."),
    FrameworkDescriptor(
        "react_aria", "React Aria", FrameworkStatus.PLANNED, "Adapter over React Aria Components."
    ),
    FrameworkDescriptor(
        "aceternity", "Aceternity UI", FrameworkStatus.PLANNED, "Adapter over Aceternity UI."
    ),
)

DEFAULT_THEME_PRESET = "blue_white"
DEFAULT_DESIGN_SYSTEM = "modern_minimal"
DEFAULT_FRAMEWORK = "shadcn"


def merge_theme(base: Mapping[str, Any], patch: Mapping[str, Any]) -> dict[str, Any]:
    """Overlay ``patch`` on ``base``; nested token groups merge, ``None`` is ignored."""
    merged = dict(base)
    for key, value in patch.items():
        if value is None:
            continue
        if isinstance(value, Mapping):
            merged[key] = merge_theme(merged.get(key) or {}, value)
        else:
            merged[key] = value
    return merged


class DesignRegistry:
    def __init__(
        self,
        themes: tuple[ThemePreset, ...] = _THEME_PRESETS,
        design_systems: tuple[DesignSystem, ...] = _DESIGN_SYSTEMS,
        frameworks: tuple[FrameworkDescriptor, ...] = _FRAMEWORKS,
        effects: tuple[EffectDescriptor, ...] = _EFFECTS,
    ) -> None:
        self._themes = {preset.id: preset for preset in themes}
        self._design_systems = {system.id: system for system in design_systems}
        self._frameworks = {framework.id: framework for framework in frameworks}
        self._effects = {effect.id: effect for effect in effects}

    def effects(self) -> tuple[EffectDescriptor, ...]:
        return tuple(self._effects.values())

    def icons(self) -> tuple[str, ...]:
        return ICONS

    def styles_for(self, brief: str, limit: int = 6) -> tuple[DesignSystem, ...]:
        """Styles ranked by how well their ``suited_for`` keywords match a product brief.

        Structured retrieval over the design catalogue; the caller (the Design
        Director) makes the final choice. Unmatched styles follow in catalogue order.
        """
        text = brief.lower()
        scored = sorted(
            self._design_systems.values(),
            key=lambda system: -sum(keyword in text for keyword in system.suited_for),
        )
        return tuple(scored[:limit])

    def themes(self) -> tuple[ThemePreset, ...]:
        return tuple(self._themes.values())

    def design_systems(self) -> tuple[DesignSystem, ...]:
        return tuple(self._design_systems.values())

    def frameworks(self) -> tuple[FrameworkDescriptor, ...]:
        return tuple(self._frameworks.values())

    def theme(self, preset_id: str) -> ThemePreset | None:
        return self._themes.get(preset_id)

    def design_system(self, system_id: str) -> DesignSystem | None:
        return self._design_systems.get(system_id)

    def is_framework_available(self, framework_id: str) -> bool:
        framework = self._frameworks.get(framework_id)
        return framework is not None and framework.status is FrameworkStatus.AVAILABLE

    def pick_theme(self, rng: random.Random | None = None) -> ThemePreset:
        """A palette for a new UI whose author did not ask for a particular look.

        Chosen at random from the curated presets, all of which pass the contrast
        rules, so an unspecified look varies between workspaces but is never unreadable.
        """
        return (rng or random).choice(self.themes())

    def default_design(self) -> DesignConfig:
        return DesignConfig(framework=DEFAULT_FRAMEWORK, design_system=DEFAULT_DESIGN_SYSTEM)

    def build_theme(self, preset_id: str, design_system_id: str) -> Theme:
        """A complete theme: the preset's colours shaped by the design system's tokens."""
        preset, system = self._themes[preset_id], self._design_systems[design_system_id]
        tokens = system.tokens.model_dump(mode="json", exclude_none=True)
        return Theme.model_validate(merge_theme(preset.theme.model_dump(mode="json"), tokens))

    def default_theme(self) -> Theme:
        return self.build_theme(DEFAULT_THEME_PRESET, DEFAULT_DESIGN_SYSTEM)


@lru_cache
def build_default_design_registry() -> DesignRegistry:
    return DesignRegistry()
