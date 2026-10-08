"""The controlled catalogue of UI components.

A component exists for the model, the validator and the frontend only if it is
registered here. Each definition carries an example that doubles as model
guidance and as API documentation.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

from pydantic import BaseModel

from app.domains.generative_ui import schemas as ui
from app.domains.generative_ui.schemas import ComponentType

ModelClass = type[BaseModel]


class ComponentCategory(StrEnum):
    LAYOUT = "layout"
    DATA_DISPLAY = "data_display"
    INPUT = "input"
    FEEDBACK = "feedback"
    PATTERN = "pattern"
    RECORD = "record"
    STRUCTURE = "structure"


@dataclass(frozen=True, slots=True)
class ComponentDefinition:
    type: ComponentType
    model: ModelClass
    category: ComponentCategory
    description: str
    example: Mapping[str, object]
    accepts_children: bool = False

    @property
    def variants(self) -> tuple[str, ...]:
        """Values of the component's ``variant`` field, if it has one."""
        field = self.model.model_fields.get("variant")
        annotation = field.annotation if field else None
        if isinstance(annotation, type) and issubclass(annotation, StrEnum):
            return tuple(member.value for member in annotation)
        return ()


class ComponentRegistry:
    """Immutable lookup of the component types that may appear in a UI."""

    def __init__(self, definitions: Iterable[ComponentDefinition]) -> None:
        self._definitions: dict[ComponentType, ComponentDefinition] = {}
        for definition in definitions:
            if definition.type in self._definitions:
                raise ValueError(f"Component '{definition.type}' is registered twice.")
            self._definitions[definition.type] = definition

    def is_registered(self, component_type: str) -> bool:
        return component_type in {registered.value for registered in self._definitions}

    def get(self, component_type: str) -> ComponentDefinition:
        try:
            return self._definitions[ComponentType(component_type)]
        except (ValueError, KeyError):
            raise KeyError(f"Component '{component_type}' is not registered.") from None

    def types(self) -> tuple[ComponentType, ...]:
        return tuple(self._definitions)

    def definitions(self) -> tuple[ComponentDefinition, ...]:
        return tuple(self._definitions.values())

    def restricted_to(self, allowed: Iterable[ComponentType]) -> "ComponentRegistry":
        """A narrower registry, e.g. for a tenant or surface with fewer components."""
        allowed_types = set(allowed)
        return ComponentRegistry(d for d in self.definitions() if d.type in allowed_types)


_LAYOUT = ComponentCategory.LAYOUT
_DATA = ComponentCategory.DATA_DISPLAY
_INPUT = ComponentCategory.INPUT
_FEEDBACK = ComponentCategory.FEEDBACK
_PATTERN = ComponentCategory.PATTERN
_RECORD = ComponentCategory.RECORD
_STRUCTURE = ComponentCategory.STRUCTURE

# Examples describe parts of one product (the sample recruitment application), so
# they can be validated together: its routes, entities and images.
_GO_SIGNUP = {"type": "navigate", "payload": {"to": "/jobs/new"}}
_OPEN_CANDIDATE = {"type": "navigate", "payload": {"to": "/candidates/:candidateId"}}
_ONE_CANDIDATE = {
    "dataset": "candidates",
    "where": [{"field": "id", "param": "candidateId"}],
}

_TEXT_EXAMPLE = {"type": "text", "id": "intro", "content": "Sales grew across all regions."}
_SELECT_EXAMPLE = {
    "type": "select",
    "id": "region_filter",
    "name": "region",
    "label": "Region",
    "options": [{"label": "North", "value": "North"}, {"label": "South", "value": "South"}],
    "on_change": {
        "type": "filter",
        "payload": {"dataset": "sales_by_region", "field": "region", "target": "regional_sales"},
    },
}

_DEFAULT_DEFINITIONS: tuple[ComponentDefinition, ...] = (
    ComponentDefinition(
        ComponentType.PAGE,
        ui.PageComponent,
        _LAYOUT,
        "Root of the UI. Exactly one, never nested.",
        {"type": "page", "title": "Regional Sales", "components": [_TEXT_EXAMPLE]},
        accepts_children=True,
    ),
    ComponentDefinition(
        ComponentType.SECTION,
        ui.SectionComponent,
        _LAYOUT,
        "Groups related components under an optional heading. variant: default, split "
        "(heading left, content right), band (tinted full-width band), editorial (large "
        "heading, wide margins), full_bleed, immersive (over a backdrop image).",
        {
            "type": "section",
            "id": "kpis",
            "variant": "default",
            "title": "Key metrics",
            "children": [_TEXT_EXAMPLE],
        },
        accepts_children=True,
    ),
    ComponentDefinition(
        ComponentType.CARD,
        ui.CardComponent,
        _LAYOUT,
        "A container for one topic. style.surface picks its look: flat, bordered, elevated, "
        "glass, minimal, featured, interactive.",
        {"type": "card", "id": "summary_card", "title": "Summary", "children": [_TEXT_EXAMPLE]},
        accepts_children=True,
    ),
    ComponentDefinition(
        ComponentType.TABS,
        ui.TabsComponent,
        _LAYOUT,
        "Switches between alternative views.",
        {
            "type": "tabs",
            "id": "views",
            "default_tab": "overview",
            "tabs": [{"id": "overview", "label": "Overview", "children": [_TEXT_EXAMPLE]}],
        },
        accepts_children=True,
    ),
    ComponentDefinition(
        ComponentType.MODAL,
        ui.ModalComponent,
        _LAYOUT,
        "A button that opens a dialog with more content.",
        {
            "type": "modal",
            "id": "details_modal",
            "title": "Details",
            "trigger_label": "View details",
            "children": [_TEXT_EXAMPLE],
        },
        accepts_children=True,
    ),
    ComponentDefinition(
        ComponentType.DIVIDER,
        ui.DividerComponent,
        _LAYOUT,
        "A horizontal separator, optionally labelled.",
        {"type": "divider", "id": "details_divider", "label": "Details"},
    ),
    ComponentDefinition(
        ComponentType.METRIC,
        ui.MetricComponent,
        _DATA,
        "A single headline number with optional trend. Prefer data_source "
        '({"dataset", "field", "aggregate"}) over a literal value so the figure comes from data. '
        "aggregate: sum, avg, min, max (number fields only), count, or first (any field).",
        {
            "type": "metric",
            "id": "revenue",
            "title": "Revenue",
            "value": "₹4.8 Cr",
            "trend": {"direction": "up", "value": "+12%", "label": "vs last quarter"},
            "description": "Total for Q3",
            "layout": {"span": 3},
        },
    ),
    ComponentDefinition(
        ComponentType.TEXT,
        ui.TextComponent,
        _DATA,
        "Plain text: heading, subheading, body or caption. No markup.",
        {**_TEXT_EXAMPLE, "variant": "body"},
    ),
    ComponentDefinition(
        ComponentType.TABLE,
        ui.TableComponent,
        _DATA,
        "Tabular data. Bind rows with data_source, or give them inline in rows. row_action "
        "runs when a row is opened (usually navigate to that record's detail screen).",
        {
            "type": "table",
            "id": "regional_breakdown",
            "title": "Breakdown by region",
            "columns": [
                {"key": "region", "label": "Region"},
                {"key": "revenue", "label": "Revenue", "format": "currency", "align": "right"},
            ],
            "data_source": {
                "dataset": "sales_by_region",
                "sort": {"field": "revenue", "direction": "desc"},
            },
        },
    ),
    ComponentDefinition(
        ComponentType.CHART,
        ui.ChartComponent,
        _DATA,
        "A chart (bar, line, area, pie, donut, scatter). x_key and y_keys name row fields. "
        "Bind rows with data_source, or give them inline in data. To chart counts or totals "
        'per group use data_source {"dataset", "group_by": "<field>"} (y_keys ["count"]) or '
        '{"dataset", "group_by", "aggregate": "sum", "field": "<number field>"} '
        '(y_keys ["<number field>"]); x_key is then the group_by field.',
        {
            "type": "chart",
            "id": "regional_sales",
            "title": "Revenue by region",
            "chart_type": "bar",
            "x_key": "region",
            "y_keys": ["revenue"],
            "data_source": {"dataset": "sales_by_region"},
        },
    ),
    ComponentDefinition(
        ComponentType.LIST,
        ui.ListComponent,
        _DATA,
        "A short list of items.",
        {
            "type": "list",
            "id": "highlights",
            "title": "Highlights",
            "items": [{"title": "North leads revenue", "description": "Largest share in Q3"}],
        },
    ),
    ComponentDefinition(
        ComponentType.TIMELINE,
        ui.TimelineComponent,
        _DATA,
        "Events or steps in chronological order.",
        {
            "type": "timeline",
            "id": "milestones",
            "items": [
                {"title": "Quarter closed", "timestamp": "2025-09-30", "status": "completed"}
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.BADGE,
        ui.BadgeComponent,
        _DATA,
        "A small status label.",
        {"type": "badge", "id": "status_badge", "label": "On track", "tone": "success"},
    ),
    ComponentDefinition(
        ComponentType.PROGRESS,
        ui.ProgressComponent,
        _FEEDBACK,
        "Progress towards a target; value must not exceed max.",
        {"type": "progress", "id": "target_progress", "label": "Target", "value": 72, "max": 100},
    ),
    ComponentDefinition(
        ComponentType.ALERT,
        ui.AlertComponent,
        _FEEDBACK,
        "A highlighted message: info, success, warning or danger.",
        {
            "type": "alert",
            "id": "data_notice",
            "title": "Demo data",
            "message": "Figures come from the demo dataset.",
            "tone": "info",
        },
    ),
    ComponentDefinition(
        ComponentType.FORM,
        ui.FormComponent,
        _INPUT,
        "Groups input, select and checkbox fields with a submit action.",
        {
            "type": "form",
            "id": "feedback_form",
            "title": "Feedback",
            "fields": [{"type": "input", "id": "comment", "name": "comment", "label": "Comment"}],
            "submit_action": {"type": "submit", "payload": {"form_id": "feedback_form"}},
            "submit_label": "Send",
        },
        accepts_children=True,
    ),
    ComponentDefinition(
        ComponentType.INPUT,
        ui.InputComponent,
        _INPUT,
        "A text, number, email, date, search or textarea field.",
        {
            "type": "input",
            "id": "search_box",
            "name": "query",
            "label": "Search",
            "input_type": "search",
            "placeholder": "Search products",
        },
    ),
    ComponentDefinition(
        ComponentType.SELECT,
        ui.SelectComponent,
        _INPUT,
        "A dropdown; commonly used as a filter via on_change.",
        _SELECT_EXAMPLE,
    ),
    ComponentDefinition(
        ComponentType.CHECKBOX,
        ui.CheckboxComponent,
        _INPUT,
        "A boolean toggle.",
        {"type": "checkbox", "id": "show_orders", "name": "show_orders", "label": "Show orders"},
    ),
    ComponentDefinition(
        ComponentType.BUTTON,
        ui.ButtonComponent,
        _INPUT,
        "Triggers one allowed action. variant: primary, secondary, outline, ghost, danger, "
        "gradient, glass.",
        {
            "type": "button",
            "id": "export_button",
            "label": "Export CSV",
            "variant": "secondary",
            "action": {
                "type": "export",
                "payload": {"dataset": "sales_by_region", "format": "csv"},
            },
        },
    ),
    # --- Application structure ------------------------------------------------------
    ComponentDefinition(
        ComponentType.SCREEN,
        ui.ScreenComponent,
        _STRUCTURE,
        "One routed screen of an application; only directly under the page. route may hold "
        "parameters ('/candidates/:candidateId'). width: narrow (forms, reading), contained "
        "(application screens), wide, full (marketing sections edge to edge).",
        {
            "type": "screen",
            "id": "candidates",
            "title": "Candidates",
            "route": "/candidates",
            "screen_type": "listing",
            "width": "contained",
            "children": [_TEXT_EXAMPLE],
        },
        accepts_children=True,
    ),
    # --- Patterns -------------------------------------------------------------------
    ComponentDefinition(
        ComponentType.HERO,
        ui.HeroComponent,
        _PATTERN,
        "The opening of a marketing screen. variant: split (text beside image), centered, "
        "immersive (text over a full-bleed image), editorial (display type, wide image "
        "below), product (headline above a framed product image). image is an asset id.",
        {
            "type": "hero",
            "id": "home_hero",
            "variant": "split",
            "eyebrow": "AI-powered hiring",
            "title": "Hire the right people in half the time",
            "subtitle": "Screen, shortlist and schedule from one calm workspace.",
            "actions": [
                {"label": "Start free", "action": _GO_SIGNUP},
                {
                    "label": "See how it works",
                    "variant": "ghost",
                    "action": {"type": "navigate", "payload": {"to": "/candidates"}},
                },
            ],
            "image": "hero_image",
            "stats": [{"label": "Faster screening", "value": "3.2x"}],
        },
    ),
    ComponentDefinition(
        ComponentType.FEATURE_GRID,
        ui.FeatureGridComponent,
        _PATTERN,
        "Capabilities or reasons. variant: grid (equal cells), bento (mixed sizes: give the "
        "one or two most important items span 2), alternating (image and text swap sides; "
        "items need image), list. icon is a name from 'Icons'.",
        {
            "type": "feature_grid",
            "id": "home_features",
            "variant": "bento",
            "title": "Everything hiring needs",
            "columns": 3,
            "items": [
                {
                    "title": "AI candidate screening",
                    "icon": "sparkles",
                    "span": 2,
                    "description": "Every résumé scored against the role in seconds.",
                },
                {
                    "title": "Shared scorecards",
                    "icon": "users",
                    "description": "Interviewers rate the same criteria.",
                },
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.LOGO_CLOUD,
        ui.LogoCloudComponent,
        _PATTERN,
        "Customer or partner names as wordmarks. variant: static or marquee.",
        {
            "type": "logo_cloud",
            "id": "home_customers",
            "title": "Trusted by hiring teams at",
            "logos": ["Northwind", "Lumen Labs", "Harbor & Co", "Fieldstone", "Atlas Freight"],
        },
    ),
    ComponentDefinition(
        ComponentType.TESTIMONIALS,
        ui.TestimonialsComponent,
        _PATTERN,
        "Customer quotes. variant: cards (several), spotlight (one, large), marquee.",
        {
            "type": "testimonials",
            "id": "home_quotes",
            "variant": "cards",
            "title": "What recruiters say",
            "items": [
                {
                    "quote": "We cut time-to-shortlist from nine days to two.",
                    "author": "Priya Raman",
                    "role": "Head of Talent",
                    "company": "Lumen Labs",
                    "rating": 5,
                },
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.PRICING,
        ui.PricingComponent,
        _PATTERN,
        "Plans side by side; mark one as highlighted.",
        {
            "type": "pricing",
            "id": "pricing_plans",
            "title": "Simple pricing",
            "plans": [
                {
                    "name": "Team",
                    "price": "$49",
                    "period": "per recruiter / month",
                    "features": ["Unlimited jobs", "AI screening", "Interview scheduling"],
                    "highlighted": True,
                    "badge": "Most popular",
                    "action": {"label": "Start free", "action": _GO_SIGNUP},
                },
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.CTA,
        ui.CtaComponent,
        _PATTERN,
        "A closing call to action. variant: centered, banner (compact band), split (with image).",
        {
            "type": "cta",
            "id": "home_cta",
            "variant": "centered",
            "title": "Fill your next role faster",
            "subtitle": "Free for your first three jobs.",
            "actions": [{"label": "Create your workspace", "action": _GO_SIGNUP}],
        },
    ),
    ComponentDefinition(
        ComponentType.STATS,
        ui.StatsComponent,
        _PATTERN,
        "Several headline figures together (a KPI strip). variant: strip (one row), cards, "
        "inline (large marketing figures). In application screens bind each item with "
        'data_source {"dataset", "field", "aggregate", "where"?} instead of writing a value.',
        {
            "type": "stats",
            "id": "dashboard_kpis",
            "variant": "strip",
            "items": [
                {
                    "label": "Open roles",
                    "icon": "briefcase",
                    "data_source": {
                        "dataset": "jobs",
                        "field": "id",
                        "aggregate": "count",
                        "where": [{"field": "status", "value": "Open"}],
                    },
                },
                {
                    "label": "Candidates",
                    "icon": "users",
                    "data_source": {"dataset": "candidates", "field": "id", "aggregate": "count"},
                },
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.GALLERY,
        ui.GalleryComponent,
        _PATTERN,
        "Curated visual items written into the document (projects, destinations, case "
        "studies). variant: grid, masonry, editorial (large, varied sizes), carousel. "
        "Each item's image is an asset id.",
        {
            "type": "gallery",
            "id": "home_projects",
            "variant": "editorial",
            "title": "Selected projects",
            "columns": 2,
            "items": [
                {
                    "title": "Casa Mirador",
                    "subtitle": "Private residence, Lisbon",
                    "image": "project_mirador",
                    "meta": [
                        {"label": "Year", "value": "2024"},
                        {"label": "Area", "value": "420 m²"},
                    ],
                },
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.IMAGE,
        ui.ImageComponent,
        _PATTERN,
        "One image by asset id. aspect: auto, square, video, wide, ultrawide, portrait.",
        {
            "type": "image",
            "id": "studio_photo",
            "image": "studio_interior",
            "aspect": "wide",
            "caption": "The studio in Porto",
        },
    ),
    ComponentDefinition(
        ComponentType.MEDIA,
        ui.MediaComponent,
        _PATTERN,
        "An image with a statement. variant: image_right, image_left, overlay (text over a "
        "wide image), framed (image shown as a product preview in a window frame).",
        {
            "type": "media",
            "id": "home_preview",
            "variant": "framed",
            "eyebrow": "The pipeline",
            "title": "See every candidate at a glance",
            "body": "Drag candidates between stages; everyone sees the same board.",
            "bullets": ["Stage-by-stage conversion", "Automatic reminders"],
            "image": "pipeline_preview",
        },
    ),
    ComponentDefinition(
        ComponentType.STEPS,
        ui.StepsComponent,
        _PATTERN,
        "A short sequence. variant: numbered, cards, timeline.",
        {
            "type": "steps",
            "id": "home_how",
            "title": "How it works",
            "items": [
                {"title": "Post the role", "description": "Describe it once; we publish it."},
                {"title": "Review the shortlist", "description": "Ranked with reasons."},
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.FAQ,
        ui.FaqComponent,
        _PATTERN,
        "Questions and answers that expand.",
        {
            "type": "faq",
            "id": "pricing_faq",
            "title": "Questions",
            "items": [
                {
                    "question": "Can I import candidates?",
                    "answer": "Yes, from CSV or your current tracker.",
                }
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.COMPARISON,
        ui.ComparisonComponent,
        _PATTERN,
        "Options compared row by row. A value is text, or true/false for a tick or a dash.",
        {
            "type": "comparison",
            "id": "pricing_compare",
            "columns": ["Starter", "Team", "Enterprise"],
            "highlight_column": 1,
            "rows": [
                {"label": "AI screening", "values": [False, True, True]},
                {"label": "Seats", "values": ["3", "25", "Unlimited"]},
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.FOOTER,
        ui.FooterComponent,
        _PATTERN,
        "The closing block of a marketing screen: brand, link columns, legal line.",
        {
            "type": "footer",
            "id": "home_footer",
            "brand": "Hirewell",
            "tagline": "Hiring, without the busywork.",
            "columns": [
                {
                    "title": "Product",
                    "links": [
                        {
                            "label": "Pricing",
                            "action": {"type": "navigate", "payload": {"to": "/jobs"}},
                        }
                    ],
                }
            ],
            "note": "© 2026 Hirewell Inc.",
        },
    ),
    ComponentDefinition(
        ComponentType.COMMAND,
        ui.CommandComponent,
        _INPUT,
        "A command bar: a search field over a short list of actions to jump to or run.",
        {
            "type": "command",
            "id": "dashboard_command",
            "placeholder": "Search candidates, jobs, actions…",
            "items": [
                {
                    "label": "Create a job",
                    "icon": "plus",
                    "hint": "New",
                    "action": {"type": "navigate", "payload": {"to": "/jobs/new"}},
                }
            ],
        },
    ),
    # --- Records ----------------------------------------------------------------------
    ComponentDefinition(
        ComponentType.COLLECTION,
        ui.CollectionComponent,
        _RECORD,
        "Records of a dataset. variant: cards, list, compact, media (image tiles; needs "
        "fields.image), feed (recent activity; needs fields.timestamp). fields name the "
        "record fields to show. item_action runs for the chosen record.",
        {
            "type": "collection",
            "id": "candidates_list",
            "variant": "list",
            "title": "Recent applicants",
            "data_source": {
                "dataset": "candidates",
                "limit": 6,
                "sort": {"field": "applied_on", "direction": "desc"},
            },
            "fields": {
                "title": "name",
                "subtitle": "role",
                "badge": "stage",
                "avatar": True,
                "meta": [{"key": "match_score", "label": "Match", "format": "percent"}],
            },
            "item_action": _OPEN_CANDIDATE,
        },
    ),
    ComponentDefinition(
        ComponentType.KANBAN,
        ui.KanbanComponent,
        _RECORD,
        "Records in columns by the value of group_by. columns lists the stages in order "
        "(value must equal the field's values). move_action is a record_update that sets "
        "that field when a card is moved.",
        {
            "type": "kanban",
            "id": "pipeline_board",
            "data_source": {"dataset": "candidates"},
            "group_by": "stage",
            "columns": [
                {"value": "Applied", "label": "Applied"},
                {"value": "Interview", "label": "Interview", "tone": "info"},
                {"value": "Offer", "label": "Offer", "tone": "success"},
            ],
            "fields": {"title": "name", "subtitle": "role", "avatar": True},
            "item_action": _OPEN_CANDIDATE,
            "move_action": {
                "type": "record_update",
                "payload": {"entity": "candidates", "set_field": "stage"},
            },
        },
    ),
    ComponentDefinition(
        ComponentType.PROFILE_HEADER,
        ui.ProfileHeaderComponent,
        _RECORD,
        "The header of a record's detail screen. Bind the one record with a where on the "
        "route parameter. variant: banner or compact.",
        {
            "type": "profile_header",
            "id": "candidate_header",
            "data_source": _ONE_CANDIDATE,
            "fields": {
                "title": "name",
                "subtitle": "role",
                "badge": "stage",
                "avatar": True,
                "meta": [
                    {"key": "location", "label": "Location"},
                    {"key": "match_score", "label": "Match", "format": "percent"},
                ],
            },
            "actions": [
                {
                    "label": "Shortlist",
                    "action": {
                        "type": "record_update",
                        "payload": {
                            "entity": "candidates",
                            "set_field": "stage",
                            "set_value": "Shortlisted",
                            "key_param": "candidateId",
                        },
                    },
                }
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.DETAIL,
        ui.DetailComponent,
        _RECORD,
        "Labelled fields of one record. variant: grid (columns) or list (narrow).",
        {
            "type": "detail",
            "id": "candidate_details",
            "title": "Profile",
            "data_source": _ONE_CANDIDATE,
            "columns": 2,
            "fields": [
                {"key": "email", "label": "Email"},
                {"key": "experience_years", "label": "Experience", "format": "number"},
            ],
        },
    ),
    ComponentDefinition(
        ComponentType.CALENDAR,
        ui.CalendarComponent,
        _RECORD,
        "Dated records as an agenda grouped by day.",
        {
            "type": "calendar",
            "id": "interviews_agenda",
            "title": "Upcoming interviews",
            "data_source": {"dataset": "interviews", "sort": {"field": "date", "direction": "asc"}},
            "date_field": "date",
            "time_field": "time",
            "title_field": "candidate_name",
            "subtitle_field": "interviewer",
            "badge_field": "format",
        },
    ),
)


@lru_cache
def build_default_registry() -> ComponentRegistry:
    return ComponentRegistry(_DEFAULT_DEFINITIONS)
