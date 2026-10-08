# ruff: noqa: E501  (the case tables read best with one operation per line)
"""Export the frontend/backend contract.

    poetry run python -m scripts.export_contract ../frontend/src/generative-ui/schema/generated

Writes two files into the target directory:

    openapi.json            The API description; TypeScript types are generated from it.
    contract-fixtures.json  Examples, registries and mutation cases. The mutation cases
                            carry results computed by the backend engine, so the frontend
                            engine can be tested for identical behaviour.

Needs no database and no network.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from app.domains.actions.schemas import ActionType
from app.domains.data_sources.providers.base import EmptyDataProvider
from app.domains.data_sources.providers.mock import MockSalesDataProvider
from app.domains.generative_ui.design_registry import DesignRegistry, build_default_design_registry
from app.domains.generative_ui.document import dump_document
from app.domains.generative_ui.mutator import DocumentMutator
from app.domains.generative_ui.operations import (
    APPLICATION_OPERATION_EXAMPLES,
    OPERATION_EXAMPLES,
    VERSION_OPERATION_EXAMPLES,
    DocumentOperation,
)
from app.domains.generative_ui.pattern_registry import build_default_pattern_registry
from app.domains.generative_ui.registry import build_default_registry
from app.domains.generative_ui.renderer import UIDataResolver
from app.domains.generative_ui.schemas import UI_SCHEMA_VERSION
from app.domains.generative_ui.service import summarise_application
from app.domains.generative_ui.validator import UISchemaValidator, ValidationContext
from app.main import create_app
from scripts.sample_build import build_sample_application

OPERATION = TypeAdapter(DocumentOperation)

SAMPLE_PAGE: dict[str, Any] = {
    "type": "page",
    "title": "Sales Dashboard",
    "description": "Q3 2025 performance",
    "components": [
        {
            "type": "metric",
            "id": "revenue_metric",
            "title": "Revenue",
            "unit": "₹",
            "format": "currency",
            "data_source": {"dataset": "sales_summary", "field": "total_revenue"},
            "layout": {"span": 3},
        },
        {
            "type": "metric",
            "id": "orders_metric",
            "title": "Orders",
            "format": "number",
            "data_source": {"dataset": "sales_summary", "field": "total_orders"},
            "layout": {"span": 3},
        },
        {
            "type": "metric",
            "id": "aov_metric",
            "title": "Avg. order value",
            "unit": "₹",
            "format": "currency",
            "data_source": {"dataset": "sales_summary", "field": "average_order_value"},
            "layout": {"span": 3},
        },
        {
            "type": "metric",
            "id": "top_region_metric",
            "title": "Top region",
            "data_source": {
                "dataset": "sales_summary",
                "field": "top_region",
                "aggregate": "first",
            },
            "layout": {"span": 3},
        },
        {
            "type": "chart",
            "id": "monthly_revenue_chart",
            "title": "Monthly revenue",
            "chart_type": "line",
            "x_key": "month",
            "y_keys": ["revenue"],
            "data_source": {"dataset": "sales_by_month"},
            "layout": {"span": 7, "height": "md"},
        },
        {
            "type": "chart",
            "id": "product_share_chart",
            "title": "Revenue by product",
            "chart_type": "donut",
            "x_key": "product",
            "y_keys": ["revenue"],
            "data_source": {"dataset": "sales_by_product"},
            "layout": {"span": 5, "height": "md"},
        },
        {
            "type": "select",
            "id": "region_filter",
            "name": "region",
            "label": "Region",
            "options": [
                {"label": "North", "value": "North"},
                {"label": "South", "value": "South"},
                {"label": "East", "value": "East"},
                {"label": "West", "value": "West"},
            ],
            "on_change": {
                "type": "filter",
                "payload": {
                    "dataset": "sales_by_region",
                    "field": "region",
                    "target": "regional_table",
                },
            },
            "layout": {"span": 4},
        },
        {
            "type": "table",
            "id": "regional_table",
            "title": "Sales by region",
            "columns": [
                {"key": "region", "label": "Region"},
                {"key": "revenue", "label": "Revenue", "format": "currency", "align": "right"},
                {"key": "orders", "label": "Orders", "format": "number", "align": "right"},
            ],
            "data_source": {"dataset": "sales_by_region"},
        },
    ],
}

_BAR_CHART = {
    "type": "chart",
    "id": "regional_table",
    "title": "Sales by region",
    "chart_type": "bar",
    "x_key": "region",
    "y_keys": ["revenue"],
    "data_source": {"dataset": "sales_by_region"},
}


# (name, operations). Expected results are computed below by the real engine.
MUTATION_CASES: tuple[tuple[str, list[dict[str, Any]]], ...] = (
    ("move revenue to the end of the first row", [
        {"type": "MOVE", "target": "revenue_metric", "after": "top_region_metric"},
    ]),
    ("move by index", [{"type": "MOVE", "target": "regional_table", "index": 0}]),
    ("resize span and height", [
        {"type": "RESIZE", "target": "monthly_revenue_chart", "span": 12, "height": "lg"},
    ]),
    ("replace table with bar chart keeps layout", [
        {"type": "RESIZE", "target": "regional_table", "span": 6},
        {"type": "REPLACE", "target": "regional_table", "component": _BAR_CHART},
    ]),
    ("create with placement", [
        {
            "type": "CREATE",
            "after": "region_filter",
            "component": {"type": "divider", "id": "charts_divider", "label": "Charts"},
        },
    ]),
    ("delete", [{"type": "DELETE", "target": "product_share_chart"}]),
    ("style then clear", [
        {"type": "STYLE", "target": "revenue_metric", "style": {"tone": "success", "emphasis": "strong"}},
        {"type": "STYLE", "target": "revenue_metric", "style": {"emphasis": None}},
    ]),
    ("update props and remove one", [
        {"type": "UPDATE", "target": "monthly_revenue_chart", "props": {"chart_type": "area", "title": None}},
        {"type": "UPDATE", "target": "page", "props": {"title": "Q3 Sales"}},
    ]),
    ("group then move into group then ungroup", [
        {
            "type": "GROUP",
            "targets": ["orders_metric", "revenue_metric"],
            "group": {"id": "kpi_section", "type": "section", "title": "Key metrics"},
        },
        {"type": "MOVE", "target": "aov_metric", "parent_id": "kpi_section", "index": 0},
        {"type": "RESIZE", "target": "kpi_section", "span": 9},
    ]),
    ("ungroup", [
        {
            "type": "GROUP",
            "targets": ["monthly_revenue_chart", "product_share_chart"],
            "group": {"id": "charts_card", "type": "card"},
        },
        {"type": "UNGROUP", "target": "charts_card"},
    ]),
    ("reorder page", [
        {
            "type": "REORDER",
            "parent_id": "page",
            "order": [
                "region_filter", "regional_table", "revenue_metric", "orders_metric",
                "aov_metric", "top_region_metric", "monthly_revenue_chart", "product_share_chart",
            ],
        },
    ]),
    ("theme preset", [{"type": "SET_THEME", "preset": "slate_dark"}]),
    ("theme tokens drop the preset label", [
        {"type": "SET_THEME", "tokens": {"colors": {"primary": "#7C3AED"}, "radius": "lg"}},
    ]),
    ("shape tokens keep the preset label", [
        {"type": "SET_THEME", "tokens": {"density": "compact", "typography": {"font": "serif"}}},
    ]),
    ("framework and design system", [
        {"type": "SET_FRAMEWORK", "framework": "material"},
        {"type": "SET_DESIGN_SYSTEM", "design_system": "material"},
    ]),
)  # fmt: skip

REJECTED_CASES: tuple[tuple[str, list[dict[str, Any]]], ...] = (
    ("unknown target", [{"type": "DELETE", "target": "ghost"}]),
    ("move into itself", [
        {"type": "GROUP", "targets": ["revenue_metric"], "group": {"id": "wrap"}},
        {"type": "MOVE", "target": "wrap", "parent_id": "wrap"},
    ]),
    ("anchor outside destination", [
        {"type": "MOVE", "target": "revenue_metric", "before": "ghost"},
    ]),
    ("incomplete reorder", [
        {"type": "REORDER", "parent_id": "page", "order": ["revenue_metric"]},
    ]),
    ("update protected prop", [
        {"type": "UPDATE", "target": "revenue_metric", "props": {"id": "renamed"}},
    ]),
    ("ungroup a leaf", [{"type": "UNGROUP", "target": "revenue_metric"}]),
    ("create in a non-container", [
        {"type": "CREATE", "parent_id": "revenue_metric", "component": {"type": "divider", "id": "x"}},
    ]),
    ("duplicate id", [
        {"type": "CREATE", "component": {"type": "divider", "id": "revenue_metric"}},
    ]),
    ("dangling action target", [{"type": "DELETE", "target": "regional_table"}]),
)  # fmt: skip


# Operations on the sample application; the frontend engine must reproduce the results.
APPLICATION_MUTATION_CASES: tuple[tuple[str, list[dict[str, Any]]], ...] = (
    ("change navigation style", [{"type": "SET_NAVIGATION", "style": "topbar"}]),
    ("rename brand and clear tagline", [
        {"type": "SET_NAVIGATION", "brand": "Hireflow", "tagline": None},
    ]),
    ("update application description", [
        {"type": "UPDATE_APPLICATION", "props": {"name": "Hireflow", "goals": None}},
    ]),
    ("delete a screen prunes navigation", [{"type": "DELETE", "target": "interviews"}]),
    ("delete the home screen moves home", [{"type": "DELETE", "target": "dashboard"}]),
    ("resize inside a screen", [
        {"type": "RESIZE", "target": "dashboard_hiring_trend", "span": 12, "height": "lg"},
    ]),
    ("move within a screen", [
        {"type": "MOVE", "target": "dashboard_this_week", "before": "dashboard_hiring_trend"},
    ]),
    ("style with surface and effects", [
        {"type": "STYLE", "target": "dashboard_this_week",
         "style": {"surface": "elevated", "effects": ["reveal"], "priority": "secondary"}},
    ]),
    ("replace a screen keeps its place", [
        {"type": "REPLACE", "target": "interviews", "component": {
            "type": "screen", "id": "interviews", "title": "Interviews", "route": "/interviews",
            "screen_type": "calendar",
            "children": [{"type": "text", "id": "interviews_note", "content": "Nothing scheduled."}],
        }},
    ]),
    ("add a screen and link it", [
        {"type": "CREATE", "parent_id": "page", "component": {
            "type": "screen", "id": "reports", "title": "Reports", "route": "/reports",
            "children": [{"type": "text", "id": "reports_note", "content": "Hiring reports."}],
        }},
        {"type": "SET_NAVIGATION", "items": [
            {"screen_id": "dashboard", "label": "Dashboard", "icon": "dashboard"},
            {"screen_id": "reports", "label": "Reports", "icon": "bar-chart"},
        ]},
    ]),
    ("restyle the whole application", [
        {"type": "SET_DESIGN_SYSTEM", "design_system": "luxury"},
        {"type": "SET_THEME", "preset": "stone_ink"},
    ]),
    ("upsert an entity", [
        {"type": "UPSERT_ENTITIES", "entities": [{
            "name": "offers", "label": "Offers", "title_field": "candidate",
            "fields": [{"key": "candidate", "label": "Candidate"},
                       {"key": "salary", "label": "Salary", "type": "currency"}],
            "records": [{"id": "off-1", "candidate": "Rafael Mendes", "salary": 92000}],
        }]},
    ]),
)  # fmt: skip

REJECTED_APPLICATION_CASES: tuple[tuple[str, list[dict[str, Any]]], ...] = (
    ("navigation to a missing screen", [{"type": "SET_NAVIGATION", "home": "nowhere"}]),
    ("delete a screen something still links to", [{"type": "DELETE", "target": "pipeline"}]),
    ("protected application field", [
        {"type": "UPDATE_APPLICATION", "props": {"entities": []}},
    ]),
    ("screen inside a screen", [
        {"type": "MOVE", "target": "jobs", "parent_id": "dashboard"},
    ]),
    ("unknown asset", [
        {"type": "UPDATE", "target": "dashboard_this_week", "props": {"image": "missing"}},
    ]),
    ("route clash", [{"type": "UPDATE", "target": "jobs", "props": {"route": "/pipeline"}}]),
)  # fmt: skip


async def _application_fixtures(
    validator: UISchemaValidator, mutator: DocumentMutator, design: DesignRegistry
) -> dict[str, Any]:
    document = await build_sample_application()
    context = ValidationContext()

    def run(operations: list[dict[str, Any]]) -> Any:
        parsed = [OPERATION.validate_python(operation) for operation in operations]
        return mutator.inspect(document, parsed, context)

    cases = []
    for name, operations in APPLICATION_MUTATION_CASES:
        outcome = run(operations)
        assert outcome.document is not None, (name, outcome.issues)
        cases.append(
            {
                "name": name,
                "operations": outcome.operations,
                "summaries": [step.summary for step in outcome.steps],
                "expected": dump_document(outcome.document),
            }
        )
    rejected = []
    for name, operations in REJECTED_APPLICATION_CASES:
        outcome = run(operations)
        assert outcome.document is None, name
        rejected.append(
            {"name": name, "operations": operations, "stage": outcome.issues[0].stage.value}
        )
    patterns = build_default_pattern_registry()
    return {
        "sample_application": dump_document(document),
        "sample_application_data": await UIDataResolver(EmptyDataProvider()).resolve(document),
        "application_summary": summarise_application(document, design).model_dump(mode="json"),  # type: ignore[union-attr]
        "application_mutation_cases": cases,
        "rejected_application_mutation_cases": rejected,
        "application_operation_examples": [e for _, e in APPLICATION_OPERATION_EXAMPLES],
        "patterns": [
            {"id": p.id, "component": p.component.value, "variant": p.variant}
            for p in patterns.patterns()
        ],
        "effects": [effect.id.value for effect in design.effects()],
        "icons": list(design.icons()),
        "component_variants": {
            d.type.value: list(d.variants)
            for d in build_default_registry().definitions()
            if d.variants
        },
    }


async def _build_fixtures() -> dict[str, Any]:
    design = build_default_design_registry()
    registry = build_default_registry()
    data_provider = MockSalesDataProvider()
    datasets = await data_provider.list_datasets()
    context = ValidationContext(datasets={dataset.name: dataset for dataset in datasets})
    validator = UISchemaValidator(registry, frozenset(ActionType), design)
    mutator = DocumentMutator(validator, design)

    document = validator.validate_document(
        {
            "page": SAMPLE_PAGE,
            "theme": design.default_theme().model_dump(mode="json", exclude_none=True),
            "design": design.default_design().model_dump(mode="json"),
        },
        context,
    )

    def run(operations: list[dict[str, Any]]) -> Any:
        parsed = [OPERATION.validate_python(operation) for operation in operations]
        return mutator.inspect(document, parsed, context)

    cases = []
    for name, operations in MUTATION_CASES:
        outcome = run(operations)
        assert outcome.document is not None, (name, outcome.issues)
        cases.append(
            {
                "name": name,
                "operations": outcome.operations,
                "summaries": [step.summary for step in outcome.steps],
                "expected": dump_document(outcome.document),
            }
        )
    rejected = []
    for name, operations in REJECTED_CASES:
        outcome = run(operations)
        assert outcome.document is None, name
        rejected.append(
            {"name": name, "operations": operations, "stage": outcome.issues[0].stage.value}
        )

    application = await _application_fixtures(validator, mutator, design)
    return {
        **application,
        "schema_version": UI_SCHEMA_VERSION,
        "sample_document": dump_document(document),
        "sample_data": await UIDataResolver(data_provider).resolve(document),
        "datasets": [dataset.model_dump(mode="json") for dataset in datasets],
        "component_examples": {d.type.value: d.example for d in registry.definitions()},
        "operation_examples": [example for _, example in OPERATION_EXAMPLES],
        "version_operation_examples": [example for _, example in VERSION_OPERATION_EXAMPLES],
        "allowed_actions": sorted(action.value for action in ActionType),
        "theme_presets": [
            {"id": p.id, "name": p.name, "theme": p.theme.model_dump(mode="json")}
            for p in design.themes()
        ],
        "default_theme": design.default_theme().model_dump(mode="json", exclude_none=True),
        "design_systems": [
            {
                "id": s.id,
                "name": s.name,
                "tokens": s.tokens.model_dump(mode="json", exclude_none=True),
                "effects": [effect.value for effect in s.effects],
                "palettes": list(s.palettes),
            }
            for s in design.design_systems()
        ],
        "frameworks": [
            {"id": f.id, "name": f.name, "status": f.status.value} for f in design.frameworks()
        ],
        "mutation_cases": cases,
        "rejected_mutation_cases": rejected,
    }


def _write(path: Path, content: Any) -> None:
    path.write_text(json.dumps(content, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"wrote {path}")


def main(target: str) -> None:
    directory = Path(target)
    directory.mkdir(parents=True, exist_ok=True)
    _write(directory / "openapi.json", create_app().openapi())
    _write(directory / "contract-fixtures.json", asyncio.run(_build_fixtures()))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
