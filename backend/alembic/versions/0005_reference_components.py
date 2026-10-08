"""reference components: source code of published UI components, kept as design reference

``reference_components`` is filled by ``python -m scripts.import_references`` from
open-source registries and, with an API key, from 21st.dev. It is reading material
only: nothing in it is rendered, executed or shown to the model.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    jsonb = postgresql.JSONB(astext_type=sa.Text())
    op.create_table(
        "reference_components",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", jsonb, nullable=False),
        sa.Column("author", sa.String(length=200), nullable=True),
        sa.Column("license", sa.String(length=64), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("preview_url", sa.String(length=500), nullable=True),
        sa.Column("dependencies", jsonb, nullable=False),
        sa.Column("registry_dependencies", jsonb, nullable=False),
        sa.Column("files", jsonb, nullable=False),
        sa.Column("file_count", sa.Integer(), nullable=False),
        sa.Column("code_size", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_revision", sa.String(length=64), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reference_components")),
        sa.UniqueConstraint("source", "slug", name=op.f("uq_reference_components_source")),
    )
    op.create_index(op.f("ix_reference_components_source"), "reference_components", ["source"])
    op.create_index(
        op.f("ix_reference_components_category"), "reference_components", ["category"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_reference_components_category"), table_name="reference_components")
    op.drop_index(op.f("ix_reference_components_source"), table_name="reference_components")
    op.drop_table("reference_components")
