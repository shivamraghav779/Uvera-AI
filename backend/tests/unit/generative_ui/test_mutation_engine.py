"""The mutation engine works on plain JSON; these tests pin its exact semantics.

The frontend engine (mutationEngine.ts) is tested against the same cases through
the exported contract fixtures.
"""

import copy
from typing import Any

import pytest

from app.domains.generative_ui.layout_map import render_layout_map
from app.domains.generative_ui.mutation_engine import (
    MutationError,
    affected_component_ids,
    apply_operations,
    describe_operation,
)
from tests.support import canonical_document

Document = dict[str, Any]


@pytest.fixture
def document() -> Document:
    return canonical_document()


def _ids(children: list[dict[str, Any]]) -> list[str]:
    return [child["id"] for child in children]


def _page_ids(document: Document) -> list[str]:
    return _ids(document["page"]["components"])


def _apply(document: Document, *operations: dict[str, Any]) -> Document:
    return apply_operations(document, list(operations))


def _reject(document: Document, *operations: dict[str, Any]) -> MutationError:
    with pytest.raises(MutationError) as error:
        _apply(document, *operations)
    return error.value


def test_input_document_is_never_modified(document: Document) -> None:
    original = copy.deepcopy(document)

    _apply(document, {"type": "DELETE", "target": "regional_sales"})

    assert document == original


def test_create_appends_to_page_by_default(document: Document) -> None:
    divider = {"type": "divider", "id": "line"}

    result = _apply(document, {"type": "CREATE", "component": divider})

    assert _page_ids(result)[-1] == "line"


@pytest.mark.parametrize(
    ("placement", "expected"),
    [
        ({"before": "region_filter"}, ["kpis", "line", "region_filter"]),
        ({"after": "kpis"}, ["kpis", "line", "region_filter"]),
        ({"index": 0}, ["line", "kpis", "region_filter"]),
        ({"index": 99}, ["kpis", "region_filter", "regional_sales", "regional_breakdown", "line"]),
    ],
)
def test_create_honours_placement(
    document: Document, placement: dict[str, Any], expected: list[str]
) -> None:
    operation = {"type": "CREATE", "component": {"type": "divider", "id": "line"}, **placement}

    assert _page_ids(_apply(document, operation))[: len(expected)] == expected


def test_create_inside_a_container(document: Document) -> None:
    metric = {"type": "metric", "id": "aov_metric", "title": "AOV", "value": 1}

    result = _apply(document, {"type": "CREATE", "parent_id": "kpis", "component": metric})

    assert _ids(result["page"]["components"][0]["children"])[-1] == "aov_metric"


def test_delete_removes_a_nested_component(document: Document) -> None:
    result = _apply(document, {"type": "DELETE", "target": "orders_metric"})

    assert _ids(result["page"]["components"][0]["children"]) == ["revenue_metric"]


def test_move_reorders_among_siblings(document: Document) -> None:
    result = _apply(
        document, {"type": "MOVE", "target": "regional_breakdown", "before": "regional_sales"}
    )

    assert _page_ids(result) == ["kpis", "region_filter", "regional_breakdown", "regional_sales"]


def test_move_into_another_container_keeps_the_component_intact(document: Document) -> None:
    original = document["page"]["components"][2]

    result = _apply(
        document, {"type": "MOVE", "target": "regional_sales", "parent_id": "kpis", "index": 0}
    )

    section = result["page"]["components"][0]
    assert _ids(section["children"]) == ["regional_sales", "revenue_metric", "orders_metric"]
    assert section["children"][0] == original
    assert "regional_sales" not in _page_ids(result)


def test_move_out_of_a_container_to_the_page(document: Document) -> None:
    result = _apply(
        document, {"type": "MOVE", "target": "revenue_metric", "parent_id": "page", "index": 0}
    )

    assert _page_ids(result)[0] == "revenue_metric"


def test_a_container_cannot_be_moved_into_itself(document: Document) -> None:
    card = {
        "type": "card",
        "id": "inner_card",
        "children": [{"type": "divider", "id": "line"}],
    }
    nested = _apply(document, {"type": "CREATE", "parent_id": "kpis", "component": card})

    error = _reject(nested, {"type": "MOVE", "target": "kpis", "parent_id": "inner_card"})

    assert "into itself" in error.message


def test_resize_changes_only_the_given_dimensions(document: Document) -> None:
    result = _apply(
        document,
        {"type": "RESIZE", "target": "regional_sales", "span": 8},
        {"type": "RESIZE", "target": "regional_sales", "height": "lg"},
    )

    assert result["page"]["components"][2]["layout"] == {"span": 8, "height": "lg"}


def test_style_merges_and_null_clears(document: Document) -> None:
    styled = _apply(
        document,
        {"type": "STYLE", "target": "revenue_metric", "style": {"tone": "success"}},
        {"type": "STYLE", "target": "revenue_metric", "style": {"emphasis": "strong"}},
    )
    metric = styled["page"]["components"][0]["children"][0]
    assert metric["style"] == {"tone": "success", "emphasis": "strong"}

    cleared = _apply(
        styled,
        {"type": "STYLE", "target": "revenue_metric", "style": {"tone": None, "emphasis": None}},
    )
    assert "style" not in cleared["page"]["components"][0]["children"][0]


def test_update_merges_props_and_null_removes(document: Document) -> None:
    result = _apply(
        document,
        {
            "type": "UPDATE",
            "target": "regional_breakdown",
            "props": {"title": None, "page_size": 10},
        },
    )

    table = result["page"]["components"][3]
    assert "title" not in table
    assert table["page_size"] == 10
    assert table["data_source"] == {"dataset": "sales_by_region"}, "untouched props are kept"


def test_update_can_retitle_the_page(document: Document) -> None:
    result = _apply(document, {"type": "UPDATE", "target": "page", "props": {"title": "Q3"}})

    assert result["page"]["title"] == "Q3"


@pytest.mark.parametrize("prop", ["id", "type", "layout", "style", "children"])
def test_update_cannot_change_identity_or_structure(document: Document, prop: str) -> None:
    error = _reject(document, {"type": "UPDATE", "target": "kpis", "props": {prop: "x"}})

    assert error.message == f"UPDATE cannot change '{prop}'."


def test_reorder_requires_the_complete_set_of_children(document: Document) -> None:
    order = ["regional_breakdown", "regional_sales", "region_filter", "kpis"]

    result = _apply(document, {"type": "REORDER", "parent_id": "page", "order": order})
    error = _reject(document, {"type": "REORDER", "parent_id": "page", "order": order[:3]})

    assert _page_ids(result) == order
    assert "every child" in error.message


def test_group_wraps_siblings_at_the_position_of_the_first(document: Document) -> None:
    result = _apply(
        document,
        {
            "type": "GROUP",
            "targets": ["regional_breakdown", "regional_sales"],
            "group": {"id": "details", "type": "card", "title": "Details"},
        },
    )

    assert _page_ids(result) == ["kpis", "region_filter", "details"]
    group = result["page"]["components"][2]
    assert (group["type"], group["title"]) == ("card", "Details")
    assert _ids(group["children"]) == ["regional_sales", "regional_breakdown"], "document order"


def test_group_targets_must_share_a_parent(document: Document) -> None:
    error = _reject(
        document,
        {"type": "GROUP", "targets": ["revenue_metric", "regional_sales"], "group": {"id": "g"}},
    )

    assert "same parent" in error.message


def test_ungroup_puts_children_where_the_container_was(document: Document) -> None:
    result = _apply(document, {"type": "UNGROUP", "target": "kpis"})

    assert _page_ids(result)[:3] == ["revenue_metric", "orders_metric", "region_filter"]


def test_only_sections_and_cards_can_be_ungrouped(document: Document) -> None:
    error = _reject(document, {"type": "UNGROUP", "target": "regional_sales"})

    assert error.message == "Only a section or card can be ungrouped."


def test_replace_swaps_in_place(document: Document) -> None:
    chart = {
        "type": "chart",
        "id": "regional_breakdown",
        "chart_type": "bar",
        "x_key": "region",
        "y_keys": ["revenue"],
        "data_source": {"dataset": "sales_by_region"},
    }

    result = _apply(
        document, {"type": "REPLACE", "target": "regional_breakdown", "component": chart}
    )

    assert result["page"]["components"][3] == chart, "the engine inserts the component as given"
    assert len(result["page"]["components"]) == 4


def test_set_theme_merges_tokens_and_tracks_the_preset(document: Document) -> None:
    dark = {"mode": "dark", "colors": {"background": "#000000", "foreground": "#FFFFFF"}}

    preset = _apply(document, {"type": "SET_THEME", "preset": "slate_dark", "tokens": dark})
    custom = _apply(document, {"type": "SET_THEME", "tokens": {"colors": {"primary": "#FF0000"}}})
    shape = _apply(document, {"type": "SET_THEME", "tokens": {"radius": "lg"}})

    assert preset["theme"]["preset"] == "slate_dark"
    assert preset["theme"]["colors"]["background"] == "#000000"
    assert preset["theme"]["colors"]["primary"] == document["theme"]["colors"]["primary"]
    assert "preset" not in custom["theme"], "custom colours are no longer the preset"
    assert shape["theme"]["preset"] == "blue_white", "shape tokens do not affect the preset"
    assert shape["theme"]["radius"] == "lg"


def test_framework_and_design_system_changes_leave_the_page_untouched(document: Document) -> None:
    tokens = {"radius": "sm", "typography": {"scale": "sm"}}

    result = _apply(
        document,
        {"type": "SET_FRAMEWORK", "framework": "material"},
        {"type": "SET_DESIGN_SYSTEM", "design_system": "compact_pro", "tokens": tokens},
    )

    assert result["design"] == {"framework": "material", "design_system": "compact_pro"}
    assert result["theme"]["radius"] == "sm"
    typography = result["theme"]["typography"]
    assert (typography["font"], typography["scale"]) == ("sans", "sm")
    assert result["page"] == document["page"]


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        ({"type": "DELETE", "target": "ghost"}, "Component 'ghost' does not exist."),
        ({"type": "DELETE", "target": "page"}, "Component 'page' does not exist."),
        (
            {"type": "MOVE", "target": "kpis", "before": "revenue_metric"},
            "'revenue_metric' is not in the destination container.",
        ),
        (
            {
                "type": "CREATE",
                "parent_id": "regional_sales",
                "component": {"type": "divider", "id": "x"},
            },
            "'regional_sales' is not a container that can hold components.",
        ),
        ({"type": "EVAL", "code": "1+1"}, "Unknown operation type 'EVAL'."),
    ],
)
def test_inapplicable_operations_are_rejected(
    document: Document, operation: dict[str, Any], message: str
) -> None:
    error = _reject(document, {"type": "RESIZE", "target": "kpis", "span": 6}, operation)

    assert (error.index, error.message) == (1, message)


def test_tabs_expose_one_slot_per_tab(document: Document) -> None:
    tabs = {
        "type": "tabs",
        "id": "views",
        "tabs": [
            {
                "id": "overview_tab",
                "label": "Overview",
                "children": [{"type": "divider", "id": "a"}],
            },
            {"id": "detail_tab", "label": "Detail", "children": [{"type": "divider", "id": "b"}]},
        ],
    }

    result = _apply(
        document,
        {"type": "CREATE", "component": tabs},
        {"type": "MOVE", "target": "regional_sales", "parent_id": "detail_tab"},
        {"type": "UPDATE", "target": "detail_tab", "props": {"label": "Charts"}},
    )

    detail = result["page"]["components"][-1]["tabs"][1]
    assert detail["label"] == "Charts"
    assert _ids(detail["children"]) == ["b", "regional_sales"]


def test_operations_are_described_for_people(document: Document) -> None:
    move = {"type": "MOVE", "target": "revenue_metric", "after": "orders_metric"}
    replace = {
        "type": "REPLACE",
        "target": "regional_breakdown",
        "component": {"type": "chart", "id": "regional_breakdown", "chart_type": "bar"},
    }

    assert describe_operation(move, document) == "Move “Revenue” after “Orders”"
    assert describe_operation(replace, document) == "Replace “Breakdown” with a bar chart"
    assert affected_component_ids(replace) == ["regional_breakdown"]


def test_layout_map_shows_rows_produced_by_spans(document: Document) -> None:
    layout_map = render_layout_map(document["page"])

    assert (
        "kpis:\n  row 1: revenue_metric (metric, span 6), orders_metric (metric, span 6)"
        in layout_map
    )
    assert "page:\n  row 1: kpis (section, span 12)\n  row 2: region_filter" in layout_map
