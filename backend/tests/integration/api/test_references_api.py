"""The reference library is filled by an import and read through the API."""

from collections.abc import AsyncIterator, Sequence

import httpx
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.domains.references.importers import ReferenceImporter
from app.domains.references.repository import ReferenceRepository
from app.domains.references.schemas import ImportedReference, ReferenceKind, ReferenceSource
from app.domains.references.service import ReferenceLibrary
from app.main import create_app
from tests.integration.api.flows import API
from tests.support import make_settings, running_client

REFERENCES = f"{API}/references"


def _reference(slug: str, category: str, **changes: object) -> ImportedReference:
    values: dict[str, object] = {
        "source": ReferenceSource.UI_LAYOUTS,
        "slug": slug,
        "name": slug.replace("-", " ").title(),
        "kind": ReferenceKind.BLOCK,
        "category": category,
        "description": "A section.",
        "author": "UI Layouts",
        "license": "MIT",
        "source_url": f"https://github.com/ui-layouts/uilayouts/blob/main/{slug}.tsx",
        "files": [{"path": f"{slug}.tsx", "content": f"export const {category} = 1"}],
    }
    return ImportedReference.model_validate({**values, **changes})


class _Importer(ReferenceImporter):
    def __init__(self, source: ReferenceSource, references: Sequence[ImportedReference]) -> None:
        self.source = source
        self._references = references

    async def components(self) -> AsyncIterator[ImportedReference]:
        for reference in self._references:
            yield reference


async def _import(db_session: AsyncSession, *references: ImportedReference) -> dict[str, int]:
    library = ReferenceLibrary(ReferenceRepository(db_session), db_session)
    report = await library.import_from(_Importer(references[0].source, references))
    return report.model_dump(include={"seen", "created", "updated", "unchanged", "with_code"})


async def test_imported_components_can_be_browsed_filtered_and_opened(
    client: httpx.AsyncClient, db_session: AsyncSession
) -> None:
    report = await _import(
        db_session,
        _reference("hero-agency", "hero"),
        _reference("hero_split", "hero"),
        _reference("pricing-tiers", "pricing"),
    )
    await _import(
        db_session,
        _reference(
            "ada/hero-x",
            "hero",
            source=ReferenceSource.TWENTY_FIRST,
            kind=ReferenceKind.COMPONENT,
            license=None,
            files=[],
            source_url="https://21st.dev/ada/hero-x",
        ),
    )
    assert report == {"seen": 3, "created": 3, "updated": 0, "unchanged": 0, "with_code": 3}

    everything = (await client.get(REFERENCES)).json()["data"]
    assert everything["total"] == 4
    assert "files" not in everything["items"][0], "a listing never carries source code"

    heroes = (await client.get(REFERENCES, params={"category": "hero", "limit": 2})).json()["data"]
    assert heroes["total"] == 3 and len(heroes["items"]) == 2

    with_code = (
        await client.get(REFERENCES, params={"category": "hero", "with_code": "true"})
    ).json()["data"]
    assert {item["source"] for item in with_code["items"]} == {"ui_layouts"}

    # "_" is text, not a wildcard: it finds hero_split and not hero-agency.
    literal = (await client.get(REFERENCES, params={"q": "hero_"})).json()["data"]
    assert [item["slug"] for item in literal["items"]] == ["hero_split"]

    facets = (await client.get(f"{REFERENCES}/facets")).json()["data"]
    assert {"source": "twenty_first", "category": "hero", "count": 1, "with_code": 0} in facets
    assert {"source": "ui_layouts", "category": "hero", "count": 2, "with_code": 2} in facets

    pricing = (await client.get(REFERENCES, params={"q": "pricing"})).json()["data"]["items"][0]
    detail = (await client.get(f"{REFERENCES}/{pricing['id']}")).json()["data"]
    assert detail["files"] == [{"path": "pricing-tiers.tsx", "content": "export const pricing = 1"}]
    assert (detail["license"], detail["author"]) == ("MIT", "UI Layouts")
    assert detail["source_url"].startswith("https://github.com/ui-layouts/uilayouts/")


async def test_importing_again_updates_what_changed_and_keeps_fetched_code(
    db_session: AsyncSession,
) -> None:
    await _import(db_session, _reference("hero-agency", "hero"), _reference("cta-band", "cta"))

    again = await _import(
        db_session,
        _reference("hero-agency", "hero"),
        _reference("cta-band", "cta", description="A stronger call to action."),
        # The same component reported without code must not erase the code we hold.
        _reference("hero-agency", "hero", files=[], description="Metadata only."),
    )

    assert again == {"seen": 3, "created": 0, "updated": 1, "unchanged": 2, "with_code": 2}
    _, rows = await ReferenceRepository(db_session).search(limit=10)
    assert {row.slug: row.code_size > 0 for row in rows} == {"hero-agency": True, "cta-band": True}


async def test_the_library_needs_a_signed_in_user_and_reports_unknown_ids(
    client: httpx.AsyncClient, database_url: str, db_engine: AsyncEngine
) -> None:
    missing = await client.get(f"{REFERENCES}/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    protected = create_app(make_settings(database_url=database_url, auth_required=True))
    async with running_client(protected) as anonymous:
        assert (await anonymous.get(REFERENCES)).status_code == 401
