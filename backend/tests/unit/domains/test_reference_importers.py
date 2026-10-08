"""Reference components are read from sources the way their owners offer them."""

import io
import json
import tarfile
from pathlib import Path
from typing import Any

import httpx
import pytest

from app.core.exceptions import ReferenceImportException
from app.domains.references.importers import (
    MAGIC_UI,
    UI_LAYOUTS,
    BootstrapImporter,
    ShadcnRegistryImporter,
    TwentyFirstImporter,
    download_registry,
)
from app.domains.references.schemas import ImportedReference, ReferenceKind, ReferenceSource
from app.domains.references.service import content_hash


def _write(root: Path, relative: str, value: Any) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _ui_layouts_checkout(root: Path) -> Path:
    registry = UI_LAYOUTS.registry_dir
    index = [
        {"name": "hero-agency", "type": "registry:block"},
        {"name": "btn-shine", "type": "registry:component"},
        {"name": "ghost", "type": "registry:component"},
        {"name": "theme", "type": "registry:style"},
        {"name": "empty", "type": "registry:component"},
    ]
    _write(root, f"{registry}/registry.json", {"name": "ui-layouts", "items": index})
    _write(
        root,
        f"{registry}/hero-agency.json",
        {
            "name": "hero-agency",
            "type": "registry:block",
            "dependencies": ["motion"],
            "registryDependencies": ["button"],
            "files": [
                {
                    "path": "../../packages/blocks/src/hero-section/hero-agency.tsx",
                    "type": "registry:block",
                    "content": "export function HeroAgency() { return null }",
                },
                {"path": "./components/ui/reveal.tsx", "content": "export const Reveal = 1"},
            ],
        },
    )
    _write(
        root,
        f"{registry}/btn-shine.json",
        {
            "name": "btn-shine",
            "files": [
                {
                    "path": "./registry/components/button/btn-shine.tsx",
                    "content": "export const B = 1",
                }
            ],
        },
    )
    _write(root, f"{registry}/empty.json", {"name": "empty", "files": [{"path": "./x.tsx"}]})
    return root


async def _collect(importer: Any) -> list[ImportedReference]:
    return [component async for component in importer.components()]


async def test_a_registry_checkout_becomes_attributed_components(tmp_path: Path) -> None:
    importer = ShadcnRegistryImporter(UI_LAYOUTS, _ui_layouts_checkout(tmp_path), "abc123")

    hero, button = await _collect(importer)

    assert (hero.source, hero.slug, hero.kind) == (
        ReferenceSource.UI_LAYOUTS,
        "hero-agency",
        ReferenceKind.BLOCK,
    )
    assert (hero.name, hero.category) == ("Hero Agency", "hero")
    assert (hero.license, hero.author, hero.source_revision) == ("MIT", "UI Layouts", "abc123")
    assert hero.source_url == (
        "https://github.com/ui-layouts/uilayouts/blob/abc123/"
        "packages/blocks/src/hero-section/hero-agency.tsx"
    ), "the link leads to the exact file that was read"
    assert hero.dependencies == ["motion"] and hero.registry_dependencies == ["button"]
    assert [file.path for file in hero.files][1] == "./components/ui/reveal.tsx"
    assert (button.kind, button.category) == (ReferenceKind.COMPONENT, "button")
    assert button.source_url.endswith("/apps/ui-layout/registry/components/button/btn-shine.tsx")
    # Styles are not components; entries without a file or without code are reported.
    assert sorted(line.split(":")[0] for line in importer.skipped) == ["empty", "ghost"]


async def test_magic_ui_examples_are_kept_apart_from_components(tmp_path: Path) -> None:
    registry = MAGIC_UI.registry_dir
    items = [
        {"name": "animated-shiny-text", "type": "registry:ui", "title": "Animated Shiny Text"},
        {"name": "marquee-demo", "type": "registry:example"},
        {"name": "utils", "type": "registry:lib"},
    ]
    _write(tmp_path, f"{registry}/registry.json", {"items": items})
    for item in items[:2]:
        _write(
            tmp_path,
            f"{registry}/{item['name']}.json",
            {
                **item,
                "description": "Shimmering text.",
                "files": [{"path": f"registry/magicui/{item['name']}.tsx", "content": "x"}],
            },
        )

    text, demo = await _collect(ShadcnRegistryImporter(MAGIC_UI, tmp_path))

    assert (text.name, text.kind, text.category) == (
        "Animated Shiny Text",
        ReferenceKind.COMPONENT,
        "text-animation",
    )
    assert text.preview_url == "https://magicui.design/docs/components/animated-shiny-text"
    assert text.description == "Shimmering text."
    assert (demo.kind, demo.category, demo.preview_url) == (ReferenceKind.EXAMPLE, "marquee", None)
    assert text.source_url.startswith("https://github.com/magicuidesign/magicui/blob/main/")


async def test_a_checkout_without_a_registry_is_an_import_error(tmp_path: Path) -> None:
    with pytest.raises(ReferenceImportException, match="No registry was found"):
        await _collect(ShadcnRegistryImporter(UI_LAYOUTS, tmp_path))

    (tmp_path / UI_LAYOUTS.registry_dir).mkdir(parents=True)
    (tmp_path / UI_LAYOUTS.registry_dir / "registry.json").write_text("{not json")
    with pytest.raises(ReferenceImportException, match="could not be read"):
        await _collect(ShadcnRegistryImporter(UI_LAYOUTS, tmp_path))


def _files_under(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())


def _archive(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


async def test_only_the_registry_directory_of_an_archive_is_unpacked(tmp_path: Path) -> None:
    wanted = f"uilayouts-main/{UI_LAYOUTS.registry_dir}/registry.json"
    archive = _archive(
        {
            wanted: b'{"items": []}',
            "uilayouts-main/package.json": b"{}",
            f"uilayouts-main/{UI_LAYOUTS.registry_dir}/../../../../escape.json": b"{}",
        }
    )
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, content=archive)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await download_registry(client, UI_LAYOUTS, tmp_path, timeout_seconds=5)

    assert seen == ["https://codeload.github.com/ui-layouts/uilayouts/tar.gz/refs/heads/main"]
    assert _files_under(tmp_path) == [f"{UI_LAYOUTS.registry_dir}/registry.json"]


@pytest.mark.parametrize(
    "response",
    [httpx.Response(404), httpx.Response(200, content=b"not an archive")],
    ids=["missing", "corrupt"],
)
async def test_an_unusable_archive_is_an_import_error(
    tmp_path: Path, response: httpx.Response
) -> None:
    transport = httpx.MockTransport(lambda _request: response)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ReferenceImportException):
            await download_registry(client, UI_LAYOUTS, tmp_path, timeout_seconds=5)


# --- 21st.dev ---------------------------------------------------------------------------


def _result(index: int) -> dict[str, Any]:
    return {
        "name": f"Hero {index}",
        "slug": f"hero-{index}",
        "install_ref": f"ada/hero-{index}",
        "description": "A hero.",
        "url": f"https://21st.dev/ada/hero-{index}",
        "preview_url": f"https://cdn.21st.dev/hero-{index}.png",
        "tags": ["hero", 3],
        "author": "ada",
    }


class _TwentyFirst:
    """A stand-in for the 21st.dev API that allows a fixed number of code fetches."""

    def __init__(self, allowance: int) -> None:
        self.allowance = allowance
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path == "/api/v1/components/search":
            return httpx.Response(200, json={"results": [_result(1), _result(2), _result(3)]})
        if self.allowance <= 0:
            return httpx.Response(402, json={"error": "quota_exceeded", "status": 402})
        self.allowance -= 1
        return httpx.Response(
            200,
            json={
                "files": [{"path": "hero.tsx", "content": "export const Hero = 1"}],
                "dependencies": ["motion"],
                "registry_dependencies": ["button"],
            },
        )

    def paths(self, prefix: str) -> list[str]:
        return [r.url.path for r in self.requests if r.url.path.startswith(prefix)]


async def test_twenty_first_uses_the_api_and_stops_when_the_allowance_ends() -> None:
    api = _TwentyFirst(allowance=1)
    async with httpx.AsyncClient(transport=httpx.MockTransport(api)) as client:
        importer = TwentyFirstImporter(
            client,
            "21st_sk_test",
            queries=[("hero", "hero section"), ("pricing", "pricing")],
            code_budget=10,
        )
        components = await _collect(importer)

    assert {r.url.host for r in api.requests} == {"21st.dev"}, "only the official API is called"
    assert all(r.headers["authorization"] == "Bearer 21st_sk_test" for r in api.requests)
    search = api.requests[0]
    assert dict(search.url.params) == {"q": "hero section", "scope": "public", "limit": "12"}
    # The same components come back for the second search and are not repeated.
    assert [c.slug for c in components] == ["ada/hero-1", "ada/hero-2", "ada/hero-3"]
    first, second, third = components
    assert first.files[0].content == "export const Hero = 1" and first.dependencies == ["motion"]
    assert (first.category, first.author, first.tags, first.license) == (
        "hero",
        "ada",
        ["hero"],
        None,
    )
    assert first.source_url == "https://21st.dev/ada/hero-1"
    # One refusal ends code fetching: the third component was never asked for.
    assert second.files == [] and third.files == []
    assert api.paths("/api/v1/components/install") == [
        "/api/v1/components/install/ada/hero-1",
        "/api/v1/components/install/ada/hero-2",
    ]
    assert importer.note is not None and "HTTP 402 quota_exceeded" in importer.note


async def test_twenty_first_fetches_no_code_unless_asked_to() -> None:
    api = _TwentyFirst(allowance=5)
    async with httpx.AsyncClient(transport=httpx.MockTransport(api)) as client:
        importer = TwentyFirstImporter(client, "key", queries=[("hero", "hero")])
        components = await _collect(importer)

    assert len(components) == 3 and all(c.files == [] for c in components)
    assert api.paths("/api/v1/components/install") == []
    assert importer.note is None


async def test_a_rejected_key_says_where_to_get_one() -> None:
    transport = httpx.MockTransport(
        lambda _r: httpx.Response(401, json={"error": "invalid_api_key"})
    )
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ReferenceImportException, match=r"21st\.dev/mcp"):
            await _collect(TwentyFirstImporter(client, "bad", queries=[("hero", "hero")]))


def test_the_content_hash_ignores_the_revision_it_was_read_at() -> None:
    def reference(revision: str, content: str = "a") -> ImportedReference:
        return ImportedReference(
            source=ReferenceSource.MAGIC_UI,
            slug="x",
            name="X",
            kind=ReferenceKind.COMPONENT,
            category="effect",
            source_url="https://github.com/o/r/blob/main/x.tsx",
            files=[{"path": "x.tsx", "content": content}],  # type: ignore[list-item]
            source_revision=revision,
        )

    assert content_hash(reference("r1")) == content_hash(reference("r2"))
    assert content_hash(reference("r1")) != content_hash(reference("r1", content="b"))


# --- Bootstrap --------------------------------------------------------------------------


def _text(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _bootstrap_checkout(root: Path) -> Path:
    _text(
        root,
        "site/src/assets/examples/heroes/index.astro",
        "---\nexport const title = 'Heroes'\n---\n<main/>",
    )
    _text(root, "site/src/assets/examples/heroes/heroes.css", ".hero{}")
    _text(root, "site/src/assets/examples/heroes/heroes.rtl.css", ".hero{}")
    (root / "site/src/assets/examples/heroes/shot.png").write_bytes(b"\x89PNG")
    _text(root, "site/src/assets/examples/heroes-rtl/index.astro", "<main/>")
    _text(root, "site/src/assets/examples/broken/readme.txt", "no page here")
    _text(
        root,
        "site/src/content/docs/components/alerts.mdx",
        "---\ntitle: Alerts\ndescription: Feedback messages.\n---\n<Example />",
    )
    _text(root, "site/src/content/docs/forms/range.mdx", "---\ntitle: Range\n---\n")
    _text(root, "scss/_alert.scss", ".alert{}")
    _text(root, "scss/_variables.scss", "$blue: #0d6efd;")
    _text(root, "scss/_mixins.scss", "@import 'mixins/x';")
    _text(root, "scss/mixins/_buttons.scss", "@mixin button-variant{}")
    _text(root, "scss/tests/_x.scss", "ignored")
    return root


async def test_bootstrap_yields_examples_documented_components_and_its_foundation(
    tmp_path: Path,
) -> None:
    importer = BootstrapImporter(_bootstrap_checkout(tmp_path), "rev9")

    items = {item.slug: item for item in await _collect(importer)}

    assert sorted(items) == [
        "docs/components/alerts",
        "docs/forms/range",
        "examples/heroes",
        "scss/mixins",
        "scss/mixins-partials",
        "scss/variables",
    ], "mirrored (RTL) pages, binary files, tests and the claimed partial are left out"
    hero = items["examples/heroes"]
    assert (hero.name, hero.kind, hero.category, hero.license) == (
        "Heroes",
        ReferenceKind.BLOCK,
        "hero",
        "MIT",
    )
    assert [file.path.rsplit("/", 1)[-1] for file in hero.files] == ["index.astro", "heroes.css"]
    assert hero.source_url == (
        "https://github.com/twbs/bootstrap/blob/rev9/site/src/assets/examples/heroes/index.astro"
    )
    alerts = items["docs/components/alerts"]
    assert (alerts.name, alerts.description, alerts.category) == (
        "Alerts",
        "Feedback messages.",
        "alerts",
    )
    # A documentation page comes with the stylesheet that implements it.
    assert [file.path for file in alerts.files][1] == "scss/_alert.scss"
    assert alerts.license == "MIT AND CC-BY-3.0", "the prose is CC BY, the code MIT"
    assert items["docs/forms/range"].category == "forms"
    assert items["scss/variables"].category == "foundation"
    # What could not be used is reported: the folder without a page, and the
    # documentation sections this small checkout does not have.
    assert importer.skipped[0] == "examples/broken: no page"
    assert "docs/layout: missing" in importer.skipped
    assert len({item.slug for item in items.values()}) == len(items)


async def test_a_checkout_that_is_not_bootstrap_is_an_import_error(tmp_path: Path) -> None:
    with pytest.raises(ReferenceImportException, match="No Bootstrap examples"):
        await _collect(BootstrapImporter(tmp_path))
