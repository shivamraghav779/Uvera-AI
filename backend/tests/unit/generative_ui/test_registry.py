import pytest
from pydantic import TypeAdapter

from app.domains.generative_ui.registry import ComponentRegistry, build_default_registry
from app.domains.generative_ui.schemas import Component, ComponentType, PageComponent

REQUIRED_COMPONENTS = {
    "page", "section", "card", "metric", "text", "table", "chart", "form", "input", "select",
    "checkbox", "button", "badge", "alert", "list", "timeline", "progress", "tabs", "divider",
    "modal",
    # application structure and patterns
    "screen", "hero", "feature_grid", "logo_cloud", "testimonials", "pricing", "cta", "stats",
    "gallery", "collection", "kanban", "detail", "profile_header", "image", "media", "steps",
    "faq", "footer", "calendar", "comparison", "command",
}  # fmt: skip


def test_default_registry_contains_exactly_the_supported_components() -> None:
    registry = build_default_registry()

    assert {component_type.value for component_type in registry.types()} == REQUIRED_COMPONENTS
    assert set(registry.types()) == set(ComponentType)


@pytest.mark.parametrize("definition", build_default_registry().definitions(), ids=lambda d: d.type)
def test_every_example_is_valid_for_its_own_schema(definition) -> None:  # type: ignore[no-untyped-def]
    """Examples are shown to the model, so a broken one would teach it invalid output."""
    parsed = definition.model.model_validate(definition.example)

    assert parsed.type == definition.type


def test_examples_are_accepted_where_the_schema_allows_them() -> None:
    adapter = TypeAdapter(Component)
    for definition in build_default_registry().definitions():
        if definition.type is ComponentType.PAGE:
            PageComponent.model_validate(definition.example)
        else:
            adapter.validate_python(definition.example)


def test_unknown_component_is_not_registered() -> None:
    registry = build_default_registry()

    assert not registry.is_registered("iframe")
    with pytest.raises(KeyError, match="iframe"):
        registry.get("iframe")


def test_duplicate_registration_is_rejected() -> None:
    definition = build_default_registry().get("text")

    with pytest.raises(ValueError, match="registered twice"):
        ComponentRegistry([definition, definition])


def test_restricted_registry_only_knows_allowed_types() -> None:
    restricted = build_default_registry().restricted_to([ComponentType.PAGE, ComponentType.TEXT])

    assert restricted.is_registered("text")
    assert not restricted.is_registered("chart")
