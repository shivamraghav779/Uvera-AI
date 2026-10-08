/**
 * A generated application at run time: routing between its screens, data
 * bindings, the actions that move the user and change records, and the shell
 * around it. Uses the backend's scripted sample application ("Hirewell").
 */
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ApplicationSummary } from "@/features/chat/ApplicationSummary";
import { BUILD_STAGES, jobText, stageStates } from "@/features/generation/stages";
import { currentItem } from "@/generative-ui/components/application/AppShell";
import { supportedComponentTypes } from "@/generative-ui/registry/componentRegistry";
import { supportedEffects } from "@/generative-ui/registry/effectRegistry";
import { iconNames, resolveIcon } from "@/generative-ui/registry/iconRegistry";
import { recordPayload, resolveDestination } from "@/generative-ui/renderer/actionRuntime";
import type { AppRuntime } from "@/generative-ui/renderer/RendererContext";
import { activeScreenId, defaultParams, locate } from "@/generative-ui/runtime/appRuntime";
import { fillRoute, imageRefs, matchRoute, resolveRoute, routeParams } from "@/generative-ui/runtime/router";
import { selectRows } from "@/generative-ui/runtime/rows";
import { screenIdOf, screensOf } from "@/generative-ui/schema/tree";
import type { UIDocument } from "@/generative-ui/schema/types";
import { WorkspaceCanvas, type WorkspaceCanvasProps } from "@/generative-ui/workspace/WorkspaceCanvas";
import { actionsApi } from "@/services/api/actions";
import type { GenerationJobRead } from "@/services/api/types";
import { useToastStore } from "@/stores/toastStore";

import { fixtures, sampleApplication } from "../fixtures";

vi.mock("@/services/api/actions", () => ({ actionsApi: { execute: vi.fn() } }));

const DATA = fixtures.sample_application_data;
const AMARA = DATA.candidates!.find((row) => row.name === "Amara Okafor")!;

function renderApp(props: Partial<WorkspaceCanvasProps> = {}, document: UIDocument = sampleApplication()) {
  return render(<WorkspaceCanvas document={document} data={DATA} mode="view" workspaceId="w1" {...props} />);
}

/** The screen on show (exactly one at a time). */
function shownScreen(): string | null {
  const shown = document.querySelectorAll("[data-screen-id]");
  expect(shown).toHaveLength(1);
  return shown[0]!.getAttribute("data-screen-id");
}

const navigation = () => within(screen.getByRole("navigation", { name: "Hirewell" }));

beforeEach(() => {
  vi.mocked(actionsApi.execute).mockReset();
  useToastStore.setState({ toasts: [] });
});

describe("the contract with the backend", () => {
  it("accepts the sample application unchanged", () => {
    expect(sampleApplication()).toEqual(fixtures.sample_application);
  });

  it("draws every icon the backend may name", () => {
    expect(iconNames().sort()).toEqual([...fixtures.icons].sort());
  });

  it("implements exactly the effects the backend offers", () => {
    expect(supportedEffects().sort()).toEqual([...fixtures.effects].sort());
  });

  it("can render every pattern in the pattern registry", () => {
    const supported = new Set(supportedComponentTypes());
    const unknown = fixtures.patterns.filter((pattern) => !supported.has(pattern.component));

    expect(unknown).toEqual([]);
  });

  it("draws a neutral glyph for an icon name it does not know", () => {
    expect(resolveIcon("definitely-not-an-icon")).toBe(resolveIcon("another-unknown-name"));
    expect(resolveIcon("definitely-not-an-icon")).not.toBe(resolveIcon("briefcase"));
    expect(resolveIcon(undefined)).toBeNull();
  });
});

describe("routing", () => {
  const screens = screensOf(sampleApplication().page);

  it("matches a path against a route pattern", () => {
    expect(routeParams("/jobs/:jobId/candidates/:candidateId")).toEqual(["jobId", "candidateId"]);
    expect(matchRoute("/candidates/:candidateId", "/candidates/cand-001")).toEqual({ candidateId: "cand-001" });
    expect(matchRoute("/candidates/:candidateId", "/candidates")).toBeNull();
    expect(matchRoute("/candidates/:candidateId", "/jobs/cand-001")).toBeNull();
    expect(matchRoute("/a/:id", "/a/x%20y")).toEqual({ id: "x y" });
  });

  it("prefers a static route over a parameterised one", () => {
    expect(resolveRoute(screens, "/jobs/new")?.screen.id).toBe("job_new");
    expect(resolveRoute(screens, "/candidates/cand-002")).toMatchObject({
      screen: { id: "candidate_detail" },
      params: { candidateId: "cand-002" },
    });
    expect(resolveRoute(screens, "/nowhere")).toBeNull();
  });

  it("never produces a path with an unfilled parameter", () => {
    expect(fillRoute("/candidates/:candidateId", { candidateId: "c 1" })).toBe("/candidates/c%201");
    expect(fillRoute("/candidates/:candidateId", {})).toBeNull();
    expect(fillRoute("/", {})).toBe("/");
  });

  it("leads home from an unknown or missing path", () => {
    const document = sampleApplication();

    expect(locate(document, DATA, null)).toMatchObject({ screen: { id: "dashboard" }, path: "/" });
    expect(locate(document, DATA, "/does/not/exist")?.screen.id).toBe("dashboard");
    expect(activeScreenId(document, DATA, "/pipeline")).toBe("pipeline");
  });

  it("shows the first record when a record screen is opened without one", () => {
    const document = sampleApplication();
    const detail = screens.find((candidate) => candidate.id === "candidate_detail")!;

    expect(defaultParams(detail, DATA)).toEqual({ candidateId: DATA.candidates![0]!.id });
    expect(locate(document, DATA, "/candidates/:candidateId")).toMatchObject({
      screen: { id: "candidate_detail" },
      path: `/candidates/${DATA.candidates![0]!.id}`,
    });
  });

  it("knows which screen a component belongs to", () => {
    const page = sampleApplication().page;

    expect(screenIdOf(page, "pipeline_board")).toBe("pipeline");
    expect(screenIdOf(page, "pipeline")).toBe("pipeline");
    expect(screenIdOf(page, "missing")).toBeNull();
  });

  it("marks the navigation entry a record screen sits under", () => {
    const links = sampleApplication().application!.navigation.items.map((item) => ({
      item,
      screen: screens.find((candidate) => candidate.id === item.screen_id)!,
    }));
    const byId = (id: string) => screens.find((candidate) => candidate.id === id)!;

    expect(currentItem(links, byId("candidates"))).toBe("candidates");
    expect(currentItem(links, byId("candidate_detail"))).toBe("candidates");
    expect(currentItem(links, byId("job_new"))).toBe("jobs");
  });
});

describe("data bindings", () => {
  const rows = DATA.candidates!;

  it("filters by a fixed value and by a route parameter", () => {
    expect(
      selectRows(rows, { dataset: "candidates", where: [{ field: "stage", operator: "equals", value: "Interview" }] }).every(
        (row) => row.stage === "Interview",
      ),
    ).toBe(true);
    expect(
      selectRows(
        rows,
        { dataset: "candidates", where: [{ field: "id", operator: "equals", param: "candidateId" }] },
        { candidateId: "cand-002" },
      ).map((row) => row.name),
    ).toEqual(["Jonas Lindqvist"]);
  });

  it("shows nothing rather than everything when the parameter is missing", () => {
    const binding = { dataset: "candidates", where: [{ field: "id", operator: "equals" as const, param: "candidateId" }] };

    expect(selectRows(rows, binding, {})).toEqual([]);
  });

  it("sorts, limits and groups", () => {
    const top = selectRows(rows, { dataset: "candidates", sort: { field: "match_score", direction: "desc" }, limit: 3 });
    expect(top).toHaveLength(3);
    expect(top[0]!.match_score).toBe(Math.max(...rows.map((row) => Number(row.match_score))));

    const grouped = selectRows(rows, { dataset: "candidates", group_by: "stage" });
    const total = grouped.reduce((sum, row) => sum + Number(row.count), 0);
    expect(total).toBe(rows.length);
    expect(new Set(grouped.map((row) => row.stage)).size).toBe(grouped.length);
  });

  it("finds asset references but not field names", () => {
    expect(imageRefs({ type: "hero", image: "hero_main", items: [{ avatar: "face_1" }] })).toEqual(["hero_main", "face_1"]);
    expect(imageRefs({ type: "collection", fields: { title: "name", image: "photo" } })).toEqual([]);
    expect(imageRefs({ type: "section", image: "bg", children: [{ type: "image", image: "nested" }] })).toEqual(["bg"]);
  });
});

describe("actions inside an application", () => {
  const document = sampleApplication();
  const screens = screensOf(document.page);
  const app = (path: string): AppRuntime => ({
    application: document.application!,
    screens,
    route: locate(document, DATA, path)!,
    navigate: vi.fn(),
  });

  it("fills a route from the record the action was triggered on", () => {
    expect(resolveDestination(app("/"), { to: "/candidates/:candidateId" }, { row: AMARA })).toEqual({
      path: `/candidates/${AMARA.id}`,
    });
  });

  it("fills a route from another field of the record when told which", () => {
    const interview = DATA.interviews![0]!;

    expect(
      resolveDestination(app("/"), { to: "/candidates/:candidateId", from_field: "candidate_id" }, { row: interview }),
    ).toEqual({ path: `/candidates/${interview.candidate_id}` });
  });

  it("refuses a destination that is not a screen of the application", () => {
    expect(resolveDestination(app("/"), { to: "/admin/secrets" }, {})).toHaveProperty("problem");
    // External links are not in-app navigation: they go through the backend's allowlist.
    expect(resolveDestination(app("/"), { to: "https://example.com" }, {})).toBeNull();
  });

  it("explains instead of navigating when a record screen has no record to show", () => {
    const empty: AppRuntime = { ...app("/"), route: { ...app("/").route, params: {} } };

    expect(resolveDestination(empty, { to: "/candidates/:candidateId" }, {})).toHaveProperty("problem");
  });

  it("builds a record update from a button on a record screen", () => {
    const action = {
      type: "record_update" as const,
      payload: { entity: "candidates", key_param: "candidateId", set_field: "stage", set_value: "Interview" },
    };

    expect(recordPayload(action, {}, {}, app("/candidates/cand-002"))).toEqual({
      entity: "candidates",
      record_id: "cand-002",
      values: { stage: "Interview" },
    });
  });

  it("builds a record update from a moved card", () => {
    const action = { type: "record_update" as const, payload: { entity: "candidates", set_field: "stage" } };

    expect(recordPayload(action, { value: "Offer" }, { row: AMARA }, app("/pipeline"))).toEqual({
      entity: "candidates",
      record_id: AMARA.id,
      values: { stage: "Offer" },
    });
  });

  it("builds a record from a submitted form and needs no record id", () => {
    const action = { type: "record_create" as const, payload: { entity: "jobs", navigate_to: "/jobs" } };

    expect(recordPayload(action, { values: { title: "Designer", openings: 2 } }, {}, app("/jobs/new"))).toEqual({
      entity: "jobs",
      navigate_to: "/jobs",
      values: { title: "Designer", openings: 2 },
    });
  });

  it("will not change a record when there is none in view", () => {
    const action = { type: "record_delete" as const, payload: { entity: "candidates" } };

    expect(recordPayload(action, {}, {}, app("/"))).toHaveProperty("problem");
  });
});

describe("rendering an application", () => {
  it("shows the home screen inside the shell, one screen at a time", () => {
    renderApp();

    expect(shownScreen()).toBe("dashboard");
    expect(navigation().getByRole("button", { name: "Dashboard" })).toHaveAttribute("aria-current", "page");
    expect(navigation().getAllByRole("button").map((button) => button.textContent)).toEqual([
      "Dashboard",
      "Jobs",
      "Candidates",
      "Pipeline",
      "Interviews",
    ]);
    expect(document.querySelector(".g-app")).toHaveAttribute("data-nav", "sidebar");
  });

  it("moves between screens from the navigation", async () => {
    const user = userEvent.setup();
    renderApp();

    await user.click(navigation().getByRole("button", { name: "Jobs" }));

    expect(shownScreen()).toBe("jobs");
    expect(screen.getByRole("heading", { level: 1, name: "Jobs" })).toBeInTheDocument();
    expect(navigation().getByRole("button", { name: "Jobs" })).toHaveAttribute("aria-current", "page");
    expect(actionsApi.execute).not.toHaveBeenCalled();
  });

  it("reports the path to its owner instead of keeping it when asked to", async () => {
    const user = userEvent.setup();
    const onPathChange = vi.fn();
    renderApp({ path: "/jobs", onPathChange });

    expect(shownScreen()).toBe("jobs");
    await user.click(navigation().getByRole("button", { name: "Pipeline" }));

    expect(onPathChange).toHaveBeenCalledWith("/pipeline");
    expect(shownScreen()).toBe("jobs");
  });

  it("opens a record from a list and shows that record", async () => {
    const user = userEvent.setup();
    renderApp({ path: "/candidates", onPathChange: undefined });
    await user.click(navigation().getByRole("button", { name: "Candidates" }));

    await user.click(screen.getByRole("button", { name: "Open Jonas Lindqvist" }));

    expect(shownScreen()).toBe("candidate_detail");
    expect(screen.getByRole("heading", { name: "Jonas Lindqvist" })).toBeInTheDocument();
    expect(screen.getByText("jonas.lindqvist@proton.me")).toBeInTheDocument();
    // A record screen keeps its list's entry marked in the navigation.
    expect(navigation().getByRole("button", { name: "Candidates" })).toHaveAttribute("aria-current", "page");
  });

  it("navigates with a button and from a table row", async () => {
    const user = userEvent.setup();
    renderApp({ path: "/jobs" });
    await user.click(navigation().getByRole("button", { name: "Jobs" }));

    await user.click(screen.getByRole("button", { name: "Create job" }));
    expect(shownScreen()).toBe("job_new");

    await user.click(navigation().getByRole("button", { name: "Jobs" }));
    await user.click(screen.getAllByRole("row")[1]!);
    expect(shownScreen()).toBe("candidates");
  });

  it("computes figures from the application's records", async () => {
    const user = userEvent.setup();
    renderApp();
    await user.click(navigation().getByRole("button", { name: "Pipeline" }));

    const interview = screen.getByRole("group", { name: /^Interview, / });
    const expected = DATA.candidates!.filter((row) => row.stage === "Interview").length;

    expect(interview).toHaveAccessibleName(`Interview, ${expected}`);
    expect(within(interview).getAllByRole("article")).toHaveLength(expected);
  });

  it("moves a card to the next stage and shows the server's rows", async () => {
    const user = userEvent.setup();
    const moved = DATA.candidates!.map((row) => (row.id === AMARA.id ? { ...row, stage: "Offer" } : row));
    vi.mocked(actionsApi.execute).mockResolvedValue({
      action_type: "record_update",
      result: { dataset: "candidates", rows: moved },
    } as never);
    renderApp();
    await user.click(navigation().getByRole("button", { name: "Pipeline" }));
    const card = screen.getByRole("button", { name: "Open Amara Okafor" }).closest("article")!;

    await user.click(within(card).getByRole("button", { name: /Move to Offer/ }));

    expect(actionsApi.execute).toHaveBeenCalledWith("w1", "record_update", {
      entity: "candidates",
      record_id: AMARA.id,
      values: { stage: "Offer" },
    });
    await waitFor(() =>
      expect(within(screen.getByRole("group", { name: /^Offer, / })).getByText("Amara Okafor")).toBeInTheDocument(),
    );
    expect(within(screen.getByRole("group", { name: /^Interview, / })).queryByText("Amara Okafor")).toBeNull();
  });

  it("submits a form as a new record and follows where the server says to go", async () => {
    const user = userEvent.setup();
    const created = { id: "job-900", title: "Staff Engineer", department: "", location: "", status: "Open", openings: 1 };
    vi.mocked(actionsApi.execute).mockResolvedValue({
      action_type: "record_create",
      result: { dataset: "jobs", rows: [...DATA.jobs!, created], navigate_to: "/jobs" },
    } as never);
    renderApp();
    await user.click(navigation().getByRole("button", { name: "Jobs" }));
    await user.click(screen.getByRole("button", { name: "Create job" }));

    await user.type(screen.getByLabelText(/^Title/), "Staff Engineer");
    await user.click(within(document.querySelector("form")!).getByRole("button"));

    await waitFor(() => expect(shownScreen()).toBe("jobs"));
    const [, type, payload] = vi.mocked(actionsApi.execute).mock.calls[0]!;
    expect(type).toBe("record_create");
    expect(payload).toMatchObject({ entity: "jobs", values: { title: "Staff Engineer" } });
    expect(screen.getByText("Staff Engineer")).toBeInTheDocument();
  });

  it("lets a preview be explored but sends nothing to the server", async () => {
    const user = userEvent.setup();
    renderApp({ mode: "preview" });

    await user.click(navigation().getByRole("button", { name: "Pipeline" }));
    expect(shownScreen()).toBe("pipeline");
    const card = screen.getByRole("button", { name: "Open Amara Okafor" }).closest("article")!;
    await user.click(within(card).getByRole("button", { name: /Move to/ }));

    expect(actionsApi.execute).not.toHaveBeenCalled();
    expect(useToastStore.getState().toasts.at(-1)?.message).toMatch(/Apply this version/);
  });

  it("selects instead of acting while editing, and still lets screens be switched", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderApp({ mode: "edit", onSelect });

    await user.click(navigation().getByRole("button", { name: "Jobs" }));
    expect(shownScreen()).toBe("jobs");
    await user.click(screen.getByRole("button", { name: "Create job" }));

    expect(shownScreen()).toBe("jobs");
    expect(onSelect).toHaveBeenCalledWith("jobs_new_job");
    expect(actionsApi.execute).not.toHaveBeenCalled();
  });

  it.each(["topbar", "bottom", "minimal", "none"] as const)("draws the %s navigation style", (style) => {
    const base = sampleApplication();
    const restyled: UIDocument = {
      ...base,
      application: { ...base.application!, navigation: { ...base.application!.navigation, style } },
    };

    renderApp({}, restyled);

    expect(document.querySelector(".g-app")).toHaveAttribute("data-nav", style);
    expect(shownScreen()).toBe("dashboard");
    if (style === "none") expect(screen.queryByRole("navigation")).toBeNull();
    else expect(navigation().getByRole("button", { name: "Dashboard" })).toBeInTheDocument();
  });

  it("shows a soft placeholder, not a broken image, for an asset it cannot resolve", () => {
    const base = sampleApplication();
    const withoutAssets: UIDocument = { ...base, application: { ...base.application!, assets: [] } };

    renderApp({}, withoutAssets);

    expect(document.querySelectorAll("img")).toHaveLength(0);
    expect(shownScreen()).toBe("dashboard");
  });

  it("only ever loads images from this application's own asset endpoint", () => {
    renderApp();

    for (const image of document.querySelectorAll("img")) {
      expect(image.getAttribute("src")).toMatch(/\/api\/v1\/assets\/[0-9a-f-]{36}\/content$/);
    }
  });
});

describe("generation progress", () => {
  const job = (overrides: Partial<GenerationJobRead>): GenerationJobRead =>
    ({ status: "running", stage: "planning", progress: 12, detail: null, ...overrides }) as GenerationJobRead;

  it("marks stages from what the server reports", () => {
    const states = stageStates(job({ stage: "generating_screens" }));
    const position = BUILD_STAGES.findIndex((entry) => entry.stage === "generating_screens");

    expect(states[position]).toBe("current");
    expect(states.slice(0, position).every((state) => state === "done")).toBe(true);
    expect(states.slice(position + 1).every((state) => state === "upcoming")).toBe(true);
    expect(stageStates(job({ status: "ready", stage: "ready" })).every((state) => state === "done")).toBe(true);
    expect(stageStates(null).every((state) => state === "upcoming")).toBe(true);
  });

  it("describes the job in the server's words", () => {
    expect(jobText(null)).toBe("Sending your request…");
    expect(jobText(job({ status: "queued", stage: "queued" }))).toBe("Waiting to start…");
    expect(jobText(job({ stage: "generating_screens", progress: 55, detail: "Designing 3 of 7 screens" }))).toBe(
      "Designing 3 of 7 screens · 55%",
    );
    expect(jobText(job({ stage: "designing", progress: 16 }))).toBe("Setting the design direction · 16%");
  });
});

describe("the application summary", () => {
  it("lists what would be saved and opens a screen on request", async () => {
    const user = userEvent.setup();
    const onOpenScreen = vi.fn();
    const summary = fixtures.application_summary;
    render(<ApplicationSummary summary={summary} quality={{ score: 91, issues: [] }} onOpenScreen={onOpenScreen} />);

    expect(screen.getByText(summary.name)).toBeInTheDocument();
    expect(within(screen.getByRole("list", { name: "Screens" })).getAllByRole("button")).toHaveLength(
      summary.screens.length,
    );
    expect(screen.getByText(summary.design.style_name)).toBeInTheDocument();
    expect(screen.getByText(/design review 91\/100/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Pipeline" }));
    expect(onOpenScreen).toHaveBeenCalledWith("/pipeline");
  });

  it("says plainly which screens could not be generated", () => {
    const summary = {
      ...fixtures.application_summary,
      screens: fixtures.application_summary.screens.map((item, index) => ({ ...item, failed: index === 1 })),
    };
    render(<ApplicationSummary summary={summary} />);

    expect(screen.getByText(new RegExp(`${summary.screens[1]!.title} could not be generated`))).toBeInTheDocument();
  });
});
