"""The UI Schema: the only thing the model is allowed to produce.

A UI is a tree of components rooted at a ``page``. Every component is a strict
Pydantic model: unknown component types and unknown fields are rejected, so the
schema has no place for code, markup or arbitrary props. The React frontend
renders these components from its own registry.

Three levels of vocabulary live here:

    primitives   button, card, table, chart, form, ...
    patterns     hero, feature_grid, pricing, kanban, collection, ... (designed
                 compositions with variants; still plain data)
    screens      a routed page of an application; the children of the root
                 ``page`` when the document is an application

Images are referenced by asset id, icons by name, colours by token. Nothing in
a component can carry a URL to load, CSS or markup.
"""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from app.domains.actions.schemas import ActionType
from app.domains.common import DataRow, Scalar, StrictModel

UI_SCHEMA_VERSION = "3.0"
GRID_COLUMNS = 12

MAX_CHILDREN = 50
MAX_DATA_ROWS = 500
MAX_ITEMS = 100

ComponentId = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,63}$",
        description="Unique within the page. Letters, digits, '_' or '-'; starts with a letter.",
    ),
]
FieldKey = Annotated[str, Field(min_length=1, max_length=64)]
# Id of an entry in the application's asset list. Never a URL.
AssetId = Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")]
# Name of an icon in the frontend's icon registry; unknown names render a neutral glyph.
IconName = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{0,39}$")]
RoutePath = Annotated[
    str,
    Field(
        pattern=r"^/(?:[A-Za-z0-9_-]+|:[A-Za-z][A-Za-z0-9_]*)?(?:/(?:[A-Za-z0-9_-]+|:[A-Za-z][A-Za-z0-9_]*))*$",
        max_length=120,
        description="In-app path such as '/jobs' or '/jobs/:jobId'.",
    ),
]
MediumText = Annotated[str, Field(min_length=1, max_length=600)]
ShortText = Annotated[str, Field(min_length=1, max_length=200)]
LongText = Annotated[str, Field(min_length=1, max_length=4000)]


class ComponentType(StrEnum):
    PAGE = "page"
    SECTION = "section"
    CARD = "card"
    METRIC = "metric"
    TEXT = "text"
    TABLE = "table"
    CHART = "chart"
    FORM = "form"
    INPUT = "input"
    SELECT = "select"
    CHECKBOX = "checkbox"
    BUTTON = "button"
    BADGE = "badge"
    ALERT = "alert"
    LIST = "list"
    TIMELINE = "timeline"
    PROGRESS = "progress"
    TABS = "tabs"
    DIVIDER = "divider"
    MODAL = "modal"
    # Application structure
    SCREEN = "screen"
    # Patterns
    HERO = "hero"
    FEATURE_GRID = "feature_grid"
    LOGO_CLOUD = "logo_cloud"
    TESTIMONIALS = "testimonials"
    PRICING = "pricing"
    CTA = "cta"
    STATS = "stats"
    GALLERY = "gallery"
    COLLECTION = "collection"
    KANBAN = "kanban"
    DETAIL = "detail"
    PROFILE_HEADER = "profile_header"
    IMAGE = "image"
    MEDIA = "media"
    STEPS = "steps"
    FAQ = "faq"
    FOOTER = "footer"
    CALENDAR = "calendar"
    COMPARISON = "comparison"
    COMMAND = "command"


class Tone(StrEnum):
    NEUTRAL = "neutral"
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


class HeightPreset(StrEnum):
    """Controlled heights; the frontend maps each to a size. No pixel values."""

    AUTO = "auto"
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"


class ColorRole(StrEnum):
    """A theme colour a component can take on. Never a raw colour value."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    WARNING = "warning"
    DESTRUCTIVE = "destructive"
    NEUTRAL = "neutral"


class Emphasis(StrEnum):
    SUBTLE = "subtle"
    DEFAULT = "default"
    STRONG = "strong"


class Aggregate(StrEnum):
    SUM = "sum"
    AVERAGE = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    FIRST = "first"


class TextVariant(StrEnum):
    HEADING = "heading"
    SUBHEADING = "subheading"
    BODY = "body"
    CAPTION = "caption"


class TrendDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class ChartType(StrEnum):
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"


class ColumnFormat(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENT = "percent"
    DATE = "date"


class Alignment(StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class InputType(StrEnum):
    TEXT = "text"
    NUMBER = "number"
    EMAIL = "email"
    DATE = "date"
    SEARCH = "search"
    TEXTAREA = "textarea"


class ButtonVariant(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    DANGER = "danger"
    GHOST = "ghost"
    OUTLINE = "outline"
    GRADIENT = "gradient"
    GLASS = "glass"


class SurfaceVariant(StrEnum):
    """How a card-like surface is drawn. Each is a token set owned by the frontend."""

    FLAT = "flat"
    BORDERED = "bordered"
    ELEVATED = "elevated"
    GLASS = "glass"
    MINIMAL = "minimal"
    FEATURED = "featured"
    INTERACTIVE = "interactive"


class VisualPriority(StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class ComponentDensity(StrEnum):
    COMPACT = "compact"
    COMFORTABLE = "comfortable"
    SPACIOUS = "spacious"


class Effect(StrEnum):
    """Visual effects the frontend implements. A component may request a few of them."""

    GRADIENT_MESH = "gradient_mesh"
    ANIMATED_GRADIENT = "animated_gradient"
    GLOW = "glow"
    GLASS = "glass"
    NOISE = "noise"
    GRID = "grid"
    SPOTLIGHT = "spotlight"
    REVEAL = "reveal"
    HOVER_LIFT = "hover_lift"
    PARALLAX = "parallax"
    MARQUEE = "marquee"
    COUNTER = "counter"


class ScreenType(StrEnum):
    LANDING = "landing"
    DASHBOARD = "dashboard"
    LISTING = "listing"
    DETAIL = "detail"
    FORM = "form"
    SETTINGS = "settings"
    ANALYTICS = "analytics"
    PROFILE = "profile"
    CALENDAR = "calendar"
    ONBOARDING = "onboarding"
    AUTHENTICATION = "authentication"
    PRICING = "pricing"
    CONTENT = "content"
    CUSTOM = "custom"


class ScreenWidth(StrEnum):
    """Content width of a screen: reading width, application width or edge to edge."""

    NARROW = "narrow"
    CONTAINED = "contained"
    WIDE = "wide"
    FULL = "full"


class SectionVariant(StrEnum):
    DEFAULT = "default"
    SPLIT = "split"
    IMMERSIVE = "immersive"
    FULL_BLEED = "full_bleed"
    EDITORIAL = "editorial"
    BAND = "band"


class SortOrder(StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class ImageAspect(StrEnum):
    AUTO = "auto"
    SQUARE = "square"
    VIDEO = "video"
    WIDE = "wide"
    ULTRAWIDE = "ultrawide"
    PORTRAIT = "portrait"


class TimelineStatus(StrEnum):
    COMPLETED = "completed"
    CURRENT = "current"
    UPCOMING = "upcoming"


class ConditionOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    IS_SET = "is_set"
    IS_EMPTY = "is_empty"


# --- Building blocks ---------------------------------------------------------


class ActionSpec(StrictModel):
    """A declarative request to run an allowlisted backend action.

    ``payload`` holds static parameters; the frontend adds runtime values (for
    example the option a user picked) before calling the actions API.
    """

    type: ActionType
    payload: dict[str, Scalar | list[Scalar]] = Field(default_factory=dict)


class VisibilityCondition(StrictModel):
    """Show the component only while a form control's value satisfies the condition."""

    field: FieldKey = Field(description="`name` of an input/select/checkbox, or a component id.")
    operator: ConditionOperator = ConditionOperator.EQUALS
    value: Scalar | list[Scalar] = None


class RowCondition(StrictModel):
    """Keep rows whose ``field`` matches a fixed ``value`` or a route parameter.

    ``param`` names a parameter of the current screen's route (``/jobs/:jobId``),
    which is how a detail screen shows the one record it was opened for.
    """

    field: FieldKey
    operator: ConditionOperator = ConditionOperator.EQUALS
    value: Scalar | list[Scalar] = None
    param: FieldKey | None = None

    @model_validator(mode="after")
    def _one_operand(self) -> Self:
        if self.param is not None and self.value is not None:
            raise ValueError("Use either 'value' or 'param', not both.")
        return self


class RowSort(StrictModel):
    field: FieldKey
    direction: SortOrder = SortOrder.ASCENDING


class DataBinding(StrictModel):
    """Reference to a dataset the backend resolves into rows before responding.

    The frontend narrows the rows declaratively: ``where`` filters, ``sort``
    orders, ``group_by`` + ``aggregate`` summarise (one row per group holding the
    group value and the aggregated ``field``, or ``count``), ``limit`` truncates.
    """

    dataset: FieldKey
    limit: int | None = Field(default=None, ge=1, le=MAX_DATA_ROWS)
    where: list[RowCondition] | None = Field(default=None, max_length=4)
    sort: RowSort | None = None
    group_by: FieldKey | None = None
    aggregate: Aggregate | None = None
    field: FieldKey | None = Field(
        default=None, description="Field aggregated per group; omit to count rows."
    )

    @model_validator(mode="after")
    def _grouping_is_complete(self) -> Self:
        if self.group_by is None and (self.aggregate is not None or self.field is not None):
            raise ValueError("'aggregate' and 'field' need 'group_by'.")
        return self


class MetricBinding(StrictModel):
    """Derive a metric's value from one field of a dataset."""

    dataset: FieldKey
    field: FieldKey
    aggregate: Aggregate = Aggregate.SUM
    where: list[RowCondition] | None = Field(default=None, max_length=4)


class LayoutSpec(StrictModel):
    """Placement intent inside the parent's 12-column flow grid."""

    span: int = Field(default=GRID_COLUMNS, ge=1, le=GRID_COLUMNS, description="Width in columns.")
    height: HeightPreset = HeightPreset.AUTO


class ComponentStyle(StrictModel):
    """Token-based styling. There is deliberately no field for CSS."""

    tone: ColorRole | None = None
    emphasis: Emphasis | None = None
    surface: SurfaceVariant | None = None
    priority: VisualPriority | None = None
    density: ComponentDensity | None = None
    align: Alignment | None = None
    effects: list[Effect] | None = Field(default=None, max_length=3)


class BaseComponent(StrictModel):
    id: ComponentId
    layout: LayoutSpec = Field(default_factory=LayoutSpec)
    style: ComponentStyle | None = None
    visible_when: VisibilityCondition | None = None
    metadata: dict[str, Scalar] | None = Field(
        default=None, description="Optional free-form annotations; never interpreted as code."
    )


# --- Leaf components ---------------------------------------------------------


class Trend(StrictModel):
    direction: TrendDirection
    value: ShortText = Field(examples=["+12.4%"])
    label: ShortText | None = Field(default=None, examples=["vs last quarter"])


class MetricComponent(BaseComponent):
    type: Literal[ComponentType.METRIC]
    title: ShortText
    value: str | int | float | None = None
    data_source: MetricBinding | None = None
    format: ColumnFormat = ColumnFormat.TEXT
    unit: ShortText | None = None
    trend: Trend | None = None
    description: ShortText | None = None


class TextComponent(BaseComponent):
    type: Literal[ComponentType.TEXT]
    content: LongText
    variant: TextVariant = TextVariant.BODY


class TableColumn(StrictModel):
    key: FieldKey
    label: ShortText
    format: ColumnFormat = ColumnFormat.TEXT
    align: Alignment = Alignment.LEFT


class TableComponent(BaseComponent):
    type: Literal[ComponentType.TABLE]
    title: ShortText | None = None
    columns: list[TableColumn] = Field(min_length=1, max_length=20)
    rows: list[DataRow] = Field(default_factory=list, max_length=MAX_DATA_ROWS)
    data_source: DataBinding | None = None
    page_size: int | None = Field(default=None, ge=1, le=100)
    row_action: ActionSpec | None = Field(
        default=None, description="Runs when a row is activated, with that row as context."
    )


class ChartComponent(BaseComponent):
    type: Literal[ComponentType.CHART]
    title: ShortText | None = None
    chart_type: ChartType
    x_key: FieldKey = Field(description="Row field used for categories / the x axis.")
    y_keys: list[FieldKey] = Field(
        min_length=1, max_length=8, description="Row fields plotted as series."
    )
    data: list[DataRow] = Field(default_factory=list, max_length=MAX_DATA_ROWS)
    data_source: DataBinding | None = None


class InputComponent(BaseComponent):
    type: Literal[ComponentType.INPUT]
    name: FieldKey
    label: ShortText
    input_type: InputType = InputType.TEXT
    placeholder: ShortText | None = None
    default_value: str | int | float | None = None
    required: bool = False
    on_change: ActionSpec | None = None


class SelectOption(StrictModel):
    label: ShortText
    value: ShortText


class SelectComponent(BaseComponent):
    type: Literal[ComponentType.SELECT]
    name: FieldKey
    label: ShortText
    options: list[SelectOption] = Field(min_length=1, max_length=MAX_ITEMS)
    default_value: ShortText | None = None
    multiple: bool = False
    required: bool = False
    on_change: ActionSpec | None = None


class CheckboxComponent(BaseComponent):
    type: Literal[ComponentType.CHECKBOX]
    name: FieldKey
    label: ShortText
    checked: bool = False
    on_change: ActionSpec | None = None


class ButtonComponent(BaseComponent):
    type: Literal[ComponentType.BUTTON]
    label: ShortText
    action: ActionSpec
    variant: ButtonVariant = ButtonVariant.PRIMARY
    disabled: bool = False


class BadgeComponent(BaseComponent):
    type: Literal[ComponentType.BADGE]
    label: ShortText
    tone: Tone = Tone.NEUTRAL


class AlertComponent(BaseComponent):
    type: Literal[ComponentType.ALERT]
    title: ShortText | None = None
    message: LongText
    tone: Tone = Tone.INFO


class ListItem(StrictModel):
    title: ShortText
    description: LongText | None = None
    badge: ShortText | None = None


class ListComponent(BaseComponent):
    type: Literal[ComponentType.LIST]
    title: ShortText | None = None
    items: list[ListItem] = Field(min_length=1, max_length=MAX_ITEMS)
    ordered: bool = False


class TimelineItem(StrictModel):
    title: ShortText
    description: LongText | None = None
    timestamp: ShortText | None = None
    status: TimelineStatus | None = None


class TimelineComponent(BaseComponent):
    type: Literal[ComponentType.TIMELINE]
    title: ShortText | None = None
    items: list[TimelineItem] = Field(min_length=1, max_length=MAX_ITEMS)


class ProgressComponent(BaseComponent):
    type: Literal[ComponentType.PROGRESS]
    label: ShortText
    value: float = Field(ge=0)
    max: float = Field(default=100, gt=0)
    tone: Tone = Tone.INFO


class DividerComponent(BaseComponent):
    type: Literal[ComponentType.DIVIDER]
    label: ShortText | None = None


FormField = Annotated[
    InputComponent | SelectComponent | CheckboxComponent, Field(discriminator="type")
]


class FormComponent(BaseComponent):
    type: Literal[ComponentType.FORM]
    title: ShortText | None = None
    fields: list[FormField] = Field(min_length=1, max_length=MAX_CHILDREN)
    submit_action: ActionSpec
    submit_label: ShortText = "Submit"


# --- Patterns ----------------------------------------------------------------
#
# A pattern is a designed composition (a hero, a pricing table, a kanban board)
# described by content, a variant and optional bindings. How it looks belongs to
# the frontend's pattern registry and the theme; the document only says what.


class ActionButton(StrictModel):
    label: ShortText
    action: ActionSpec
    variant: ButtonVariant = ButtonVariant.PRIMARY
    icon: IconName | None = None


class LabelValue(StrictModel):
    label: ShortText
    value: ShortText


class FieldDisplay(StrictModel):
    """One field of a record to show, with its label and format."""

    key: FieldKey
    label: ShortText
    format: ColumnFormat = ColumnFormat.TEXT


class HeroVariant(StrEnum):
    SPLIT = "split"
    CENTERED = "centered"
    IMMERSIVE = "immersive"
    EDITORIAL = "editorial"
    PRODUCT = "product"


class HeroComponent(BaseComponent):
    type: Literal[ComponentType.HERO]
    variant: HeroVariant = HeroVariant.SPLIT
    eyebrow: ShortText | None = None
    title: ShortText
    subtitle: MediumText | None = None
    actions: list[ActionButton] = Field(default_factory=list, max_length=3)
    image: AssetId | None = None
    stats: list[LabelValue] = Field(default_factory=list, max_length=4)
    badges: list[ShortText] = Field(default_factory=list, max_length=5)


class FeatureGridVariant(StrEnum):
    GRID = "grid"
    BENTO = "bento"
    LIST = "list"
    ALTERNATING = "alternating"


class FeatureItem(StrictModel):
    title: ShortText
    description: MediumText | None = None
    icon: IconName | None = None
    image: AssetId | None = None
    badge: ShortText | None = None
    span: int = Field(default=1, ge=1, le=2, description="Bento cell width in columns.")


class FeatureGridComponent(BaseComponent):
    type: Literal[ComponentType.FEATURE_GRID]
    variant: FeatureGridVariant = FeatureGridVariant.GRID
    eyebrow: ShortText | None = None
    title: ShortText | None = None
    subtitle: MediumText | None = None
    columns: int = Field(default=3, ge=2, le=4)
    items: list[FeatureItem] = Field(min_length=1, max_length=12)


class LogoCloudVariant(StrEnum):
    STATIC = "static"
    MARQUEE = "marquee"


class LogoCloudComponent(BaseComponent):
    """Names of customers or partners, set as wordmarks. No third-party logo files."""

    type: Literal[ComponentType.LOGO_CLOUD]
    variant: LogoCloudVariant = LogoCloudVariant.STATIC
    title: ShortText | None = None
    logos: list[ShortText] = Field(min_length=2, max_length=14)


class TestimonialsVariant(StrEnum):
    CARDS = "cards"
    SPOTLIGHT = "spotlight"
    MARQUEE = "marquee"


class Testimonial(StrictModel):
    quote: MediumText
    author: ShortText
    role: ShortText | None = None
    company: ShortText | None = None
    avatar: AssetId | None = None
    rating: int | None = Field(default=None, ge=1, le=5)


class TestimonialsComponent(BaseComponent):
    type: Literal[ComponentType.TESTIMONIALS]
    variant: TestimonialsVariant = TestimonialsVariant.CARDS
    eyebrow: ShortText | None = None
    title: ShortText | None = None
    items: list[Testimonial] = Field(min_length=1, max_length=9)


class PricingPlan(StrictModel):
    name: ShortText
    price: ShortText = Field(examples=["$29"])
    period: ShortText | None = Field(default=None, examples=["per seat / month"])
    description: ShortText | None = None
    features: list[ShortText] = Field(default_factory=list, max_length=12)
    action: ActionButton | None = None
    highlighted: bool = False
    badge: ShortText | None = None


class PricingComponent(BaseComponent):
    type: Literal[ComponentType.PRICING]
    eyebrow: ShortText | None = None
    title: ShortText | None = None
    subtitle: MediumText | None = None
    plans: list[PricingPlan] = Field(min_length=1, max_length=4)


class CtaVariant(StrEnum):
    BANNER = "banner"
    CENTERED = "centered"
    SPLIT = "split"


class CtaComponent(BaseComponent):
    type: Literal[ComponentType.CTA]
    variant: CtaVariant = CtaVariant.CENTERED
    eyebrow: ShortText | None = None
    title: ShortText
    subtitle: MediumText | None = None
    actions: list[ActionButton] = Field(min_length=1, max_length=2)
    image: AssetId | None = None


class StatsVariant(StrEnum):
    STRIP = "strip"
    CARDS = "cards"
    INLINE = "inline"


class StatItem(StrictModel):
    """One figure. Prefer ``data_source`` so the number comes from data."""

    label: ShortText
    value: str | int | float | None = None
    data_source: MetricBinding | None = None
    format: ColumnFormat = ColumnFormat.TEXT
    unit: ShortText | None = None
    trend: Trend | None = None
    icon: IconName | None = None
    description: ShortText | None = None


class StatsComponent(BaseComponent):
    type: Literal[ComponentType.STATS]
    variant: StatsVariant = StatsVariant.STRIP
    title: ShortText | None = None
    items: list[StatItem] = Field(min_length=1, max_length=8)


class GalleryVariant(StrEnum):
    GRID = "grid"
    MASONRY = "masonry"
    EDITORIAL = "editorial"
    CAROUSEL = "carousel"


class GalleryItem(StrictModel):
    title: ShortText
    subtitle: ShortText | None = None
    description: MediumText | None = None
    image: AssetId | None = None
    badge: ShortText | None = None
    meta: list[LabelValue] = Field(default_factory=list, max_length=4)
    action: ActionSpec | None = None


class GalleryComponent(BaseComponent):
    """Curated visual items: projects, destinations, case studies, products."""

    type: Literal[ComponentType.GALLERY]
    variant: GalleryVariant = GalleryVariant.GRID
    eyebrow: ShortText | None = None
    title: ShortText | None = None
    subtitle: MediumText | None = None
    columns: int = Field(default=3, ge=1, le=4)
    items: list[GalleryItem] = Field(min_length=1, max_length=24)


class CollectionVariant(StrEnum):
    CARDS = "cards"
    LIST = "list"
    COMPACT = "compact"
    MEDIA = "media"
    FEED = "feed"


class RecordCardFields(StrictModel):
    """Which fields of a record a card shows. Every value names a field."""

    title: FieldKey
    subtitle: FieldKey | None = None
    description: FieldKey | None = None
    image: FieldKey | None = Field(default=None, description="Field holding an asset id.")
    badge: FieldKey | None = None
    timestamp: FieldKey | None = None
    avatar: bool = Field(default=False, description="Show an initials avatar from the title.")
    meta: list[FieldDisplay] = Field(default_factory=list, max_length=5)


class CollectionComponent(BaseComponent):
    """Records of a dataset as cards, a list, media tiles or an activity feed."""

    type: Literal[ComponentType.COLLECTION]
    variant: CollectionVariant = CollectionVariant.CARDS
    title: ShortText | None = None
    subtitle: ShortText | None = None
    data_source: DataBinding
    fields: RecordCardFields
    columns: int = Field(default=3, ge=1, le=4)
    item_action: ActionSpec | None = None
    empty_text: ShortText | None = None


class KanbanColumn(StrictModel):
    value: ShortText = Field(description="Value of the grouping field for this column.")
    label: ShortText
    tone: Tone = Tone.NEUTRAL


class KanbanComponent(BaseComponent):
    """Records grouped into columns by one field (a pipeline, a task board)."""

    type: Literal[ComponentType.KANBAN]
    title: ShortText | None = None
    data_source: DataBinding
    group_by: FieldKey
    columns: list[KanbanColumn] = Field(min_length=2, max_length=8)
    fields: RecordCardFields
    item_action: ActionSpec | None = None
    move_action: ActionSpec | None = Field(
        default=None, description="A record_update run when a card is moved to another column."
    )


class DetailVariant(StrEnum):
    LIST = "list"
    GRID = "grid"


class DetailComponent(BaseComponent):
    """Labelled fields of one record (the first row the binding yields)."""

    type: Literal[ComponentType.DETAIL]
    variant: DetailVariant = DetailVariant.GRID
    title: ShortText | None = None
    data_source: DataBinding
    fields: list[FieldDisplay] = Field(min_length=1, max_length=24)
    columns: int = Field(default=2, ge=1, le=3)


class ProfileHeaderVariant(StrEnum):
    BANNER = "banner"
    COMPACT = "compact"


class ProfileHeaderComponent(BaseComponent):
    """Identity of one record: name, summary, status, key facts and actions."""

    type: Literal[ComponentType.PROFILE_HEADER]
    variant: ProfileHeaderVariant = ProfileHeaderVariant.BANNER
    data_source: DataBinding
    fields: RecordCardFields
    actions: list[ActionButton] = Field(default_factory=list, max_length=4)


class ImageFit(StrEnum):
    COVER = "cover"
    CONTAIN = "contain"


class ImageComponent(BaseComponent):
    type: Literal[ComponentType.IMAGE]
    image: AssetId
    caption: ShortText | None = None
    aspect: ImageAspect = ImageAspect.AUTO
    fit: ImageFit = ImageFit.COVER
    rounded: bool = True


class MediaVariant(StrEnum):
    IMAGE_LEFT = "image_left"
    IMAGE_RIGHT = "image_right"
    OVERLAY = "overlay"
    FRAMED = "framed"


class MediaComponent(BaseComponent):
    """An image with text beside or over it; ``framed`` presents it as a product preview."""

    type: Literal[ComponentType.MEDIA]
    variant: MediaVariant = MediaVariant.IMAGE_RIGHT
    eyebrow: ShortText | None = None
    title: ShortText
    body: LongText | None = None
    bullets: list[ShortText] = Field(default_factory=list, max_length=6)
    image: AssetId | None = None
    actions: list[ActionButton] = Field(default_factory=list, max_length=2)


class StepsVariant(StrEnum):
    NUMBERED = "numbered"
    CARDS = "cards"
    TIMELINE = "timeline"


class StepItem(StrictModel):
    title: ShortText
    description: MediumText | None = None
    icon: IconName | None = None


class StepsComponent(BaseComponent):
    type: Literal[ComponentType.STEPS]
    variant: StepsVariant = StepsVariant.NUMBERED
    eyebrow: ShortText | None = None
    title: ShortText | None = None
    items: list[StepItem] = Field(min_length=2, max_length=8)


class FaqItem(StrictModel):
    question: ShortText
    answer: LongText


class FaqComponent(BaseComponent):
    type: Literal[ComponentType.FAQ]
    title: ShortText | None = None
    items: list[FaqItem] = Field(min_length=1, max_length=12)


class FooterLink(StrictModel):
    label: ShortText
    action: ActionSpec | None = None


class FooterColumn(StrictModel):
    title: ShortText
    links: list[FooterLink] = Field(min_length=1, max_length=8)


class FooterComponent(BaseComponent):
    type: Literal[ComponentType.FOOTER]
    brand: ShortText | None = None
    tagline: ShortText | None = None
    columns: list[FooterColumn] = Field(default_factory=list, max_length=5)
    note: ShortText | None = None


class CalendarComponent(BaseComponent):
    """Dated records as an agenda grouped by day (interviews, bookings, events)."""

    type: Literal[ComponentType.CALENDAR]
    title: ShortText | None = None
    data_source: DataBinding
    date_field: FieldKey
    time_field: FieldKey | None = None
    title_field: FieldKey
    subtitle_field: FieldKey | None = None
    badge_field: FieldKey | None = None
    item_action: ActionSpec | None = None


class ComparisonRow(StrictModel):
    label: ShortText
    values: list[ShortText | bool] = Field(min_length=1, max_length=5)


class ComparisonComponent(BaseComponent):
    type: Literal[ComponentType.COMPARISON]
    title: ShortText | None = None
    columns: list[ShortText] = Field(min_length=2, max_length=5)
    rows: list[ComparisonRow] = Field(min_length=1, max_length=24)
    highlight_column: int | None = Field(default=None, ge=0, le=4)


class CommandItem(StrictModel):
    label: ShortText
    hint: ShortText | None = None
    icon: IconName | None = None
    action: ActionSpec


class CommandComponent(BaseComponent):
    """A command bar: type to filter a short list of actions, then run one."""

    type: Literal[ComponentType.COMMAND]
    placeholder: ShortText = "Search or jump to…"
    items: list[CommandItem] = Field(min_length=1, max_length=12)


# --- Containers --------------------------------------------------------------


class SectionComponent(BaseComponent):
    type: Literal[ComponentType.SECTION]
    variant: SectionVariant = SectionVariant.DEFAULT
    eyebrow: ShortText | None = None
    title: ShortText | None = None
    description: MediumText | None = None
    image: AssetId | None = Field(default=None, description="Backdrop for immersive sections.")
    children: list["Component"] = Field(min_length=1, max_length=MAX_CHILDREN)


class CardComponent(BaseComponent):
    type: Literal[ComponentType.CARD]
    title: ShortText | None = None
    subtitle: ShortText | None = None
    children: list["Component"] = Field(min_length=1, max_length=MAX_CHILDREN)


class ModalComponent(BaseComponent):
    """A button that opens a dialog containing ``children``."""

    type: Literal[ComponentType.MODAL]
    title: ShortText
    trigger_label: ShortText
    children: list["Component"] = Field(min_length=1, max_length=MAX_CHILDREN)


class Tab(StrictModel):
    id: ComponentId
    label: ShortText
    children: list["Component"] = Field(min_length=1, max_length=MAX_CHILDREN)


class TabsComponent(BaseComponent):
    type: Literal[ComponentType.TABS]
    tabs: list[Tab] = Field(min_length=1, max_length=10)
    default_tab: ComponentId | None = None


class ScreenComponent(BaseComponent):
    """One routed screen of an application. Only valid directly under the root page."""

    type: Literal[ComponentType.SCREEN]
    title: ShortText
    route: RoutePath
    screen_type: ScreenType = ScreenType.CUSTOM
    purpose: ShortText | None = None
    width: ScreenWidth = ScreenWidth.CONTAINED
    show_title: bool = Field(default=True, description="Render the title as a page heading.")
    children: list["Component"] = Field(min_length=1, max_length=MAX_CHILDREN)


Component = Annotated[
    ScreenComponent
    | HeroComponent
    | FeatureGridComponent
    | LogoCloudComponent
    | TestimonialsComponent
    | PricingComponent
    | CtaComponent
    | StatsComponent
    | GalleryComponent
    | CollectionComponent
    | KanbanComponent
    | DetailComponent
    | ProfileHeaderComponent
    | ImageComponent
    | MediaComponent
    | StepsComponent
    | FaqComponent
    | FooterComponent
    | CalendarComponent
    | ComparisonComponent
    | CommandComponent
    | SectionComponent
    | CardComponent
    | MetricComponent
    | TextComponent
    | TableComponent
    | ChartComponent
    | FormComponent
    | InputComponent
    | SelectComponent
    | CheckboxComponent
    | ButtonComponent
    | BadgeComponent
    | AlertComponent
    | ListComponent
    | TimelineComponent
    | ProgressComponent
    | TabsComponent
    | ModalComponent
    | DividerComponent,
    Field(discriminator="type"),
]


class PageComponent(StrictModel):
    """Root of every UI. A page cannot be nested inside another component."""

    type: Literal[ComponentType.PAGE]
    id: ComponentId = "page"
    title: ShortText
    description: ShortText | None = None
    components: list[Component] = Field(min_length=1, max_length=MAX_CHILDREN)
    metadata: dict[str, Scalar] | None = None


# Any node of the tree, root included.
AnyComponent = PageComponent | Component

for _container in (
    ScreenComponent,
    SectionComponent,
    CardComponent,
    ModalComponent,
    Tab,
    TabsComponent,
    PageComponent,
):
    _container.model_rebuild()
