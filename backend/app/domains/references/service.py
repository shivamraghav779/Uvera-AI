"""The reference library: importing components and reading them back."""

import hashlib
import json
import uuid

from app.core.exceptions import ResourceNotFoundException
from app.core.logging import get_logger
from app.database.unit_of_work import UnitOfWork
from app.domains.references.importers import ReferenceImporter
from app.domains.references.models import ReferenceComponent
from app.domains.references.repository import ReferenceRepository
from app.domains.references.schemas import (
    ImportedReference,
    ImportReport,
    ReferenceCatalog,
    ReferenceDetail,
    ReferenceFacet,
    ReferenceFile,
    ReferenceKind,
    ReferenceSource,
    ReferenceSummary,
)
from app.utils.datetime import utc_now

logger = get_logger(__name__)
COMMIT_EVERY = 50


def content_hash(reference: ImportedReference) -> str:
    """Identity of what would be stored, so an unchanged component is not rewritten."""
    payload = reference.model_dump(mode="json", exclude={"source_revision"})
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


class ReferenceLibrary:
    def __init__(self, repository: ReferenceRepository, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    # --- Importing -----------------------------------------------------------------

    @staticmethod
    def _apply(row: ReferenceComponent, reference: ImportedReference, digest: str) -> None:
        files = [file.model_dump() for file in reference.files]
        row.name = reference.name
        row.kind = reference.kind.value
        row.category = reference.category
        row.description = reference.description
        row.tags = reference.tags
        row.author = reference.author
        row.license = reference.license
        row.source_url = reference.source_url
        row.preview_url = reference.preview_url
        row.dependencies = reference.dependencies
        row.registry_dependencies = reference.registry_dependencies
        row.files = files
        row.file_count = len(files)
        row.code_size = sum(len(file.content) for file in reference.files)
        row.content_hash = digest
        row.source_revision = reference.source_revision
        row.fetched_at = utc_now()

    async def _store(self, reference: ImportedReference, report: ImportReport) -> None:
        digest = content_hash(reference)
        existing = await self._repository.get_by_slug(reference.source.value, reference.slug)
        if existing is None:
            row = ReferenceComponent(source=reference.source.value, slug=reference.slug)
            self._apply(row, reference, digest)
            await self._repository.add(row)
            report.created += 1
        elif existing.content_hash == digest:
            report.unchanged += 1
        elif existing.code_size > 0 and not reference.files:
            # Metadata-only news about a component whose code we hold: keep the code.
            report.unchanged += 1
        else:
            self._apply(existing, reference, digest)
            report.updated += 1
        if reference.files:
            report.with_code += 1

    async def import_from(self, importer: ReferenceImporter) -> ImportReport:
        """Store everything the importer yields. Safe to run again: unchanged
        components are left alone, changed ones are updated in place."""
        report = ImportReport(source=importer.source)
        async for reference in importer.components():
            report.seen += 1
            await self._store(reference, report)
            if report.seen % COMMIT_EVERY == 0:
                await self._uow.commit()
        await self._uow.commit()
        report.skipped = list(getattr(importer, "skipped", []))
        report.note = importer.note
        logger.info(
            "references_imported",
            extra={
                "source": report.source.value,
                "seen": report.seen,
                "created_count": report.created,
                "updated_count": report.updated,
            },
        )
        return report

    # --- Reading -------------------------------------------------------------------

    async def search(
        self,
        *,
        source: ReferenceSource | None,
        kind: ReferenceKind | None,
        category: str | None,
        query: str | None,
        with_code: bool | None,
        limit: int,
        offset: int,
    ) -> ReferenceCatalog:
        total, rows = await self._repository.search(
            source=source.value if source else None,
            kind=kind.value if kind else None,
            category=category,
            query=query,
            with_code=with_code,
            limit=limit,
            offset=offset,
        )
        return ReferenceCatalog(
            total=total, items=[ReferenceSummary.model_validate(row) for row in rows]
        )

    async def facets(self) -> list[ReferenceFacet]:
        return [
            ReferenceFacet(
                source=ReferenceSource(source), category=category, count=count, with_code=code
            )
            for source, category, count, code in await self._repository.facets()
        ]

    async def get(self, reference_id: uuid.UUID) -> ReferenceDetail:
        row = await self._repository.get_with_files(reference_id)
        if row is None:
            raise ResourceNotFoundException.for_resource("Reference component", reference_id)
        summary = ReferenceSummary.model_validate(row)
        return ReferenceDetail(
            **summary.model_dump(), files=[ReferenceFile.model_validate(f) for f in row.files]
        )
