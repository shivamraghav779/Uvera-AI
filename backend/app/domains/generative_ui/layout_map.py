"""Describes where components end up in the 12-column flow grid.

Given to the model so that requests like "top right" or "in one row" can be
reasoned about without it simulating the grid itself.
"""

from app.domains.generative_ui.mutation_engine import Node, iter_slots
from app.domains.generative_ui.schemas import GRID_COLUMNS


def _span(node: Node) -> int:
    return int((node.get("layout") or {}).get("span", GRID_COLUMNS))


def flow_rows(children: list[Node]) -> list[list[Node]]:
    """Split children into the rows the flow grid produces."""
    rows: list[list[Node]] = []
    used = GRID_COLUMNS
    for child in children:
        span = _span(child)
        if used + span > GRID_COLUMNS:
            rows.append([])
            used = 0
        rows[-1].append(child)
        used += span
    return rows


def render_layout_map(page: Node) -> str:
    lines: list[str] = []
    for slot_id, children in iter_slots(page):
        lines.append(f"{slot_id}:")
        for number, row in enumerate(flow_rows(children), start=1):
            cells = ", ".join(
                f"{child['id']} ({child['type']}, span {_span(child)})" for child in row
            )
            lines.append(f"  row {number}: {cells}")
    return "\n".join(lines)
