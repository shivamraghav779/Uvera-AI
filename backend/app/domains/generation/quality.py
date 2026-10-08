"""Design quality evaluation of a generated application.

The validator answers "is this a legal document?". This module answers "would a
designer be content with it as a first draft?" with checks a reviewer would make:
hierarchy, variety, realistic content, imagery where the style calls for it,
calls to action, navigation that reaches everything, restraint with effects.

The checks are deterministic rules over the document, so the same draft always
gets the same review and each finding names what to change. Findings on a
screen become that screen's refinement brief; the pipeline runs a bounded
number of refinement passes.
"""

import re
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

from pydantic import BaseModel

from app.domains.generative_ui.application import image_refs, unreachable_screens
from app.domains.generative_ui.design_registry import DesignRegistry
from app.domains.generative_ui.document import ImageryKind, UIDocument
from app.domains.generative_ui.schemas import (
    GRID_COLUMNS,
    AnyComponent,
    ButtonComponent,
    CalendarComponent,
    CollectionComponent,
    CtaComponent,
    FormComponent,
    GalleryComponent,
    HeroComponent,
    KanbanComponent,
    ProfileHeaderComponent,
    ScreenComponent,
    ScreenType,
    SectionComponent,
    StatsComponent,
    TableComponent,
)
from app.domains.generative_ui.tree import action_specs, screens, walk


class QualityCategory(StrEnum):
    HIERARCHY = "hierarchy"
    VARIETY = "variety"
    COMPLETENESS = "completeness"
    CONTENT = "content"
    IMAGERY = "imagery"
    CALL_TO_ACTION = "call_to_action"
    NAVIGATION = "navigation"
    DENSITY = "density"
    EFFECTS = "effects"
    LAYOUT = "layout"
    ACCESSIBILITY = "accessibility"


class Severity(StrEnum):
    MAJOR = "major"
    MINOR = "minor"


class QualityIssue(BaseModel):
    category: QualityCategory
    severity: Severity
    message: str
    recommendation: str
    screen_id: str | None = None


class QualityReport(BaseModel):
    """A review of one draft: a score out of 100 and what would raise it."""

    score: int
    issues: list[QualityIssue]
    recommendations: list[str]

    def for_screen(self, screen_id: str) -> list[QualityIssue]:
        return [issue for issue in self.issues if issue.screen_id == screen_id]

    @property
    def screens_to_refine(self) -> list[str]:
        """Screens with a major finding, worst first."""
        counts = Counter(
            issue.screen_id
            for issue in self.issues
            if issue.screen_id and issue.severity is Severity.MAJOR
        )
        return [screen_id for screen_id, _ in counts.most_common()]


_PENALTY = {Severity.MAJOR: 8, Severity.MINOR: 3}
_MARKETING = frozenset({ScreenType.LANDING, ScreenType.CONTENT, ScreenType.PRICING})
_DATA_SCREENS = frozenset(
    {ScreenType.DASHBOARD, ScreenType.ANALYTICS, ScreenType.LISTING, ScreenType.DETAIL}
)
_OPENERS = (HeroComponent, ProfileHeaderComponent, StatsComponent)
_SELF_SUFFICIENT = (
    KanbanComponent,
    CalendarComponent,
    TableComponent,
    CollectionComponent,
    GalleryComponent,
    FormComponent,
)
_PLACEHOLDER = re.compile(
    r"\blorem ipsum\b|\bdolor sit\b|\bfeature \d+\b|\bitem \d+\b|\bdescription here\b"
    r"|\bimage here\b|\byour (?:title|text|company) here\b|\bplaceholder\b|\btbd\b"
    r"|\bjohn doe\b|\bjane doe\b|\bacme\b|\bfoo\b|\bbar baz\b|\bsample text\b|\bexample\.com\b",
    re.IGNORECASE,
)
# A field key where words belong ("title", "project_type"): the model described a record
# instead of writing content.
_FIELD_NAME = re.compile(
    r"^(title|name|subtitle|description|label|value|image|[a-z][a-z0-9]*(?:_[a-z0-9]+)+)$"
)
_SKIPPED_TEXT_KEYS = frozenset({"id", "type", "image", "icon", "route", "avatar", "placeholder"})
MIN_MARKETING_SECTIONS = 4
MAX_SCREEN_SECTIONS = 14
MAX_SAME_TYPE_RUN = 3
MAX_EFFECTS_PER_SCREEN = 4
MIN_IMAGES_FOR_VISUAL_STYLE = 2
_Finding = tuple[QualityCategory, Severity, str, str]


def _field_names_as_content(value: object, in_items: bool = False) -> Iterator[str]:
    """Texts inside written item lists that are bare field keys."""
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"fields", "data_source", "columns", "action", "actions"}:
                continue  # these legitimately name fields
            if in_items and isinstance(nested, str) and key in {"title", "subtitle", "value"}:
                if _FIELD_NAME.match(nested):
                    yield nested
            else:
                yield from _field_names_as_content(nested, in_items or key == "items")
    elif isinstance(value, list):
        for nested in value:
            yield from _field_names_as_content(nested, in_items)


def _strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, nested in value.items():
            if key not in _SKIPPED_TEXT_KEYS:
                yield from _strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _strings(nested)


def _top_level(screen: ScreenComponent) -> list[AnyComponent]:
    return list(screen.children)


def _spans(screen: ScreenComponent) -> list[int]:
    """Widths of the screen's blocks, looking inside plain sections that only group a row."""
    spans: list[int] = []
    for child in screen.children:
        if isinstance(child, SectionComponent) and child.layout.span == GRID_COLUMNS:
            spans += [inner.layout.span for inner in child.children]
        else:
            spans.append(child.layout.span)
    return spans


class DesignQualityEvaluator:
    def __init__(self, design: DesignRegistry) -> None:
        self._design = design

    def evaluate(self, document: UIDocument) -> QualityReport:
        issues: list[QualityIssue] = []
        app_screens = screens(document.page)
        for screen in app_screens:
            issues += [
                QualityIssue(
                    category=category,
                    severity=severity,
                    message=message,
                    recommendation=recommendation,
                    screen_id=screen.id,
                )
                for category, severity, message, recommendation in self._screen(screen, document)
            ]
        issues += [
            QualityIssue(
                category=category, severity=severity, message=message, recommendation=recommendation
            )
            for category, severity, message, recommendation in self._application(
                document, app_screens
            )
        ]
        penalty = sum(_PENALTY[issue.severity] for issue in issues)
        return QualityReport(
            score=max(0, 100 - penalty),
            issues=issues,
            recommendations=list(dict.fromkeys(issue.recommendation for issue in issues))[:12],
        )

    # --- One screen -----------------------------------------------------------------

    def _screen(self, screen: ScreenComponent, document: UIDocument) -> Iterator[_Finding]:
        top = _top_level(screen)
        types = [child.type.value for child in top]
        dumped = screen.model_dump(mode="json")
        marketing = screen.screen_type in _MARKETING
        yield from self._hierarchy(screen, top, marketing)
        yield from self._variety(screen, types, marketing)
        yield from self._content(dumped)
        yield from self._calls_to_action(screen, marketing)
        yield from self._density(screen, top)
        yield from self._effects(screen, document)
        if screen.screen_type in _DATA_SCREENS and '"data_source"' not in screen.model_dump_json():
            yield (
                QualityCategory.COMPLETENESS,
                Severity.MAJOR,
                f"“{screen.title}” is a {screen.screen_type.value} screen but shows no data.",
                "Bind tables, collections, charts and figures to the application's entities.",
            )

    @staticmethod
    def _hierarchy(
        screen: ScreenComponent, top: Sequence[AnyComponent], marketing: bool
    ) -> Iterator[_Finding]:
        if not top:
            return
        first = top[0]
        if marketing and not isinstance(first, HeroComponent):
            yield (
                QualityCategory.HIERARCHY,
                Severity.MAJOR,
                f"“{screen.title}” does not open with a hero.",
                "Start marketing screens with a hero that states the offer and one main action.",
            )
        if isinstance(first, TableComponent) and screen.screen_type is ScreenType.DASHBOARD:
            yield (
                QualityCategory.HIERARCHY,
                Severity.MAJOR,
                f"“{screen.title}” opens with a table.",
                "Open a dashboard with headline figures, then the main chart, then the detail.",
            )
        if screen.screen_type in (ScreenType.DETAIL, ScreenType.PROFILE) and not any(
            isinstance(child, _OPENERS) for child in top[:2]
        ):
            yield (
                QualityCategory.HIERARCHY,
                Severity.MINOR,
                f"“{screen.title}” has no header identifying the record.",
                "Open a detail screen with a profile_header bound to the record.",
            )

    @staticmethod
    def _variety(
        screen: ScreenComponent, types: Sequence[str], marketing: bool
    ) -> Iterator[_Finding]:
        run, longest = 1, 1
        for previous, current in pairwise(types):
            run = run + 1 if previous == current else 1
            longest = max(longest, run)
        if longest > MAX_SAME_TYPE_RUN:
            yield (
                QualityCategory.VARIETY,
                Severity.MAJOR,
                f"“{screen.title}” repeats the same component {longest} times in a row.",
                "Combine repeated cards or metrics into one pattern (stats, feature_grid, "
                "collection) and vary the rhythm of sections.",
            )
        if marketing and len(set(types)) < MIN_MARKETING_SECTIONS:
            yield (
                QualityCategory.VARIETY,
                Severity.MAJOR,
                f"“{screen.title}” has only {len(set(types))} kinds of section.",
                "A landing page needs a story: hero, proof, what it does, how it looks, "
                "why believe it, and a closing call to action.",
            )
        spans = _spans(screen)
        if not marketing and len(spans) >= 4 and len(set(spans)) == 1 and spans[0] != 12:
            yield (
                QualityCategory.LAYOUT,
                Severity.MINOR,
                f"Every block on “{screen.title}” has the same width.",
                "Use asymmetric rows (8/4 or 7/5): the main content wide, support beside it.",
            )
        if not marketing and len(spans) >= 3 and all(span == 12 for span in spans):
            yield (
                QualityCategory.LAYOUT,
                Severity.MINOR,
                f"“{screen.title}” is a single column of full-width blocks.",
                "Place related blocks side by side (8/4 or 7/5) instead of stacking everything.",
            )

    @staticmethod
    def _content(dumped: dict[str, object]) -> Iterator[_Finding]:
        hits = sorted(
            {
                match.group(0).lower()
                for text in _strings(dumped)
                for match in _PLACEHOLDER.finditer(text)
            }
        )
        if hits:
            yield (
                QualityCategory.CONTENT,
                Severity.MAJOR,
                f"Placeholder wording found: {', '.join(hits[:4])}.",
                "Write specific, believable content for this product: real feature names, "
                "plausible people, companies and figures.",
            )

        keys = sorted(set(_field_names_as_content(dumped)))
        if keys:
            yield (
                QualityCategory.CONTENT,
                Severity.MAJOR,
                f"Field names are shown as content: {', '.join(keys[:4])}.",
                "Items hold the words a visitor reads. Write real titles and values, or show "
                "an entity's records with a collection, table or board bound to it.",
            )

    @staticmethod
    def _calls_to_action(screen: ScreenComponent, marketing: bool) -> Iterator[_Finding]:
        nodes = [node.component for node in walk(screen)]
        if marketing:
            hero = next((n for n in nodes if isinstance(n, HeroComponent)), None)
            if hero is not None and not hero.actions:
                yield (
                    QualityCategory.CALL_TO_ACTION,
                    Severity.MAJOR,
                    f"The hero on “{screen.title}” has no action.",
                    "Give the hero one primary action and at most one quieter alternative.",
                )
            if screen.screen_type is ScreenType.LANDING and not any(
                isinstance(n, CtaComponent) for n in nodes
            ):
                yield (
                    QualityCategory.CALL_TO_ACTION,
                    Severity.MINOR,
                    f"“{screen.title}” ends without a call to action.",
                    "Close the landing page with a cta section repeating the main action.",
                )
        if screen.screen_type is ScreenType.FORM and not any(
            isinstance(n, FormComponent) for n in nodes
        ):
            yield (
                QualityCategory.COMPLETENESS,
                Severity.MAJOR,
                f"“{screen.title}” is a form screen without a form.",
                "Add a form whose fields are the entity's fields, submitting a record_create.",
            )
        if screen.screen_type in (ScreenType.DETAIL, ScreenType.LISTING) and not any(
            action_specs(n) for n in nodes
        ):
            yield (
                QualityCategory.CALL_TO_ACTION,
                Severity.MINOR,
                f"Nothing can be done on “{screen.title}”.",
                "Let rows or cards open their record, and offer the screen's main action.",
            )

    @staticmethod
    def _density(screen: ScreenComponent, top: Sequence[AnyComponent]) -> Iterator[_Finding]:
        # One rich component (a board, a table, a form) can be the whole screen.
        if len(top) < 2 and not isinstance(top[0] if top else None, _SELF_SUFFICIENT):
            yield (
                QualityCategory.COMPLETENESS,
                Severity.MAJOR,
                f"“{screen.title}” is nearly empty.",
                "Give the screen what its purpose needs: context, the main content and "
                "supporting information.",
            )
        if len(top) > MAX_SCREEN_SECTIONS:
            yield (
                QualityCategory.DENSITY,
                Severity.MINOR,
                f"“{screen.title}” has {len(top)} top-level blocks.",
                "Group related blocks into sections, or move secondary content to its own screen.",
            )
        buttons = [n.component for n in walk(screen) if isinstance(n.component, ButtonComponent)]
        primary = [b for b in buttons if b.variant.value in ("primary", "gradient")]
        if len(primary) > 3:
            yield (
                QualityCategory.HIERARCHY,
                Severity.MINOR,
                f"“{screen.title}” has {len(primary)} primary buttons.",
                "One primary action per screen; make the others secondary or ghost.",
            )

    def _effects(self, screen: ScreenComponent, document: UIDocument) -> Iterator[_Finding]:
        used = [
            effect
            for node in walk(screen)
            if node.component.style and node.component.style.effects  # type: ignore[union-attr]
            for effect in node.component.style.effects  # type: ignore[union-attr]
        ]
        style = self._design.design_system(document.design.design_system)
        allowed = set(style.effects) if style else set()
        foreign = sorted({effect.value for effect in used if effect not in allowed})
        if foreign:
            yield (
                QualityCategory.EFFECTS,
                Severity.MINOR,
                f"“{screen.title}” uses effects that do not belong to this style: "
                f"{', '.join(foreign)}.",
                "Use only the effects of the chosen visual style, and only where they add focus.",
            )
        if len(used) > MAX_EFFECTS_PER_SCREEN:
            yield (
                QualityCategory.EFFECTS,
                Severity.MINOR,
                f"“{screen.title}” uses {len(used)} effects.",
                "Keep effects to the one or two sections that deserve attention.",
            )

    # --- The application as a whole ------------------------------------------------

    def _application(
        self, document: UIDocument, app_screens: Sequence[ScreenComponent]
    ) -> Iterator[_Finding]:
        application = document.application
        if application is None or not app_screens:
            return
        for screen_id in unreachable_screens(document):
            title = next(s.title for s in app_screens if s.id == screen_id)
            yield (
                QualityCategory.NAVIGATION,
                Severity.MAJOR,
                f"No navigation item or action leads to “{title}”.",
                "Link every screen: from the navigation, or from the rows, cards and buttons "
                "of the screen people come from.",
            )
        signatures = Counter(
            tuple(child.type.value for child in screen.children) for screen in app_screens
        )
        repeated = [sig for sig, count in signatures.items() if count > 2 and len(sig) > 1]
        if repeated:
            yield (
                QualityCategory.VARIETY,
                Severity.MINOR,
                "Several screens have exactly the same structure.",
                "Compose each screen for its purpose instead of repeating one layout.",
            )
        direction = application.design_direction
        visual = direction is not None and direction.imagery in (
            ImageryKind.PHOTOGRAPHY,
            ImageryKind.PRODUCT,
            ImageryKind.ILLUSTRATION,
        )
        referenced = {
            asset_id for _path, asset_id in image_refs(document.page.model_dump(mode="json"))
        }
        if (
            visual
            and application.assets
            and len(referenced) < min(MIN_IMAGES_FOR_VISUAL_STYLE, len(application.assets))
        ):
            yield (
                QualityCategory.IMAGERY,
                Severity.MAJOR,
                "The design direction is image-led, but the screens use almost none of the "
                "prepared images.",
                "Use the prepared images in heroes, media sections and galleries.",
            )
        missing_alt = [asset.id for asset in application.assets if len(asset.alt.strip()) < 4]
        if missing_alt:
            yield (
                QualityCategory.ACCESSIBILITY,
                Severity.MINOR,
                f"{len(missing_alt)} image(s) have no meaningful description.",
                "Describe what each image shows in its alt text.",
            )
        if len(application.navigation.items) > 8:
            yield (
                QualityCategory.NAVIGATION,
                Severity.MINOR,
                f"The navigation has {len(application.navigation.items)} items.",
                "Keep primary navigation to at most eight destinations; group the rest.",
            )


@dataclass(frozen=True, slots=True)
class RefinementBrief:
    """What to ask for when a screen is generated again after review."""

    screen_id: str
    findings: tuple[str, ...]

    def as_text(self) -> str:
        return "\n".join(f"- {finding}" for finding in self.findings)


def refinement_briefs(report: QualityReport, limit: int) -> list[RefinementBrief]:
    """One brief per screen worth regenerating, worst screens first."""
    briefs = []
    for screen_id in report.screens_to_refine[:limit]:
        findings = tuple(
            f"{issue.message} {issue.recommendation}" for issue in report.for_screen(screen_id)
        )
        briefs.append(RefinementBrief(screen_id=screen_id, findings=findings))
    return briefs
