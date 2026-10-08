"""The house design vocabulary: 500 UI patterns, 500 effects and a few recipes."""

import importlib
import pkgutil
from collections.abc import Iterator

from app.domains.references.schemas import (
    ImportedReference,
    ReferenceFile,
    ReferenceKind,
    ReferenceSource,
)
from app.domains.references.vocabulary.base import Section, scoped, slug, standalone_page

_KINDS = {
    "patterns": ReferenceKind.COMPONENT,
    "effects": ReferenceKind.EFFECT,
    "recipes": ReferenceKind.RECIPE,
}
AUTHOR = "Generative UI Platform"


def sections() -> list[Section]:
    """Every section, patterns first, each group in the order of its numbering."""
    found: list[Section] = []
    for module in pkgutil.iter_modules(__path__):
        if module.name in {"base"}:
            continue
        loaded = importlib.import_module(f"{__name__}.{module.name}")
        section = getattr(loaded, "SECTION", None)
        if isinstance(section, Section):
            found.append(section)
    order = {"patterns": 0, "effects": 1, "recipes": 2}
    return sorted(found, key=lambda section: (order[section.group], section.start))


def entries() -> Iterator[ImportedReference]:
    for section in sections():
        category = slug(section.title)[:64]
        for offset, item in enumerate(section.items):
            number = section.start + offset
            identifier = f"{section.group}/{number:03d}-{slug(item.name)}"
            files = [
                ReferenceFile(path="index.html", content=standalone_page(item.name, item)),
                ReferenceFile(path="markup.html", content=item.html.strip() + "\n"),
                ReferenceFile(path="styles.css", content=item.css.strip() + "\n"),
            ]
            if item.js.strip():
                files.append(ReferenceFile(path="script.js", content=scoped(item.js) + "\n"))
            yield ImportedReference(
                source=ReferenceSource.VOCABULARY,
                slug=identifier,
                name=item.name,
                kind=_KINDS[section.group],
                category=category,
                description=item.note or None,
                tags=[section.group, section.title, f"#{number}"],
                author=AUTHOR,
                license="Project",
                source_url=f"vocabulary://{identifier}",
                files=files,
            )
