"""The design knowledge library: patterns, compositions, styles and their retrieval."""

from app.domains.generative_ui.design_registry import build_default_design_registry
from app.domains.generative_ui.pattern_registry import (
    PatternRegistry,
    build_default_pattern_registry,
)
from app.domains.generative_ui.registry import build_default_registry
from app.domains.generative_ui.schemas import ComponentType, Effect, ScreenType

PATTERNS = build_default_pattern_registry()
DESIGN = build_default_design_registry()


def test_every_pattern_names_a_registered_component_and_one_of_its_variants() -> None:
    registry = build_default_registry()

    for pattern in PATTERNS.patterns():
        definition = registry.get(pattern.component.value)
        if pattern.variant is not None:
            assert pattern.variant in definition.variants, pattern.id
        assert pattern.purpose and pattern.screen_types, pattern.id
        assert pattern.responsive, "every pattern says how it behaves on a small screen"


def test_compositions_only_use_known_patterns() -> None:
    for composition in PATTERNS.compositions():
        assert all(PATTERNS.get(pattern_id) for pattern_id in composition.patterns), composition.id
    assert {c.screen_type for c in PATTERNS.compositions()} >= {
        ScreenType.LANDING, ScreenType.DASHBOARD, ScreenType.LISTING, ScreenType.DETAIL,
    }  # fmt: skip


def test_selection_is_limited_to_the_kind_of_screen() -> None:
    dashboard = PATTERNS.select(ScreenType.DASHBOARD)
    landing = PATTERNS.select(ScreenType.LANDING)

    assert all(ScreenType.DASHBOARD in p.screen_types for p in dashboard)
    assert "hero.split" not in {p.id for p in dashboard}
    assert {"hero.split", "pricing", "cta.centered"} <= {p.id for p in landing}
    assert "kanban" not in {p.id for p in landing}


def test_selection_ranks_patterns_that_suit_the_product_first() -> None:
    travel = [p.id for p in PATTERNS.select(ScreenType.LANDING, "premium travel platform")]
    developer = [p.id for p in PATTERNS.select(ScreenType.LANDING, "developer api platform")]

    assert travel.index("hero.immersive") < travel.index("hero.product")
    assert developer.index("hero.product") < developer.index("hero.immersive")


def test_compositions_differ_by_product() -> None:
    [studio] = PATTERNS.compositions_for(ScreenType.LANDING, "architecture studio", limit=1)
    [saas] = PATTERNS.compositions_for(ScreenType.LANDING, "b2b saas platform", limit=1)

    assert (studio.id, saas.id) == ("editorial_studio", "saas_landing")
    assert studio.patterns != saas.patterns


def test_components_behind_patterns_are_listed_once() -> None:
    components = PATTERNS.components(["hero.split", "hero.centered", "stats.strip", "ghost"])

    assert components == [ComponentType.HERO, ComponentType.STATS]


def test_a_registry_rejects_duplicate_patterns() -> None:
    first = PATTERNS.patterns()[0]

    try:
        PatternRegistry([first, first], [])
    except ValueError as error:
        assert first.id in str(error)
    else:
        raise AssertionError("a duplicate pattern must be refused")


# --- Visual styles --------------------------------------------------------------------


def test_styles_define_more_than_colour_and_name_real_palettes() -> None:
    for style in DESIGN.design_systems():
        tokens = style.tokens.model_dump(exclude_none=True)
        assert {"radius", "density", "spacing", "shadows", "surface", "motion", "typography"} <= (
            tokens.keys()
        ), style.id
        assert "colors" not in tokens, "colours belong to palettes"
        assert style.palettes and all(DESIGN.theme(p) for p in style.palettes), style.id
        assert style.mood, style.id


def test_different_products_are_offered_different_styles_first() -> None:
    def first(brief: str) -> str:
        return DESIGN.styles_for(brief, limit=1)[0].id

    assert first("luxury hotel concierge") == "luxury"
    assert first("developer api cloud infrastructure") == "developer_tool"
    assert first("fintech payments and invoicing") == "fintech"
    assert first("travel booking for unique experiences") == "travel"
    assert first("enterprise cybersecurity operations") == "enterprise"


def test_restrained_styles_carry_no_effects_and_expressive_ones_do() -> None:
    assert DESIGN.design_system("enterprise").effects == ()  # type: ignore[union-attr]
    assert Effect.GLOW not in DESIGN.design_system("fintech").effects  # type: ignore[union-attr]
    assert Effect.MARQUEE in DESIGN.design_system("creative_agency").effects  # type: ignore[union-attr]


def test_every_effect_and_icon_is_described_once() -> None:
    assert {effect.id for effect in DESIGN.effects()} == set(Effect)
    assert len(DESIGN.icons()) == len(set(DESIGN.icons())) > 60
