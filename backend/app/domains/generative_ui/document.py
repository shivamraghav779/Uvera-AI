"""The UI document: everything one version of a workspace consists of.

    page         what the interface contains (framework-agnostic component tree).
                 In an application the page's children are its ``screen``s.
    theme        design tokens (colours, type, shape, surfaces, motion, ...)
    design       which framework adapter and visual style render it
    application  the product around the screens: who it is for, navigation,
                 data entities with sample records, assets, interactions and the
                 design direction. Absent for a single stand-alone view.

Changing ``theme`` or ``design`` never touches ``page``; that is what lets a
workspace switch look or framework without regenerating its UI.
"""

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import Field

from app.domains.actions.schemas import ActionType
from app.domains.common import DataRow, StrictModel
from app.domains.generative_ui.schemas import (
    AssetId,
    ComponentId,
    Effect,
    FieldKey,
    IconName,
    LongText,
    MediumText,
    PageComponent,
    ShortText,
)

# Colours are 6-digit hex only: a token can never smuggle in CSS.
HexColor = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")]


class ThemeMode(StrEnum):
    LIGHT = "light"
    DARK = "dark"


class Radius(StrEnum):
    NONE = "none"
    SM = "sm"
    MD = "md"
    LG = "lg"
    FULL = "full"


class Density(StrEnum):
    COMPACT = "compact"
    COMFORTABLE = "comfortable"
    SPACIOUS = "spacious"


class Spacing(StrEnum):
    TIGHT = "tight"
    NORMAL = "normal"
    RELAXED = "relaxed"


class Shadows(StrEnum):
    NONE = "none"
    SUBTLE = "subtle"
    MEDIUM = "medium"


class FontFamily(StrEnum):
    """Type families the frontend bundles. A name, never a font file or URL."""

    SANS = "sans"
    SERIF = "serif"
    MONO = "mono"
    ROUNDED = "rounded"
    GROTESK = "grotesk"
    GEOMETRIC = "geometric"


class HeadingScale(StrEnum):
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"


class HeadingWeight(StrEnum):
    REGULAR = "regular"
    MEDIUM = "medium"
    SEMIBOLD = "semibold"
    BOLD = "bold"
    BLACK = "black"


class SurfaceStyle(StrEnum):
    """How cards and panels are drawn across the whole UI."""

    FLAT = "flat"
    BORDERED = "bordered"
    ELEVATED = "elevated"
    GLASS = "glass"
    BRUTAL = "brutal"


class MotionLevel(StrEnum):
    NONE = "none"
    SUBTLE = "subtle"
    EXPRESSIVE = "expressive"


class GradientLevel(StrEnum):
    NONE = "none"
    SUBTLE = "subtle"
    VIVID = "vivid"


class TypeScale(StrEnum):
    SM = "sm"
    MD = "md"
    LG = "lg"


class ThemeColors(StrictModel):
    primary: HexColor
    secondary: HexColor
    background: HexColor
    surface: HexColor
    foreground: HexColor
    muted: HexColor
    border: HexColor
    destructive: HexColor
    success: HexColor
    warning: HexColor
    accent: HexColor | None = Field(
        default=None, description="Second accent for gradients and highlights."
    )


class Typography(StrictModel):
    font: FontFamily = FontFamily.SANS
    scale: TypeScale = TypeScale.MD
    heading_font: FontFamily | None = Field(default=None, description="Defaults to `font`.")
    heading_scale: HeadingScale = HeadingScale.MD
    heading_weight: HeadingWeight = HeadingWeight.SEMIBOLD


class Theme(StrictModel):
    preset: FieldKey | None = Field(
        default=None, description="Name of the preset the colours came from, if unmodified."
    )
    mode: ThemeMode
    colors: ThemeColors
    radius: Radius = Radius.MD
    density: Density = Density.COMFORTABLE
    spacing: Spacing = Spacing.NORMAL
    shadows: Shadows = Shadows.SUBTLE
    typography: Typography = Field(default_factory=Typography)
    surface: SurfaceStyle = SurfaceStyle.BORDERED
    motion: MotionLevel = MotionLevel.SUBTLE
    gradient: GradientLevel = GradientLevel.NONE


class ThemeColorsPatch(StrictModel):
    primary: HexColor | None = None
    secondary: HexColor | None = None
    background: HexColor | None = None
    surface: HexColor | None = None
    foreground: HexColor | None = None
    muted: HexColor | None = None
    border: HexColor | None = None
    destructive: HexColor | None = None
    success: HexColor | None = None
    warning: HexColor | None = None
    accent: HexColor | None = None


class TypographyPatch(StrictModel):
    font: FontFamily | None = None
    scale: TypeScale | None = None
    heading_font: FontFamily | None = None
    heading_scale: HeadingScale | None = None
    heading_weight: HeadingWeight | None = None


class ThemePatch(StrictModel):
    """A partial theme: only the tokens to change."""

    mode: ThemeMode | None = None
    colors: ThemeColorsPatch | None = None
    radius: Radius | None = None
    density: Density | None = None
    spacing: Spacing | None = None
    shadows: Shadows | None = None
    typography: TypographyPatch | None = None
    surface: SurfaceStyle | None = None
    motion: MotionLevel | None = None
    gradient: GradientLevel | None = None


class DesignConfig(StrictModel):
    framework: FieldKey = Field(description="Id of the frontend adapter that renders the UI.")
    design_system: FieldKey = Field(description="Id of the visual style in use.")


# --- Application ----------------------------------------------------------------

MAX_SCREENS = 20
MAX_ENTITIES = 20
MAX_RECORDS_PER_ENTITY = 60
MAX_ASSETS = 60
MAX_INTERACTIONS = 60
PRIMARY_KEY = "id"

EntityName = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")]
# Assets are served by this application only; a document can never point elsewhere.
AssetUrl = Annotated[str, Field(pattern=r"^/api/v1/assets/[0-9a-f-]{36}/content$")]


class NavigationStyle(StrEnum):
    SIDEBAR = "sidebar"
    TOPBAR = "topbar"
    BOTTOM = "bottom"
    MINIMAL = "minimal"
    NONE = "none"


class NavigationItem(StrictModel):
    screen_id: ComponentId
    label: ShortText
    icon: IconName | None = None
    group: ShortText | None = None


class Navigation(StrictModel):
    """The application shell: how people move between screens."""

    style: NavigationStyle = NavigationStyle.SIDEBAR
    brand: ShortText | None = None
    tagline: ShortText | None = None
    home: ComponentId = Field(description="Id of the screen shown first.")
    items: list[NavigationItem] = Field(default_factory=list, max_length=MAX_SCREENS)
    action: NavigationItem | None = Field(
        default=None, description="A highlighted call to action in the shell."
    )


class EntityFieldType(StrEnum):
    TEXT = "text"
    LONG_TEXT = "long_text"
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENT = "percent"
    DATE = "date"
    TIME = "time"
    BOOLEAN = "boolean"
    STATUS = "status"
    EMAIL = "email"
    IMAGE = "image"
    REFERENCE = "reference"


class EntityField(StrictModel):
    key: FieldKey
    label: ShortText
    type: EntityFieldType = EntityFieldType.TEXT
    options: list[ShortText] = Field(
        default_factory=list, max_length=12, description="Allowed values of a status field."
    )
    references: EntityName | None = Field(
        default=None, description="Entity whose id a reference field holds."
    )


class Entity(StrictModel):
    """A kind of record the application works with, plus sample records.

    Every screen that shows this entity binds to the same records by ``name``,
    so a candidate is the same candidate in the list, the board and the detail.
    """

    name: EntityName
    label: ShortText
    description: ShortText | None = None
    title_field: FieldKey = Field(description="Field that names a record to a person.")
    fields: list[EntityField] = Field(min_length=1, max_length=24)
    records: list[DataRow] = Field(default_factory=list, max_length=MAX_RECORDS_PER_ENTITY)


class Interaction(StrictModel):
    """Something a user can do, as planned for the product. Descriptive: the
    executable form is the action declared on the component that triggers it."""

    id: ComponentId
    label: ShortText
    type: ActionType
    description: ShortText | None = None
    screen_id: ComponentId | None = None
    entity: EntityName | None = None
    result: ShortText | None = None


class AssetKind(StrEnum):
    PHOTO = "photo"
    ILLUSTRATION = "illustration"
    ABSTRACT = "abstract"
    PRODUCT = "product"
    AVATAR = "avatar"


class AssetSource(StrEnum):
    GENERATED = "generated"
    SEARCH = "search"
    INTERNAL = "internal"


class Asset(StrictModel):
    """Reference to a stored image. The bytes live in the asset store, not here."""

    id: AssetId
    kind: AssetKind = AssetKind.PHOTO
    source: AssetSource
    provider: FieldKey
    url: AssetUrl
    alt: ShortText
    prompt: LongText | None = Field(default=None, description="Prompt or search query used.")
    width: int = Field(ge=16, le=4096)
    height: int = Field(ge=16, le=4096)
    usage: ShortText | None = None
    screen_id: ComponentId | None = None
    attribution: ShortText | None = None
    created_at: str | None = Field(default=None, max_length=40)


class ImageryKind(StrEnum):
    PHOTOGRAPHY = "photography"
    ILLUSTRATION = "illustration"
    ABSTRACT = "abstract"
    PRODUCT = "product"
    NONE = "none"


class DesignDirection(StrictModel):
    """The visual language chosen for the product before any screen was designed."""

    style: FieldKey = Field(description="Id of the visual style the direction builds on.")
    summary: ShortText
    mood: list[ShortText] = Field(default_factory=list, max_length=6)
    rationale: MediumText | None = None
    imagery: ImageryKind = ImageryKind.NONE
    visual_language: MediumText | None = Field(
        default=None, description="What every image of this product has in common."
    )
    layout: ShortText | None = Field(default=None, description="Layout philosophy.")
    effects: list[Effect] = Field(default_factory=list, max_length=6)


class ApplicationSpec(StrictModel):
    name: ShortText
    category: ShortText = Field(examples=["Recruitment SaaS"])
    description: MediumText
    target_users: list[ShortText] = Field(default_factory=list, max_length=8)
    goals: list[ShortText] = Field(default_factory=list, max_length=8)
    features: list[ShortText] = Field(default_factory=list, max_length=16)
    navigation: Navigation
    entities: list[Entity] = Field(default_factory=list, max_length=MAX_ENTITIES)
    interactions: list[Interaction] = Field(default_factory=list, max_length=MAX_INTERACTIONS)
    assets: list[Asset] = Field(default_factory=list, max_length=MAX_ASSETS)
    design_direction: DesignDirection | None = None


class UIDocument(StrictModel):
    schema_version: Literal["3.0"] = "3.0"
    page: PageComponent
    theme: Theme
    design: DesignConfig
    application: ApplicationSpec | None = None


def dump_document(document: UIDocument) -> dict[str, Any]:
    """Canonical JSON form: defaults filled in, unset optional fields omitted."""
    return document.model_dump(mode="json", exclude_none=True)
