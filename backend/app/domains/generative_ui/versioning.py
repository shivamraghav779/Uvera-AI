"""Version engine: the only code path that changes what a workspace's UI is.

Every approved change appends an immutable ``UIVersion`` and moves the
workspace's ``current_version_id``. Writes must name the version they were
prepared against; a stale base is rejected instead of overwriting newer work.
"""

import uuid
from typing import Any

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import (
    ResourceNotFoundException,
    StoredDataException,
    ValidationException,
    VersionConflictException,
)
from app.core.logging import get_logger
from app.core.security import Principal
from app.database.unit_of_work import UnitOfWork
from app.domains.data_sources.providers.base import DataProvider
from app.domains.generative_ui.contracts import (
    ChangeRead,
    VersionComparison,
    VersionCreate,
    VersionDetail,
    VersionRestore,
    VersionSource,
    VersionSummary,
)
from app.domains.generative_ui.diff import Change, diff_documents
from app.domains.generative_ui.document import UIDocument, dump_document
from app.domains.generative_ui.models import UIVersion
from app.domains.generative_ui.mutator import DocumentMutator
from app.domains.generative_ui.renderer import RecordChangeSource, UIDataResolver
from app.domains.generative_ui.repository import UIVersionRepository
from app.domains.generative_ui.validator import UISchemaValidator, ValidationContext
from app.domains.workspaces.models import Workspace
from app.domains.workspaces.service import WorkspaceService

logger = get_logger(__name__)

MAX_VERSIONS_LISTED = 200
MAX_SUMMARIES_IN_DESCRIPTION = 3
MAX_DESCRIPTION_LENGTH = 300


def to_document(version: UIVersion) -> UIDocument:
    try:
        return UIDocument.model_validate(
            {
                "page": version.ui_schema,
                "theme": version.theme,
                "design": version.design,
                "application": version.application,
            }
        )
    except ValidationError:
        logger.error("stored_version_unreadable", extra={"version_number": version.version_number})
        raise StoredDataException(
            f"Version {version.version_number} is stored in a form this release cannot read."
        ) from None


def to_summary(version: UIVersion, current_version_id: uuid.UUID | None) -> VersionSummary:
    return VersionSummary(
        id=version.id,
        workspace_id=version.workspace_id,
        version_number=version.version_number,
        parent_version_id=version.parent_version_id,
        description=version.description,
        source=VersionSource(version.source),
        metadata=version.source_metadata,
        created_at=version.created_at,
        created_by=version.created_by,
        is_current=version.id == current_version_id,
    )


def to_change_reads(changes: list[Change]) -> list[ChangeRead]:
    return [
        ChangeRead(kind=change.kind, summary=change.summary, component_id=change.component_id)
        for change in changes
    ]


async def validation_context(data_provider: DataProvider) -> ValidationContext:
    datasets = await data_provider.list_datasets()
    return ValidationContext(datasets={dataset.name: dataset for dataset in datasets})


def ensure_current(
    workspace: Workspace, base_version_id: uuid.UUID | None, current: UIVersion | None
) -> None:
    """Reject work prepared against anything but the workspace's current version."""
    if workspace.current_version_id == base_version_id:
        return
    details: list[dict[str, object]] = []
    if current is not None:
        details.append(
            {
                "current_version_id": str(current.id),
                "current_version_number": current.version_number,
            }
        )
    raise VersionConflictException(details=details)


def generated_description(document: UIDocument) -> str:
    application = document.application
    if application is None:
        return f"Generated “{document.page.title}”"
    count = len(document.page.components)
    return f"Generated “{application.name}” ({count} screen{'' if count == 1 else 's'})"


def _summarise(summaries: list[str]) -> str:
    listed = "; ".join(summaries[:MAX_SUMMARIES_IN_DESCRIPTION])
    remaining = len(summaries) - MAX_SUMMARIES_IN_DESCRIPTION
    text = f"{listed} (+{remaining} more)" if remaining > 0 else listed
    return text[:MAX_DESCRIPTION_LENGTH]


class VersionService:
    def __init__(
        self,
        *,
        workspaces: WorkspaceService,
        versions: UIVersionRepository,
        validator: UISchemaValidator,
        mutator: DocumentMutator,
        data_provider: DataProvider,
        uow: UnitOfWork,
        records: RecordChangeSource | None = None,
    ) -> None:
        self._workspaces = workspaces
        self._versions = versions
        self._validator = validator
        self._mutator = mutator
        self._data_provider = data_provider
        self._data = UIDataResolver(data_provider, records)
        self._uow = uow

    async def list_versions(
        self, principal: Principal, workspace_id: uuid.UUID
    ) -> list[VersionSummary]:
        workspace = await self._workspaces.get(principal, workspace_id)
        versions = await self._versions.list_for_workspace(workspace.id, limit=MAX_VERSIONS_LISTED)
        return [to_summary(version, workspace.current_version_id) for version in versions]

    async def get_version(
        self, principal: Principal, workspace_id: uuid.UUID, version_id: uuid.UUID
    ) -> VersionDetail:
        workspace = await self._workspaces.get(principal, workspace_id)
        version = await self._require(workspace.id, version_id)
        return await self._detail(version, workspace.current_version_id)

    async def create(
        self, principal: Principal, workspace_id: uuid.UUID, payload: VersionCreate
    ) -> VersionDetail:
        workspace = await self._workspaces.get(principal, workspace_id, for_update=True)
        current = await self._current(workspace)
        ensure_current(workspace, payload.base_version_id, current)

        context = await validation_context(self._data_provider)
        metadata: dict[str, Any] = {}
        if payload.operations is not None:
            if current is None:
                raise ValidationException("Operations need an existing version to apply to.")
            outcome = self._mutator.apply(to_document(current), payload.operations, context)
            assert outcome.document is not None
            document = outcome.document
            metadata["operations"] = outcome.operations
            description = _summarise([step.summary for step in outcome.steps])
        else:
            document = self._validator.validate_document(payload.document, context)
            description = generated_description(document)

        if payload.proposal_id is not None:
            metadata["proposal_id"] = str(payload.proposal_id)
        if payload.instruction is not None:
            metadata["instruction"] = payload.instruction
        version = await self._append(
            workspace,
            current,
            document,
            description=payload.description or description,
            source=payload.source,
            metadata=metadata,
            principal=principal,
        )
        return await self._detail(version, version.id)

    async def restore(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        version_id: uuid.UUID,
        payload: VersionRestore,
    ) -> VersionDetail:
        """Make an old version current by appending a copy of it. Nothing is rewritten."""
        workspace = await self._workspaces.get(principal, workspace_id, for_update=True)
        current = await self._current(workspace)
        ensure_current(workspace, payload.base_version_id, current)
        target = await self._require(workspace.id, version_id)
        if current is not None and target.id == current.id:
            raise ValidationException(f"Version {target.version_number} is already current.")

        metadata: dict[str, Any] = {
            "restored_from_version_id": str(target.id),
            "restored_from_version_number": target.version_number,
        }
        if payload.proposal_id is not None:
            metadata["proposal_id"] = str(payload.proposal_id)
        version = await self._append(
            workspace,
            current,
            to_document(target),
            description=f"Restored from Version {target.version_number}",
            source=VersionSource.RESTORE,
            metadata=metadata,
            principal=principal,
        )
        return await self._detail(version, version.id)

    async def compare(
        self,
        principal: Principal,
        workspace_id: uuid.UUID,
        version_id: uuid.UUID,
        other_version_id: uuid.UUID | None,
    ) -> VersionComparison:
        """Changes that turn ``version_id`` into ``other_version_id`` (default: current)."""
        workspace = await self._workspaces.get(principal, workspace_id)
        origin = await self._require(workspace.id, version_id)
        other_id = other_version_id or workspace.current_version_id
        if other_id is None:
            raise ValidationException("The workspace has no current version to compare with.")
        other = await self._require(workspace.id, other_id)
        changes = diff_documents(
            dump_document(to_document(origin)), dump_document(to_document(other))
        )
        return VersionComparison(
            from_version=to_summary(origin, workspace.current_version_id),
            to_version=to_summary(other, workspace.current_version_id),
            changes=to_change_reads(changes),
        )

    async def _current(self, workspace: Workspace) -> UIVersion | None:
        if workspace.current_version_id is None:
            return None
        return await self._versions.get(workspace.id, workspace.current_version_id)

    async def _require(self, workspace_id: uuid.UUID, version_id: uuid.UUID) -> UIVersion:
        version = await self._versions.get(workspace_id, version_id)
        if version is None:
            raise ResourceNotFoundException.for_resource("Version", version_id)
        return version

    async def _append(
        self,
        workspace: Workspace,
        current: UIVersion | None,
        document: UIDocument,
        *,
        description: str,
        source: VersionSource,
        metadata: dict[str, Any],
        principal: Principal,
    ) -> UIVersion:
        content = dump_document(document)
        try:
            version = await self._add(
                workspace, current, content, description, source, metadata, principal
            )
        except IntegrityError:
            # The row lock makes this unreachable in practice; the unique constraint is the
            # backstop, and losing that race is the same situation as a stale base.
            await self._uow.rollback()
            raise VersionConflictException() from None
        workspace.current_version_id = version.id
        if workspace.title is None:
            application = document.application
            workspace.title = application.name if application else document.page.title
        await self._uow.commit()
        logger.info(
            "ui_version_created",
            extra={"version_number": version.version_number, "source": source.value},
        )
        return version

    async def _add(
        self,
        workspace: Workspace,
        current: UIVersion | None,
        content: dict[str, Any],
        description: str,
        source: VersionSource,
        metadata: dict[str, Any],
        principal: Principal,
    ) -> UIVersion:
        return await self._versions.add(
            workspace_id=workspace.id,
            version_number=(current.version_number if current else 0) + 1,
            parent_version_id=current.id if current else None,
            ui_schema=content["page"],
            theme=content["theme"],
            design=content["design"],
            application=content.get("application"),
            description=description,
            source=source.value,
            source_metadata=metadata,
            created_by=principal.user_id,
        )

    async def _detail(
        self, version: UIVersion, current_version_id: uuid.UUID | None
    ) -> VersionDetail:
        document = to_document(version)
        summary = to_summary(version, current_version_id)
        return VersionDetail(
            **summary.model_dump(),
            document=document,
            data=await self._data.resolve(document, version.workspace_id),
        )
