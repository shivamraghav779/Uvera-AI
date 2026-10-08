"""The generation pipeline: stages in order, contained failures, bounded refinement."""

import json
import uuid
from collections.abc import Sequence
from typing import Any

import pytest

from app.ai.llm.base import GenerationOptions, LLMMessage, LLMResponse
from app.ai.orchestration.application.runner import StageRunner, reject
from app.ai.prompts.base import PromptTemplate
from app.core.exceptions import (
    LLMException,
    LLMFailureKind,
    LLMProvidersExhaustedException,
    UIGenerationException,
)
from app.domains.generative_ui.contracts import ApplicationBuildInput, ApplicationBuildOutput
from app.domains.generative_ui.document import dump_document
from scripts import sample_app
from scripts.sample_build import (
    SAMPLE_WORKSPACE_ID,
    MemoryAssetRepository,
    ScriptedStageLLM,
    build_stack,
    offline_settings,
)

PROMPT = PromptTemplate(name="test_stage", version="9.9.9", system="Return JSON.")
GENERATOR = "You are a senior product designer"


class StageLLM(ScriptedStageLLM):
    """The scripted application, with answers that can be overridden per stage."""

    def __init__(self) -> None:
        super().__init__()
        self.overrides: dict[str, list[str | Exception]] = {}
        self.prompts: list[tuple[str, str]] = []

    def override(self, opening: str, *answers: str | Exception) -> None:
        self.overrides.setdefault(opening, []).extend(answers)

    def _answer(self, messages: Sequence[LLMMessage]) -> LLMResponse:
        system, prompt = messages[0].content, messages[1].content
        self.prompts.append((system, messages[-1].content))
        for opening, answers in self.overrides.items():
            if system.startswith(opening) and answers:
                answer = answers.pop(0)
                if isinstance(answer, Exception):
                    raise answer
                self.stages.append(system.split(".")[0])
                return LLMResponse(content=answer, provider=self.name, model=self.model)
        del prompt
        return super()._answer(messages)


def _request(
    idea: str = "Build me a recruitment platform", **overrides: Any
) -> ApplicationBuildInput:
    values: dict[str, Any] = {
        "user_request": idea,
        "workspace_id": SAMPLE_WORKSPACE_ID,
        "history": (),
        "datasets": (),
        "framework": "shadcn",
        "design_system": None,
        "theme_preset": None,
    }
    return ApplicationBuildInput(**(values | overrides))


def _count(llm: StageLLM, opening: str) -> int:
    return sum(stage.startswith(opening) for stage in llm.stages)


async def _build(llm: StageLLM, **settings: Any) -> ApplicationBuildOutput:
    stack = build_stack(llm, settings=offline_settings(**settings))
    return await stack.builder.build(_request())


async def test_every_stage_runs_once_and_screens_once_each() -> None:
    llm = StageLLM()

    output = await _build(llm)

    planning = [stage for stage in llm.stages if not stage.startswith(GENERATOR)]
    names = [stage.split(" of ")[0].split(":")[0] for stage in planning]
    assert names[0] == "You are the product architect", "understanding comes first"
    # Sample data is written while the design is decided, so the order in between varies.
    assert sorted(names) == sorted(
        [
            "You are the product architect",
            "You are the design director",
            "You write the sample data",
            "You write the sample data",  # four entities are filled in two calls
            "You are the visual composition planner",
            "You plan what people can do in an application",
            "You are the art director",
        ]
    )
    assert _count(llm, GENERATOR) == len(sample_app.BLUEPRINT["screens"])
    assert output.document is not None and output.failed_screen_ids == ()
    assert output.quality_score is not None and output.quality_score >= 90


async def test_a_request_for_one_view_is_handed_back_without_building() -> None:
    llm = StageLLM()
    stack = build_stack(llm)

    output = await stack.builder.build(_request("Show revenue by region as a chart"))

    assert output.document is None
    assert len(llm.stages) == 1, "only product understanding ran"


async def test_progress_follows_the_real_stages_in_order() -> None:
    seen: list[tuple[str, int]] = []

    async def progress(stage: str, percent: int, _detail: str | None) -> None:
        seen.append((stage, percent))

    stack = build_stack(StageLLM())
    await stack.builder.build(_request(progress=progress))

    order = list(dict.fromkeys(stage for stage, _ in seen))
    assert order == [
        "understanding", "planning", "designing", "generating_assets", "generating_screens",
        "assembling", "validating",
    ]  # fmt: skip
    assert [percent for _, percent in seen] == sorted(percent for _, percent in seen)
    assert seen[-1][1] < 100, "ready is reported by whoever stores the result"


async def test_a_screen_that_cannot_be_generated_becomes_a_marked_stand_in() -> None:
    llm = StageLLM()
    # The pipeline screen is unusable; with no repair attempts it fails.
    llm.override(GENERATOR, json.dumps({"children": [{"type": "hologram", "id": "x"}]}))

    output = await _build(llm, app_screen_concurrency=1)

    assert output.failed_screen_ids == ("dashboard",), "screens are generated in order"
    document = dump_document(output.document)  # type: ignore[arg-type]
    dashboard = document["page"]["components"][0]
    assert dashboard["children"][0]["type"] == "alert"
    assert "regenerate “Dashboard”" in dashboard["children"][0]["message"]
    assert len(document["page"]["components"]) == 7, "the rest of the application is intact"


async def test_invalid_screen_output_is_sent_back_with_the_findings() -> None:
    llm = StageLLM()
    llm.override(GENERATOR, json.dumps({"children": [{"type": "hologram", "id": "x"}]}))

    output = await _build(llm, llm_max_repair_attempts=1, app_screen_concurrency=1)

    assert output.failed_screen_ids == ()
    assert output.repair_attempts == 1
    repair = next(prompt for system, prompt in llm.prompts if "was rejected" in prompt)
    assert "Unknown type 'hologram'" in repair


async def test_nothing_is_returned_when_no_screen_can_be_generated() -> None:
    llm = StageLLM()
    llm.override(GENERATOR, *(["not json"] * 7))

    with pytest.raises(UIGenerationException, match="None of the application's screens"):
        await _build(llm, app_screen_concurrency=1)


async def test_images_are_optional_a_failing_asset_stage_is_skipped() -> None:
    llm = StageLLM()
    llm.override("You are the art director", "not json")

    output = await _build(llm)

    assert output.document is not None and output.document.application is not None
    assert output.document.application.assets == []
    media = dump_document(output.document)["page"]["components"][0]["children"][-1]
    assert "image" not in media, "a component never points at an image that does not exist"


async def test_no_images_are_planned_when_imagery_is_switched_off() -> None:
    llm = StageLLM()

    output = await _build(llm, app_max_assets=0)

    assert _count(llm, "You are the art director") == 0
    assert output.document.application.assets == []  # type: ignore[union-attr]


async def test_look_preferences_override_the_design_director() -> None:
    stack = build_stack(StageLLM())

    output = await stack.builder.build(
        _request(design_system="editorial", theme_preset="warm_sand", framework="material")
    )

    document = output.document
    assert document is not None
    assert document.design.model_dump() == {"framework": "material", "design_system": "editorial"}
    assert document.theme.preset == "warm_sand"


async def test_a_weak_draft_is_refined_once_with_the_review_as_brief() -> None:
    llm = StageLLM()
    weak = [{"type": "table", "id": "t", "title": "Lorem ipsum",
             "columns": [{"key": "title", "label": "Role"}], "data_source": {"dataset": "jobs"}},
            {"type": "text", "id": "note", "content": "Feature 1"}]  # fmt: skip
    llm.override(GENERATOR, json.dumps({"children": weak}))
    stack = build_stack(
        llm, settings=offline_settings(app_refinement_passes=1, app_screen_concurrency=1)
    )

    output = await stack.builder.build(_request())

    review = next(p for s, p in llm.prompts if "Design review of your previous draft" in p)
    assert "Placeholder wording found" in review and "opens with a table" in review
    assert _count(llm, GENERATOR) == 8, "seven screens and one refinement"
    dashboard = dump_document(output.document)["page"]["components"][0]  # type: ignore[arg-type]
    assert dashboard["children"][0]["type"] == "stats", "the refined screen replaced the draft"
    assert output.quality_score is not None and output.quality_score >= 90


async def test_stored_images_are_referenced_by_application_urls_only() -> None:
    assets = MemoryAssetRepository()
    stack = build_stack(StageLLM(), assets=assets)

    output = await stack.builder.build(_request())

    [stored] = assets.assets
    [reference] = output.document.application.assets  # type: ignore[union-attr]
    assert reference.url == f"/api/v1/assets/{stored.id}/content"
    assert (stored.provider, stored.content_type) == ("internal", "image/svg+xml")
    assert stored.workspace_id == SAMPLE_WORKSPACE_ID
    assert b"<script" not in stored.content


# --- The stage runner ----------------------------------------------------------------------


def _messages() -> list[LLMMessage]:
    return [LLMMessage("system", "Return JSON."), LLMMessage("user", "Go")]  # type: ignore[arg-type]


class _Queue(ScriptedStageLLM):
    def __init__(self, *answers: str | Exception) -> None:
        super().__init__()
        self.answers = list(answers)
        self.options: list[GenerationOptions | None] = []

    async def generate_structured(
        self, messages: Sequence[LLMMessage], options: GenerationOptions | None = None
    ) -> LLMResponse:
        self.options.append(options)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return LLMResponse(content=answer, provider="p", model="m")


def _runner(llm: _Queue, **kwargs: Any) -> StageRunner:
    waits: list[float] = kwargs.pop("waits", [])

    async def sleep(seconds: float) -> None:
        waits.append(seconds)

    return StageRunner(
        llm, options=GenerationOptions(max_tokens=100), max_repair_attempts=1, sleep=sleep, **kwargs
    )


def _parse(payload: object) -> int:
    assert isinstance(payload, dict)
    if "n" not in payload:
        raise reject("n", "The field 'n' is required.")
    return int(payload["n"])


async def test_runner_returns_the_parsed_value_and_who_answered() -> None:
    result = await _runner(_Queue('```json\n{"n": 4}\n```')).run(PROMPT, _messages(), _parse)

    assert (result.value, result.provider, result.model) == (4, "p", "m")
    assert (result.prompt_version, result.repair_attempts) == ("9.9.9", 0)


async def test_runner_repairs_once_then_gives_up_with_the_findings() -> None:
    repaired = await _runner(_Queue("{}", '{"n": 2}')).run(PROMPT, _messages(), _parse)
    assert (repaired.value, repaired.repair_attempts) == (2, 1)

    with pytest.raises(UIGenerationException) as error:
        await _runner(_Queue("oops", "{}")).run(PROMPT, _messages(), _parse)
    assert list(error.value.details) == [
        {"stage": "schema", "path": "n", "message": "The field 'n' is required."}
    ]


def _rate_limited() -> LLMException:
    return LLMException(provider="p", model="m", kind=LLMFailureKind.RATE_LIMITED, reason="429")


async def test_runner_waits_out_rate_limits_a_bounded_number_of_times() -> None:
    waits: list[float] = []
    exhausted = LLMProvidersExhaustedException(
        details=[
            {"kind": "rate_limited", "retry_after_seconds": 40.0},
            {"kind": "timeout"},
        ]
    )
    asked = LLMException(
        provider="p", model="m", kind=LLMFailureKind.RATE_LIMITED, reason="429",
        retry_after_seconds=30.0,
    )  # fmt: skip
    runner = _runner(
        _Queue(_rate_limited(), asked, exhausted, '{"n": 1}'),
        rate_limit_retries=3, rate_limit_wait_seconds=5, waits=waits,
    )  # fmt: skip

    result = await runner.run(PROMPT, _messages(), _parse)

    assert result.value == 1
    assert waits == [5, 30, 15], (
        "at least the configured wait, growing; longer when the provider asks; and when one "
        "provider only timed out there is no reason to wait for the rate-limited one"
    )

    stubborn = _runner(_Queue(_rate_limited(), _rate_limited()), rate_limit_retries=1)
    with pytest.raises(LLMException):
        await stubborn.run(PROMPT, _messages(), _parse)


async def test_runner_does_not_wait_for_failures_that_waiting_cannot_fix() -> None:
    waits: list[float] = []
    broken = LLMException(provider="p", model="m", kind=LLMFailureKind.AUTHENTICATION, reason="401")
    refused = LLMProvidersExhaustedException(details=[{"kind": "bad_request"}])
    for failure in (broken, refused):
        runner = _runner(
            _Queue(failure), rate_limit_retries=3, rate_limit_wait_seconds=5, waits=waits
        )
        with pytest.raises((LLMException, LLMProvidersExhaustedException)):
            await runner.run(PROMPT, _messages(), _parse)
    assert waits == []


async def test_short_stages_ask_for_a_smaller_output_budget() -> None:
    llm = _Queue('{"n": 1}', '{"n": 1}')
    runner = _runner(llm)

    await runner.limited_to(40).run(PROMPT, _messages(), _parse)
    await runner.limited_to(4000).run(PROMPT, _messages(), _parse)

    assert [options.max_tokens for options in llm.options if options] == [40, 100]


def test_workspace_id_of_the_sample_is_a_uuid() -> None:
    assert isinstance(SAMPLE_WORKSPACE_ID, uuid.UUID)


def test_existing_data_reaches_a_product_idea_only_when_the_idea_is_about_it() -> None:
    from app.ai.orchestration.application.pipeline import datasets_for
    from app.domains.data_sources.schemas import DatasetDescriptor

    sales = DatasetDescriptor(name="sales_by_region", description="Sales per region.", fields=[])
    tickets = DatasetDescriptor(name="tickets", description="Support tickets.", fields=[])
    both = [sales, tickets]

    # One view of what is there: everything is offered.
    assert datasets_for("Create a sales dashboard with revenue and orders.", both) == both
    assert datasets_for("Show revenue by product as a donut chart.", both) == both
    # A product gets its own data model.
    assert datasets_for("Build me a modern AI recruitment SaaS.", both) == []
    assert datasets_for("Create a premium website for an architecture studio.", both) == []
    assert datasets_for("Build a modern AI productivity SaaS for small teams.", both) == []
    # Unless it is about that data, or says to use the user's data.
    assert datasets_for("Build a sales analytics platform.", both) == [sales]
    assert datasets_for("Build a support app for our tickets.", both) == [tickets]
    assert datasets_for("Build an app around my data.", both) == both
