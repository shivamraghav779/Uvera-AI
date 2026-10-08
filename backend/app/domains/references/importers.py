"""Where reference components come from.

Two kinds of source, both used the way their owners offer them:

* Open-source shadcn registries (UI Layouts, Magic UI; both MIT). The importer
  reads the registry published in the project's own repository, from a local
  checkout or from a GitHub archive of it, and records licence, author and a
  link to the exact file.
* 21st.dev, through its official API with the caller's API key. Its terms
  forbid crawling the site, so nothing here does: search returns metadata, and
  source code is fetched one component at a time, for as long as the key's
  plan allows.

Nothing imported is executed or rendered. See ``ReferenceComponent``.
"""

import io
import json
import re
import tarfile
import tempfile
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

import httpx

from app.core.exceptions import ReferenceImportException
from app.core.logging import get_logger
from app.domains.references.schemas import (
    ImportedReference,
    ReferenceFile,
    ReferenceKind,
    ReferenceSource,
)

logger = get_logger(__name__)

MAX_ARCHIVE_BYTES = 300 * 1024 * 1024
MAX_FILE_CHARS = 400_000
MAX_FILES_PER_COMPONENT = 40
_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    return _SLUG.sub("-", value.lower()).strip("-")


def _strings(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


class ReferenceImporter(ABC):
    """Yields components of one source. Network and parsing problems are
    ``ReferenceImportException``; a single unusable component is skipped."""

    source: ReferenceSource

    @abstractmethod
    def components(self) -> AsyncIterator[ImportedReference]: ...

    @property
    def note(self) -> str | None:
        """Something the person running the import should know (a quota was reached...)."""
        return None


# --- Open-source shadcn registries ---------------------------------------------------


@dataclass(frozen=True, slots=True)
class RegistrySource:
    source: ReferenceSource
    # GitHub "owner/name" and the branch whose archive is read.
    repository: str
    branch: str
    # Directory, inside the repository, holding registry.json and one JSON per item.
    registry_dir: str
    # Directory the item file paths are relative to.
    files_root: str
    license: str
    author: str
    kinds: Mapping[str, ReferenceKind]
    categorise: Callable[[str, str, str], str]
    preview: Callable[[str, ReferenceKind], str | None]


def _ui_layouts_category(name: str, registry_type: str, first_path: str) -> str:
    parts = PurePosixPath(first_path).parts
    if "blocks" in parts and "src" in parts:
        section = parts[parts.index("src") + 1] if len(parts) > parts.index("src") + 1 else name
        return slugify(section.removesuffix("-section")) or "block"
    if "registry" in parts and "components" in parts:
        after = parts[parts.index("components") + 1 :]
        return slugify(after[0]) if len(after) > 1 else slugify(name)
    return "primitive"


_MAGIC_UI_CATEGORIES: Sequence[tuple[str, re.Pattern[str]]] = (
    ("text-animation", re.compile(r"text|typing|word|letter|number-ticker|hyper|morphing")),
    ("button", re.compile(r"button")),
    ("mockup", re.compile(r"iphone|android|safari|terminal|browser|device")),
    ("background", re.compile(r"background|pattern|grid|particles|meteors|ripple|warp|retro|dot")),
    ("marquee", re.compile(r"marquee|ticker|scroll|velocity")),
    ("card", re.compile(r"card|bento|dock|list|avatar|file-tree|tweet|globe|orbit|icon-cloud")),
    ("effect", re.compile(r"beam|border|shine|blur|confetti|cursor|pointer|lens|light|spark")),
)


def _magic_ui_category(name: str, registry_type: str, first_path: str) -> str:
    for category, pattern in _MAGIC_UI_CATEGORIES:
        if pattern.search(name):
            return category
    return "component"


UI_LAYOUTS = RegistrySource(
    source=ReferenceSource.UI_LAYOUTS,
    repository="ui-layouts/uilayouts",
    branch="main",
    registry_dir="apps/ui-layout/public/r",
    files_root="apps/ui-layout",
    license="MIT",
    author="UI Layouts",
    kinds={"registry:component": ReferenceKind.COMPONENT, "registry:block": ReferenceKind.BLOCK},
    categorise=_ui_layouts_category,
    preview=lambda name, kind: None,
)
MAGIC_UI = RegistrySource(
    source=ReferenceSource.MAGIC_UI,
    repository="magicuidesign/magicui",
    branch="main",
    registry_dir="apps/www/public/r",
    files_root="apps/www",
    license="MIT",
    author="Magic UI",
    kinds={"registry:ui": ReferenceKind.COMPONENT, "registry:example": ReferenceKind.EXAMPLE},
    categorise=_magic_ui_category,
    preview=lambda name, kind: (
        f"https://magicui.design/docs/components/{name}"
        if kind is ReferenceKind.COMPONENT
        else None
    ),
)
REGISTRY_SOURCES: Mapping[ReferenceSource, RegistrySource] = {
    UI_LAYOUTS.source: UI_LAYOUTS,
    MAGIC_UI.source: MAGIC_UI,
}


def _title(name: str) -> str:
    return " ".join(word.capitalize() for word in re.split(r"[-_]+", name) if word)


class ShadcnRegistryImporter(ReferenceImporter):
    """Reads a shadcn registry from a checkout of the project that publishes it."""

    def __init__(self, config: RegistrySource, checkout: Path, revision: str | None = None) -> None:
        self.source = config.source
        self._config = config
        self._checkout = checkout
        self._revision = revision
        self._skipped: list[str] = []

    @property
    def skipped(self) -> Sequence[str]:
        return self._skipped

    def _read_json(self, path: Path) -> dict[str, Any]:
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReferenceImportException(
                f"'{path.name}' of the {self.source.value} registry could not be read."
            ) from exc
        if not isinstance(loaded, dict):
            raise ReferenceImportException(f"'{path.name}' is not a registry document.")
        return loaded

    def _source_url(self, first_path: str) -> str:
        """The file on GitHub, at the revision that was read when it is known."""
        config = self._config
        resolved = PurePosixPath(config.files_root)
        for part in PurePosixPath(first_path).parts:
            if part == "..":
                resolved = resolved.parent
            elif part != ".":
                resolved = resolved / part
        ref = self._revision or config.branch
        return f"https://github.com/{config.repository}/blob/{ref}/{quote(str(resolved))}"

    def _component(self, entry: Mapping[str, Any]) -> ImportedReference | None:
        config = self._config
        name, registry_type = entry.get("name"), entry.get("type")
        if not isinstance(name, str) or not isinstance(registry_type, str):
            return None
        kind = config.kinds.get(registry_type)
        if kind is None:
            return None  # styles, libs and the like are not components
        item_path = self._checkout / config.registry_dir / f"{name}.json"
        if not item_path.is_file():
            self._skipped.append(f"{name}: listed in the registry but has no item file")
            return None
        item = self._read_json(item_path)
        files = [
            ReferenceFile(path=file["path"], content=file["content"])
            for file in item.get("files", [])
            if isinstance(file, dict)
            and isinstance(file.get("path"), str)
            and isinstance(file.get("content"), str)
            and len(file["content"]) <= MAX_FILE_CHARS
        ][:MAX_FILES_PER_COMPONENT]
        if not files:
            self._skipped.append(f"{name}: no source files")
            return None
        description = item.get("description") or entry.get("description")
        title = item.get("title") or entry.get("title")
        return ImportedReference(
            source=config.source,
            slug=name,
            name=title if isinstance(title, str) and title else _title(name),
            kind=kind,
            category=config.categorise(name, registry_type, files[0].path)[:64] or "component",
            description=description if isinstance(description, str) else None,
            tags=[registry_type.removeprefix("registry:")],
            author=config.author,
            license=config.license,
            source_url=self._source_url(files[0].path),
            preview_url=config.preview(name, kind),
            dependencies=_strings(item.get("dependencies")),
            registry_dependencies=_strings(item.get("registryDependencies")),
            files=files,
            source_revision=self._revision,
        )

    def _entries(self) -> Iterator[Mapping[str, Any]]:
        index_path = self._checkout / self._config.registry_dir / "registry.json"
        if not index_path.is_file():
            raise ReferenceImportException(
                f"No registry was found at '{self._config.registry_dir}' in the "
                f"{self._config.repository} checkout."
            )
        items = self._read_json(index_path).get("items")
        if not isinstance(items, list):
            raise ReferenceImportException("The registry index lists no items.")
        yield from (item for item in items if isinstance(item, dict))

    async def components(self) -> AsyncIterator[ImportedReference]:
        for entry in self._entries():
            component = self._component(entry)
            if component is not None:
                yield component


def _safe_members(
    archive: tarfile.TarFile, wanted_dirs: Sequence[str]
) -> Iterator[tarfile.TarInfo]:
    """Regular files under the wanted directories of a GitHub archive, top folder removed."""
    prefixes = tuple(f"{directory.strip('/')}/" for directory in wanted_dirs)
    for member in archive:
        parts = PurePosixPath(member.name).parts[1:]
        if not member.isfile() or not parts or ".." in parts:
            continue
        relative = "/".join(parts)
        if relative.startswith(prefixes):
            member.name = relative
            yield member


async def download_directories(
    client: httpx.AsyncClient,
    repository: str,
    branch: str,
    directories: Sequence[str],
    destination: Path,
    *,
    timeout_seconds: float,
) -> str | None:
    """Fetch a GitHub repository's archive and unpack only the named directories.

    Returns the commit the archive was made from, when GitHub reports it.
    """
    url = f"https://codeload.github.com/{repository}/tar.gz/refs/heads/{branch}"
    try:
        async with client.stream(
            "GET", url, timeout=timeout_seconds, follow_redirects=True
        ) as response:
            if response.is_error:
                raise ReferenceImportException(
                    f"GitHub answered {response.status_code} for the {repository} archive."
                )
            buffer = io.BytesIO()
            async for chunk in response.aiter_bytes():
                buffer.write(chunk)
                if buffer.tell() > MAX_ARCHIVE_BYTES:
                    raise ReferenceImportException(
                        f"The {repository} archive is larger than expected."
                    )
    except httpx.HTTPError as exc:
        raise ReferenceImportException(
            f"The {repository} archive could not be downloaded ({type(exc).__name__})."
        ) from exc
    buffer.seek(0)
    try:
        with tarfile.open(fileobj=buffer, mode="r:gz") as archive:
            # The archive's comment is the commit id.
            revision = archive.pax_headers.get("comment")
            for member in _safe_members(archive, directories):
                archive.extract(member, destination, filter="data")
    except (tarfile.TarError, OSError) as exc:
        raise ReferenceImportException(f"The {repository} archive could not be unpacked.") from exc
    return revision[:40] if isinstance(revision, str) and revision else None


async def download_registry(
    client: httpx.AsyncClient, config: RegistrySource, destination: Path, *, timeout_seconds: float
) -> str | None:
    """The registry directory of an open-source shadcn registry."""
    return await download_directories(
        client,
        config.repository,
        config.branch,
        [config.registry_dir],
        destination,
        timeout_seconds=timeout_seconds,
    )


# --- Bootstrap ---------------------------------------------------------------------------

BOOTSTRAP_REPOSITORY = "twbs/bootstrap"
BOOTSTRAP_BRANCH = "main"
BOOTSTRAP_EXAMPLES = "site/src/assets/examples"
BOOTSTRAP_DOCS = "site/src/content/docs"
BOOTSTRAP_SCSS = "scss"
BOOTSTRAP_DIRECTORIES: Sequence[str] = (BOOTSTRAP_EXAMPLES, BOOTSTRAP_DOCS, BOOTSTRAP_SCSS)
# Documentation sections that describe things one builds with.
BOOTSTRAP_DOC_SECTIONS: Sequence[str] = (
    "components",
    "forms",
    "content",
    "layout",
    "helpers",
    "utilities",
    "customize",
)
# The stylesheet partial behind a documentation page, where the names differ.
_BOOTSTRAP_PARTIALS: Mapping[str, str] = {
    "alerts": "alert",
    "close-button": "close",
    "dropdowns": "dropdown",
    "navs-tabs": "nav",
    "popovers": "popover",
    "tooltips": "tooltip",
    "tables": "tables",
    "typography": "type",
    "reboot": "reboot",
    "images": "images",
    "containers": "containers",
    "grid": "grid",
    "css-variables": "root",
    "color-modes": "variables-dark",
    "sass": "variables",
}
_BOOTSTRAP_EXAMPLE_CATEGORIES: Mapping[str, str] = {
    "heroes": "hero",
    "jumbotron": "hero",
    "jumbotrons": "hero",
    "cover": "hero",
    "features": "feature",
    "footers": "footer",
    "sticky-footer": "footer",
    "sticky-footer-navbar": "footer",
    "headers": "navigation",
    "sidebars": "sidebar",
    "sign-in": "form",
    "checkout": "form",
    "list-groups": "list",
    "album": "gallery",
    "masonry": "gallery",
    "blog": "content",
    "product": "landing",
}
_TEXT_SUFFIXES = frozenset({".astro", ".html", ".css", ".scss", ".js", ".mdx", ".md"})
_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---", re.DOTALL)
_ASTRO_TITLE = re.compile(r"export const title = ['\"](.+?)['\"]")


def _frontmatter(text: str, key: str) -> str | None:
    block = _FRONTMATTER.match(text)
    if block is None:
        return None
    found = re.search(rf"^{key}:\s*(.+)$", block.group(1), re.MULTILINE)
    return found.group(1).strip().strip("'\"") if found else None


class BootstrapImporter(ReferenceImporter):
    """Bootstrap from a checkout of its repository (code MIT, documentation CC BY 3.0).

    Three kinds of entry: every example page (heroes, pricing, dashboard...)
    with its markup and styles; every documentation page of a component, form
    control, helper or utility together with the stylesheet partial that
    implements it; and the stylesheet foundation (variables, mixins, root
    custom properties), which is where the look is defined.
    """

    source = ReferenceSource.BOOTSTRAP
    AUTHOR = "The Bootstrap Authors"

    def __init__(self, checkout: Path, revision: str | None = None) -> None:
        self._checkout = checkout
        self._revision = revision
        self._skipped: list[str] = []
        self._attached_partials: set[str] = set()

    @property
    def skipped(self) -> Sequence[str]:
        return self._skipped

    def _url(self, relative: str) -> str:
        ref = self._revision or BOOTSTRAP_BRANCH
        return f"https://github.com/{BOOTSTRAP_REPOSITORY}/blob/{ref}/{quote(relative)}"

    def _file(self, path: Path) -> ReferenceFile | None:
        if path.suffix not in _TEXT_SUFFIXES or not path.is_file():
            return None
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            self._skipped.append(f"{path.name}: not readable as text")
            return None
        if len(content) > MAX_FILE_CHARS:
            self._skipped.append(f"{path.name}: too large")
            return None
        return ReferenceFile(path=str(path.relative_to(self._checkout)), content=content)

    def _reference(
        self,
        *,
        slug: str,
        name: str,
        kind: ReferenceKind,
        category: str,
        description: str | None,
        tags: list[str],
        license: str,
        files: list[ReferenceFile],
        preview_url: str | None = None,
    ) -> ImportedReference:
        return ImportedReference(
            source=self.source,
            slug=slug,
            name=name[:200],
            kind=kind,
            category=category[:64],
            description=description,
            tags=tags,
            author=self.AUTHOR,
            license=license,
            source_url=self._url(files[0].path),
            preview_url=preview_url,
            files=files[:MAX_FILES_PER_COMPONENT],
            source_revision=self._revision,
        )

    def _examples(self) -> Iterator[ImportedReference]:
        root = self._checkout / BOOTSTRAP_EXAMPLES
        if not root.is_dir():
            raise ReferenceImportException(
                f"No Bootstrap examples were found at '{BOOTSTRAP_EXAMPLES}' in the checkout."
            )
        for directory in sorted(path for path in root.iterdir() if path.is_dir()):
            name = directory.name
            if name.endswith("-rtl"):
                continue  # the same page mirrored
            page = next(
                (p for p in (directory / "index.astro", directory / "index.html") if p.is_file()),
                None,
            )
            files = [f for f in map(self._file, [page] if page else []) if f is not None]
            files += [
                f
                for f in map(self._file, sorted(directory.iterdir()))
                if f is not None
                and f.path != (files[0].path if files else None)
                and ".rtl." not in f.path
            ]
            if not page or not files:
                self._skipped.append(f"examples/{name}: no page")
                continue
            title = _ASTRO_TITLE.search(files[0].content)
            yield self._reference(
                slug=f"examples/{name}",
                name=title.group(1) if title else _title(name),
                kind=ReferenceKind.BLOCK,
                category=_BOOTSTRAP_EXAMPLE_CATEGORIES.get(name, slugify(name)),
                description=f"Bootstrap example page: {_title(name)}.",
                tags=["example"],
                license="MIT",
                files=files,
                preview_url=f"https://getbootstrap.com/docs/5.3/examples/{name}/",
            )

    def _partial(self, page: str) -> ReferenceFile | None:
        stem = _BOOTSTRAP_PARTIALS.get(page, page)
        for candidate in (stem, stem.removesuffix("s")):
            path = self._checkout / BOOTSTRAP_SCSS / f"_{candidate}.scss"
            if path.is_file():
                self._attached_partials.add(path.name)
                return self._file(path)
        return None

    def _documentation(self) -> Iterator[ImportedReference]:
        for section in BOOTSTRAP_DOC_SECTIONS:
            directory = self._checkout / BOOTSTRAP_DOCS / section
            if not directory.is_dir():
                self._skipped.append(f"docs/{section}: missing")
                continue
            for path in sorted(directory.glob("*.mdx")):
                page = self._file(path)
                if page is None:
                    continue
                partial = self._partial(path.stem)
                yield self._reference(
                    slug=f"docs/{section}/{path.stem}",
                    name=_frontmatter(page.content, "title") or _title(path.stem),
                    kind=ReferenceKind.COMPONENT,
                    category=slugify(path.stem) if section == "components" else section,
                    description=_frontmatter(page.content, "description"),
                    tags=["documentation", section],
                    # The prose is CC BY 3.0, the code in it and the stylesheet MIT.
                    license="MIT AND CC-BY-3.0",
                    files=[page, *([partial] if partial else [])],
                    preview_url=f"https://getbootstrap.com/docs/5.3/{section}/{path.stem}/",
                )

    def _foundation(self) -> Iterator[ImportedReference]:
        root = self._checkout / BOOTSTRAP_SCSS
        if not root.is_dir():
            self._skipped.append("scss: missing")
            return
        for path in sorted(root.glob("*.scss")):
            file = self._file(path)
            if file is None or path.name in self._attached_partials:
                continue
            stem = path.stem.removeprefix("_")
            yield self._reference(
                slug=f"scss/{stem}",
                name=f"Stylesheet: {_title(stem)}",
                kind=ReferenceKind.COMPONENT,
                category="foundation",
                description="Part of Bootstrap's stylesheet source.",
                tags=["scss"],
                license="MIT",
                files=[file],
            )
        for directory in sorted(path for path in root.iterdir() if path.is_dir()):
            if directory.name in {"tests", "vendor"}:
                continue
            files = [f for f in map(self._file, sorted(directory.glob("*.scss"))) if f is not None]
            if files:
                yield self._reference(
                    slug=f"scss/{directory.name}-partials",
                    name=f"Stylesheet: {_title(directory.name)} partials",
                    kind=ReferenceKind.COMPONENT,
                    category="foundation",
                    description=f"Bootstrap's {directory.name} stylesheet partials.",
                    tags=["scss"],
                    license="MIT",
                    files=files,
                )

    async def components(self) -> AsyncIterator[ImportedReference]:
        for reference in self._examples():
            yield reference
        for reference in self._documentation():
            yield reference
        for reference in self._foundation():  # after the docs: they claim their partials
            yield reference


def temporary_checkout() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="reference-registry-")


# --- 21st.dev (official API) -------------------------------------------------------------

# What the platform's own patterns cover; searched one by one.
TWENTY_FIRST_QUERIES: Sequence[tuple[str, str]] = (
    ("hero", "hero section"),
    ("feature", "features section"),
    ("pricing", "pricing section"),
    ("testimonial", "testimonials"),
    ("cta", "call to action"),
    ("footer", "footer"),
    ("navigation", "navbar"),
    ("sidebar", "sidebar"),
    ("dashboard", "dashboard"),
    ("stats", "stats"),
    ("card", "card"),
    ("table", "data table"),
    ("form", "form"),
    ("gallery", "gallery"),
    ("faq", "faq accordion"),
    ("kanban", "kanban board"),
    ("calendar", "calendar"),
    ("background", "background"),
    ("button", "button"),
    ("text-animation", "text animation"),
)


class TwentyFirstImporter(ReferenceImporter):
    """Curated search of 21st.dev through its API.

    ``code_budget`` is how many components to fetch source code for; the rest
    are stored as metadata with a link. Fetching stops for good the first time
    the API refuses for a reason retrying will not fix (the plan's allowance
    is used up, the key is not allowed to install), and what was collected up
    to then is kept.
    """

    BASE_URL = "https://21st.dev/api/v1"
    source = ReferenceSource.TWENTY_FIRST

    def __init__(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        *,
        queries: Sequence[tuple[str, str]] = TWENTY_FIRST_QUERIES,
        per_query: int = 12,
        code_budget: int = 0,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._client = client
        self._headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        self._queries = queries
        self._per_query = max(1, min(per_query, 50))
        self._code_budget = max(0, code_budget)
        self._timeout = timeout_seconds
        self._code_stopped: str | None = None
        self.code_fetched = 0

    @property
    def note(self) -> str | None:
        if self._code_stopped:
            return (
                f"Source code was fetched for {self.code_fetched} components, then 21st.dev "
                f"declined further requests ({self._code_stopped}). The rest are metadata only."
            )
        return None

    async def _get(
        self, path: str, params: Mapping[str, str | int] | None = None
    ) -> httpx.Response:
        try:
            return await self._client.get(
                f"{self.BASE_URL}{path}",
                params=params,
                headers=self._headers,
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise ReferenceImportException(
                f"21st.dev could not be reached ({type(exc).__name__})."
            ) from exc

    @staticmethod
    def _error(response: httpx.Response) -> str:
        try:
            body = response.json()
        except ValueError:
            body = None
        code = body.get("error") if isinstance(body, dict) else None
        return f"HTTP {response.status_code}" + (f" {code}" if isinstance(code, str) else "")

    async def _search(self, query: str) -> list[dict[str, Any]]:
        response = await self._get(
            "/components/search", {"q": query, "scope": "public", "limit": self._per_query}
        )
        if response.status_code == httpx.codes.UNAUTHORIZED:
            raise ReferenceImportException(
                "21st.dev rejected the API key. Create one at https://21st.dev/mcp and set "
                "TWENTYFIRST_API_KEY."
            )
        if response.is_error:
            raise ReferenceImportException(f"21st.dev search failed ({self._error(response)}).")
        try:
            results = response.json().get("results")
        except (ValueError, AttributeError) as exc:
            raise ReferenceImportException("21st.dev sent an unreadable search result.") from exc
        return [r for r in results if isinstance(r, dict)] if isinstance(results, list) else []

    async def _files(self, install_ref: str) -> tuple[list[ReferenceFile], dict[str, Any]]:
        """Source of one component, or nothing once the API has said no."""
        if self._code_stopped or self.code_fetched >= self._code_budget:
            return [], {}
        username, _, slug = install_ref.partition("/")
        if not username or not slug:
            return [], {}
        response = await self._get(
            f"/components/install/{quote(username, safe='')}/{quote(slug, safe='')}"
        )
        if response.status_code == httpx.codes.NOT_FOUND:
            return [], {}
        if response.is_error:
            # Out of allowance, not permitted, rate limited: asking again would only repeat it.
            self._code_stopped = self._error(response)
            logger.warning("reference_code_fetch_stopped", extra={"reason": self._code_stopped})
            return [], {}
        try:
            body = response.json()
        except ValueError:
            return [], {}
        if not isinstance(body, dict):
            return [], {}
        files = [
            ReferenceFile(path=file["path"], content=file["content"])
            for file in body.get("files") or []
            if isinstance(file, dict)
            and isinstance(file.get("path"), str)
            and isinstance(file.get("content"), str)
            and len(file["content"]) <= MAX_FILE_CHARS
        ][:MAX_FILES_PER_COMPONENT]
        if files:
            self.code_fetched += 1
        return files, body

    async def components(self) -> AsyncIterator[ImportedReference]:
        seen: set[str] = set()
        for category, query in self._queries:
            for result in await self._search(query):
                reference = result.get("install_ref") or result.get("slug")
                name, url = result.get("name"), result.get("url")
                if (
                    not isinstance(reference, str)
                    or not isinstance(name, str)
                    or not isinstance(url, str)
                    or not url.startswith("https://")
                    or reference in seen
                ):
                    continue
                seen.add(reference)
                files, detail = await self._files(reference)
                author = result.get("author")
                if isinstance(author, dict):
                    author = author.get("username") or author.get("name")
                preview = result.get("preview_url")
                description = result.get("description")
                yield ImportedReference(
                    source=self.source,
                    slug=reference[:200],
                    name=name[:200],
                    kind=ReferenceKind.COMPONENT,
                    category=category,
                    description=description if isinstance(description, str) else None,
                    tags=_strings(result.get("tags"))[:20],
                    author=author[:200] if isinstance(author, str) else None,
                    # 21st.dev states no licence per component: the author keeps their rights.
                    license=None,
                    source_url=url[:500],
                    preview_url=preview[:500] if isinstance(preview, str) else None,
                    dependencies=_strings(detail.get("dependencies")),
                    registry_dependencies=_strings(detail.get("registry_dependencies")),
                    files=files,
                )


# --- The house vocabulary ----------------------------------------------------------------


class VocabularyImporter(ReferenceImporter):
    """The platform's own design vocabulary, written in this repository
    (``app/domains/references/vocabulary``): one runnable snippet per named
    pattern or effect."""

    source = ReferenceSource.VOCABULARY

    async def components(self) -> AsyncIterator[ImportedReference]:
        # Imported here: the vocabulary is large and only an import needs it.
        from app.domains.references import vocabulary

        for reference in vocabulary.entries():
            yield reference
