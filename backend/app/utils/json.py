"""JSON helpers for handling model output safely."""

import json
import re
from typing import NoReturn

_CODE_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)


def _reject_constant(name: str) -> NoReturn:
    # NaN/Infinity are not valid JSON and cannot be stored as JSONB.
    raise ValueError(f"Non-standard JSON constant '{name}' is not allowed.")


def _loads(text: str) -> object:
    return json.loads(text, parse_constant=_reject_constant)


def parse_json_document(text: str) -> object:
    """Parse JSON from model output, tolerating code fences and surrounding prose.

    Raises ``ValueError`` when no JSON document can be recovered.
    """
    candidate = text.strip()
    fenced = _CODE_FENCE.match(candidate)
    if fenced:
        candidate = fenced.group(1)
    try:
        return _loads(candidate)
    except ValueError:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("Output does not contain a JSON object.") from None
        return _loads(candidate[start : end + 1])


def to_compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
