/**
 * The approval model, exercised through the real hook and stores with only the
 * HTTP layer replaced: propose -> (preview) -> apply or reject -> persist.
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, renderHook, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";

import { progressText } from "@/features/chat/ChatMessage";
import { ProposalCard } from "@/features/chat/ProposalCard";
import { useAssistant } from "@/features/chat/useAssistant";
import { ApiError } from "@/services/api/client";
import { generationApi } from "@/services/api/generation";
import type { GenerationJobRead, ProposalRead, VersionDetail, VersionSummary } from "@/services/api/types";
import { uiApi } from "@/services/api/ui";
import { versionsApi } from "@/services/api/versions";
import { useChatStore } from "@/stores/chatStore";
import { useEditorStore } from "@/stores/editorStore";
import { selectDraft, useWorkspaceStore } from "@/stores/workspaceStore";

import { documentWith, fixtures } from "../fixtures";

vi.mock("@/services/api/ui", () => ({
  uiApi: { mutateStream: vi.fn(), frameworks: vi.fn(), themes: vi.fn() },
}));
vi.mock("@/services/api/generation", () => ({
  generationApi: { start: vi.fn(), get: vi.fn(), latest: vi.fn(), cancel: vi.fn() },
}));
vi.mock("@/services/api/versions", () => ({ versionsApi: { create: vi.fn(), restore: vi.fn() } }));

const WORKSPACE = "w1";
const twoSteps = fixtures.mutation_cases.find((item) => item.name === "replace table with bar chart keeps layout")!;

function proposal(overrides: Partial<ProposalRead>): ProposalRead {
  return {
    proposal_id: "p-1",
    kind: "mutate",
    workspace_id: WORKSPACE,
    base_version_id: "v1",
    message: "I'll make those changes.",
    steps: [],
    document: null,
    data: fixtures.sample_data,
    changes: [],
    affected_component_ids: [],
    target_version: null,
    validation: { valid: true, issues: [] },
    metadata: { schema_version: fixtures.schema_version, repair_attempts: 0 },
    ...overrides,
  } as ProposalRead;
}

/** A generation job as the server reports it; finished by default. */
function job(overrides: Partial<GenerationJobRead> = {}): GenerationJobRead {
  return {
    id: "job-1",
    workspace_id: WORKSPACE,
    kind: "build",
    instruction: "Create a sales dashboard",
    status: "ready",
    stage: "ready",
    progress: 100,
    detail: null,
    base_version_id: null,
    proposal: null,
    error: null,
    created_at: "2026-10-05T10:00:00Z",
    updated_at: "2026-10-05T10:00:05Z",
    finished_at: "2026-10-05T10:00:05Z",
    ...overrides,
  };
}

const asJobProposal = (value: ProposalRead) => value as unknown as GenerationJobRead["proposal"];
const generated = () =>
  job({
    proposal: asJobProposal(
      proposal({
        kind: "generate",
        base_version_id: null,
        document: fixtures.sample_document as ProposalRead["document"],
      }),
    ),
  });

const mutateProposal = () =>
  proposal({
    steps: twoSteps.operations.map((operation, index) => ({
      operation: operation as unknown as Record<string, never>,
      summary: twoSteps.summaries[index]!,
      affected_component_ids: ["regional_table"],
    })),
    document: twoSteps.expected as ProposalRead["document"],
  });

function versionDetail(number: number, document: unknown): VersionDetail {
  return {
    id: `v${number}`,
    workspace_id: WORKSPACE,
    version_number: number,
    parent_version_id: number > 1 ? `v${number - 1}` : null,
    description: "saved",
    source: "ai_mutation",
    metadata: {},
    created_at: "2026-10-05T10:00:00Z",
    created_by: null,
    is_current: true,
    document: document as VersionDetail["document"],
    data: fixtures.sample_data,
  };
}

function setup({ withVersion = true } = {}) {
  useWorkspaceStore.setState({ workspaceId: null, base: null, history: null, preview: null, loadIssues: null });
  useChatStore.getState().reset();
  useEditorStore.getState().reset();
  if (withVersion) {
    useWorkspaceStore.getState().hydrate(WORKSPACE, versionDetail(1, fixtures.sample_document));
  } else {
    useWorkspaceStore.getState().open(WORKSPACE);
  }
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  return renderHook(() => useAssistant(WORKSPACE), { wrapper });
}

beforeEach(() => {
  for (const mock of Object.values(generationApi)) vi.mocked(mock).mockReset();
  vi.mocked(uiApi.mutateStream).mockReset();
  vi.mocked(versionsApi.create).mockReset();
  vi.mocked(versionsApi.restore).mockReset();
  vi.mocked(uiApi.frameworks).mockResolvedValue({
    default_framework: "shadcn",
    default_design_system: "modern_minimal",
    frameworks: fixtures.frameworks.map((framework) => ({ ...framework, description: "" })),
    design_systems: fixtures.design_systems.map((system) => ({ ...system, description: "", imagery: "none" })),
  });
});

describe("generating in an empty workspace", () => {
  it("previews the draft immediately but saves nothing until applied", async () => {
    vi.mocked(generationApi.start).mockResolvedValue(generated());
    const { result } = setup({ withVersion: false });

    await act(() => result.current.send("Create a sales dashboard"));

    expect(generationApi.start).toHaveBeenCalledWith(
      expect.objectContaining({ workspace_id: WORKSPACE, instruction: "Create a sales dashboard", kind: "build" }),
    );
    expect(useWorkspaceStore.getState().preview).toMatchObject({ kind: "proposal" });
    expect(useWorkspaceStore.getState().base).toBeNull();
    expect(versionsApi.create).not.toHaveBeenCalled();
  });

  it("persists the approved document as the first version and adopts it", async () => {
    vi.mocked(generationApi.start).mockResolvedValue(generated());
    vi.mocked(versionsApi.create).mockResolvedValue(versionDetail(1, fixtures.sample_document));
    const { result } = setup({ withVersion: false });
    await act(() => result.current.send("Create a sales dashboard"));

    act(() => result.current.apply());

    await waitFor(() => expect(useWorkspaceStore.getState().base?.number).toBe(1));
    expect(versionsApi.create).toHaveBeenCalledWith(WORKSPACE, {
      base_version_id: null,
      proposal_id: "p-1",
      instruction: "Create a sales dashboard",
      source: "ai_generation",
      document: fixtures.sample_document,
    });
    expect(useChatStore.getState().proposal).toBeNull();
    expect(useWorkspaceStore.getState().preview).toBeNull();
  });
});

describe("editing an existing UI", () => {
  it("sends the base version and the selected component with the instruction", async () => {
    vi.mocked(uiApi.mutateStream).mockResolvedValue(mutateProposal());
    const { result } = setup();
    useEditorStore.getState().select("regional_table");

    await act(() => result.current.send("Make this a bar chart"));

    expect(uiApi.mutateStream).toHaveBeenCalledWith(
      {
        workspace_id: WORKSPACE,
        base_version_id: "v1",
        instruction: "Make this a bar chart",
        selected_component_id: "regional_table",
        active_screen_id: null,
      },
      expect.any(Function),
      undefined,
    );
    expect(generationApi.start).not.toHaveBeenCalled();
    // The proposal is held for a decision; the working copy has not moved.
    expect(selectDraft(useWorkspaceStore.getState())).toEqual(fixtures.sample_document);
    expect(useWorkspaceStore.getState().preview).toBeNull();
  });

  it("previews the result without touching the working copy", async () => {
    vi.mocked(uiApi.mutateStream).mockResolvedValue(mutateProposal());
    const { result } = setup();
    await act(() => result.current.send("Replace the table"));

    act(() => result.current.preview());

    const preview = useWorkspaceStore.getState().preview!;
    expect(preview.document).toEqual(twoSteps.expected);
    expect(preview.highlightIds).toContain("regional_table");
    expect(selectDraft(useWorkspaceStore.getState())).toEqual(fixtures.sample_document);

    act(() => result.current.stopPreview());
    expect(useWorkspaceStore.getState().preview).toBeNull();
  });

  it("applies only the steps the user kept", async () => {
    vi.mocked(uiApi.mutateStream).mockResolvedValue(mutateProposal());
    vi.mocked(versionsApi.create).mockResolvedValue(versionDetail(2, twoSteps.expected));
    const { result } = setup();
    await act(() => result.current.send("Replace the table"));
    act(() => useChatStore.getState().toggleStep(1));

    act(() => result.current.preview());
    const previewed = useWorkspaceStore.getState().preview!.document;
    expect(previewed.page.components.at(-1)).toMatchObject({ type: "table", layout: { span: 6 } });

    act(() => result.current.apply());

    await waitFor(() => expect(useWorkspaceStore.getState().base?.number).toBe(2));
    expect(versionsApi.create).toHaveBeenCalledWith(
      WORKSPACE,
      expect.objectContaining({
        base_version_id: "v1",
        source: "ai_mutation",
        operations: [twoSteps.operations[0]],
      }),
    );
  });

  it("rejecting discards the proposal and calls nothing", async () => {
    vi.mocked(uiApi.mutateStream).mockResolvedValue(mutateProposal());
    const { result } = setup();
    await act(() => result.current.send("Replace the table"));
    act(() => result.current.preview());

    act(() => result.current.reject());

    expect(useChatStore.getState().proposal).toBeNull();
    expect(useWorkspaceStore.getState().preview).toBeNull();
    expect(useWorkspaceStore.getState().base?.number).toBe(1);
    expect(versionsApi.create).not.toHaveBeenCalled();
  });

  it("does not ask the assistant while there are unsaved edits", async () => {
    const { result } = setup();
    useWorkspaceStore.getState().applyOperations([{ type: "RESIZE", target: "aov_metric", span: 6 }]);

    await act(() => result.current.send("Make it dark"));

    expect(uiApi.mutateStream).not.toHaveBeenCalled();
  });

  it("restores through the restore endpoint, naming the current base", async () => {
    const target = { id: "v0", version_number: 3 } as VersionSummary;
    vi.mocked(uiApi.mutateStream).mockResolvedValue(
      proposal({ kind: "restore", target_version: target, document: fixtures.sample_document as ProposalRead["document"] }),
    );
    vi.mocked(versionsApi.restore).mockResolvedValue(versionDetail(5, fixtures.sample_document));
    const { result } = setup();
    await act(() => result.current.send("Go back to version 3"));

    act(() => result.current.apply());

    await waitFor(() => expect(useWorkspaceStore.getState().base?.number).toBe(5));
    expect(versionsApi.restore).toHaveBeenCalledWith(WORKSPACE, "v0", "v1", "p-1");
    expect(versionsApi.create).not.toHaveBeenCalled();
  });

  it("opens the comparison for a compare request", async () => {
    const target = { id: "v0", version_number: 1 } as VersionSummary;
    vi.mocked(uiApi.mutateStream).mockResolvedValue(proposal({ kind: "compare", target_version: target }));
    const { result } = setup();

    await act(() => result.current.send("Compare with version 1"));

    expect(useEditorStore.getState().compareVersionId).toBe("v0");
  });
});

describe("live progress", () => {
  it("shows what the server reports while it works, then clears it", async () => {
    const seen: (string | undefined)[] = [];
    vi.mocked(uiApi.mutateStream).mockImplementation(async (_body, onProgress) => {
      onProgress({ stage: "generating", characters: 320 });
      seen.push(useChatStore.getState().progress?.stage);
      onProgress({ stage: "validating", characters: null });
      seen.push(useChatStore.getState().progress?.stage);
      return mutateProposal();
    });
    const { result } = setup();

    await act(() => result.current.send("Replace the table"));

    expect(seen).toEqual(["generating", "validating"]);
    expect(useChatStore.getState().progress).toBeNull();
    expect(progressText({ stage: "generating", characters: 1234 })).toMatch(/Writing the changes… \(1[,.]?234 characters\)/);
    expect(progressText(null)).toBe("Sending your request…");
  });
});

describe("failures never corrupt the workspace", () => {
  it("a stale base on apply raises the conflict and keeps the current version", async () => {
    vi.mocked(uiApi.mutateStream).mockResolvedValue(mutateProposal());
    vi.mocked(versionsApi.create).mockRejectedValue(
      new ApiError("VERSION_CONFLICT", "changed", 409, [{ current_version_number: 4 }]),
    );
    const { result } = setup();
    await act(() => result.current.send("Replace the table"));

    act(() => result.current.apply());

    await waitFor(() => expect(useEditorStore.getState().conflict).toEqual({ currentVersionNumber: 4 }));
    expect(useWorkspaceStore.getState().base?.number).toBe(1);
    expect(selectDraft(useWorkspaceStore.getState())).toEqual(fixtures.sample_document);
  });

  it("a stale base when asking raises the conflict too", async () => {
    vi.mocked(uiApi.mutateStream).mockRejectedValue(new ApiError("VERSION_CONFLICT", "changed", 409));
    const { result } = setup();

    await act(() => result.current.send("Make it dark"));

    expect(useEditorStore.getState().conflict).not.toBeNull();
    expect(useChatStore.getState().proposal).toBeNull();
  });

  it("discards a proposal whose document does not match the schema", async () => {
    const malformed = documentWith({ type: "iframe", id: "x", src: "https://evil.example" });
    vi.mocked(uiApi.mutateStream).mockResolvedValue(proposal({ document: malformed as ProposalRead["document"] }));
    const { result } = setup();

    await act(() => result.current.send("Do something"));

    expect(useChatStore.getState().proposal).toBeNull();
    expect(useChatStore.getState().error).toMatch(/could not be displayed/);
    expect(useWorkspaceStore.getState().preview).toBeNull();
  });

  it.each([
    ["PROVIDER_NOT_CONFIGURED", /No language model is configured/],
    ["LLM_ALL_PROVIDERS_FAILED", /not responding/],
    ["UI_SCHEMA_INVALID", /could not produce a valid change/],
    ["TIMEOUT", /took too long/],
    ["RATE_LIMIT_EXCEEDED", /too quickly/],
    ["DATABASE_UNAVAILABLE", /temporarily unavailable/],
  ])("explains %s without losing state", async (code, message) => {
    vi.mocked(uiApi.mutateStream).mockRejectedValue(new ApiError(code, "raw server text", 502));
    const { result } = setup();

    await act(() => result.current.send("Make it dark"));

    expect(useChatStore.getState()).toMatchObject({ status: "idle", proposal: null });
    expect(useChatStore.getState().error).toMatch(message);
    expect(useWorkspaceStore.getState().base?.number).toBe(1);
  });
});

describe("proposal card", () => {
  const handlers = () => ({
    onToggleStep: vi.fn(),
    onPreview: vi.fn(),
    onStopPreview: vi.fn(),
    onApply: vi.fn(),
    onReject: vi.fn(),
    onOpenComparison: vi.fn(),
  });

  it("lists each operation and lets the user keep or drop it", async () => {
    const actions = handlers();
    render(
      <ProposalCard proposal={mutateProposal()} accepted={[true, false]} previewing={false} applying={false} {...actions} />,
    );

    expect(screen.getByText("2 proposed changes")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply 1 of 2" })).toBeEnabled();
    expect(screen.getByText("Not saved until you apply")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("checkbox", { name: /Replace “Sales by region”/ }));
    await userEvent.click(screen.getByRole("button", { name: "Preview" }));
    await userEvent.click(screen.getByRole("button", { name: "Reject" }));

    expect(actions.onToggleStep).toHaveBeenCalledWith(1);
    expect(actions.onPreview).toHaveBeenCalledOnce();
    expect(actions.onReject).toHaveBeenCalledOnce();
    expect(actions.onApply).not.toHaveBeenCalled();
  });

  it("cannot apply when every step was dropped", () => {
    render(
      <ProposalCard proposal={mutateProposal()} accepted={[false, false]} previewing applying={false} {...handlers()} />,
    );

    expect(screen.getByRole("button", { name: "Apply 0 of 2" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Hide preview" })).toBeInTheDocument();
  });

  it("names the version a restore would bring back", () => {
    const restore = proposal({
      kind: "restore",
      target_version: { id: "v3", version_number: 3 } as VersionSummary,
      changes: [{ kind: "replaced", summary: "Bar chart “Sales by region” replaced with table" }],
    });
    render(<ProposalCard proposal={restore} accepted={[]} previewing={false} applying={false} {...handlers()} />);

    expect(screen.getByRole("button", { name: "Restore version 3" })).toBeInTheDocument();
    expect(screen.getByText("Bar chart “Sales by region” replaced with table")).toBeInTheDocument();
  });

  it("offers nothing to apply for a plain reply", () => {
    render(
      <ProposalCard
        proposal={proposal({ kind: "message", message: "I can't add video players." })}
        accepted={[]}
        previewing={false}
        applying={false}
        {...handlers()}
      />,
    );

    expect(screen.queryByRole("button", { name: /Apply/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dismiss" })).toBeInTheDocument();
  });
});
