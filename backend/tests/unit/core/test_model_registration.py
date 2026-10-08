import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[3]

CHECK = """
import app.main
from app.database.base import Base

tables = Base.metadata.tables
for table in tables.values():
    for foreign_key in table.foreign_keys:
        foreign_key.column  # raises NoReferencedTableError when the target is not registered
print(",".join(sorted(tables)))
"""


def test_importing_the_application_registers_every_table() -> None:
    """Runs in a clean interpreter: the server must not rely on test or Alembic imports."""
    result = subprocess.run(
        [sys.executable, "-c", CHECK], cwd=BACKEND_ROOT, capture_output=True, text=True, check=False
    )

    assert result.returncode == 0, result.stderr
    assert (
        result.stdout.strip()
        == "assets,conversations,data_sources,generation_jobs,reference_components,"
        "ui_actions,ui_versions,users,workspace_records,workspaces"
    )
