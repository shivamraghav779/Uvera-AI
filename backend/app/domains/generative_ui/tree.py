"""Traversal helpers for a UI component tree."""

from collections.abc import Iterator
from dataclasses import dataclass

from app.domains.generative_ui.schemas import (
    ActionButton,
    ActionSpec,
    AnyComponent,
    ButtonComponent,
    CalendarComponent,
    CardComponent,
    CheckboxComponent,
    CollectionComponent,
    CommandComponent,
    CtaComponent,
    FooterComponent,
    FormComponent,
    GalleryComponent,
    HeroComponent,
    InputComponent,
    KanbanComponent,
    MediaComponent,
    ModalComponent,
    PageComponent,
    PricingComponent,
    ProfileHeaderComponent,
    ScreenComponent,
    SectionComponent,
    SelectComponent,
    TableComponent,
    TabsComponent,
)

FormControl = InputComponent | SelectComponent | CheckboxComponent
_ChildList = SectionComponent | CardComponent | ModalComponent | ScreenComponent
_ButtonList = HeroComponent | CtaComponent | MediaComponent | ProfileHeaderComponent
_ItemAction = CollectionComponent | KanbanComponent | CalendarComponent


@dataclass(frozen=True, slots=True)
class ComponentNode:
    component: AnyComponent
    path: str
    depth: int


def child_components(component: AnyComponent) -> list[tuple[str, AnyComponent]]:
    """Direct children of ``component`` with their path segment."""
    if isinstance(component, PageComponent):
        return [(f"components.{i}", child) for i, child in enumerate(component.components)]
    if isinstance(component, _ChildList):
        return [(f"children.{i}", child) for i, child in enumerate(component.children)]
    if isinstance(component, FormComponent):
        return [(f"fields.{i}", field) for i, field in enumerate(component.fields)]
    if isinstance(component, TabsComponent):
        return [
            (f"tabs.{t}.children.{i}", child)
            for t, tab in enumerate(component.tabs)
            for i, child in enumerate(tab.children)
        ]
    return []


def walk(root: AnyComponent, path: str = "", depth: int = 1) -> Iterator[ComponentNode]:
    """Yield every node of the tree, parents before children."""
    yield ComponentNode(component=root, path=path, depth=depth)
    for segment, child in child_components(root):
        yield from walk(child, f"{path}.{segment}" if path else segment, depth + 1)


def screens(page: PageComponent) -> list[ScreenComponent]:
    """The screens of an application document (empty for a single view)."""
    return [child for child in page.components if isinstance(child, ScreenComponent)]


def _buttons(prefix: str, buttons: list[ActionButton]) -> list[tuple[str, ActionSpec]]:
    return [(f"{prefix}.{i}.action", button.action) for i, button in enumerate(buttons)]


def action_specs(component: AnyComponent) -> list[tuple[str, ActionSpec]]:
    """Actions declared directly on ``component``, with the field holding them."""
    if isinstance(component, ButtonComponent):
        return [("action", component.action)]
    if isinstance(component, FormComponent):
        return [("submit_action", component.submit_action)]
    if isinstance(component, FormControl) and component.on_change is not None:
        return [("on_change", component.on_change)]
    if isinstance(component, _ButtonList):
        return _buttons("actions", component.actions)
    if isinstance(component, TableComponent) and component.row_action is not None:
        return [("row_action", component.row_action)]
    if isinstance(component, _ItemAction):
        found = [("item_action", component.item_action)] if component.item_action else []
        if isinstance(component, KanbanComponent) and component.move_action is not None:
            found.append(("move_action", component.move_action))
        return found
    if isinstance(component, PricingComponent):
        return [
            (f"plans.{i}.action.action", plan.action.action)
            for i, plan in enumerate(component.plans)
            if plan.action is not None
        ]
    if isinstance(component, GalleryComponent):
        return [
            (f"items.{i}.action", item.action)
            for i, item in enumerate(component.items)
            if item.action is not None
        ]
    if isinstance(component, CommandComponent):
        return [(f"items.{i}.action", item.action) for i, item in enumerate(component.items)]
    if isinstance(component, FooterComponent):
        return [
            (f"columns.{c}.links.{i}.action", link.action)
            for c, column in enumerate(component.columns)
            for i, link in enumerate(column.links)
            if link.action is not None
        ]
    return []
