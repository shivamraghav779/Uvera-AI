"""Schema-based comparison of two UI documents.

Produces a list of human-readable changes ("Theme changed from light to dark",
"“Regional sales” replaced with bar chart"). It compares structure and tokens,
never pixels, and identifies components by their stable ids.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.domains.generative_ui.mutation_engine import Node, kind_label, node_label, slots_of

_STRUCTURE_KEYS = frozenset({"children", "components", "fields"})
_PLACEMENT_KEYS = frozenset({"layout", "style"})
MAX_LISTED_PROPS = 3
MAX_LISTED_COLOURS = 4


class ChangeKind(StrEnum):
    THEME = "theme"
    FRAMEWORK = "framework"
    DESIGN_SYSTEM = "design_system"
    ADDED = "added"
    REMOVED = "removed"
    REPLACED = "replaced"
    MOVED = "moved"
    RESIZED = "resized"
    RESTYLED = "restyled"
    UPDATED = "updated"
    NAVIGATION = "navigation"
    APPLICATION = "application"
    DATA = "data"


@dataclass(frozen=True, slots=True)
class Change:
    kind: ChangeKind
    summary: str
    component_id: str | None = None


@dataclass(frozen=True, slots=True)
class _Entry:
    node: Node
    slot_id: str | None
    parent_component_id: str | None


def _own_props(node: Node) -> dict[str, Any]:
    """A node's fields without its children (tabs keep only their id and label)."""
    props = {
        key: value
        for key, value in node.items()
        if key not in _STRUCTURE_KEYS and key not in _PLACEMENT_KEYS
    }
    if "tabs" in props:
        props["tabs"] = [{"id": tab["id"], "label": tab["label"]} for tab in props["tabs"]]
    return props


def _index(page: Node) -> tuple[dict[str, _Entry], dict[str, list[str]]]:
    entries: dict[str, _Entry] = {page["id"]: _Entry(page, None, None)}
    slots: dict[str, list[str]] = {}

    def visit(node: Node) -> None:
        for slot_id, children in slots_of(node):
            slots[slot_id] = [child["id"] for child in children]
            for child in children:
                entries[child["id"]] = _Entry(child, slot_id, node["id"])
                visit(child)

    visit(page)
    return entries, slots


def _token_changes(old: Node, new: Node) -> list[Change]:
    changes: list[Change] = []
    old_theme, new_theme = old["theme"], new["theme"]
    if old_theme["mode"] != new_theme["mode"]:
        summary = f"Theme changed from {old_theme['mode']} to {new_theme['mode']}"
        changes.append(Change(ChangeKind.THEME, summary))
    colours = [
        name
        for name, value in new_theme["colors"].items()
        if old_theme["colors"].get(name) != value
    ]
    if len(colours) > MAX_LISTED_COLOURS:
        changes.append(Change(ChangeKind.THEME, "Colour palette changed"))
    elif colours:
        changes.append(Change(ChangeKind.THEME, f"Colours changed: {', '.join(colours)}"))
    for token in (
        "radius", "density", "spacing", "shadows", "typography", "surface", "motion", "gradient",
    ):  # fmt: skip
        if old_theme.get(token) != new_theme.get(token):
            changes.append(Change(ChangeKind.THEME, f"{token.capitalize()} changed"))
    if old["design"]["framework"] != new["design"]["framework"]:
        summary = (
            f"Framework changed from {old['design']['framework']} to {new['design']['framework']}"
        )
        changes.append(Change(ChangeKind.FRAMEWORK, summary))
    if old["design"]["design_system"] != new["design"]["design_system"]:
        summary = (
            f"Visual style changed from {old['design']['design_system']} "
            f"to {new['design']['design_system']}"
        )
        changes.append(Change(ChangeKind.DESIGN_SYSTEM, summary))
    return changes


def _application_changes(old: Node, new: Node) -> list[Change]:
    """Differences in the product around the screens."""
    before, after = old.get("application"), new.get("application")
    if before is None and after is None:
        return []
    if before is None or after is None:
        summary = "Became an application" if after else "Became a single view"
        return [Change(ChangeKind.APPLICATION, summary)]
    changes: list[Change] = []
    old_nav, new_nav = before["navigation"], after["navigation"]
    if old_nav.get("style") != new_nav.get("style"):
        summary = f"Navigation changed from {old_nav.get('style')} to {new_nav.get('style')}"
        changes.append(Change(ChangeKind.NAVIGATION, summary))
    if {k: v for k, v in old_nav.items() if k != "style"} != {
        k: v for k, v in new_nav.items() if k != "style"
    }:
        changes.append(Change(ChangeKind.NAVIGATION, "Navigation items changed"))
    described = ("name", "category", "description", "target_users", "goals", "features")
    changed = [key for key in described if before.get(key) != after.get(key)]
    if changed:
        changes.append(Change(ChangeKind.APPLICATION, f"Application {', '.join(changed)} changed"))
    if before.get("design_direction") != after.get("design_direction"):
        changes.append(Change(ChangeKind.APPLICATION, "Design direction changed"))
    old_entities = {entity["name"]: entity for entity in before.get("entities", [])}
    new_entities = {entity["name"]: entity for entity in after.get("entities", [])}
    for name, entity in new_entities.items():
        if name not in old_entities:
            changes.append(Change(ChangeKind.DATA, f"Data “{entity['label']}” added"))
        elif old_entities[name] != entity:
            changes.append(Change(ChangeKind.DATA, f"Data “{entity['label']}” changed"))
    changes += [
        Change(ChangeKind.DATA, f"Data “{entity['label']}” removed")
        for name, entity in old_entities.items()
        if name not in new_entities
    ]
    old_assets = {asset["id"] for asset in before.get("assets", [])}
    new_assets = {asset["id"] for asset in after.get("assets", [])}
    added, removed = len(new_assets - old_assets), len(old_assets - new_assets)
    if added or removed:
        parts = [f"{added} added"] * bool(added) + [f"{removed} removed"] * bool(removed)
        changes.append(Change(ChangeKind.APPLICATION, f"Images: {', '.join(parts)}"))
    return changes


def _component_changes(component_id: str, old: _Entry, new: _Entry) -> list[Change]:
    label = f"“{node_label(new.node, component_id)}”"
    if old.node.get("type") != new.node.get("type"):
        summary = (
            f"{kind_label(old.node).capitalize()} {label} replaced with {kind_label(new.node)}"
        )
        return [Change(ChangeKind.REPLACED, summary, component_id)]
    changes: list[Change] = []
    if old.slot_id != new.slot_id:
        changes.append(
            Change(ChangeKind.MOVED, f"{label} moved to another container", component_id)
        )
    if old.node.get("layout") != new.node.get("layout"):
        changes.append(Change(ChangeKind.RESIZED, f"{label} resized", component_id))
    if old.node.get("style") != new.node.get("style"):
        changes.append(Change(ChangeKind.RESTYLED, f"{label} restyled", component_id))
    old_props, new_props = _own_props(old.node), _own_props(new.node)
    changed = sorted(
        key
        for key in old_props.keys() | new_props.keys()
        if old_props.get(key) != new_props.get(key)
    )
    if changed:
        listed = ", ".join(changed[:MAX_LISTED_PROPS]) + (
            "…" if len(changed) > MAX_LISTED_PROPS else ""
        )
        changes.append(Change(ChangeKind.UPDATED, f"{label} updated ({listed})", component_id))
    return changes


def _order_changes(
    old_slots: dict[str, list[str]], new_slots: dict[str, list[str]], new_entries: dict[str, _Entry]
) -> list[Change]:
    changes: list[Change] = []
    for slot_id, new_order in new_slots.items():
        old_order = old_slots.get(slot_id)
        if old_order is None:
            continue
        shared = set(old_order) & set(new_order)
        if [i for i in old_order if i in shared] != [i for i in new_order if i in shared]:
            owner = new_entries.get(slot_id)
            label = node_label(owner.node if owner else None, slot_id)
            changes.append(Change(ChangeKind.MOVED, f"Items reordered in “{label}”", slot_id))
    return changes


def diff_documents(old: Node, new: Node) -> list[Change]:
    """Changes that turn ``old`` into ``new`` (both in canonical JSON form)."""
    old_entries, old_slots = _index(old["page"])
    new_entries, new_slots = _index(new["page"])
    changes = _token_changes(old, new) + _application_changes(old, new)

    for component_id, entry in new_entries.items():
        previous = old_entries.get(component_id)
        if previous is not None:
            changes += _component_changes(component_id, previous, entry)
        elif entry.parent_component_id in old_entries or entry.parent_component_id is None:
            # Report only the top of an added subtree.
            summary = f"{kind_label(entry.node).capitalize()} “{node_label(entry.node)}” added"
            changes.append(Change(ChangeKind.ADDED, summary, component_id))

    for component_id, entry in old_entries.items():
        if component_id in new_entries:
            continue
        if entry.parent_component_id in new_entries or entry.parent_component_id is None:
            summary = f"{kind_label(entry.node).capitalize()} “{node_label(entry.node)}” removed"
            changes.append(Change(ChangeKind.REMOVED, summary, component_id))

    return changes + _order_changes(old_slots, new_slots, new_entries)
