import uuid
from collections.abc import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.actions.models import UIAction


class UIActionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(
        self, *, workspace_id: uuid.UUID, action_type: str, payload: Mapping[str, object]
    ) -> UIAction:
        action = UIAction(workspace_id=workspace_id, action_type=action_type, payload=dict(payload))
        self._db.add(action)
        await self._db.flush()
        return action

    async def list_by_type(
        self, workspace_id: uuid.UUID, action_type: str, *, limit: int, offset: int
    ) -> Sequence[UIAction]:
        """Executed actions of one type, newest first."""
        statement = (
            select(UIAction)
            .where(UIAction.workspace_id == workspace_id, UIAction.action_type == action_type)
            .order_by(UIAction.created_at.desc(), UIAction.id)
            .limit(limit)
            .offset(offset)
        )
        return (await self._db.scalars(statement)).all()
