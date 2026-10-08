"""A scripted stand-in for the Groq chat API, for local development and end-to-end tests.

    poetry run python -m scripts.dev_llm            # listens on 127.0.0.1:8787

    # backend/.env
    GROQ_API_KEY=dev
    GROQ_BASE_URL=http://127.0.0.1:8787

THIS IS NOT A LANGUAGE MODEL. It recognises a handful of phrases and answers with
the structured output a model would give:

    "Build me a modern AI recruitment SaaS"   a complete application (always the same
                                              one: see scripts/sample_app.py)
    "Redesign the dashboard", "Make the entire application more premium",
    "Add an offers section"                    screen- and application-level edits
    "Create a sales dashboard ..."             a single view over the demo data
    "make it dark", "move the revenue card to the top right", "replace the table
    with a bar chart", "go back to version 2", ...   component-level edits
 It exists so the whole product — proposals, previews, versions, restore —
can be exercised without credentials. Its replies still pass through the real
validation pipeline, exactly like a model's.
"""

import json
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from scripts import sample_app
from scripts.export_contract import SAMPLE_PAGE

HOST, PORT = "127.0.0.1", 8787

FEEDBACK_PAGE: dict[str, Any] = {
    "type": "page",
    "title": "Feedback",
    "components": [
        {"type": "text", "id": "intro_text", "content": "Tell us how we are doing."},
        {
            "type": "form",
            "id": "feedback_form",
            "title": "Your feedback",
            "layout": {"span": 6},
            "fields": [
                {
                    "type": "input",
                    "id": "name_input",
                    "name": "name",
                    "label": "Name",
                    "required": True,
                },
                {
                    "type": "input",
                    "id": "email_input",
                    "name": "email",
                    "label": "Email",
                    "input_type": "email",
                },
                {
                    "type": "input",
                    "id": "comments_input",
                    "name": "comments",
                    "label": "Comments",
                    "input_type": "textarea",
                },
                {
                    "type": "checkbox",
                    "id": "contact_checkbox",
                    "name": "contact_me",
                    "label": "You may contact me about this",
                },
            ],
            "submit_action": {"type": "submit", "payload": {"form_id": "feedback_form"}},
            "submit_label": "Send feedback",
        },
    ],
}

THEME_WORDS = (
    ("dark", "slate_dark"),
    ("violet", "violet_night"),
    ("futuristic", "violet_night"),
    ("emerald", "emerald"),
    ("green", "emerald"),
    ("sand", "warm_sand"),
    ("warm", "warm_sand"),
    ("mono", "mono_minimal"),
    ("minimal", "mono_minimal"),
    ("blue", "blue_white"),
    ("light", "blue_white"),
)
HELP = (
    "I'm the scripted development stand-in, not a real model. Try: “make it dark”, "
    "“move the revenue card to the top right”, “replace the table with a bar chart”, "
    "“add a region filter”, “use a compact design”, “use a Material style”, "
    "“go back to version 2” or “compare with version 1”."
)


def _section(content: str, title: str) -> str:
    """Text of one titled block of the prompt (blocks are separated by blank lines)."""
    match = re.search(
        rf"(?:^|\n\n){re.escape(title)}\n(.*?)(?=\n\n[A-Z][^\n]*\n|\Z)", content, re.S
    )
    return match.group(1).strip() if match else ""


def _walk(node: dict[str, Any]) -> list[dict[str, Any]]:
    children = node.get("components") or node.get("children") or []
    if node.get("type") == "form":
        children = node.get("fields", [])
    nested = [child for tab in node.get("tabs", []) for child in tab.get("children", [])]
    found = []
    for child in [*children, *nested]:
        found.append(child)
        found.extend(_walk(child))
    return found


def _first(page: dict[str, Any], kind: str) -> dict[str, Any] | None:
    return next((node for node in _walk(page) if node["type"] == kind), None)


def _first_row(page: dict[str, Any]) -> list[dict[str, Any]]:
    row, used = [], 0
    for component in page["components"]:
        span = component.get("layout", {}).get("span", 12)
        if row and used + span > 12:
            break
        row.append(component)
        used += span
    return row


def _version_request(request: str, versions: str) -> tuple[str, dict[str, Any]] | None:
    numbers = [int(n) for n in re.findall(r"^- version (\d+)", versions, re.M)]
    current = max(numbers, default=1)
    named = re.search(r"version\s+(\d+)", request)
    if "compare" in request:
        target = int(named.group(1)) if named else max(current - 1, 1)
        return (
            f"Here is what changed since version {target}.",
            {"type": "COMPARE_VERSIONS", "version_number": target},
        )
    if not re.search(r"go back|restore|undo|revert", request):
        return None
    if named:
        target = int(named.group(1))
    elif re.search(r"\boriginal\b|\bfirst version\b", request):
        target = min(numbers, default=1)
    elif "before" in request and "table" in request:
        replaced = re.search(r"^- version (\d+)[^\n]*: Replace", versions, re.M)
        target = int(replaced.group(1)) - 1 if replaced else current - 1
    else:
        target = current - 1
    return (
        f"I'll restore version {target}. The versions after it stay in the history.",
        {"type": "RESTORE_VERSION", "version_number": target},
    )


def _table_to_chart(table: dict[str, Any]) -> dict[str, Any]:
    keys = [column["key"] for column in table["columns"]]
    chart = {
        "type": "chart",
        "id": table["id"],
        "chart_type": "bar",
        "x_key": keys[0],
        "y_keys": keys[1:2] or keys[:1],
    }
    for key in ("title", "data_source"):
        if key in table:
            chart[key] = table[key]
    return chart


def _edits(
    request: str, page: dict[str, Any], selected: str | None
) -> tuple[str, list[dict[str, Any]]]:
    operations: list[dict[str, Any]] = []
    notes: list[str] = []
    table, chart = _first(page, "table"), _first(page, "chart")
    metrics = [node for node in page["components"] if node["type"] == "metric"]

    if "material" in request:
        operations += [
            {"type": "SET_FRAMEWORK", "framework": "material"},
            {"type": "SET_DESIGN_SYSTEM", "design_system": "material"},
        ]
        notes.append("render it with the Material adapter")
    elif "compact" in request:
        operations.append({"type": "SET_DESIGN_SYSTEM", "design_system": "compact_pro"})
        notes.append("switch to the compact design system")
    else:
        for word, preset in THEME_WORDS:
            if re.search(rf"\b{word}\b", request):
                operations.append({"type": "SET_THEME", "preset": preset})
                notes.append(f"change the theme to {preset.replace('_', ' ')}")
                break

    if "revenue" in request and re.search(r"move|right", request):
        row = _first_row(page)
        target = next((node for node in page["components"] if "revenue" in node["id"]), None)
        if target and row and row[-1]["id"] != target["id"]:
            operations.append({"type": "MOVE", "target": target["id"], "after": row[-1]["id"]})
            notes.append("move Revenue to the top right")
    if table and "table" in request and re.search(r"replace|turn|convert", request):
        operations.append(
            {"type": "REPLACE", "target": table["id"], "component": _table_to_chart(table)}
        )
        notes.append("replace the table with a bar chart of the same data")
    if table and chart and "above the table" in request:
        operations.append({"type": "MOVE", "target": chart["id"], "before": table["id"]})
        notes.append("put the chart above the table")
    if "filter" in request and "add" in request and not _first(page, "select") and table:
        operations.append(
            {
                "type": "CREATE",
                "before": table["id"],
                "component": {
                    "type": "select",
                    "id": "region_filter",
                    "name": "region",
                    "label": "Region",
                    "layout": {"span": 4},
                    "options": [
                        {"label": r, "value": r} for r in ("North", "South", "East", "West")
                    ],
                    "on_change": {
                        "type": "filter",
                        "payload": {
                            "dataset": "sales_by_region",
                            "field": "region",
                            "target": table["id"],
                        },
                    },
                },
            }
        )
        notes.append("add a region filter")
    if "one row" in request and metrics:
        span = max(12 // len(metrics), 1)
        operations += [{"type": "RESIZE", "target": m["id"], "span": span} for m in metrics]
        notes.append("put the metrics in one row")

    if selected:
        if re.search(r"remove|delete", request):
            operations.append({"type": "DELETE", "target": selected})
            notes.append("remove the selected component")
        if "half" in request:
            operations.append({"type": "RESIZE", "target": selected, "span": 6})
            notes.append("make the selected component half width")
        if re.search(r"wider|full width", request):
            operations.append({"type": "RESIZE", "target": selected, "span": 12})
            notes.append("make the selected component full width")
        if "top" in request and "move" in request:
            operations.append(
                {"type": "MOVE", "target": selected, "parent_id": page["id"], "index": 0}
            )
            notes.append("move the selected component to the top")
        for chart_type in ("bar", "line", "area", "pie", "donut"):
            if f"{chart_type} chart" in request:
                operations.append(
                    {"type": "UPDATE", "target": selected, "props": {"chart_type": chart_type}}
                )
                notes.append(f"show it as a {chart_type} chart")

    if not operations:
        return HELP, []
    return f"I'll {', '.join(notes)}.", operations


def _current_page(prompt: str) -> dict[str, Any]:
    """The component tree an edit request is about: a single view, or one screen of an
    application presented the way a page is (children under ``components``)."""
    single = _section(prompt, "Current UI")
    if single:
        return json.loads(single)  # type: ignore[no-any-return]
    screen = json.loads(_section(prompt, "Current screen"))
    return {**screen, "components": screen.get("children", [])}


def reply_to(messages: list[dict[str, str]]) -> str:
    system = messages[0]["content"]
    # On a repair turn the original prompt is still the first user message.
    prompt = next(message["content"] for message in messages if message["role"] == "user")
    staged = sample_app.reply(system, prompt)
    if staged is not None:
        return staged
    request = _section(prompt, "User request").lower()

    if system.startswith("You analyse a user's request"):
        form = bool(re.search(r"form|feedback", request))
        return json.dumps(
            {
                "intent": "data_entry" if form else "overview",
                "title": "Feedback" if form else "Sales Dashboard",
                "required_data": []
                if form
                else ["sales_summary", "sales_by_month", "sales_by_product", "sales_by_region"],
            }
        )

    if "interface designer" in system:
        preset = next((p for word, p in THEME_WORDS if re.search(rf"\b{word}\b", request)), None)
        page = FEEDBACK_PAGE if re.search(r"form|feedback", request) else SAMPLE_PAGE
        return json.dumps({"theme_preset": preset, "page": page})

    version = _version_request(request, _section(prompt, "Version history (newest first)"))
    if version:
        return json.dumps({"message": version[0], "operations": [version[1]]})
    page = _current_page(prompt)
    selected = _section(prompt, "Selected component")
    message, operations = _edits(request, page, None if selected == "(none)" else selected)
    return json.dumps({"message": message, "operations": operations})


STREAM_CHUNK_CHARACTERS = 48


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        content = reply_to(body["messages"])
        if body.get("stream"):
            self._send_stream(content)
        else:
            self._send_json(content)

    def _send_json(self, content: str) -> None:
        payload = json.dumps(
            {
                "choices": [{"message": {"role": "assistant", "content": content}}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0},
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_stream(self, content: str) -> None:
        """OpenAI-style server-sent events, a few characters at a time."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for start in range(0, len(content), STREAM_CHUNK_CHARACTERS):
            piece = content[start : start + STREAM_CHUNK_CHARACTERS]
            event = {"choices": [{"delta": {"content": piece}}]}
            self.wfile.write(f"data: {json.dumps(event)}\n\n".encode())
            self.wfile.flush()
            time.sleep(0.01)
        self.wfile.write(b"data: [DONE]\n\n")

    def log_message(self, *_: object) -> None:
        return


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    print(f"Scripted LLM stand-in (not a real model) on http://{HOST}:{port}")
    ThreadingHTTPServer((HOST, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
