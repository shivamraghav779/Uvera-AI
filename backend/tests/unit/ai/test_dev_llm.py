"""The scripted development model answers every stage the product can ask it."""

import json

from scripts import dev_llm, sample_app
from tests.support import sample_application


def _ask(system: str, **blocks: str) -> dict[str, object]:
    prompt = "\n\n".join(f"{title}\n{body}" for title, body in blocks.items())
    reply = dev_llm.reply_to(
        [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    )
    return json.loads(reply)  # type: ignore[no-any-return]


def test_a_product_idea_gets_the_application_and_a_view_request_does_not() -> None:
    architect = "You are the product architect of a Generative Application Engine."

    app = _ask(architect, **{"User idea": "Build me a modern AI recruitment SaaS."})
    view = _ask(architect, **{"User idea": "Create a light sales dashboard with revenue."})

    assert (app["scope"], app["name"]) == ("application", "Hirewell")
    assert view["scope"] == "single_view"


def test_edit_requests_are_routed_by_their_wording() -> None:
    router = "You route an edit request for an existing application to the right level."
    outline = "- screen dashboard “Dashboard” (dashboard, route /): a\n- screen jobs “Jobs”: b"

    def intent(request: str) -> tuple[object, object]:
        route = _ask(router, **{"Application outline": outline, "User request": request})
        return route["intent"], route.get("screen_id")

    assert intent("Redesign the dashboard") == ("redesign_screen", "dashboard")
    assert intent("Make the entire application more premium") == ("restyle", None)
    assert intent("Add an offers section") == ("add_screen", None)
    assert intent("Go back to the original version") == ("edit", None)
    assert intent("Make this half width") == ("edit", None)


async def test_component_edits_work_on_the_current_screen_of_an_application() -> None:
    document = await sample_application()
    candidates = next(s for s in document["page"]["components"] if s["id"] == "candidates")

    reply = _ask(
        "You are the editing engine of a Generative UI workspace.",
        **{
            "Current screen": json.dumps(candidates),
            "Version history (newest first)": "- version 1 (current): Generated",
            "Selected component": "candidates_candidate_list",
            "User request": "Make this half width",
        },
    )

    assert reply["operations"] == [
        {"type": "RESIZE", "target": "candidates_candidate_list", "span": 6}
    ]


def test_the_original_version_is_the_first_one() -> None:
    reply = _ask(
        "You are the editing engine of a Generative UI workspace.",
        **{
            "Current screen": json.dumps({"id": "s", "children": []}),
            "Version history (newest first)": (
                "- version 3 (current): x\n- version 2: y\n- version 1: z"
            ),
            "Selected component": "(none)",
            "User request": "Go back to the original version",
        },
    )

    assert reply["operations"] == [{"type": "RESTORE_VERSION", "version_number": 1}]


def test_every_scripted_screen_has_a_plan_and_children() -> None:
    planned = {screen["id"] for screen in sample_app.BLUEPRINT["screens"]}

    assert planned <= sample_app.SCREEN_PLANS.keys()
    assert planned <= sample_app.SCREENS.keys()
