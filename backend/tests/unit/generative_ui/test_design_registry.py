"""The automatic palette: what a new UI gets when its author names no colours."""

import random

from app.domains.generative_ui.color import contrast_ratio
from app.domains.generative_ui.design_registry import build_default_design_registry
from app.domains.generative_ui.validator import MIN_TEXT_CONTRAST

DESIGN = build_default_design_registry()


def test_pick_theme_is_reproducible_for_a_given_random_source() -> None:
    first = [DESIGN.pick_theme(random.Random(7)).id for _ in range(3)]

    assert len(set(first)) == 1
    assert DESIGN.theme(first[0]) is not None


def test_pick_theme_varies_and_reaches_every_preset() -> None:
    rng = random.Random(2026)

    picked = {DESIGN.pick_theme(rng).id for _ in range(600)}

    assert picked == {preset.id for preset in DESIGN.themes()}


def test_the_catalogue_offers_light_and_dark_palettes_with_unique_ids() -> None:
    presets = DESIGN.themes()

    assert len({preset.id for preset in presets}) == len(presets) >= 12
    assert {preset.theme.mode.value for preset in presets} == {"light", "dark"}
    assert all(preset.theme.preset == preset.id for preset in presets)


def test_every_palette_keeps_text_readable_on_its_backdrops() -> None:
    for preset in DESIGN.themes():
        colors = preset.theme.colors
        for backdrop in (colors.background, colors.surface, colors.muted):
            assert contrast_ratio(colors.foreground, backdrop) >= MIN_TEXT_CONTRAST, preset.id
