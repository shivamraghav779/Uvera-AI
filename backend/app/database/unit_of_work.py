from typing import Protocol


class UnitOfWork(Protocol):
    """Transaction boundary used by services.

    ``AsyncSession`` satisfies this structurally, so services decide when a use
    case commits without importing SQLAlchemy.
    """

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
