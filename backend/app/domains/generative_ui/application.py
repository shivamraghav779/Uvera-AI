"""Application-level views of a UI document: routes, data entities and the screen graph.

An application is a document whose page holds ``screen`` components and which
carries an ``application`` section. Everything here is derived from the
document; nothing is stored separately, so a version is always self-describing.
"""

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from typing import Any

from app.domains.actions.schemas import ActionType
from app.domains.common import DataRow
from app.domains.data_sources.schemas import DatasetDescriptor, DatasetField, FieldKind
from app.domains.generative_ui.document import (
    PRIMARY_KEY,
    Entity,
    EntityFieldType,
    UIDocument,
)
from app.domains.generative_ui.schemas import AnyComponent, ScreenComponent
from app.domains.generative_ui.tree import action_specs, screens, walk

_PARAM = re.compile(r":([A-Za-z][A-Za-z0-9_]*)")
_NUMERIC_TYPES = frozenset(
    {EntityFieldType.NUMBER, EntityFieldType.CURRENCY, EntityFieldType.PERCENT}
)
NAVIGATE_TO = "to"


# --- Routes -----------------------------------------------------------------------


def route_params(route: str) -> list[str]:
    """Parameter names of a route: ``/jobs/:jobId`` -> ``["jobId"]``."""
    return _PARAM.findall(route)


def _segments(path: str) -> list[str]:
    return [segment for segment in path.split("?")[0].split("/") if segment]


def match_route(route: str, path: str) -> dict[str, str] | None:
    """Parameters if ``path`` is an instance of ``route``, else ``None``."""
    pattern, actual = _segments(route), _segments(path)
    if len(pattern) != len(actual):
        return None
    params: dict[str, str] = {}
    for expected, value in zip(pattern, actual, strict=True):
        if expected.startswith(":"):
            params[expected[1:]] = value
        elif expected != value:
            return None
    return params


def resolve_route(routes: Mapping[str, str], path: str) -> str | None:
    """Id of the screen ``path`` leads to. ``routes`` maps screen id -> route.

    ``path`` may be a route itself (``/jobs/:jobId``, filled in at run time) or a
    concrete path (``/jobs/j-102``). Static routes win over parameterised ones.
    """
    for screen_id, route in routes.items():
        if _segments(route) == _segments(path):
            return screen_id
    for screen_id, route in routes.items():
        if match_route(route, path) is not None:
            return screen_id
    return None


def screen_routes(document: UIDocument) -> dict[str, str]:
    return {screen.id: screen.route for screen in screens(document.page)}


# --- Entities as datasets -----------------------------------------------------------


def entity_descriptor(entity: Entity) -> DatasetDescriptor:
    """How an entity looks to everything that works with datasets."""
    fields = [DatasetField(name=PRIMARY_KEY, kind=FieldKind.STRING)]
    fields += [
        DatasetField(
            name=field.key,
            kind=FieldKind.NUMBER if field.type in _NUMERIC_TYPES else FieldKind.STRING,
        )
        for field in entity.fields
        if field.key != PRIMARY_KEY
    ]
    return DatasetDescriptor(
        name=entity.name,
        description=entity.description or f"{entity.label} of the application.",
        fields=fields,
    )


def entity_datasets(document: UIDocument) -> dict[str, DatasetDescriptor]:
    if document.application is None:
        return {}
    return {entity.name: entity_descriptor(entity) for entity in document.application.entities}


def entity_rows(entity: Entity) -> list[DataRow]:
    """Records with every declared field present, in declaration order."""
    keys = [PRIMARY_KEY, *(field.key for field in entity.fields if field.key != PRIMARY_KEY)]
    return [{key: record.get(key) for key in keys} for record in entity.records]


# --- Image references ---------------------------------------------------------------

# Fields that hold an asset id, wherever they appear inside a component.
_IMAGE_KEYS = frozenset({"image", "avatar"})


def image_refs(value: object, path: str = "") -> Iterator[tuple[str, str]]:
    """``(path, asset id)`` for every image reference inside a dumped component.

    ``fields.image`` / ``fields.avatar`` of record components name *fields* (or
    are booleans), not assets, and are skipped.
    """
    if isinstance(value, dict):
        for key, nested in value.items():
            child = f"{path}.{key}" if path else str(key)
            if key == "fields" and isinstance(nested, dict):
                continue
            if key in _IMAGE_KEYS and isinstance(nested, str):
                yield child, nested
            else:
                yield from image_refs(nested, child)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from image_refs(nested, f"{path}.{index}" if path else str(index))


# --- Application graph --------------------------------------------------------------


class EdgeKind(StrEnum):
    NAVIGATION = "navigation"
    ACTION = "action"
    DATA = "data"


@dataclass(frozen=True, slots=True)
class GraphNode:
    id: str
    title: str
    route: str
    screen_type: str
    in_navigation: bool
    is_home: bool
    component_count: int
    datasets: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: str
    target: str
    kind: EdgeKind
    label: str | None = None


@dataclass(frozen=True, slots=True)
class ApplicationGraph:
    """Screens and how they relate: the shell's links, transitions triggered by
    actions, and entities shared between screens."""

    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]

    def reachable_from(self, start: str) -> set[str]:
        """Screens a user can get to from ``start`` by navigation or actions."""
        outgoing: dict[str, set[str]] = {}
        for edge in self.edges:
            if edge.kind is not EdgeKind.DATA:
                outgoing.setdefault(edge.source, set()).add(edge.target)
        in_shell = {node.id for node in self.nodes if node.in_navigation}
        seen: set[str] = set()
        frontier = [start, *in_shell]
        while frontier:
            current = frontier.pop()
            if current in seen:
                continue
            seen.add(current)
            frontier.extend(outgoing.get(current, ()))
        return seen


def bound_dataset_names(value: object) -> list[str]:
    """Dataset names referenced by any ``data_source`` inside a dumped component tree."""
    names: list[str] = []

    def visit(node: object) -> None:
        if isinstance(node, dict):
            source = node.get("data_source")
            if isinstance(source, dict) and isinstance(source.get("dataset"), str):
                names.append(source["dataset"])
            for nested in node.values():
                visit(nested)
        elif isinstance(node, list):
            for nested in node:
                visit(nested)

    visit(value)
    return list(dict.fromkeys(names))


def navigation_targets(
    component: AnyComponent, routes: Mapping[str, str]
) -> Iterator[tuple[str, str]]:
    """``(screen id, label)`` for each in-app navigation the component can trigger."""
    for _field, action in action_specs(component):
        destination: Any = None
        if action.type is ActionType.NAVIGATE:
            destination = action.payload.get(NAVIGATE_TO)
        elif action.type in (ActionType.RECORD_CREATE, ActionType.RECORD_DELETE):
            destination = action.payload.get("navigate_to")
        if isinstance(destination, str) and destination.startswith("/"):
            target = resolve_route(routes, destination)
            if target is not None:
                yield target, action.type.value


def _screen_node(screen: ScreenComponent, document: UIDocument) -> GraphNode:
    application = document.application
    navigation = application.navigation if application else None
    in_shell = {item.screen_id for item in navigation.items} if navigation else set()
    if navigation and navigation.action:
        in_shell.add(navigation.action.screen_id)
    return GraphNode(
        id=screen.id,
        title=screen.title,
        route=screen.route,
        screen_type=screen.screen_type.value,
        in_navigation=screen.id in in_shell,
        is_home=bool(navigation and navigation.home == screen.id),
        component_count=sum(1 for _ in walk(screen)) - 1,
        datasets=tuple(bound_dataset_names(screen.model_dump(mode="json"))),
    )


def build_graph(document: UIDocument) -> ApplicationGraph:
    routes = screen_routes(document)
    app_screens = screens(document.page)
    nodes = tuple(_screen_node(screen, document) for screen in app_screens)
    edges: list[GraphEdge] = []
    for screen in app_screens:
        for node in walk(screen):
            for target, label in navigation_targets(node.component, routes):
                if target != screen.id:
                    edges.append(GraphEdge(screen.id, target, EdgeKind.ACTION, label))
    # Screens showing the same entity depend on the same data.
    by_dataset: dict[str, list[str]] = {}
    for graph_node in nodes:
        for dataset in graph_node.datasets:
            by_dataset.setdefault(dataset, []).append(graph_node.id)
    for dataset, screen_ids in by_dataset.items():
        edges += [
            GraphEdge(first, second, EdgeKind.DATA, dataset)
            for first, second in pairwise(screen_ids)
        ]
    home = next((node.id for node in nodes if node.is_home), None)
    if home is not None:
        edges += [
            GraphEdge(home, node.id, EdgeKind.NAVIGATION)
            for node in nodes
            if node.in_navigation and node.id != home
        ]
    unique = list(dict.fromkeys(edges))
    return ApplicationGraph(nodes=nodes, edges=tuple(unique))


def unreachable_screens(document: UIDocument) -> list[str]:
    """Screens no navigation item or action leads to (the home screen is always reachable)."""
    application = document.application
    if application is None:
        return []
    graph = build_graph(document)
    reachable = graph.reachable_from(application.navigation.home)
    return [node.id for node in graph.nodes if node.id not in reachable]


def first_records(entities: Sequence[Entity], limit: int) -> dict[str, list[DataRow]]:
    return {entity.name: entity_rows(entity)[:limit] for entity in entities}
