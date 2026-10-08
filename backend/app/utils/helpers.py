import re
from collections.abc import Hashable, Iterable

_WORD = re.compile(r"[a-z0-9]+")


def truncate(text: str, limit: int, suffix: str = "…") -> str:
    """Shorten ``text`` to at most ``limit`` characters."""
    if len(text) <= limit:
        return text
    return text[: max(limit - len(suffix), 0)] + suffix


def tokenize(text: str) -> set[str]:
    """Lower-case alphanumeric words in ``text``."""
    return set(_WORD.findall(text.lower()))


def unique[T: Hashable](items: Iterable[T]) -> list[T]:
    """De-duplicate while preserving first-seen order."""
    return list(dict.fromkeys(items))
