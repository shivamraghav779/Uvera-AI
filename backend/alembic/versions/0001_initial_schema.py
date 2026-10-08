"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _id() -> sa.Column:
    return sa.Column("id", sa.Uuid(), nullable=False)


def _timestamp(name: str) -> sa.Column:
    return sa.Column(
        name, sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def _json(name: str) -> sa.Column:
    return sa.Column(name, postgresql.JSONB(astext_type=sa.Text()), nullable=False)


def _session_id() -> sa.Column:
    return sa.Column("session_id", sa.Uuid(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "users",
        _id(),
        sa.Column("email", sa.String(length=320), nullable=False),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.create_table(
        "sessions",
        _id(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=True),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_sessions_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sessions")),
    )
    op.create_index(op.f("ix_sessions_user_id"), "sessions", ["user_id"])

    op.create_table(
        "data_sources",
        _id(),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        _json("configuration"),
        _timestamp("created_at"),
        _timestamp("updated_at"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_data_sources_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_data_sources")),
    )
    op.create_index(op.f("ix_data_sources_user_id"), "data_sources", ["user_id"])

    op.create_table(
        "conversations",
        _id(),
        _session_id(),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        _timestamp("created_at"),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name=op.f("ck_conversations_message_role"),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name=op.f("fk_conversations_session_id_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
    )
    op.create_index(
        "ix_conversations_session_id_created_at", "conversations", ["session_id", "created_at"]
    )

    op.create_table(
        "ui_states",
        _id(),
        _session_id(),
        sa.Column("version", sa.Integer(), nullable=False),
        _json("ui_schema"),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name=op.f("fk_ui_states_session_id_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ui_states")),
        sa.UniqueConstraint("session_id", "version", name="uq_ui_states_session_id_version"),
    )

    op.create_table(
        "ui_actions",
        _id(),
        _session_id(),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        _json("payload"),
        _timestamp("created_at"),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["sessions.id"],
            name=op.f("fk_ui_actions_session_id_sessions"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ui_actions")),
    )
    op.create_index(
        "ix_ui_actions_session_id_created_at", "ui_actions", ["session_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_table("ui_actions")
    op.drop_table("ui_states")
    op.drop_table("conversations")
    op.drop_table("data_sources")
    op.drop_table("sessions")
    op.drop_table("users")
