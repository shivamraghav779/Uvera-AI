import uuid
from collections.abc import Sequence

from sqlalchemy import ColumnElement, Integer, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import undefer

from app.domains.references.models import ReferenceComponent


class ReferenceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_slug(self, source: str, slug: str) -> ReferenceComponent | None:
        statement = (
            select(ReferenceComponent)
            .where(ReferenceComponent.source == source, ReferenceComponent.slug == slug)
            .options(undefer(ReferenceComponent.files))
        )
        return (await self._db.scalars(statement)).first()

    async def get_with_files(self, reference_id: uuid.UUID) -> ReferenceComponent | None:
        statement = (
            select(ReferenceComponent)
            .where(ReferenceComponent.id == reference_id)
            .options(undefer(ReferenceComponent.files))
        )
        return (await self._db.scalars(statement)).first()

    async def add(self, reference: ReferenceComponent) -> ReferenceComponent:
        self._db.add(reference)
        await self._db.flush()
        return reference

    @staticmethod
    def _filters(
        *,
        source: str | None,
        kind: str | None,
        category: str | None,
        query: str | None,
        with_code: bool | None,
    ) -> list[ColumnElement[bool]]:
        filters: list[ColumnElement[bool]] = []
        if source:
            filters.append(ReferenceComponent.source == source)
        if kind:
            filters.append(ReferenceComponent.kind == kind)
        if category:
            filters.append(ReferenceComponent.category == category)
        if with_code is not None:
            filters.append(
                ReferenceComponent.code_size > 0 if with_code else ReferenceComponent.code_size == 0
            )
        if query:
            # The user's text is a literal: % and _ in it are not wildcards.
            escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            pattern = f"%{escaped}%"
            filters.append(
                or_(
                    ReferenceComponent.name.ilike(pattern, escape="\\"),
                    ReferenceComponent.slug.ilike(pattern, escape="\\"),
                    ReferenceComponent.category.ilike(pattern, escape="\\"),
                    ReferenceComponent.description.ilike(pattern, escape="\\"),
                )
            )
        return filters

    async def search(
        self,
        *,
        source: str | None = None,
        kind: str | None = None,
        category: str | None = None,
        query: str | None = None,
        with_code: bool | None = None,
        limit: int,
        offset: int = 0,
    ) -> tuple[int, Sequence[ReferenceComponent]]:
        """Matching components without their code, by category then name, and how many there are."""
        filters = self._filters(
            source=source, kind=kind, category=category, query=query, with_code=with_code
        )
        total = await self._db.scalar(
            select(func.count()).select_from(ReferenceComponent).where(*filters)
        )
        statement = (
            select(ReferenceComponent)
            .where(*filters)
            .order_by(ReferenceComponent.category, ReferenceComponent.name, ReferenceComponent.id)
            .limit(limit)
            .offset(offset)
        )
        return int(total or 0), (await self._db.scalars(statement)).all()

    async def facets(self) -> Sequence[tuple[str, str, int, int]]:
        """(source, category, components, components with code), for browsing."""
        has_code = cast(ReferenceComponent.code_size > 0, Integer)
        statement = (
            select(
                ReferenceComponent.source,
                ReferenceComponent.category,
                func.count(),
                func.coalesce(func.sum(has_code), 0),
            )
            .group_by(ReferenceComponent.source, ReferenceComponent.category)
            .order_by(ReferenceComponent.source, ReferenceComponent.category)
        )
        return [(s, c, int(n), int(w)) for s, c, n, w in (await self._db.execute(statement)).all()]
