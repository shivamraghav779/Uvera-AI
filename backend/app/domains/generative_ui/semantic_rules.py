"""Semantic checks applied to a structurally valid UI.

Each rule inspects the whole tree and yields ``(path, message)`` findings. Rules
are independent; add a new one by appending it to ``SEMANTIC_RULES``.
"""

import re
from collections import Counter
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass

from app.domains.actions.schemas import ActionType, is_safe_navigation_target
from app.domains.common import DataRow
from app.domains.data_sources.schemas import DatasetDescriptor, FieldKind
from app.domains.generative_ui.application import (
    image_refs,
    resolve_route,
    route_params,
)
from app.domains.generative_ui.document import (
    PRIMARY_KEY,
    ApplicationSpec,
    EntityFieldType,
)
from app.domains.generative_ui.schemas import (
    Aggregate,
    AnyComponent,
    CalendarComponent,
    ChartComponent,
    CollectionComponent,
    DataBinding,
    DetailComponent,
    FormComponent,
    KanbanComponent,
    MetricBinding,
    MetricComponent,
    PageComponent,
    ProfileHeaderComponent,
    ProgressComponent,
    RecordCardFields,
    RowCondition,
    ScreenComponent,
    SelectComponent,
    StatsComponent,
    TableComponent,
    TabsComponent,
)
from app.domains.generative_ui.tree import ComponentNode, FormControl, action_specs

Finding = tuple[str, str]

# Markup or URL schemes that could execute in a browser if a renderer were careless.
_UNSAFE_CONTENT = re.compile(
    r"<\s*/?\s*(script|iframe|object|embed)\b|javascript\s*:|vbscript\s*:|data\s*:\s*text/html"
    r"|\bon(click|error|load|mouseover|focus)\s*=",
    re.IGNORECASE,
)
_TARGET_KEY = "target"
_NAVIGATE_DESTINATION_KEY = "to"


_RECORD_ACTIONS = frozenset(
    {ActionType.RECORD_CREATE, ActionType.RECORD_UPDATE, ActionType.RECORD_DELETE}
)


@dataclass(frozen=True, slots=True)
class ValidationLimits:
    max_depth: int = 8
    # For a single view, and for each screen of an application.
    max_components: int = 200
    max_application_components: int = 1500


@dataclass(frozen=True, slots=True)
class RuleInput:
    page: PageComponent
    nodes: tuple[ComponentNode, ...]
    datasets: Mapping[str, DatasetDescriptor]
    limits: ValidationLimits
    application: ApplicationSpec | None = None

    @property
    def screens(self) -> list[ScreenComponent]:
        return [c for c in self.page.components if isinstance(c, ScreenComponent)]

    @property
    def routes(self) -> dict[str, str]:
        return {screen.id: screen.route for screen in self.screens}

    def screen_of(self, node: ComponentNode) -> ScreenComponent | None:
        """The screen containing ``node`` (or the node itself when it is a screen)."""
        parts = node.path.split(".")
        if len(parts) < 2 or parts[0] != "components":
            return None
        child = self.page.components[int(parts[1])]
        return child if isinstance(child, ScreenComponent) else None

    @property
    def component_ids(self) -> set[str]:
        return {node.component.id for node in self.nodes}

    @property
    def control_names(self) -> set[str]:
        return {
            node.component.name for node in self.nodes if isinstance(node.component, FormControl)
        }


SemanticRule = Callable[[RuleInput], Iterator[Finding]]


def _join(path: str, field: str) -> str:
    return f"{path}.{field}" if path else field


def check_size(rule_input: RuleInput) -> Iterator[Finding]:
    limits = rule_input.limits
    is_application = bool(rule_input.screens)
    total_limit = limits.max_application_components if is_application else limits.max_components
    if len(rule_input.nodes) > total_limit:
        yield "", f"UI has {len(rule_input.nodes)} components; the limit is {total_limit}."
    if is_application:
        per_screen = Counter(
            screen.id for node in rule_input.nodes if (screen := rule_input.screen_of(node))
        )
        for index, child in enumerate(rule_input.page.components):
            if per_screen.get(child.id, 0) > limits.max_components:
                yield (
                    f"components.{index}",
                    f"Screen '{child.id}' has {per_screen[child.id]} components; "
                    f"the limit is {limits.max_components}.",
                )
    deepest = max(rule_input.nodes, key=lambda node: node.depth)
    # A screen adds one level above what a single view has.
    if deepest.depth > limits.max_depth + (1 if is_application else 0):
        yield (
            deepest.path,
            f"Nesting depth {deepest.depth} exceeds the limit of {limits.max_depth}.",
        )


def check_unique_ids(rule_input: RuleInput) -> Iterator[Finding]:
    ids = [(node.path, node.component.id) for node in rule_input.nodes]
    for node in rule_input.nodes:
        if isinstance(node.component, TabsComponent):
            ids.extend(
                (_join(node.path, f"tabs.{index}"), tab.id)
                for index, tab in enumerate(node.component.tabs)
            )
    counts = Counter(identifier for _, identifier in ids)
    for path, identifier in ids:
        if counts[identifier] > 1:
            yield _join(path, "id"), f"Duplicate id '{identifier}'; ids must be unique."


def _unknown_dataset(path: str, name: str, rule_input: RuleInput) -> Finding:
    available = ", ".join(sorted(rule_input.datasets)) or "none"
    return (
        _join(path, "data_source.dataset"),
        f"Unknown dataset '{name}'. Available datasets: {available}.",
    )


def _check_conditions(
    path: str,
    dataset: str,
    conditions: list[RowCondition] | None,
    fields: frozenset[str],
    node: ComponentNode,
    rule_input: RuleInput,
) -> Iterator[Finding]:
    screen = rule_input.screen_of(node)
    params = route_params(screen.route) if screen else []
    for index, condition in enumerate(conditions or []):
        where = _join(path, f"data_source.where.{index}")
        if condition.field not in fields:
            yield where, f"Dataset '{dataset}' has no field '{condition.field}'."
        if condition.param is not None and condition.param not in params:
            known = ", ".join(params) or "none"
            yield (
                _join(where, "param"),
                f"'{condition.param}' is not a parameter of this screen's route "
                f"(parameters: {known}).",
            )


def _grouped_keys(binding: DataBinding) -> list[str]:
    """Fields of the rows a grouped binding produces."""
    assert binding.group_by is not None
    return [binding.group_by, binding.field or "count"]


def _check_binding(
    node: ComponentNode, binding: DataBinding, keys: list[str], rule_input: RuleInput
) -> Iterator[Finding]:
    """A binding's dataset and every field it or the component names must exist."""
    path = node.path
    descriptor = rule_input.datasets.get(binding.dataset)
    if descriptor is None:
        yield _unknown_dataset(path, binding.dataset, rule_input)
        return
    fields = descriptor.field_names
    yield from _check_conditions(path, binding.dataset, binding.where, fields, node, rule_input)
    own = [name for name in (binding.group_by, binding.field) if name is not None]
    if binding.sort is not None and binding.group_by is None:
        own.append(binding.sort.field)
    for key in own:
        if key not in fields:
            yield _join(path, "data_source"), f"Dataset '{binding.dataset}' has no field '{key}'."
    if binding.group_by is not None:
        produced = _grouped_keys(binding)
        for key in keys:
            if key not in produced:
                yield (
                    path,
                    f"A grouped binding yields the fields {', '.join(produced)}; "
                    f"'{key}' is not one of them.",
                )
        return
    for key in keys:
        if key not in fields:
            yield path, f"Dataset '{binding.dataset}' has no field '{key}'."


def _check_inline_rows(path: str, rows: list[DataRow], keys: list[str]) -> Iterator[Finding]:
    for key in keys:
        if any(key not in row for row in rows):
            yield path, f"Field '{key}' is missing from one or more inline rows."


_NUMERIC_AGGREGATES = frozenset({Aggregate.SUM, Aggregate.AVERAGE, Aggregate.MIN, Aggregate.MAX})


def _check_metric_binding(
    node: ComponentNode, path: str, binding: MetricBinding, rule_input: RuleInput
) -> Iterator[Finding]:
    descriptor = rule_input.datasets.get(binding.dataset)
    if descriptor is None:
        yield _unknown_dataset(path, binding.dataset, rule_input)
        return
    kinds = {field.name: field.kind for field in descriptor.fields}
    yield from _check_conditions(
        path, binding.dataset, binding.where, descriptor.field_names, node, rule_input
    )
    if binding.field not in kinds:
        yield path, f"Dataset '{binding.dataset}' has no field '{binding.field}'."
    elif binding.aggregate in _NUMERIC_AGGREGATES and kinds[binding.field] is not FieldKind.NUMBER:
        yield (
            _join(path, "data_source.aggregate"),
            f"'{binding.aggregate.value}' needs a numeric field; '{binding.field}' is text.",
        )


def _check_metric(
    node: ComponentNode, metric: MetricComponent, rule_input: RuleInput
) -> Iterator[Finding]:
    if metric.data_source is None:
        if metric.value is None:
            yield node.path, "Metric has no value: provide 'value' or a data_source binding."
        return
    yield from _check_metric_binding(node, node.path, metric.data_source, rule_input)


def _check_stats(
    node: ComponentNode, stats: StatsComponent, rule_input: RuleInput
) -> Iterator[Finding]:
    for index, item in enumerate(stats.items):
        path = _join(node.path, f"items.{index}")
        if item.data_source is not None:
            yield from _check_metric_binding(node, path, item.data_source, rule_input)
        elif item.value is None:
            yield path, "Stat has no value: provide 'value' or a data_source binding."


def _card_fields(fields: RecordCardFields) -> list[str]:
    named = [fields.title, fields.subtitle, fields.description, fields.image, fields.badge]
    named.append(fields.timestamp)
    return [name for name in named if name is not None] + [item.key for item in fields.meta]


def _record_component_keys(component: AnyComponent) -> list[str] | None:
    """Fields a record-bound component reads, or ``None`` if it is not one."""
    if isinstance(component, CollectionComponent | ProfileHeaderComponent):
        return _card_fields(component.fields)
    if isinstance(component, KanbanComponent):
        return [component.group_by, *_card_fields(component.fields)]
    if isinstance(component, DetailComponent):
        return [field.key for field in component.fields]
    if isinstance(component, CalendarComponent):
        named = [component.date_field, component.time_field, component.title_field]
        named += [component.subtitle_field, component.badge_field]
        return [name for name in named if name is not None]
    return None


def check_data(rule_input: RuleInput) -> Iterator[Finding]:
    """Data-driven components need data, and the fields they reference must exist."""
    for node in rule_input.nodes:
        component = node.component
        if isinstance(component, MetricComponent):
            yield from _check_metric(node, component, rule_input)
            continue
        if isinstance(component, StatsComponent):
            yield from _check_stats(node, component, rule_input)
            continue
        record_keys = _record_component_keys(component)
        if record_keys is not None:
            binding = getattr(component, "data_source", None)
            assert isinstance(binding, DataBinding)
            yield from _check_binding(node, binding, record_keys, rule_input)
            continue
        if isinstance(component, ChartComponent):
            keys, rows = [component.x_key, *component.y_keys], component.data
        elif isinstance(component, TableComponent):
            keys, rows = [column.key for column in component.columns], component.rows
        else:
            continue
        if component.data_source is not None:
            yield from _check_binding(node, component.data_source, keys, rule_input)
        elif rows:
            yield from _check_inline_rows(node.path, rows, keys)
        else:
            yield node.path, "No data: provide inline rows or a data_source binding."


def _check_in_app_path(path: str, destination: object, rule_input: RuleInput) -> Iterator[Finding]:
    """Inside an application an in-app path must lead to one of its screens."""
    routes = rule_input.routes
    if not routes or not isinstance(destination, str) or not destination.startswith("/"):
        return
    if resolve_route(routes, destination) is None:
        known = ", ".join(sorted(routes.values()))
        yield path, f"'{destination}' is not a screen of this application. Routes: {known}."


def _check_record_action(
    path: str, payload: Mapping[str, object], rule_input: RuleInput
) -> Iterator[Finding]:
    entities = (
        {e.name: e for e in rule_input.application.entities} if rule_input.application else {}
    )
    name = payload.get("entity")
    entity = entities.get(name) if isinstance(name, str) else None
    if entity is None:
        known = ", ".join(sorted(entities)) or "none"
        yield _join(path, "entity"), f"'{name}' is not an entity of this application ({known})."
        return
    field = payload.get("set_field")
    if field is not None and field not in {f.key for f in entity.fields}:
        yield _join(path, "set_field"), f"Entity '{entity.name}' has no field '{field}'."


def check_actions(rule_input: RuleInput) -> Iterator[Finding]:
    """Action payloads may only point at existing components, screens and entities."""
    component_ids = rule_input.component_ids
    for node in rule_input.nodes:
        for field, action in action_specs(node.component):
            path = _join(node.path, f"{field}.payload")
            target = action.payload.get(_TARGET_KEY)
            if target is not None and target not in component_ids:
                yield _join(path, _TARGET_KEY), f"Action target '{target}' is not a component id."
            destination = action.payload.get(_NAVIGATE_DESTINATION_KEY)
            if action.type is ActionType.NAVIGATE:
                if not (isinstance(destination, str) and is_safe_navigation_target(destination)):
                    yield (
                        _join(path, _NAVIGATE_DESTINATION_KEY),
                        "Navigate needs 'to' set to an in-app path ('/...') or an https URL.",
                    )
                else:
                    yield from _check_in_app_path(
                        _join(path, _NAVIGATE_DESTINATION_KEY), destination, rule_input
                    )
            if action.type in _RECORD_ACTIONS:
                yield from _check_record_action(path, action.payload, rule_input)
                yield from _check_in_app_path(
                    _join(path, "navigate_to"), action.payload.get("navigate_to"), rule_input
                )


def check_application_structure(rule_input: RuleInput) -> Iterator[Finding]:
    """Screens live directly under the page, and an application has screens and a shell."""
    application, screens = rule_input.application, rule_input.screens
    for node in rule_input.nodes:
        if isinstance(node.component, ScreenComponent) and node.depth != 2:
            yield node.path, "A screen can only be placed directly under the page."
    if screens and len(screens) != len(rule_input.page.components):
        yield "components", "A page holds either screens only, or no screens at all."
    if application is None:
        if screens:
            yield "", "Screens need an 'application' section describing the product."
        return
    if not screens:
        yield "", "An application needs at least one screen."
        return
    seen: dict[str, str] = {}
    for index, screen in enumerate(screens):
        shape = "/".join(":" if part.startswith(":") else part for part in screen.route.split("/"))
        if shape in seen:
            yield (
                f"components.{index}.route",
                f"Route '{screen.route}' clashes with screen '{seen[shape]}'.",
            )
        seen[shape] = screen.id
        parameters = route_params(screen.route)
        if len(parameters) != len(set(parameters)):
            yield f"components.{index}.route", "A route cannot use the same parameter twice."


def check_navigation(rule_input: RuleInput) -> Iterator[Finding]:
    application = rule_input.application
    if application is None:
        return
    routes, navigation = rule_input.routes, application.navigation
    by_id = {screen.id: screen for screen in rule_input.screens}
    if navigation.home not in routes:
        yield "application.navigation.home", f"'{navigation.home}' is not a screen."
    elif route_params(by_id[navigation.home].route):
        yield "application.navigation.home", "The home screen's route cannot have parameters."
    linked = [(f"items.{i}", item) for i, item in enumerate(navigation.items)]
    if navigation.action is not None:
        linked.append(("action", navigation.action))
    for path, item in linked:
        where = f"application.navigation.{path}.screen_id"
        if item.screen_id not in routes:
            yield where, f"'{item.screen_id}' is not a screen."
        elif route_params(by_id[item.screen_id].route):
            yield where, "A navigation item cannot point at a route with parameters."
    ids = [item.screen_id for item in navigation.items]
    for screen_id, count in Counter(ids).items():
        if count > 1:
            yield "application.navigation.items", f"Screen '{screen_id}' is listed {count} times."


def _check_records(
    path: str, entity_index: int, rule_input: RuleInput, asset_ids: set[str]
) -> Iterator[Finding]:
    assert rule_input.application is not None
    entities = rule_input.application.entities
    entity = entities[entity_index]
    by_key = {field.key: field for field in entity.fields}
    known = {*by_key, PRIMARY_KEY}
    ids = [record.get(PRIMARY_KEY) for record in entity.records]
    if any(value is None or value == "" for value in ids):
        yield _join(path, "records"), f"Every record needs an '{PRIMARY_KEY}'."
    for value, count in Counter(str(v) for v in ids if v is not None).items():
        if count > 1:
            yield _join(path, "records"), f"Record id '{value}' is used {count} times."
    for index, record in enumerate(entity.records):
        where = _join(path, f"records.{index}")
        unknown = sorted(set(record) - known)
        if unknown:
            yield where, f"Unknown field(s) {', '.join(unknown)} for entity '{entity.name}'."
        for key, cell in record.items():
            field = by_key.get(key)
            if field is None or cell is None:
                continue
            if field.type is EntityFieldType.IMAGE and cell not in asset_ids:
                yield _join(where, key), f"'{cell}' is not an asset of this application."


def check_entities(rule_input: RuleInput) -> Iterator[Finding]:
    application = rule_input.application
    if application is None:
        return
    asset_ids = {asset.id for asset in application.assets}
    names = Counter(entity.name for entity in application.entities)
    for index, entity in enumerate(application.entities):
        path = f"application.entities.{index}"
        if names[entity.name] > 1:
            yield _join(path, "name"), f"Entity '{entity.name}' is defined twice."
        keys = Counter(field.key for field in entity.fields)
        for key, count in keys.items():
            if count > 1:
                yield _join(path, "fields"), f"Field '{key}' is defined {count} times."
        if entity.title_field not in keys and entity.title_field != PRIMARY_KEY:
            yield _join(path, "title_field"), f"'{entity.title_field}' is not a field."
        for field in entity.fields:
            if field.references is not None and field.references not in names:
                yield _join(path, "fields"), f"'{field.references}' is not an entity."
        yield from _check_records(path, index, rule_input, asset_ids)


def check_assets(rule_input: RuleInput) -> Iterator[Finding]:
    """Every image reference names an asset the application actually has."""
    application = rule_input.application
    asset_ids = {asset.id for asset in application.assets} if application else set()
    if application is not None:
        for asset_id, count in Counter(asset.id for asset in application.assets).items():
            if count > 1:
                yield "application.assets", f"Asset id '{asset_id}' is used {count} times."
    for node in rule_input.nodes:
        own = node.component.model_dump(
            mode="json", exclude={"children", "components", "fields", "tabs"}
        )
        for path, asset_id in image_refs(own):
            if asset_id not in asset_ids:
                yield _join(node.path, path), f"'{asset_id}' is not an asset of this UI."


def check_references(rule_input: RuleInput) -> Iterator[Finding]:
    known = rule_input.component_ids | rule_input.control_names
    for node in rule_input.nodes:
        component = node.component
        condition = getattr(component, "visible_when", None)
        if condition is not None and condition.field not in known:
            yield (
                _join(node.path, "visible_when.field"),
                f"'{condition.field}' is not the name of a form control or a component id.",
            )
        if isinstance(component, TabsComponent) and component.default_tab not in (
            None,
            *(tab.id for tab in component.tabs),
        ):
            yield _join(node.path, "default_tab"), "default_tab must be the id of one of the tabs."
        if isinstance(component, SelectComponent) and component.default_value not in (
            None,
            *(option.value for option in component.options),
        ):
            yield _join(node.path, "default_value"), "default_value must be one of the options."


def check_component_consistency(rule_input: RuleInput) -> Iterator[Finding]:
    for node in rule_input.nodes:
        component = node.component
        if isinstance(component, ProgressComponent) and component.value > component.max:
            yield _join(node.path, "value"), "Progress value must not exceed max."
        if isinstance(component, FormComponent):
            names = Counter(field.name for field in component.fields)
            for name, count in names.items():
                if count > 1:
                    yield _join(node.path, "fields"), f"Form field name '{name}' is used twice."


def _unsafe_strings(value: object, path: str) -> Iterator[Finding]:
    if isinstance(value, str):
        if _UNSAFE_CONTENT.search(value):
            yield path, "Text contains markup or a script URL; only plain text is allowed."
    elif isinstance(value, dict):
        for key, nested in value.items():
            yield from _unsafe_strings(nested, _join(path, str(key)))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _unsafe_strings(nested, _join(path, str(index)))


def check_unsafe_content(rule_input: RuleInput) -> Iterator[Finding]:
    yield from _unsafe_strings(rule_input.page.model_dump(mode="json"), "")
    if rule_input.application is not None:
        described = rule_input.application.model_dump(mode="json")
        for path, message in _unsafe_strings(described, "application"):
            yield f"@{path}", message


SEMANTIC_RULES: tuple[SemanticRule, ...] = (
    check_size,
    check_unique_ids,
    check_application_structure,
    check_navigation,
    check_entities,
    check_assets,
    check_data,
    check_actions,
    check_references,
    check_component_consistency,
    check_unsafe_content,
)
