"""applications: screens, application data, assets and generation jobs

A version can now hold a whole application: ``ui_versions.application`` stores
the product around the screens (navigation, entities, assets, design direction).
Existing versions keep NULL there and remain single views.

New tables:
    workspace_records   changes users make to an application's data while using it
    assets              images belonging to a workspace (bytes and provenance)
    generation_jobs     background runs of the application generation pipeline

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_GUARDED_BEFORE = (
    "workspace_id",
    "version_number",
    "ui_schema",
    "theme",
    "design",
    "description",
    "source",
    "created_at",
)


def _immutability_function(columns: Sequence[str]) -> str:
    changed = "\n        OR ".join(f"NEW.{c} IS DISTINCT FROM OLD.{c}" for c in columns)
    return f"""
CREATE OR REPLACE FUNCTION ui_versions_reject_content_update() RETURNS trigger AS $$
BEGIN
    IF {changed}
    THEN
        RAISE EXCEPTION 'ui_versions rows are immutable'
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""


def _timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    jsonb = postgresql.JSONB(astext_type=sa.Text())

    op.add_column("ui_versions", sa.Column("application", jsonb, nullable=True))
    # The application is part of a version's content, so it is immutable too.
    op.execute(_immutability_function([*_GUARDED_BEFORE, "application"]))

    op.create_table(
        "workspace_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("entity", sa.String(length=64), nullable=False),
        sa.Column("record_key", sa.String(length=128), nullable=False),
        sa.Column("data", jsonb, nullable=False),
        sa.Column("deleted", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_workspace_records_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workspace_records")),
        sa.UniqueConstraint(
            "workspace_id", "entity", "record_key", name="uq_workspace_records_workspace_id_entity"
        ),
    )
    op.create_index(
        op.f("ix_workspace_records_workspace_id"), "workspace_records", ["workspace_id"]
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("alt", sa.String(length=200), nullable=False),
        sa.Column("attribution", sa.String(length=200), nullable=True),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_assets_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_assets")),
    )
    op.create_index(op.f("ix_assets_workspace_id"), "assets", ["workspace_id"])

    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("options", jsonb, nullable=False),
        sa.Column("base_version_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("detail", sa.String(length=300), nullable=True),
        sa.Column("result", jsonb, nullable=True),
        sa.Column("error", jsonb, nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_generation_jobs_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_generation_jobs_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generation_jobs")),
    )
    op.create_index(
        "ix_generation_jobs_workspace_id_created_at",
        "generation_jobs",
        ["workspace_id", "created_at"],
    )


def downgrade() -> None:
    """Drops application data. Versions that are applications lose their application
    section and can no longer be displayed, so only downgrade an unused installation."""
    op.drop_index("ix_generation_jobs_workspace_id_created_at", table_name="generation_jobs")
    op.drop_table("generation_jobs")
    op.drop_index(op.f("ix_assets_workspace_id"), table_name="assets")
    op.drop_table("assets")
    op.drop_index(op.f("ix_workspace_records_workspace_id"), table_name="workspace_records")
    op.drop_table("workspace_records")
    op.execute(_immutability_function(_GUARDED_BEFORE))
    op.drop_column("ui_versions", "application")
