"""Allowlist of executable actions.

Only actions registered here can run. The model can *name* an action in a UI
schema, but it can never add one or reach any other backend function.
"""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, ClassVar

from pydantic import ValidationError

from app.core.exceptions import ActionNotAllowedException, ActionPayloadException
from app.core.logging import get_logger
from app.domains.actions.schemas import ActionPayload, ActionType

logger = get_logger(__name__)

# JSON-serialisable result returned to the client.
ActionResult = dict[str, Any]


class ActionHandler[PayloadT: ActionPayload](ABC):
    action_type: ClassVar[ActionType]
    description: ClassVar[str]
    payload_model: type[PayloadT]

    @abstractmethod
    async def handle(self, payload: PayloadT) -> ActionResult:
        """Perform the action for an already-validated payload."""


class ActionRegistry:
    def __init__(self) -> None:
        self._handlers: dict[ActionType, ActionHandler[ActionPayload]] = {}

    def register(self, handler: ActionHandler[ActionPayload]) -> None:
        if handler.action_type in self._handlers:
            raise ValueError(f"Action '{handler.action_type}' is already registered.")
        self._handlers[handler.action_type] = handler

    def allowed_types(self) -> frozenset[ActionType]:
        return frozenset(self._handlers)

    def handlers(self) -> tuple[ActionHandler[ActionPayload], ...]:
        return tuple(self._handlers.values())

    def get(self, action_type: str) -> ActionHandler[ActionPayload]:
        try:
            return self._handlers[ActionType(action_type)]
        except (ValueError, KeyError):
            logger.warning("action_rejected", extra={"action_type": action_type[:64]})
            raise ActionNotAllowedException(
                f"Action '{action_type}' is not an allowed action."
            ) from None

    async def execute(self, action_type: str, payload: Mapping[str, object]) -> ActionResult:
        handler = self.get(action_type)
        try:
            validated = handler.payload_model.model_validate(payload)
        except ValidationError as exc:
            raise ActionPayloadException(details=_payload_issues(exc)) from exc
        return await handler.handle(validated)


def _payload_issues(error: ValidationError) -> list[dict[str, str]]:
    return [
        {"path": ".".join(str(part) for part in issue["loc"]), "message": issue["msg"]}
        for issue in error.errors(include_url=False, include_input=False)
    ]
