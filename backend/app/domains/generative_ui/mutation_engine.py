"""Applies operations to a UI document.

The engine works on plain JSON (dicts and lists) so that its behaviour can be
mirrored exactly by the frontend engine (``mutationEngine.ts``). It only
restructures data; the result must still pass the validator before it is used.

Vocabulary: a *slot* is a list that holds child components. Containers have one
slot addressed by the container's id; a ``tabs`` component has one slot per tab,
addressed by the tab's id.
"""

import copy
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.domains.generative_ui.design_registry import merge_theme

Node = dict[str, Any]

_CHILD_KEY_BY_TYPE: Mapping[str, str] = {
    "page": "components",
    "section": "children",
    "card": "children",
    "modal": "children",
    "form": "fields",
    "screen": "children",
}
_TABS = "tabs"
_UNGROUPABLE = frozenset({"section", "card"})
# UPDATE may not touch identity, placement, styling or structure.
PROTECTED_PROPS = frozenset(
    {"id", "type", "layout", "style", "children", "components", "fields", "tabs"}
)
_THEME_IDENTITY_TOKENS = frozenset({"mode", "colors"})
_APPLICATION = "application"
_NAVIGATION_FIELDS = ("style", "brand", "tagline", "home", "items", "action")
# UPDATE_APPLICATION may only touch descriptive fields; the rest have their own operations.
APPLICATION_PROPS = frozenset(
    {
        "name",
        "category",
        "description",
        "target_users",
        "goals",
        "features",
        "interactions",
        "design_direction",
    }
)


class MutationError(Exception):
    """An operation cannot be applied to the document it was given."""

    def __init__(self, index: int, message: str) -> None:
        super().__init__(message)
        self.index = index
        self.message = message


class _RejectError(Exception):
    pass


@dataclass(slots=True)
class _Location:
    node: Node
    siblings: list[Node]
    index: int
    slot_id: str


def slots_of(node: Node) -> list[tuple[str, list[Node]]]:
    """The child slots of ``node`` as ``(slot id, children)`` pairs."""
    if node.get("type") == _TABS:
        return [(tab["id"], tab["children"]) for tab in node.get(_TABS, [])]
    key = _CHILD_KEY_BY_TYPE.get(str(node.get("type")))
    return [(node["id"], node[key])] if key and key in node else []


def iter_slots(root: Node) -> Iterator[tuple[str, list[Node]]]:
    for slot_id, children in slots_of(root):
        yield slot_id, children
        for child in children:
            yield from iter_slots(child)


def iter_nodes(root: Node) -> Iterator[Node]:
    yield root
    for _, children in slots_of(root):
        for child in children:
            yield from iter_nodes(child)


def _locate(page: Node, target: str) -> _Location:
    for slot_id, children in iter_slots(page):
        for index, child in enumerate(children):
            if child.get("id") == target:
                return _Location(child, children, index, slot_id)
    raise _RejectError(f"Component '{target}' does not exist.")


def _slot(page: Node, slot_id: str) -> list[Node]:
    for candidate, children in iter_slots(page):
        if candidate == slot_id:
            return children
    raise _RejectError(f"'{slot_id}' is not a container that can hold components.")


def _insertion_index(siblings: list[Node], operation: Node) -> int:
    for anchor, offset in (("before", 0), ("after", 1)):
        anchor_id = operation.get(anchor)
        if anchor_id is None:
            continue
        for index, sibling in enumerate(siblings):
            if sibling.get("id") == anchor_id:
                return index + offset
        raise _RejectError(f"'{anchor_id}' is not in the destination container.")
    position = operation.get("index")
    return len(siblings) if position is None else min(int(position), len(siblings))


def _create(document: Node, operation: Node) -> None:
    page = document["page"]
    siblings = _slot(page, operation.get("parent_id") or page["id"])
    siblings.insert(_insertion_index(siblings, operation), operation["component"])


def _application(document: Node) -> Node:
    application = document.get(_APPLICATION)
    if not isinstance(application, dict):
        raise _RejectError("This UI is not an application.")
    return application


def _prune_navigation(document: Node) -> None:
    """Keep the shell consistent with the screens that exist."""
    application = document.get(_APPLICATION)
    if not isinstance(application, dict):
        return
    screen_ids = [
        child["id"] for child in document["page"]["components"] if child.get("type") == "screen"
    ]
    navigation = application["navigation"]
    navigation["items"] = [
        item for item in navigation.get("items", []) if item["screen_id"] in screen_ids
    ]
    action = navigation.get("action")
    if action is not None and action["screen_id"] not in screen_ids:
        del navigation["action"]
    if navigation.get("home") not in screen_ids and screen_ids:
        navigation["home"] = screen_ids[0]


def _delete(document: Node, operation: Node) -> None:
    location = _locate(document["page"], operation["target"])
    removed = location.siblings[location.index]
    del location.siblings[location.index]
    if removed.get("type") == "screen":
        _prune_navigation(document)


def _move(document: Node, operation: Node) -> None:
    page = document["page"]
    location = _locate(page, operation["target"])
    destination_id = operation.get("parent_id") or location.slot_id
    if any(slot_id == destination_id for slot_id, _ in iter_slots(location.node)):
        raise _RejectError("A component cannot be moved into itself.")
    destination = _slot(page, destination_id)
    del location.siblings[location.index]
    destination.insert(_insertion_index(destination, operation), location.node)


def _resize(document: Node, operation: Node) -> None:
    node = _locate(document["page"], operation["target"]).node
    layout = dict(node.get("layout") or {})
    for key in ("span", "height"):
        if operation.get(key) is not None:
            layout[key] = operation[key]
    node["layout"] = layout


def _style(document: Node, operation: Node) -> None:
    node = _locate(document["page"], operation["target"]).node
    style = dict(node.get("style") or {})
    for key, value in operation["style"].items():
        if value is None:
            style.pop(key, None)
        else:
            style[key] = value
    if style:
        node["style"] = style
    else:
        node.pop("style", None)


def _find_tab(page: Node, tab_id: str) -> Node | None:
    for node in iter_nodes(page):
        for tab in node.get(_TABS, []) if node.get("type") == _TABS else []:
            if tab.get("id") == tab_id:
                return tab  # type: ignore[no-any-return]
    return None


def _update(document: Node, operation: Node) -> None:
    page, target = document["page"], operation["target"]
    is_page = target == page["id"]
    node = page if is_page else _find_tab(page, target) or _locate(page, target).node
    for key, value in operation["props"].items():
        if key in PROTECTED_PROPS:
            raise _RejectError(f"UPDATE cannot change '{key}'.")
        if value is None:
            node.pop(key, None)
        else:
            node[key] = value


def _reorder(document: Node, operation: Node) -> None:
    siblings = _slot(document["page"], operation["parent_id"])
    by_id = {child["id"]: child for child in siblings}
    order = operation["order"]
    if len(order) != len(by_id) or set(order) != set(by_id):
        raise _RejectError("REORDER must list every child of the container exactly once.")
    siblings[:] = [by_id[component_id] for component_id in order]


def _group(document: Node, operation: Node) -> None:
    page = document["page"]
    locations = [_locate(page, target) for target in dict.fromkeys(operation["targets"])]
    if len({location.slot_id for location in locations}) != 1:
        raise _RejectError("GROUP targets must share the same parent.")
    siblings = locations[0].siblings
    members = sorted(locations, key=lambda location: location.index)
    spec = operation["group"]
    container: Node = {"type": spec.get("type", "section"), "id": spec["id"]}
    if spec.get("title"):
        container["title"] = spec["title"]
    container["children"] = [member.node for member in members]
    position = members[0].index
    member_ids = {member.node["id"] for member in members}
    siblings[:] = [child for child in siblings if child["id"] not in member_ids]
    siblings.insert(position, container)


def _ungroup(document: Node, operation: Node) -> None:
    location = _locate(document["page"], operation["target"])
    if location.node.get("type") not in _UNGROUPABLE:
        raise _RejectError("Only a section or card can be ungrouped.")
    location.siblings[location.index : location.index + 1] = location.node["children"]


def _replace(document: Node, operation: Node) -> None:
    location = _locate(document["page"], operation["target"])
    replaced = location.siblings[location.index]
    location.siblings[location.index] = operation["component"]
    if replaced.get("type") == "screen" and operation["component"].get("id") != replaced["id"]:
        _prune_navigation(document)


def _set_theme(document: Node, operation: Node) -> None:
    tokens = operation.get("tokens") or {}
    theme = merge_theme(document["theme"], tokens)
    if operation.get("preset") is not None:
        theme["preset"] = operation["preset"]
    elif _THEME_IDENTITY_TOKENS & tokens.keys():
        # Colours no longer match the preset they came from.
        theme.pop("preset", None)
    document["theme"] = theme


def _set_framework(document: Node, operation: Node) -> None:
    document["design"] = {**document["design"], "framework": operation["framework"]}


def _set_design_system(document: Node, operation: Node) -> None:
    document["design"] = {**document["design"], "design_system": operation["design_system"]}
    document["theme"] = merge_theme(document["theme"], operation.get("tokens") or {})


def _set_navigation(document: Node, operation: Node) -> None:
    navigation = dict(_application(document)["navigation"])
    for key in _NAVIGATION_FIELDS:
        if key not in operation:
            continue
        if operation[key] is None:
            navigation.pop(key, None)
        else:
            navigation[key] = operation[key]
    document[_APPLICATION] = {**document[_APPLICATION], "navigation": navigation}


def _update_application(document: Node, operation: Node) -> None:
    application = dict(_application(document))
    for key, value in operation["props"].items():
        if key not in APPLICATION_PROPS:
            raise _RejectError(f"UPDATE_APPLICATION cannot change '{key}'.")
        if value is None:
            application.pop(key, None)
        else:
            application[key] = value
    document[_APPLICATION] = application


def _upsert(existing: list[Node], incoming: list[Node], key: str) -> list[Node]:
    """``existing`` with each incoming item replacing the one of the same key, or appended."""
    merged = list(existing)
    positions = {item[key]: index for index, item in enumerate(merged)}
    for item in incoming:
        if item[key] in positions:
            merged[positions[item[key]]] = item
        else:
            positions[item[key]] = len(merged)
            merged.append(item)
    return merged


def _add_assets(document: Node, operation: Node) -> None:
    application = _application(document)
    assets = _upsert(application.get("assets", []), operation["assets"], "id")
    document[_APPLICATION] = {**application, "assets": assets}


def _upsert_entities(document: Node, operation: Node) -> None:
    application = _application(document)
    entities = _upsert(application.get("entities", []), operation["entities"], "name")
    document[_APPLICATION] = {**application, "entities": entities}


_HANDLERS: Mapping[str, Callable[[Node, Node], None]] = {
    "CREATE": _create,
    "DELETE": _delete,
    "MOVE": _move,
    "RESIZE": _resize,
    "STYLE": _style,
    "UPDATE": _update,
    "REORDER": _reorder,
    "GROUP": _group,
    "UNGROUP": _ungroup,
    "REPLACE": _replace,
    "SET_THEME": _set_theme,
    "SET_FRAMEWORK": _set_framework,
    "SET_DESIGN_SYSTEM": _set_design_system,
    "SET_NAVIGATION": _set_navigation,
    "UPDATE_APPLICATION": _update_application,
    "ADD_ASSETS": _add_assets,
    "UPSERT_ENTITIES": _upsert_entities,
}


def apply_operations(document: Node, operations: Sequence[Node]) -> Node:
    """Return a new document with ``operations`` applied in order.

    Raises ``MutationError`` (carrying the operation's index) on the first
    operation that cannot be applied; the input is never modified.
    """
    result = copy.deepcopy(document)
    for index, operation in enumerate(operations):
        handler = _HANDLERS.get(str(operation.get("type")))
        if handler is None:
            raise MutationError(index, f"Unknown operation type '{operation.get('type')}'.")
        try:
            handler(result, copy.deepcopy(operation))
        except _RejectError as exc:
            raise MutationError(index, str(exc)) from None
    return result


# --- Human-readable descriptions ----------------------------------------------


def find_node(page: Node, component_id: str) -> Node | None:
    return next((node for node in iter_nodes(page) if node.get("id") == component_id), None)


def node_label(node: Node | None, fallback: str = "") -> str:
    """How a person would refer to a component."""
    if node is None:
        return fallback
    return str(node.get("title") or node.get("label") or node.get("id") or fallback)


def kind_label(node: Node) -> str:
    if node.get("type") == "chart":
        return f"{node.get('chart_type', '')} chart".strip()
    return str(node.get("type", "component")).replace("_", " ")


def _quoted(page: Node, component_id: str) -> str:
    return f"“{node_label(find_node(page, component_id), component_id)}”"


def describe_operation(operation: Node, document: Node) -> str:
    """One sentence describing ``operation`` against the document it applies to."""
    page, kind = document["page"], operation.get("type")
    target = str(operation.get("target", ""))
    if kind == "CREATE":
        component = operation["component"]
        return f"Add {kind_label(component)} “{node_label(component)}”"
    if kind == "DELETE":
        return f"Remove {_quoted(page, target)}"
    if kind == "MOVE":
        for anchor in ("before", "after"):
            if operation.get(anchor):
                return f"Move {_quoted(page, target)} {anchor} {_quoted(page, operation[anchor])}"
        if operation.get("parent_id"):
            return f"Move {_quoted(page, target)} into {_quoted(page, operation['parent_id'])}"
        return f"Move {_quoted(page, target)}"
    if kind == "RESIZE":
        parts = []
        if operation.get("span") is not None:
            parts.append(f"{operation['span']} of 12 columns wide")
        if operation.get("height") is not None:
            parts.append(f"height {operation['height']}")
        return f"Resize {_quoted(page, target)} to {' and '.join(parts)}"
    if kind == "STYLE":
        return f"Restyle {_quoted(page, target)}"
    if kind == "UPDATE":
        return f"Update {', '.join(operation['props'])} of {_quoted(page, target)}"
    if kind == "REORDER":
        return f"Reorder the contents of {_quoted(page, operation['parent_id'])}"
    if kind == "GROUP":
        group = operation["group"]
        return f"Group {len(operation['targets'])} components into “{node_label(group)}”"
    if kind == "UNGROUP":
        return f"Ungroup {_quoted(page, target)}"
    if kind == "REPLACE":
        return f"Replace {_quoted(page, target)} with a {kind_label(operation['component'])}"
    if kind == "SET_THEME":
        preset = operation.get("preset")
        return f"Change theme to {preset}" if preset else "Adjust theme tokens"
    if kind == "SET_FRAMEWORK":
        return f"Render with the {operation['framework']} framework"
    if kind == "SET_DESIGN_SYSTEM":
        return f"Switch visual style to {operation['design_system']}"
    if kind == "SET_NAVIGATION":
        if operation.get("style"):
            return f"Change navigation to {operation['style']}"
        return "Update the navigation"
    if kind == "UPDATE_APPLICATION":
        return f"Update the application's {', '.join(sorted(operation['props']))}"
    if kind == "ADD_ASSETS":
        count = len(operation["assets"])
        return f"Add {count} image{'' if count == 1 else 's'}"
    if kind == "UPSERT_ENTITIES":
        names = ", ".join(entity["label"] for entity in operation["entities"])
        return f"Update data: {names}"
    return f"Apply {kind}"


def affected_component_ids(operation: Node) -> list[str]:
    """Ids a client should highlight for ``operation``."""
    ids = [operation[key] for key in ("target",) if operation.get(key)]
    ids += list(operation.get("targets", []))
    for key in ("component", "group"):
        if isinstance(operation.get(key), Mapping) and operation[key].get("id"):
            ids.append(operation[key]["id"])
    if operation.get("type") == "REORDER":
        ids.append(operation["parent_id"])
    return list(dict.fromkeys(ids))
