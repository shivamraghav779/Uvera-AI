import uuid
from collections.abc import Callable

from app.core.logging import get_logger
from app.core.security import Principal
from app.database.unit_of_work import UnitOfWork
from app.domains.actions.handlers import RecordWriter
from app.domains.actions.registry import ActionRegistry
from app.domains.actions.repository import UIActionRepository
from app.domains.actions.schemas import (
    ActionExecuteRequest,
    ActionExecuteResponse,
    ActionType,
    FormSubmissionRead,
)
from app.domains.data_sources.providers.base import DataProvider
from app.domains.data_sources.providers.composite import CompositeDataProvider
from app.domains.generative_ui.repository import UIVersionRepository
from app.domains.generative_ui.versioning import to_document
from app.domains.records.repository import WorkspaceRecordRepository
from app.domains.records.store import ApplicationDataProvider, RecordStore
from app.domains.workspaces.models import Workspace
from app.domains.workspaces.service import WorkspaceService

logger = get_logger(__name__)


RegistryFactory = Callable[[DataProvider, RecordWriter | None], ActionRegistry]


class ActionService:
    """Runs an allowlisted action for a workspace and records it.

    Actions run against the workspace they were triggered in: when that
    workspace holds an application, its entities are readable as datasets and
    writable through the record actions.
    """

    def __init__(
        self,
        *,
        build_registry: RegistryFactory,
        data_provider: DataProvider,
        repository: UIActionRepository,
        workspaces: WorkspaceService,
        versions: UIVersionRepository,
        records: WorkspaceRecordRepository,
        uow: UnitOfWork,
    ) -> None:
        self._build_registry = build_registry
        self._data_provider = data_provider
        self._repository = repository
        self._workspaces = workspaces
        self._versions = versions
        self._records = records
        self._uow = uow

    async def execute(
        self, principal: Principal, request: ActionExecuteRequest
    ) -> ActionExecuteResponse:
        workspace = await self._workspaces.get(principal, request.workspace_id)
        registry = await self._registry_for(workspace)
        result = await registry.execute(request.action_type, request.payload)
        record = await self._repository.add(
            workspace_id=workspace.id, action_type=request.action_type, payload=request.payload
        )
        await self._uow.commit()
        logger.info("action_executed", extra={"action_type": request.action_type})
        return ActionExecuteResponse(
            action_id=record.id,
            workspace_id=workspace.id,
            action_type=ActionType(request.action_type),
            result=result,
        )

    async def reset_data(self, principal: Principal, workspace_id: uuid.UUID) -> int:
        """Forget every change made to the application's data; sample records return."""
        workspace = await self._workspaces.get(principal, workspace_id)
        removed = await self._records.clear(workspace.id)
        await self._uow.commit()
        return removed

    async def _registry_for(self, workspace: Workspace) -> ActionRegistry:
        store = await self._record_store(workspace)
        if store is None:
            return self._build_registry(self._data_provider, None)
        provider = CompositeDataProvider([ApplicationDataProvider(store), self._data_provider])
        return self._build_registry(provider, store)

    async def _record_store(self, workspace: Workspace) -> RecordStore | None:
        if workspace.current_version_id is None:
            return None
        version = await self._versions.get(workspace.id, workspace.current_version_id)
        if version is None or version.application is None:
            return None
        application = to_document(version).application
        assert application is not None
        return RecordStore(workspace.id, application, self._records)

    async def list_submissions(
        self, principal: Principal, workspace_id: uuid.UUID, *, limit: int, offset: int
    ) -> list[FormSubmissionRead]:
        """Form submissions received by a workspace's UI, newest first."""
        workspace = await self._workspaces.get(principal, workspace_id)
        records = await self._repository.list_by_type(
            workspace.id, ActionType.SUBMIT.value, limit=limit, offset=offset
        )
        return [
            FormSubmissionRead(
                id=record.id,
                form_id=str(record.payload.get("form_id", "")),
                values=record.payload.get("values") or {},
                submitted_at=record.created_at,
            )
            for record in records
        ]
