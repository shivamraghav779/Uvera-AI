"""Turns the pipeline's plans into the parts of a UI document.

The model writes plans and component trees; this module makes them fit
together deterministically: it resolves a design plan into a theme, cleans
generated records, gives every component an id that is unique in the whole
application, and repairs references (routes, assets, entities) that point at
nothing. What remains wrong after that is reported by the validator and goes
back to the model.
"""

import difflib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import TypeAdapter, ValidationError

from app.domains.assets.schemas import IMAGE_DECISIONS, PlannedAsset
from app.domains.common import DataRow, Scalar
from app.domains.generation.blueprint import (
    ApplicationBlueprint,
    AssetBrief,
    DataPlan,
    DesignPlan,
    EntityBrief,
    InteractionBrief,
    ScreenBrief,
    ScreenPlan,
    SectionPlan,
    slug,
)
from app.domains.generative_ui.application import bound_dataset_names, resolve_route
from app.domains.generative_ui.color import contrast_ratio
from app.domains.generative_ui.design_registry import DesignRegistry, merge_theme
from app.domains.generative_ui.document import (
    MAX_RECORDS_PER_ENTITY,
    PRIMARY_KEY,
    ApplicationSpec,
    Asset,
    DesignConfig,
    DesignDirection,
    Entity,
    EntityFieldType,
    Interaction,
    Navigation,
    NavigationItem,
    Theme,
    ThemePatch,
    UIDocument,
)
from app.domains.generative_ui.pattern_registry import PatternRegistry
from app.domains.generative_ui.schemas import (
    ScreenComponent,
    ScreenType,
    ScreenWidth,
    VisualPriority,
)

Node = dict[str, Any]

MIN_TEXT_CONTRAST = 4.5
_NUMERIC = frozenset({EntityFieldType.NUMBER, EntityFieldType.CURRENCY, EntityFieldType.PERCENT})


def _child_nodes(node: Node) -> list[Node]:
    """Component children of a node. ``fields`` holds components only in a form."""
    keys = ["children", "components"] + (["fields"] if node.get("type") == "form" else [])
    return [child for key in keys for child in node.get(key) or [] if isinstance(child, dict)]


_ID_LIMIT = 64
_RECORD_ACTIONS = frozenset({"record_create", "record_update", "record_delete"})
# Action-bearing keys whose action may simply be dropped when it cannot work.
_OPTIONAL_ACTION_KEYS = ("item_action", "row_action", "move_action", "on_change")


# --- Design ------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResolvedDesign:
    theme: Theme
    design: DesignConfig
    direction: DesignDirection


def _readable(colors: Mapping[str, Any]) -> bool:
    return all(
        contrast_ratio(colors["foreground"], colors[backdrop]) >= MIN_TEXT_CONTRAST
        for backdrop in ("background", "surface", "muted")
    )


def resolve_design(
    plan: DesignPlan,
    registry: DesignRegistry,
    *,
    framework: str,
    forced_style: str | None = None,
    forced_palette: str | None = None,
) -> ResolvedDesign:
    """A complete theme from a design plan: style tokens, then a palette, then overrides.

    Unknown ids fall back to the catalogue; colour overrides are kept only if text
    stays readable; token overrides only if they are valid tokens.
    """
    style_id = forced_style or plan.style
    style = registry.design_system(style_id) or registry.styles_for(plan.summary, limit=1)[0]

    palette_id = forced_palette or plan.palette
    candidates = [palette_id, *style.palettes] if palette_id else list(style.palettes)
    if plan.mode is not None and not forced_palette:
        # A stated mode outranks a palette of the other mode.
        matching = [p for p in candidates if (t := registry.theme(p)) and t.theme.mode is plan.mode]
        matching += [p.id for p in registry.themes() if p.theme.mode is plan.mode]
        candidates = matching or candidates
    preset = next((registry.theme(p) for p in candidates if registry.theme(p)), None)
    preset = preset or registry.themes()[0]

    theme = registry.build_theme(preset.id, style.id).model_dump(mode="json", exclude_none=True)
    if plan.colors is not None and not forced_palette:
        overrides = plan.colors.model_dump(mode="json", exclude_none=True)
        candidate = {**theme["colors"], **overrides}
        if overrides and _readable(candidate):
            theme["colors"] = candidate
            theme.pop("preset", None)
    if plan.tokens is not None:
        raw = plan.tokens.model_dump(mode="json", exclude_none=True)
        accepted: Node = {}
        for key, value in raw.items():
            try:
                ThemePatch.model_validate({key: value})
            except ValidationError:
                continue
            accepted[key] = value
        theme = merge_theme(theme, accepted)

    effects = [effect for effect in plan.effects if effect in style.effects][:6]
    direction = DesignDirection(
        style=style.id,
        summary=(plan.summary or style.description)[:200],
        mood=[m[:200] for m in (plan.mood or list(style.mood))[:6] if m],
        rationale=plan.rationale[:600] if plan.rationale else None,
        imagery=plan.imagery,
        visual_language=plan.visual_language[:600] if plan.visual_language else None,
        layout=plan.layout[:200] if plan.layout else None,
        effects=effects,
    )
    return ResolvedDesign(
        theme=Theme.model_validate(theme),
        design=DesignConfig(framework=framework, design_system=style.id),
        direction=direction,
    )


def palette_of(theme: Theme) -> tuple[str, ...]:
    """Colours handed to the internal image provider: accents first, then backdrops."""
    colors = theme.colors
    accents = [colors.primary, colors.accent or colors.secondary, colors.success]
    return (*accents, colors.background, colors.foreground)


# --- Data --------------------------------------------------------------------------------


def _coerce(value: Scalar, field_type: EntityFieldType) -> Scalar:
    if value is None:
        return None
    if field_type in _NUMERIC:
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return value
        text = str(value).replace(",", "").replace("%", "").replace("$", "").strip()
        try:
            number = float(text)
        except ValueError:
            return None
        return int(number) if number.is_integer() else number
    if field_type is EntityFieldType.BOOLEAN:
        return value if isinstance(value, bool) else str(value).lower() in {"true", "yes", "1"}
    if field_type is EntityFieldType.IMAGE:
        return None  # filled in later from the asset plan
    return value if isinstance(value, str) else str(value)


def build_entities(briefs: Sequence[EntityBrief], plan: DataPlan) -> list[Entity]:
    """Entities with cleaned sample records: declared fields only, typed, unique ids."""
    generated = {slug(item.name, "entity"): item.records for item in plan.entities}
    entities: list[Entity] = []
    for brief in briefs:
        types = {field.key: field.type for field in brief.fields}
        records: list[DataRow] = []
        seen: set[str] = set()
        for index, raw in enumerate(generated.get(brief.name, [])[:MAX_RECORDS_PER_ENTITY]):
            record_id = str(raw.get(PRIMARY_KEY) or f"{brief.name[:3]}-{index + 1:03d}")[:64]
            if record_id in seen:
                record_id = f"{record_id}-{index + 1}"
            seen.add(record_id)
            row: DataRow = {PRIMARY_KEY: record_id}
            for key, field_type in types.items():
                row[key] = _coerce(raw.get(key), field_type)
            records.append(row)
        entities.append(
            Entity(
                name=brief.name,
                label=brief.label,
                description=brief.description,
                title_field=brief.title_field,
                fields=brief.fields,
                records=records,
            )
        )
    return entities


# --- Screen plans ------------------------------------------------------------------------

_DEFAULT_WIDTH: Mapping[ScreenType, ScreenWidth] = {
    ScreenType.LANDING: ScreenWidth.FULL,
    ScreenType.CONTENT: ScreenWidth.FULL,
    ScreenType.PRICING: ScreenWidth.FULL,
    ScreenType.FORM: ScreenWidth.NARROW,
    ScreenType.AUTHENTICATION: ScreenWidth.NARROW,
    ScreenType.ONBOARDING: ScreenWidth.NARROW,
    ScreenType.SETTINGS: ScreenWidth.NARROW,
}


def normalise_screen_plans(
    plans: Sequence[ScreenPlan], blueprint: ApplicationBlueprint, patterns: PatternRegistry
) -> dict[str, ScreenPlan]:
    """A plan for every blueprint screen, using known patterns only.

    A screen the planner skipped, or planned with nothing usable, gets the
    catalogue's composition for its kind as a starting point.
    """
    by_id = {plan.screen_id: plan for plan in plans}
    entity_names = {entity.name for entity in blueprint.entities}
    result: dict[str, ScreenPlan] = {}
    for screen in blueprint.screens:
        plan = by_id.get(screen.id)
        sections = [
            section.model_copy(
                update={
                    "purpose": section.purpose[:200],
                    "entity": section.entity if section.entity in entity_names else None,
                    "image_brief": section.image_brief[:400] if section.image_brief else None,
                }
            )
            for section in (plan.sections if plan else [])
            if patterns.get(section.pattern) is not None
        ][:12]
        if not sections:
            compositions = patterns.compositions_for(screen.type, blueprint.brief, limit=1)
            ids = compositions[0].patterns if compositions else ("table",)
            sections = [
                SectionPlan(pattern=p, priority=VisualPriority.SECONDARY, entity=screen.entity)
                for p in ids
            ]
        width = plan.width if plan else _DEFAULT_WIDTH.get(screen.type, ScreenWidth.CONTAINED)
        result[screen.id] = ScreenPlan(
            screen_id=screen.id,
            width=width,
            composition=(plan.composition if plan else "")[:300],
            sections=sections,
            responsive=plan.responsive[:300] if plan and plan.responsive else None,
        )
    return result


# --- Assets ------------------------------------------------------------------------------


def plan_assets(
    briefs: Sequence[AssetBrief], blueprint: ApplicationBlueprint, limit: int
) -> tuple[list[PlannedAsset], dict[str, AssetBrief]]:
    """Valid, uniquely named image requests (at most ``limit``) and their briefs by id."""
    screen_ids = {screen.id for screen in blueprint.screens}
    planned: list[PlannedAsset] = []
    by_id: dict[str, AssetBrief] = {}
    for brief in briefs:
        if len(planned) >= limit:
            break
        if brief.decision not in IMAGE_DECISIONS or not (brief.prompt or brief.query):
            continue
        asset_id = slug(brief.id, "image")[:60]
        if asset_id in by_id:
            continue
        prompt = (brief.prompt or brief.query)[:4000]
        try:
            asset = PlannedAsset(
                id=asset_id,
                decision=brief.decision,
                kind=brief.kind,
                prompt=prompt,
                query=(brief.query or brief.alt or prompt)[:200],
                alt=(brief.alt or brief.query or prompt)[:200],
                width=min(max(brief.width, 256), 1920),
                height=min(max(brief.height, 256), 1920),
                usage=brief.usage[:200] if brief.usage else None,
                screen_id=brief.screen_id if brief.screen_id in screen_ids else None,
            )
        except ValidationError:
            continue
        planned.append(asset)
        by_id[asset_id] = brief
    return planned, by_id


def attach_record_images(
    entities: Sequence[Entity], assets: Sequence[Asset], briefs: Mapping[str, AssetBrief]
) -> None:
    """Put each record image's asset id into the record field it was planned for."""
    by_name = {entity.name: entity for entity in entities}
    for asset in assets:
        brief = briefs.get(asset.id)
        if brief is None or not (brief.entity and brief.field and brief.record_id):
            continue
        entity = by_name.get(brief.entity)
        field = next((f for f in entity.fields if f.key == brief.field), None) if entity else None
        if entity is None or field is None or field.type is not EntityFieldType.IMAGE:
            continue
        for record in entity.records:
            if str(record.get(PRIMARY_KEY)) == brief.record_id:
                record[brief.field] = asset.id


# --- Interactions ------------------------------------------------------------------------


def build_interactions(
    briefs: Sequence[InteractionBrief], blueprint: ApplicationBlueprint
) -> list[Interaction]:
    screen_ids = {screen.id for screen in blueprint.screens}
    entity_names = {entity.name for entity in blueprint.entities}
    interactions: list[Interaction] = []
    taken: set[str] = set()
    for brief in briefs[:60]:
        interaction_id = slug(brief.id or brief.label, "interaction")[:60]
        if interaction_id in taken or not brief.label:
            continue
        taken.add(interaction_id)
        interactions.append(
            Interaction(
                id=interaction_id,
                label=brief.label[:200],
                type=brief.type,
                description=brief.trigger[:200] if brief.trigger else None,
                screen_id=brief.screen_id if brief.screen_id in screen_ids else None,
                entity=brief.entity if brief.entity in entity_names else None,
                result=brief.result[:200] if brief.result else None,
            )
        )
    return interactions


# --- Navigation and the application section --------------------------------------------


def build_navigation(blueprint: ApplicationBlueprint, style: str | None = None) -> Navigation:
    items = [
        NavigationItem(screen_id=screen.id, label=screen.name, icon=screen.icon, group=screen.group)
        for screen in blueprint.screens
        if screen.in_navigation
    ]
    return Navigation.model_validate(
        {
            "style": style or blueprint.navigation_style.value,
            "brand": blueprint.name,
            "home": blueprint.home,
            "items": [item.model_dump(mode="json", exclude_none=True) for item in items],
        }
    )


def build_application(
    blueprint: ApplicationBlueprint,
    *,
    navigation: Navigation,
    entities: Sequence[Entity],
    interactions: Sequence[Interaction],
    assets: Sequence[Asset],
    direction: DesignDirection,
) -> ApplicationSpec:
    return ApplicationSpec(
        name=blueprint.name,
        category=blueprint.category,
        description=blueprint.description,
        target_users=blueprint.target_users,
        goals=blueprint.goals,
        features=blueprint.features,
        navigation=navigation,
        entities=list(entities),
        interactions=list(interactions),
        assets=list(assets),
        design_direction=direction,
    )


# --- Screens -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScreenContext:
    """What a generated screen may refer to."""

    routes: Mapping[str, str]  # screen id -> route
    home_route: str
    asset_ids: frozenset[str]
    entity_names: frozenset[str]


def _namespace(screen_id: str, children: list[Node], taken: set[str]) -> dict[str, str]:
    """Rename component ids so they are unique in the application; return old -> new."""
    renamed: dict[str, str] = {}
    prefix = f"{screen_id}_"

    def visit(node: Node) -> None:
        raw = str(node.get("id") or node.get("type") or "item")
        candidate = slug(raw, "item")
        if not candidate.startswith(prefix):
            candidate = prefix + candidate
        candidate = candidate[: _ID_LIMIT - 4]
        unique, counter = candidate, 2
        while unique in taken:
            unique, counter = f"{candidate}_{counter}", counter + 1
        taken.add(unique)
        if "id" in node:
            renamed.setdefault(str(node["id"]), unique)
        node["id"] = unique
        for child in _child_nodes(node):
            visit(child)
        for tab in node.get("tabs") or []:
            if isinstance(tab, dict):
                visit(tab)

    for child in children:
        visit(child)
    return renamed


def _fix_action(action: Node, renamed: Mapping[str, str], context: ScreenContext) -> bool:
    """Repair an action in place. Returns False when it cannot be made to work."""
    payload = action.get("payload")
    if not isinstance(payload, dict):
        payload = action["payload"] = {}
    target = payload.get("target")
    if isinstance(target, str):
        if target in renamed:
            payload["target"] = renamed[target]
        else:
            payload.pop("target")
    kind = action.get("type")
    for key in ("to", "navigate_to"):
        destination = payload.get(key)
        if not isinstance(destination, str) or not destination.startswith("/"):
            continue
        if resolve_route(context.routes, destination) is None:
            close = difflib.get_close_matches(destination, list(context.routes.values()), n=1)
            payload[key] = close[0] if close else context.home_route
    if kind == "navigate" and not isinstance(payload.get("to"), str):
        return False
    return not (kind in _RECORD_ACTIONS and payload.get("entity") not in context.entity_names)


def _clean(node: Any, renamed: Mapping[str, str], context: ScreenContext) -> Any:
    """Drop nulls, dangling image references and actions that cannot work."""
    if isinstance(node, list):
        cleaned = [_clean(item, renamed, context) for item in node]
        return [item for item in cleaned if item is not None]
    if not isinstance(node, dict):
        return node
    if node.get("type") == "image" and node.get("image") not in context.asset_ids:
        return None
    result: Node = {}
    for key, value in node.items():
        if value is None:
            continue
        if key in ("image", "avatar") and isinstance(value, str):
            if value in context.asset_ids:
                result[key] = value
            continue
        if key == "fields" and isinstance(value, dict):
            result[key] = {k: v for k, v in value.items() if v is not None}
            continue
        is_action = key.endswith("action") or key == "on_change"
        if is_action and isinstance(value, dict) and "type" in value:
            if _fix_action(value, renamed, context):
                result[key] = value
            elif key == "submit_action":
                # The form stays usable: its values are recorded as a plain submission.
                result[key] = {"type": "submit", "payload": {}}
            elif key not in _OPTIONAL_ACTION_KEYS:
                return None  # the element exists only to trigger this action
            continue
        cleaned_value = _clean(value, renamed, context)
        if cleaned_value is not None:
            result[key] = cleaned_value
    condition = result.get("visible_when")
    if isinstance(condition, dict) and condition.get("field") in renamed:
        condition["field"] = renamed[condition["field"]]
    if isinstance(result.get("default_tab"), str) and result["default_tab"] in renamed:
        result["default_tab"] = renamed[result["default_tab"]]
    return result


_SECTION_OWN_CONTENT = ("title", "eyebrow", "description", "image")
MAX_COMPONENT_EFFECTS = 3


def unwrap_bare_sections(nodes: Sequence[Node]) -> list[Node]:
    """Top-level components with pointless section wrappers removed.

    Models like to wrap every block of a screen in a section of its own. A
    section with no heading that holds one component adds nothing but an
    extra box (and hides the block from the design review), so the component
    takes its place, keeping the styling the section asked for. An untitled
    plain section around several components is just the screen's own grid.
    """
    result: list[Node] = []
    for node in nodes:
        inner = node.get("children")
        bare = (
            node.get("type") == "section"
            and isinstance(inner, list)
            and not any(node.get(key) for key in _SECTION_OWN_CONTENT)
        )
        children = [c for c in inner if isinstance(c, dict)] if bare and inner else []
        if len(children) == 1:
            child = dict(children[0])
            outer, own = node.get("style"), child.get("style")
            style = {
                **(outer if isinstance(outer, dict) else {}),
                **(own if isinstance(own, dict) else {}),
            }
            effects = [
                *(outer.get("effects") or [] if isinstance(outer, dict) else []),
                *(own.get("effects") or [] if isinstance(own, dict) else []),
            ]
            if effects:
                style["effects"] = list(dict.fromkeys(effects))[:MAX_COMPONENT_EFFECTS]
            if style:
                child["style"] = style
            if isinstance(node.get("layout"), dict):
                child["layout"] = node["layout"]
            result.extend(unwrap_bare_sections([child]))
        elif children and node.get("variant", "default") == "default" and not node.get("style"):
            result.extend(unwrap_bare_sections(children))
        else:
            result.append(node)
    return result


def build_screen(
    brief: ScreenBrief,
    plan: ScreenPlan,
    children: Sequence[Any],
    context: ScreenContext,
    taken_ids: set[str],
) -> Node:
    """A screen component (as JSON) from the model's children, cleaned and namespaced.

    ``taken_ids`` is updated with the ids used, so the next screen avoids them.
    """
    nodes = unwrap_bare_sections([child for child in children if isinstance(child, dict)])
    renamed = _namespace(brief.id, nodes, taken_ids)
    cleaned = [c for c in (_clean(node, renamed, context) for node in nodes) if c is not None]
    marketing = plan.width is ScreenWidth.FULL
    return repair_schema_slips(
        {
            "type": "screen",
            "id": brief.id,
            "title": brief.name,
            "route": brief.route,
            "screen_type": brief.type.value,
            **({"purpose": brief.purpose} if brief.purpose else {}),
            "width": plan.width.value,
            # A marketing screen opens with its hero; a heading above it would repeat it.
            "show_title": not marketing,
            "children": cleaned,
        }
    )


def placeholder_screen(brief: ScreenBrief, reason: str) -> Node:
    """What stands in for a screen that could not be generated, so the rest still works."""
    return {
        "type": "screen",
        "id": brief.id,
        "title": brief.name,
        "route": brief.route,
        "screen_type": brief.type.value,
        "width": "contained",
        "children": [
            {
                "type": "alert",
                "id": f"{brief.id}_pending",
                "tone": "warning",
                "title": "This screen is not ready yet",
                "message": f"{reason} Ask the assistant to regenerate “{brief.name}”.",
            }
        ],
    }


def stub_screen(brief: ScreenBrief) -> Node:
    """A minimal stand-in for another screen while one screen is validated on its own."""
    return {
        "type": "screen",
        "id": brief.id,
        "title": brief.name,
        "route": brief.route,
        "children": [{"type": "text", "id": f"{brief.id}_stub", "content": brief.name}],
    }


def _remap_references(node: Any, renamed: Mapping[str, str]) -> None:
    """Point action targets and visibility conditions at renamed components."""
    if isinstance(node, list):
        for item in node:
            _remap_references(item, renamed)
        return
    if not isinstance(node, dict):
        return
    payload = node.get("payload")
    if isinstance(payload, dict) and payload.get("target") in renamed:
        payload["target"] = renamed[payload["target"]]
    condition = node.get("visible_when")
    if isinstance(condition, dict) and condition.get("field") in renamed:
        condition["field"] = renamed[condition["field"]]
    if node.get("default_tab") in renamed:
        node["default_tab"] = renamed[node["default_tab"]]
    for value in node.values():
        _remap_references(value, renamed)


def ensure_unique_ids(screens: Sequence[Node]) -> None:
    """Make component ids unique across screens that were generated independently.

    Each screen prefixes its ids with its own id, which almost always suffices;
    this catches the rest (one screen id being a prefix of another).
    """
    taken: set[str] = {"page", *(str(screen["id"]) for screen in screens)}
    for screen in screens:
        renamed: dict[str, str] = {}

        def visit(node: Node, renamed: dict[str, str] = renamed) -> None:
            for child in _child_nodes(node):
                claim(child, renamed)
                visit(child, renamed)
            for tab in node.get("tabs") or []:
                if isinstance(tab, dict):
                    claim(tab, renamed)
                    visit(tab, renamed)

        def claim(node: Node, renamed: dict[str, str]) -> None:
            original = str(node["id"])
            unique, counter = original, 2
            while unique in taken:
                unique, counter = f"{original[: _ID_LIMIT - 4]}_{counter}", counter + 1
            taken.add(unique)
            if unique != original:
                renamed[original] = unique
                node["id"] = unique

        visit(screen)
        if renamed:
            _remap_references(screen, renamed)


def blueprint_from_document(document: UIDocument) -> ApplicationBlueprint:
    """The blueprint an existing application document corresponds to.

    Edits that plan or generate screens (redesign, add a screen) need the same
    product context the first generation had; it is all in the document.
    """
    application = document.application
    assert application is not None, "only application documents have a blueprint"
    in_navigation = {item.screen_id: item for item in application.navigation.items}
    datasets = {entity.name for entity in application.entities}
    screens = []
    for screen in document.page.components:
        if not isinstance(screen, ScreenComponent):
            continue
        bound = [n for n in bound_dataset_names(screen.model_dump(mode="json")) if n in datasets]
        item = in_navigation.get(screen.id)
        screens.append(
            ScreenBrief(
                id=screen.id,
                name=screen.title,
                route=screen.route,
                type=screen.screen_type,
                purpose=screen.purpose or "",
                in_navigation=item is not None,
                icon=item.icon if item else None,
                group=item.group if item else None,
                entity=bound[0] if bound else None,
            )
        )
    return ApplicationBlueprint(
        name=application.name,
        category=application.category,
        description=application.description,
        target_users=application.target_users,
        goals=application.goals,
        features=application.features,
        navigation_style=application.navigation.style,
        home=application.navigation.home,
        screens=screens,
        entities=[
            EntityBrief(
                name=entity.name,
                label=entity.label,
                description=entity.description,
                title_field=entity.title_field,
                fields=entity.fields,
            )
            for entity in application.entities
        ],
    )


# --- Tolerating small schema slips --------------------------------------------------------

# Errors that can be fixed without guessing what the model meant.
_DROPPABLE = frozenset({"extra_forbidden", "enum", "literal_error"})
_MAX_FIX_ROUNDS = 4


def _locate(root: Any, loc: Sequence[Any]) -> tuple[Any, Any] | None:
    """Container and key a Pydantic error location points at.

    Locations of discriminated unions contain the union tag ("hero", "screen")
    between real keys; those segments are skipped.
    """
    current = root
    path = list(loc)
    for index, part in enumerate(path):
        last = index == len(path) - 1
        if (isinstance(current, list) and isinstance(part, int) and part < len(current)) or (
            isinstance(current, dict) and part in current
        ):
            if last:
                return current, part
            current = current[part]
        elif isinstance(part, str) and not last:
            continue  # a union tag
        else:
            return None
    return None


def repair_schema_slips(screen: Node) -> Node:
    """Remove what a strict schema rejects but a reader would shrug at.

    Models occasionally add a field that does not exist, use a style token that
    is not one, or write a text or list slightly over its limit. Those are
    dropped or cut here; anything that changes meaning (a missing required
    field, a wrong type) is left for the validator to report back.
    """
    adapter = _SCREEN_ADAPTER
    for _ in range(_MAX_FIX_ROUNDS):
        try:
            adapter.validate_python(screen)
        except ValidationError as error:
            changed = False
            # Deepest and last first, so deleting one item does not shift another's index.
            ordered = sorted(
                error.errors(), key=lambda e: (len(e["loc"]), str(e["loc"])), reverse=True
            )
            for issue in ordered:
                found = _locate(screen, issue["loc"])
                if found is None:
                    continue
                container, key = found
                kind, context = issue["type"], issue.get("ctx") or {}
                if kind in _DROPPABLE and isinstance(container, dict):
                    del container[key]
                elif kind == "string_too_long" and isinstance(container[key], str):
                    container[key] = container[key][: int(context["max_length"]) - 1] + "…"
                elif kind == "too_long" and isinstance(container[key], list):
                    container[key] = container[key][: int(context["max_length"])]
                else:
                    continue
                changed = True
            if not changed:
                break
        else:
            break
    return screen


_SCREEN_ADAPTER: TypeAdapter[ScreenComponent] = TypeAdapter(ScreenComponent)
