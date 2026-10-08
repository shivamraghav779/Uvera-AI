import uuid
from datetime import timedelta
from typing import Any

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.actions.models import UIAction
from app.domains.actions.repository import UIActionRepository
from app.domains.conversation.models import ConversationMessage
from app.domains.conversation.repository import ConversationRepository
from app.domains.conversation.schemas import MessageRole
from app.domains.data_sources.repository import DataSourceRepository
from app.domains.generative_ui.models import UIVersion
from app.domains.generative_ui.repository import UIVersionRepository
from app.domains.users.models import User
from app.domains.workspaces.models import Workspace
from app.domains.workspaces.repository import WorkspaceRepository
from tests.support import canonical_document


@pytest.fixture
async def workspace(db_session: AsyncSession) -> Workspace:
    return await WorkspaceRepository(db_session).create(user_id=None, title="Workspace")


async def _add_version(
    db_session: AsyncSession, workspace: Workspace, number: int, parent: UIVersion | None = None
) -> UIVersion:
    document: dict[str, Any] = canonical_document()
    return await UIVersionRepository(db_session).add(
        workspace_id=workspace.id,
        version_number=number,
        parent_version_id=parent.id if parent else None,
        ui_schema=document["page"],
        theme=document["theme"],
        design=document["design"],
        description=f"Version {number}",
        source="manual_edit",
        source_metadata={"note": number},
        created_by=None,
    )


async def test_workspace_gets_uuid_and_timezone_aware_timestamps(
    db_session: AsyncSession, workspace: Workspace
) -> None:
    await db_session.commit()
    db_session.expunge_all()

    stored = await WorkspaceRepository(db_session).get(workspace.id)

    assert stored is not None
    assert isinstance(stored.id, uuid.UUID)
    assert stored.created_at.utcoffset() == timedelta(0)
    assert stored.current_version_id is None


async def test_workspaces_are_scoped_to_their_owner(db_session: AsyncSession) -> None:
    owner = User(email="owner@example.com", password_hash="!")
    db_session.add(owner)
    await db_session.flush()
    repository = WorkspaceRepository(db_session)
    owned = await repository.create(user_id=owner.id, title="Mine")
    anonymous = await repository.create(user_id=None, title="Anonymous")

    assert [w.id for w in await repository.list_for_user(owner.id, limit=10, offset=0)] == [
        owned.id
    ]
    assert [w.id for w in await repository.list_for_user(None, limit=10, offset=0)] == [
        anonymous.id
    ]


async def test_messages_keep_order_and_structured_details(
    db_session: AsyncSession, workspace: Workspace
) -> None:
    repository = ConversationRepository(db_session)
    for index in range(4):
        await repository.add(
            workspace_id=workspace.id, role=MessageRole.USER, content=f"message {index}"
        )
    details = {"proposal_id": str(uuid.uuid4()), "kind": "mutate"}
    await repository.add(
        workspace_id=workspace.id, role=MessageRole.ASSISTANT, content="proposal", details=details
    )
    await db_session.commit()
    db_session.expunge_all()

    listed = await repository.list_for_workspace(workspace.id, limit=10, offset=0)
    recent = await repository.recent(workspace.id, limit=2)

    assert [m.content for m in listed] == [*(f"message {i}" for i in range(4)), "proposal"]
    assert [m.content for m in recent] == ["message 3", "proposal"], "latest two, oldest first"
    assert listed[-1].details == details
    assert listed[0].details is None


async def test_database_rejects_unknown_roles(
    db_session: AsyncSession, workspace: Workspace
) -> None:
    statement = text(
        "INSERT INTO conversations (id, workspace_id, role, content) "
        "VALUES (:id, :workspace_id, 'root', 'x')"
    )

    with pytest.raises(IntegrityError, match="ck_conversations_message_role"):
        await db_session.execute(statement, {"id": uuid.uuid4(), "workspace_id": workspace.id})


async def test_versions_round_trip_and_are_listed_newest_first(
    db_session: AsyncSession, workspace: Workspace
) -> None:
    repository = UIVersionRepository(db_session)
    first = await _add_version(db_session, workspace, 1)
    second = await _add_version(db_session, workspace, 2, parent=first)
    await db_session.commit()
    db_session.expunge_all()

    listed = await repository.list_for_workspace(workspace.id, limit=10)
    by_number = await repository.get_by_number(workspace.id, 1)

    assert [v.version_number for v in listed] == [2, 1]
    assert listed[0].parent_version_id == first.id
    assert by_number is not None and by_number.id == first.id
    document = canonical_document()
    assert (listed[0].ui_schema, listed[0].theme, listed[0].design) == (
        document["page"],
        document["theme"],
        document["design"],
    ), "JSONB round-trips the document exactly"
    assert await repository.numbers_for([first.id, second.id]) == {first.id: 1, second.id: 2}
    assert await repository.get(uuid.uuid4(), first.id) is None, "scoped to the workspace"


async def test_version_number_is_unique_per_workspace(
    db_session: AsyncSession, workspace: Workspace
) -> None:
    await _add_version(db_session, workspace, 1)

    with pytest.raises(IntegrityError, match="uq_ui_versions_workspace_id_version_number"):
        await _add_version(db_session, workspace, 1)


async def test_locking_a_workspace_returns_its_latest_state(
    db_session: AsyncSession, workspace: Workspace
) -> None:
    version = await _add_version(db_session, workspace, 1)
    workspace.current_version_id = version.id
    await db_session.commit()

    locked = await WorkspaceRepository(db_session).get(workspace.id, for_update=True)

    assert locked is not None
    assert locked.current_version_id == version.id


async def test_deleting_a_workspace_cascades_to_everything_it_owns(
    db_session: AsyncSession, workspace: Workspace
) -> None:
    await ConversationRepository(db_session).add(
        workspace_id=workspace.id, role=MessageRole.USER, content="hi"
    )
    first = await _add_version(db_session, workspace, 1)
    second = await _add_version(db_session, workspace, 2, parent=first)
    workspace.current_version_id = second.id
    await UIActionRepository(db_session).add(
        workspace_id=workspace.id, action_type="refresh", payload={"dataset": "sales"}
    )
    await db_session.commit()

    await WorkspaceRepository(db_session).delete(workspace)
    await db_session.commit()

    for model in (ConversationMessage, UIVersion, UIAction, Workspace):
        assert await db_session.scalar(select(func.count()).select_from(model)) == 0


async def test_data_source_configuration_is_stored_as_jsonb(db_session: AsyncSession) -> None:
    repository = DataSourceRepository(db_session)
    configuration = {"host": "db.internal", "options": {"ssl": True, "schemas": ["sales"]}}

    created = await repository.create(
        user_id=None, name="Warehouse", type="postgresql", configuration=configuration
    )
    await db_session.commit()
    db_session.expunge_all()

    [stored] = await repository.list_for_user(None, limit=10, offset=0)
    assert (stored.id, stored.configuration) == (created.id, configuration)
    column_types = (
        await db_session.execute(
            text(
                "SELECT table_name || '.' || column_name, data_type "
                "FROM information_schema.columns "
                "WHERE column_name IN ('configuration', 'ui_schema', 'theme', 'design', 'details')"
            )
        )
    ).all()
    assert {data_type for _, data_type in column_types} == {"jsonb"}
    assert len(column_types) == 5
