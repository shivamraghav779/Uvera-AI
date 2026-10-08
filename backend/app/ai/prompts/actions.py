"""Prompt fragment describing the allowlisted actions a UI may declare."""

from collections.abc import Sequence
from dataclasses import dataclass

ACTIONS_GUIDE_HEADER = """\
Allowed actions
An action is written as {"type": "<action type>", "payload": {...}}. It is a declarative \
request the backend may run; it is never code. The payload holds static parameters only \
(the frontend adds runtime values such as the option a user selected). Use "target" to name \
the id of the component the result should update. Only these action types exist:"""

NO_ACTIONS_GUIDE = "Allowed actions\nNo actions are available. Do not add buttons or forms."


@dataclass(frozen=True, slots=True)
class ActionGuideEntry:
    type: str
    description: str
    payload_fields: tuple[str, ...]


def render_actions_guide(entries: Sequence[ActionGuideEntry]) -> str:
    if not entries:
        return NO_ACTIONS_GUIDE
    lines = [
        f"- {entry.type}: {entry.description} Payload fields: {', '.join(entry.payload_fields)}."
        for entry in entries
    ]
    return "\n".join([ACTIONS_GUIDE_HEADER, *lines])
