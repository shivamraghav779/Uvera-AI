"""workspaces and immutable ui versions

Sessions become workspaces and UI states become immutable UI versions with a
parent chain, theme and design configuration. Stored UI schemas are upgraded
from schema 1.0 (section-level layout) to 2.0 (per-component layout spans).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-05
"""

import json
from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Frozen copies of the defaults at the time of this migration (blue_white + modern_minimal).
DEFAULT_THEME = {
    "preset": "blue_white",
    "mode": "light",
    "colors": {
        "primary": "#2563EB",
        "secondary": "#64748B",
        "background": "#F8FAFC",
        "surface": "#FFFFFF",
        "foreground": "#0F172A",
        "muted": "#F1F5F9",
        "border": "#E2E8F0",
        "destructive": "#DC2626",
        "success": "#16A34A",
        "warning": "#D97706",
    },
    "radius": "md",
    "density": "comfortable",
    "spacing": "normal",
    "shadows": "none",
    "typography": {"font": "sans", "scale": "md"},
}
DEFAULT_DESIGN = {"framework": "shadcn", "design_system": "modern_minimal"}
GRID_COLUMNS = 12

RENAMES = (
    # (kind, old name, new name, table after rename)
    ("INDEX", "pk_sessions", "pk_workspaces", None),
    ("INDEX", "ix_sessions_user_id", "ix_workspaces_user_id", None),
    ("CONSTRAINT", "fk_sessions_user_id_users", "fk_workspaces_user_id_users", "workspaces"),
    ("INDEX", "pk_ui_states", "pk_ui_versions", None),
    ("CONSTRAINT", "fk_ui_states_session_id_sessions", "fk_ui_versions_workspace_id_workspaces", "ui_versions"),
    ("CONSTRAINT", "uq_ui_states_session_id_version", "uq_ui_versions_workspace_id_version_number", "ui_versions"),
    ("INDEX", "ix_conversations_session_id_created_at", "ix_conversations_workspace_id_created_at", None),
    ("CONSTRAINT", "fk_conversations_session_id_sessions", "fk_conversations_workspace_id_workspaces", "conversations"),
    ("INDEX", "ix_ui_actions_session_id_created_at", "ix_ui_actions_workspace_id_created_at", None),
    ("CONSTRAINT", "fk_ui_actions_session_id_sessions", "fk_ui_actions_workspace_id_workspaces", "ui_actions"),
)

IMMUTABILITY_FUNCTION = """
CREATE FUNCTION ui_versions_reject_content_update() RETURNS trigger AS $$
BEGIN
    IF NEW.workspace_id IS DISTINCT FROM OLD.workspace_id
        OR NEW.version_number IS DISTINCT FROM OLD.version_number
        OR NEW.ui_schema IS DISTINCT FROM OLD.ui_schema
        OR NEW.theme IS DISTINCT FROM OLD.theme
        OR NEW.design IS DISTINCT FROM OLD.design
        OR NEW.description IS DISTINCT FROM OLD.description
        OR NEW.source IS DISTINCT FROM OLD.source
        OR NEW.created_at IS DISTINCT FROM OLD.created_at
    THEN
        RAISE EXCEPTION 'ui_versions rows are immutable'
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
IMMUTABILITY_TRIGGER = """
CREATE TRIGGER ui_versions_immutable
    BEFORE UPDATE ON ui_versions
    FOR EACH ROW EXECUTE FUNCTION ui_versions_reject_content_update();
"""


def _rename(kind: str, old: str, new: str, table: str | None) -> None:
    if kind == "INDEX":
        op.execute(f"ALTER INDEX {old} RENAME TO {new}")
    else:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {old} TO {new}")


def _upgrade_node(node: dict[str, Any]) -> None:
    """Schema 1.0 -> 2.0: a section's layout mode becomes spans on its children."""
    children = node.get("children") or node.get("components") or node.get("fields") or []
    if node.get("type") == "section":
        mode, columns = node.pop("layout", "stack"), node.pop("columns", None)
        if mode == "grid" and columns:
            span = GRID_COLUMNS // int(columns)
        elif mode == "row" and children:
            span = max(GRID_COLUMNS // len(children), 1)
        else:
            span = GRID_COLUMNS
        for child in children:
            child["layout"] = {"span": span, "height": "auto"}
    for child in children:
        _upgrade_node(child)
    for tab in node.get("tabs") or []:
        for child in tab.get("children") or []:
            _upgrade_node(child)


def _upgrade_stored_schemas() -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, ui_schema FROM ui_versions")).fetchall()
    for row in rows:
        schema = row.ui_schema if isinstance(row.ui_schema, dict) else json.loads(row.ui_schema)
        _upgrade_node(schema)
        connection.execute(
            sa.text("UPDATE ui_versions SET ui_schema = CAST(:schema AS jsonb) WHERE id = :id"),
            {"schema": json.dumps(schema), "id": row.id},
        )


def upgrade() -> None:
    op.rename_table("sessions", "workspaces")
    op.rename_table("ui_states", "ui_versions")
    op.alter_column("ui_versions", "session_id", new_column_name="workspace_id")
    op.alter_column("ui_versions", "version", new_column_name="version_number")
    op.alter_column("conversations", "session_id", new_column_name="workspace_id")
    op.alter_column("ui_actions", "session_id", new_column_name="workspace_id")
    for rename in RENAMES:
        _rename(*rename)

    jsonb = postgresql.JSONB(astext_type=sa.Text())
    op.add_column("conversations", sa.Column("details", jsonb, nullable=True))

    op.add_column("ui_versions", sa.Column("parent_version_id", sa.Uuid(), nullable=True))
    op.add_column(
        "ui_versions",
        sa.Column("theme", jsonb, nullable=False, server_default=json.dumps(DEFAULT_THEME)),
    )
    op.add_column(
        "ui_versions",
        sa.Column("design", jsonb, nullable=False, server_default=json.dumps(DEFAULT_DESIGN)),
    )
    op.add_column(
        "ui_versions",
        sa.Column(
            "description", sa.String(length=300), nullable=False, server_default="Generated UI"
        ),
    )
    op.add_column(
        "ui_versions",
        sa.Column("source", sa.String(length=32), nullable=False, server_default="ai_generation"),
    )
    op.add_column(
        "ui_versions",
        sa.Column("source_metadata", jsonb, nullable=False, server_default="{}"),
    )
    op.add_column("ui_versions", sa.Column("created_by", sa.Uuid(), nullable=True))
    # Defaults only existed to back-fill existing rows.
    for column in ("theme", "design", "description", "source", "source_metadata"):
        op.alter_column("ui_versions", column, server_default=None)
    op.create_foreign_key(
        op.f("fk_ui_versions_parent_version_id_ui_versions"),
        "ui_versions",
        "ui_versions",
        ["parent_version_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_ui_versions_created_by_users"),
        "ui_versions",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("workspaces", sa.Column("current_version_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_workspaces_current_version_id_ui_versions"),
        "workspaces",
        "ui_versions",
        ["current_version_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Back-fill: link each version to its predecessor and point workspaces at their latest.
    op.execute(
        """
        UPDATE ui_versions AS child SET parent_version_id = parent.id
        FROM ui_versions AS parent
        WHERE parent.workspace_id = child.workspace_id
          AND parent.version_number = child.version_number - 1
        """
    )
    op.execute(
        """
        UPDATE workspaces SET current_version_id = latest.id
        FROM (
            SELECT DISTINCT ON (workspace_id) id, workspace_id
            FROM ui_versions ORDER BY workspace_id, version_number DESC
        ) AS latest
        WHERE latest.workspace_id = workspaces.id
        """
    )
    _upgrade_stored_schemas()

    op.execute(IMMUTABILITY_FUNCTION)
    op.execute(IMMUTABILITY_TRIGGER)


def downgrade() -> None:
    """Structural downgrade. Stored UI schemas stay in 2.0 form."""
    op.execute("DROP TRIGGER ui_versions_immutable ON ui_versions")
    op.execute("DROP FUNCTION ui_versions_reject_content_update()")

    op.drop_constraint(
        op.f("fk_workspaces_current_version_id_ui_versions"), "workspaces", type_="foreignkey"
    )
    op.drop_column("workspaces", "current_version_id")
    op.drop_constraint(op.f("fk_ui_versions_created_by_users"), "ui_versions", type_="foreignkey")
    op.drop_constraint(
        op.f("fk_ui_versions_parent_version_id_ui_versions"), "ui_versions", type_="foreignkey"
    )
    for column in (
        "created_by",
        "source_metadata",
        "source",
        "description",
        "design",
        "theme",
        "parent_version_id",
    ):
        op.drop_column("ui_versions", column)
    op.drop_column("conversations", "details")

    for kind, old, new, table in reversed(RENAMES):
        _rename(kind, new, old, table)
    op.alter_column("ui_actions", "workspace_id", new_column_name="session_id")
    op.alter_column("conversations", "workspace_id", new_column_name="session_id")
    op.alter_column("ui_versions", "version_number", new_column_name="version")
    op.alter_column("ui_versions", "workspace_id", new_column_name="session_id")
    op.rename_table("ui_versions", "ui_states")
    op.rename_table("workspaces", "sessions")
