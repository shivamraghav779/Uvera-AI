"""The design pattern catalogue: what the platform knows about composing screens.

Three kinds of knowledge live here, all as structured metadata:

    patterns       a component type in one variant ("hero.split"), with what it
                   is for, where it fits, what it needs and how it behaves
    compositions   proven orders of patterns for a kind of screen. They are
                   examples to reason from, never templates that get stamped out
    retrieval      ``PatternRegistry.select`` ranks patterns for a screen so each
                   AI stage sees the relevant part of the catalogue only

Retrieval is keyword scoring over this metadata. The interface (a brief in,
ranked patterns out) is what a semantic index would implement later.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

from app.domains.generative_ui.schemas import ComponentType, Effect, ScreenType


class PatternCategory(StrEnum):
    HERO = "hero"
    NAVIGATION = "navigation"
    CONTENT = "content"
    DATA = "data"
    COMMERCE = "commerce"
    SOCIAL = "social"
    CONVERSION = "conversion"
    RECORD = "record"
    INPUT = "input"


class PatternDensity(StrEnum):
    AIRY = "airy"
    BALANCED = "balanced"
    DENSE = "dense"


class ImageNeed(StrEnum):
    NONE = "none"
    OPTIONAL = "optional"
    REQUIRED = "required"


@dataclass(frozen=True, slots=True)
class PatternDescriptor:
    id: str
    component: ComponentType
    variant: str | None
    category: PatternCategory
    purpose: str
    screen_types: tuple[ScreenType, ...]
    # Lower-case keywords of products the pattern suits; empty means any product.
    suited_for: tuple[str, ...] = ()
    density: PatternDensity = PatternDensity.BALANCED
    characteristics: tuple[str, ...] = ()
    needs_data: bool = False
    image: ImageNeed = ImageNeed.NONE
    effects: tuple[Effect, ...] = ()
    responsive: str = "Stacks to one column on narrow screens."
    frameworks: tuple[str, ...] = ("shadcn", "material")


@dataclass(frozen=True, slots=True)
class Composition:
    """An ordered set of patterns that makes a coherent screen of some kind."""

    id: str
    name: str
    screen_type: ScreenType
    suited_for: tuple[str, ...]
    patterns: tuple[str, ...]
    note: str = ""


_S = ScreenType
_C = ComponentType
_E = Effect
_MARKETING = (_S.LANDING, _S.CONTENT, _S.PRICING, _S.ONBOARDING)
_APP = (_S.DASHBOARD, _S.ANALYTICS, _S.LISTING, _S.DETAIL, _S.PROFILE)


def _pattern(
    pattern_id: str,
    component: ComponentType,
    category: PatternCategory,
    purpose: str,
    screen_types: tuple[ScreenType, ...],
    **extra: object,
) -> PatternDescriptor:
    variant = pattern_id.split(".", 1)[1] if "." in pattern_id else None
    return PatternDescriptor(
        id=pattern_id,
        component=component,
        variant=variant,
        category=category,
        purpose=purpose,
        screen_types=screen_types,
        **extra,  # type: ignore[arg-type]
    )


_HERO = PatternCategory.HERO
_CONTENT = PatternCategory.CONTENT
_DATA = PatternCategory.DATA
_SOCIAL = PatternCategory.SOCIAL
_CONVERSION = PatternCategory.CONVERSION
_RECORD = PatternCategory.RECORD
_COMMERCE = PatternCategory.COMMERCE

_PATTERNS: tuple[PatternDescriptor, ...] = (
    # --- Hero -------------------------------------------------------------------
    _pattern("hero.split", _C.HERO, _HERO,
             "Headline and actions beside an image. The dependable opening of a product page.",
             _MARKETING, image=ImageNeed.REQUIRED,
             characteristics=("two columns", "image right"),
             effects=(_E.REVEAL, _E.GRADIENT_MESH),
             responsive="Image moves under the text on narrow screens."),
    _pattern("hero.centered", _C.HERO, _HERO,
             "A centred statement with actions; nothing competes with the words.",
             _MARKETING, suited_for=("saas", "ai", "developer", "fintech"),
             density=PatternDensity.AIRY, image=ImageNeed.OPTIONAL,
             characteristics=("centred", "large type"),
             effects=(_E.SPOTLIGHT, _E.GRID, _E.GRADIENT_MESH)),
    _pattern("hero.immersive", _C.HERO, _HERO,
             "Full-bleed photograph with the headline over it. For products sold by feeling.",
             (_S.LANDING, _S.CONTENT),
             suited_for=("travel", "hospitality", "luxury", "real estate", "food", "event"),
             density=PatternDensity.AIRY, image=ImageNeed.REQUIRED,
             characteristics=("full bleed", "text over image"), effects=(_E.PARALLAX,)),
    _pattern("hero.editorial", _C.HERO, _HERO,
             "Very large type with a small label and a wide image below, like a magazine opener.",
             (_S.LANDING, _S.CONTENT),
             suited_for=("architecture", "studio", "agency", "portfolio", "fashion", "magazine"),
             density=PatternDensity.AIRY, image=ImageNeed.REQUIRED,
             characteristics=("asymmetric", "display type"), effects=(_E.REVEAL,)),
    _pattern("hero.product", _C.HERO, _HERO,
             "Headline above a large framed screenshot of the product itself.",
             (_S.LANDING,), suited_for=("saas", "ai", "developer", "productivity", "platform"),
             image=ImageNeed.REQUIRED, characteristics=("product preview", "centred"),
             effects=(_E.GLOW, _E.SPOTLIGHT, _E.REVEAL)),
    # --- Content ------------------------------------------------------------------
    _pattern("feature_grid.grid", _C.FEATURE_GRID, _CONTENT,
             "Equal cells, each one capability with an icon.", _MARKETING,
             characteristics=("regular grid",), effects=(_E.HOVER_LIFT, _E.REVEAL),
             responsive="Collapses from three or four columns to one."),
    _pattern("feature_grid.bento", _C.FEATURE_GRID, _CONTENT,
             "Cells of different sizes; the important capabilities get the large cells.",
             _MARKETING, suited_for=("saas", "ai", "productivity", "consumer", "platform"),
             image=ImageNeed.OPTIONAL, characteristics=("asymmetric", "mixed cell sizes"),
             effects=(_E.SPOTLIGHT, _E.HOVER_LIFT, _E.REVEAL)),
    _pattern("feature_grid.alternating", _C.FEATURE_GRID, _CONTENT,
             "Features told one at a time, image and text swapping sides.",
             (_S.LANDING, _S.CONTENT), density=PatternDensity.AIRY, image=ImageNeed.REQUIRED,
             characteristics=("storytelling", "image/text split"), effects=(_E.REVEAL,)),
    _pattern("feature_grid.list", _C.FEATURE_GRID, _CONTENT,
             "A plain list of points with short explanations.",
             (*_MARKETING, _S.SETTINGS), density=PatternDensity.DENSE,
             characteristics=("text only",)),
    _pattern("media.image_right", _C.MEDIA, _CONTENT,
             "A statement with supporting points beside one image.",
             (*_MARKETING, _S.DETAIL), image=ImageNeed.REQUIRED,
             characteristics=("7/5 split",), effects=(_E.REVEAL,)),
    _pattern("media.image_left", _C.MEDIA, _CONTENT,
             "Image first, then the statement; alternate with image_right for rhythm.",
             (*_MARKETING, _S.DETAIL), image=ImageNeed.REQUIRED,
             characteristics=("5/7 split",), effects=(_E.REVEAL,)),
    _pattern("media.framed", _C.MEDIA, _CONTENT,
             "A product preview in a window frame with the explanation beside it.",
             (_S.LANDING,), suited_for=("saas", "ai", "developer", "platform"),
             image=ImageNeed.REQUIRED, characteristics=("product preview",),
             effects=(_E.GLOW, _E.REVEAL)),
    _pattern("media.overlay", _C.MEDIA, _CONTENT,
             "Text set over a wide image: a pause between sections.",
             (_S.LANDING, _S.CONTENT), suited_for=("travel", "luxury", "architecture", "wellness"),
             density=PatternDensity.AIRY, image=ImageNeed.REQUIRED,
             characteristics=("full bleed",), effects=(_E.PARALLAX,)),
    _pattern("gallery.editorial", _C.GALLERY, _CONTENT,
             "Selected work as large images of different sizes with small metadata.",
             (_S.LANDING, _S.CONTENT, _S.LISTING),
             suited_for=("architecture", "studio", "portfolio", "agency", "photography"),
             density=PatternDensity.AIRY, image=ImageNeed.REQUIRED,
             characteristics=("asymmetric", "large imagery"), effects=(_E.REVEAL, _E.HOVER_LIFT)),
    _pattern("gallery.grid", _C.GALLERY, _CONTENT,
             "Image tiles of equal size: destinations, categories, products.",
             (_S.LANDING, _S.CONTENT, _S.LISTING), image=ImageNeed.REQUIRED,
             characteristics=("regular grid", "image tiles"), effects=(_E.HOVER_LIFT,)),
    _pattern("gallery.masonry", _C.GALLERY, _CONTENT,
             "Images at their own heights in columns.",
             (_S.LANDING, _S.CONTENT), suited_for=("photography", "inspiration", "travel"),
             image=ImageNeed.REQUIRED, characteristics=("varied heights",)),
    _pattern("gallery.carousel", _C.GALLERY, _CONTENT,
             "A row of tiles that scrolls sideways.",
             (_S.LANDING, _S.DASHBOARD), image=ImageNeed.REQUIRED,
             characteristics=("horizontal scroll",),
             responsive="Scrolls horizontally at every width."),
    _pattern("steps.numbered", _C.STEPS, _CONTENT,
             "How it works in a few numbered steps.", (*_MARKETING, _S.ONBOARDING),
             characteristics=("sequence",), effects=(_E.REVEAL,)),
    _pattern("steps.timeline", _C.STEPS, _CONTENT,
             "A process or history along a line.", (*_MARKETING, _S.DETAIL),
             characteristics=("vertical line",)),
    _pattern("steps.cards", _C.STEPS, _CONTENT,
             "Steps as cards in a row.", (*_MARKETING, _S.ONBOARDING),
             effects=(_E.HOVER_LIFT,)),
    _pattern("faq", _C.FAQ, _CONTENT, "Questions people ask before committing.",
             (_S.LANDING, _S.PRICING, _S.CONTENT), density=PatternDensity.DENSE),
    _pattern("comparison", _C.COMPARISON, _COMMERCE,
             "Options side by side, feature by feature.",
             (_S.PRICING, _S.LANDING, _S.DETAIL), density=PatternDensity.DENSE,
             responsive="Scrolls horizontally on narrow screens."),
    _pattern("footer", _C.FOOTER, PatternCategory.NAVIGATION,
             "Closing links and the legal line.", (_S.LANDING, _S.CONTENT, _S.PRICING)),
    # --- Social proof ---------------------------------------------------------------
    _pattern("logo_cloud.static", _C.LOGO_CLOUD, _SOCIAL,
             "Names of customers or partners in a quiet row.", (_S.LANDING, _S.PRICING),
             suited_for=("saas", "b2b", "agency", "fintech", "developer")),
    _pattern("logo_cloud.marquee", _C.LOGO_CLOUD, _SOCIAL,
             "Customer names scrolling continuously.", (_S.LANDING,),
             suited_for=("saas", "agency", "consumer"), effects=(_E.MARQUEE,)),
    _pattern("testimonials.cards", _C.TESTIMONIALS, _SOCIAL,
             "Several short quotes with names and roles.", (_S.LANDING, _S.PRICING),
             effects=(_E.REVEAL,)),
    _pattern("testimonials.spotlight", _C.TESTIMONIALS, _SOCIAL,
             "One long quote given the whole width.", (_S.LANDING, _S.CONTENT),
             density=PatternDensity.AIRY, characteristics=("single large quote",)),
    _pattern("stats.strip", _C.STATS, _DATA,
             "Three to five headline figures in one row: a KPI strip.",
             (*_APP, _S.LANDING), needs_data=True, density=PatternDensity.DENSE,
             characteristics=("one row",), effects=(_E.COUNTER,),
             responsive="Wraps to two per row, then one."),
    _pattern("stats.cards", _C.STATS, _DATA,
             "Figures as separate cards with trend and context.",
             _APP, needs_data=True, effects=(_E.COUNTER,)),
    _pattern("stats.inline", _C.STATS, _DATA,
             "Large figures set in running layout, for proof on a marketing page.",
             (_S.LANDING, _S.CONTENT), density=PatternDensity.AIRY, effects=(_E.COUNTER,)),
    # --- Conversion -----------------------------------------------------------------
    _pattern("pricing", _C.PRICING, _COMMERCE,
             "Plans with price, what is included and one action each.",
             (_S.PRICING, _S.LANDING), suited_for=("saas", "subscription", "membership"),
             characteristics=("highlighted plan",), effects=(_E.HOVER_LIFT,)),
    _pattern("cta.centered", _C.CTA, _CONVERSION,
             "The closing ask: one sentence and one or two actions.",
             (_S.LANDING, _S.CONTENT, _S.PRICING), density=PatternDensity.AIRY,
             effects=(_E.GRADIENT_MESH, _E.SPOTLIGHT)),
    _pattern("cta.banner", _C.CTA, _CONVERSION,
             "A compact band with the ask on the left and the action on the right.",
             (_S.LANDING, _S.DASHBOARD, _S.LISTING)),
    _pattern("cta.split", _C.CTA, _CONVERSION,
             "The ask beside an image.", (_S.LANDING, _S.CONTENT),
             image=ImageNeed.REQUIRED),
    # --- Data and records -----------------------------------------------------------
    _pattern("collection.cards", _C.COLLECTION, _RECORD,
             "Records as cards with title, status and a few facts.",
             (_S.LISTING, _S.DASHBOARD, _S.PROFILE), needs_data=True,
             effects=(_E.HOVER_LIFT,)),
    _pattern("collection.media", _C.COLLECTION, _RECORD,
             "Records as image tiles: products, places, listings.",
             (_S.LISTING, _S.LANDING, _S.DASHBOARD),
             suited_for=("ecommerce", "travel", "real estate", "marketplace", "food"),
             needs_data=True, image=ImageNeed.REQUIRED, effects=(_E.HOVER_LIFT,)),
    _pattern("collection.list", _C.COLLECTION, _RECORD,
             "Records as rows with avatar, title and status.",
             (_S.LISTING, _S.DASHBOARD, _S.DETAIL), needs_data=True,
             density=PatternDensity.DENSE),
    _pattern("collection.compact", _C.COLLECTION, _RECORD,
             "A short list for a sidebar or a dashboard panel.",
             (_S.DASHBOARD, _S.DETAIL, _S.ANALYTICS), needs_data=True,
             density=PatternDensity.DENSE),
    _pattern("collection.feed", _C.COLLECTION, _RECORD,
             "Recent activity in time order.",
             (_S.DASHBOARD, _S.DETAIL, _S.PROFILE), needs_data=True,
             density=PatternDensity.DENSE, characteristics=("timestamps",)),
    _pattern("kanban", _C.KANBAN, _RECORD,
             "Records in columns by stage; cards move between stages.",
             (_S.LISTING, _S.DASHBOARD, _S.CUSTOM),
             suited_for=("recruitment", "crm", "sales", "project", "support", "pipeline"),
             needs_data=True, density=PatternDensity.DENSE,
             responsive="Columns scroll horizontally on narrow screens."),
    _pattern("calendar", _C.CALENDAR, _RECORD,
             "Dated records as an agenda grouped by day.",
             (_S.CALENDAR, _S.DASHBOARD, _S.DETAIL), needs_data=True),
    _pattern("profile_header.banner", _C.PROFILE_HEADER, _RECORD,
             "Who or what this record is: name, status, key facts and the main actions.",
             (_S.DETAIL, _S.PROFILE), needs_data=True, image=ImageNeed.OPTIONAL),
    _pattern("profile_header.compact", _C.PROFILE_HEADER, _RECORD,
             "A one-line record header for dense detail screens.",
             (_S.DETAIL, _S.PROFILE), needs_data=True, density=PatternDensity.DENSE),
    _pattern("detail.grid", _C.DETAIL, _RECORD,
             "A record's fields as labelled values in columns.",
             (_S.DETAIL, _S.PROFILE, _S.SETTINGS), needs_data=True),
    _pattern("detail.list", _C.DETAIL, _RECORD,
             "A record's fields as a narrow label/value list for a side column.",
             (_S.DETAIL, _S.PROFILE), needs_data=True, density=PatternDensity.DENSE),
    _pattern("table", _C.TABLE, _DATA,
             "Many records with several comparable fields; rows open the record.",
             (_S.LISTING, _S.DASHBOARD, _S.ANALYTICS, _S.DETAIL), needs_data=True,
             density=PatternDensity.DENSE,
             responsive="Scrolls horizontally when columns do not fit."),
    _pattern("chart", _C.CHART, _DATA,
             "One relationship in the data: a trend, a ranking, a split.",
             (_S.DASHBOARD, _S.ANALYTICS, _S.DETAIL), needs_data=True),
    _pattern("command", _C.COMMAND, PatternCategory.INPUT,
             "A command bar to jump to screens and run common actions.",
             (_S.DASHBOARD, _S.LANDING, _S.CUSTOM),
             suited_for=("developer", "ai", "productivity", "saas")),
    _pattern("form", _C.FORM, PatternCategory.INPUT,
             "Collect or edit one record.",
             (_S.FORM, _S.SETTINGS, _S.ONBOARDING, _S.AUTHENTICATION, _S.DETAIL)),
)  # fmt: skip

_COMPOSITIONS: tuple[Composition, ...] = (
    Composition("saas_landing", "SaaS landing page", _S.LANDING,
                ("saas", "platform", "b2b", "ai", "productivity"),
                ("hero.product", "logo_cloud.static", "feature_grid.bento", "media.framed",
                 "stats.inline", "testimonials.cards", "pricing", "cta.centered", "footer"),
                "Show the product early; proof before price."),
    Composition("editorial_studio", "Studio or portfolio site", _S.LANDING,
                ("architecture", "studio", "agency", "portfolio", "fashion"),
                ("hero.editorial", "media.image_right", "gallery.editorial", "media.overlay",
                 "stats.inline", "testimonials.spotlight", "cta.centered", "footer"),
                "Few sections, each given room. Images are the content."),
    Composition("travel_experience", "Travel or hospitality landing", _S.LANDING,
                ("travel", "hospitality", "experiences", "tourism", "booking"),
                ("hero.immersive", "gallery.grid", "feature_grid.alternating", "media.overlay",
                 "testimonials.cards", "cta.split", "footer"),
                "Open with place, then choice, then reassurance."),
    Composition("commerce_home", "Shop home", _S.LANDING,
                ("ecommerce", "shop", "store", "marketplace", "retail"),
                ("hero.split", "gallery.grid", "collection.media", "media.image_left",
                 "testimonials.cards", "cta.banner", "footer")),
    Composition("developer_landing", "Developer product landing", _S.LANDING,
                ("developer", "api", "devops", "infrastructure", "open source"),
                ("hero.centered", "command", "feature_grid.grid", "media.framed",
                 "logo_cloud.static", "pricing", "cta.banner", "footer"),
                "Precise claims, product on screen, no stock photography."),
    Composition("operations_dashboard", "Operational dashboard", _S.DASHBOARD,
                ("saas", "recruitment", "crm", "operations", "support", "logistics"),
                ("stats.strip", "chart", "collection.feed", "table"),
                "Figures first, then the main trend beside what needs attention (8/4), "
                "then the working list."),
    Composition("analytics_overview", "Analytics screen", _S.ANALYTICS,
                ("analytics", "fintech", "marketing", "saas"),
                ("stats.cards", "chart", "chart", "table"),
                "One wide chart, then two narrower ones side by side (7/5), then the table."),
    Composition("record_listing", "Listing of records", _S.LISTING, (),
                ("stats.strip", "table"),
                "A filter row above the list; cards instead of a table when records are visual."),
    Composition("record_detail", "Record detail", _S.DETAIL, (),
                ("profile_header.banner", "stats.strip", "detail.grid", "collection.feed"),
                "Header across the top, then main content beside a narrower side column (8/4)."),
    Composition("pipeline_board", "Pipeline board", _S.LISTING,
                ("recruitment", "crm", "sales", "project"),
                ("stats.strip", "kanban")),
    Composition("schedule", "Schedule", _S.CALENDAR, (),
                ("stats.strip", "calendar", "collection.compact"),
                "Agenda in the wide column, what is next in the narrow one."),
    Composition("pricing_page", "Pricing page", _S.PRICING, ("saas", "subscription"),
                ("hero.centered", "pricing", "comparison", "faq", "cta.centered", "footer")),
    Composition("record_form", "Create or edit form", _S.FORM, (),
                ("form",), "One focused form, narrow width, with a way back."),
    Composition("settings", "Settings", _S.SETTINGS, (),
                ("form", "feature_grid.list")),
)  # fmt: skip


class PatternRegistry:
    def __init__(
        self,
        patterns: Iterable[PatternDescriptor] = _PATTERNS,
        compositions: Iterable[Composition] = _COMPOSITIONS,
    ) -> None:
        self._patterns: dict[str, PatternDescriptor] = {}
        for pattern in patterns:
            if pattern.id in self._patterns:
                raise ValueError(f"Pattern '{pattern.id}' is registered twice.")
            self._patterns[pattern.id] = pattern
        self._compositions = tuple(compositions)
        for composition in self._compositions:
            unknown = [p for p in composition.patterns if p not in self._patterns]
            if unknown:
                raise ValueError(f"Composition '{composition.id}' uses unknown patterns {unknown}.")

    def patterns(self) -> tuple[PatternDescriptor, ...]:
        return tuple(self._patterns.values())

    def compositions(self) -> tuple[Composition, ...]:
        return self._compositions

    def get(self, pattern_id: str) -> PatternDescriptor | None:
        return self._patterns.get(pattern_id)

    def components(self, pattern_ids: Iterable[str]) -> list[ComponentType]:
        """Component types behind ``pattern_ids``, without duplicates, in first-use order."""
        types = [self._patterns[p].component for p in pattern_ids if p in self._patterns]
        return list(dict.fromkeys(types))

    def select(
        self, screen_type: ScreenType, brief: str = "", *, limit: int = 40
    ) -> tuple[PatternDescriptor, ...]:
        """Patterns that fit a screen of ``screen_type`` for the product in ``brief``.

        Patterns made for this kind of screen come first; among them, those whose
        keywords match the brief. Patterns for other kinds of screen are left out.
        """
        text = brief.lower()
        fitting = [p for p in self._patterns.values() if screen_type in p.screen_types]

        def score(pattern: PatternDescriptor) -> int:
            matches = sum(keyword in text for keyword in pattern.suited_for)
            # A pattern with no keywords suits everything; one with keywords that all miss
            # is a weaker candidate than a general one.
            return matches * 2 if matches else (1 if not pattern.suited_for else 0)

        return tuple(sorted(fitting, key=lambda pattern: -score(pattern))[:limit])

    def compositions_for(
        self, screen_type: ScreenType, brief: str = "", *, limit: int = 2
    ) -> tuple[Composition, ...]:
        text = brief.lower()
        fitting = [c for c in self._compositions if c.screen_type is screen_type]
        ranked = sorted(fitting, key=lambda c: -sum(keyword in text for keyword in c.suited_for))
        return tuple(ranked[:limit])


@lru_cache
def build_default_pattern_registry() -> PatternRegistry:
    return PatternRegistry()
