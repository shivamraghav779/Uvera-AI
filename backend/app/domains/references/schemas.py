"""Contracts of the reference component library."""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ReferenceSource(StrEnum):
    UI_LAYOUTS = "ui_layouts"
    MAGIC_UI = "magic_ui"
    BOOTSTRAP = "bootstrap"
    # The platform's own design vocabulary: one runnable snippet per named pattern or effect.
    VOCABULARY = "vocabulary"
    TWENTY_FIRST = "twenty_first"


class ReferenceKind(StrEnum):
    COMPONENT = "component"
    # A whole page section (hero, pricing, footer...).
    BLOCK = "block"
    # A usage demo of a component.
    EXAMPLE = "example"
    # A visual or motion effect (hover, scroll, loading...).
    EFFECT = "effect"
    # Several effects combined on one element.
    RECIPE = "recipe"


class ReferenceFile(BaseModel):
    path: str
    content: str


class ImportedReference(BaseModel):
    """One component as an importer hands it over, before it is stored."""

    source: ReferenceSource
    slug: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=200)
    kind: ReferenceKind
    category: str = Field(min_length=1, max_length=64)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    author: str | None = Field(default=None, max_length=200)
    license: str | None = Field(default=None, max_length=64)
    source_url: str = Field(max_length=500)
    preview_url: str | None = Field(default=None, max_length=500)
    dependencies: list[str] = Field(default_factory=list)
    registry_dependencies: list[str] = Field(default_factory=list)
    files: list[ReferenceFile] = Field(default_factory=list)
    source_revision: str | None = Field(default=None, max_length=64)


class ReferenceSummary(BaseModel):
    """A component without its code."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: ReferenceSource
    slug: str
    name: str
    kind: ReferenceKind
    category: str
    description: str | None
    tags: list[str]
    author: str | None
    license: str | None = Field(description="SPDX id when known; null means 'see the source'.")
    source_url: str = Field(description="Where it was published. Credit the author when reusing.")
    preview_url: str | None
    dependencies: list[str]
    registry_dependencies: list[str]
    file_count: int
    code_size: int = Field(description="Characters of source code stored; 0 means metadata only.")
    fetched_at: datetime


class ReferenceDetail(ReferenceSummary):
    files: list[ReferenceFile]


class ReferenceFacet(BaseModel):
    source: ReferenceSource
    category: str
    count: int
    with_code: int


class ReferenceCatalog(BaseModel):
    total: int
    items: list[ReferenceSummary]


class ImportReport(BaseModel):
    source: ReferenceSource
    seen: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    with_code: int = 0
    skipped: list[str] = Field(default_factory=list)
    note: str | None = None
