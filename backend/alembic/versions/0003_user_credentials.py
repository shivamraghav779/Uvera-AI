"""user credentials

Adds the password hash needed for sign-in. Accounts that existed before this
migration (none are created by earlier releases) get an unusable hash and must
re-register.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Matches no password: verification of a hash without the "scrypt$" scheme always fails.
UNUSABLE_HASH = "!"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(length=255), nullable=False, server_default=UNUSABLE_HASH),
    )
    op.alter_column("users", "password_hash", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "password_hash")
