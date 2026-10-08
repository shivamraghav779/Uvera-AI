import { apiRequest, ApiError, isApiError } from "@/services/api/client";
import { parseEvents, requestProposalStream } from "@/services/api/stream";
import { useAuthStore } from "@/stores/authStore";

function respond(status: number, body: unknown, raw = false): Response {
  return new Response(raw ? (body as string) : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  fetchMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  useAuthStore.getState().signOut();
});
afterEach(() => vi.unstubAllGlobals());

async function failure(promise: Promise<unknown>): Promise<ApiError> {
  try {
    await promise;
  } catch (error) {
    if (error instanceof ApiError) return error;
    throw error;
  }
  throw new Error("expected the request to fail");
}

describe("api client", () => {
  it("unwraps the success envelope and sends JSON", async () => {
    fetchMock.mockResolvedValue(respond(201, { success: true, data: { id: "w1" } }));

    const data = await apiRequest<{ id: string }>("/workspaces", { method: "POST", body: { title: "A" } });

    expect(data).toEqual({ id: "w1" });
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://localhost:8000/api/v1/workspaces");
    expect(init).toMatchObject({ method: "POST", body: '{"title":"A"}' });
  });

  it("adds query parameters, skipping undefined ones", async () => {
    fetchMock.mockResolvedValue(respond(200, { success: true, data: [] }));

    await apiRequest("/workspaces/w/versions/v/compare", { query: { with: "v2", other: undefined } });

    expect(fetchMock.mock.calls[0]![0]).toBe("http://localhost:8000/api/v1/workspaces/w/versions/v/compare?with=v2");
  });

  it("turns the error envelope into an ApiError with its code and details", async () => {
    fetchMock.mockResolvedValue(
      respond(409, {
        success: false,
        error: {
          code: "VERSION_CONFLICT",
          message: "The workspace has changed since this change was prepared.",
          request_id: "req-1",
          details: [{ current_version_number: 6 }],
        },
      }),
    );

    const error = await failure(apiRequest("/workspaces/w/versions", { method: "POST", body: {} }));

    expect(error).toMatchObject({ code: "VERSION_CONFLICT", status: 409, requestId: "req-1" });
    expect(error.details).toEqual([{ current_version_number: 6 }]);
    expect(isApiError(error, "VERSION_CONFLICT")).toBe(true);
    expect(isApiError(error, "TIMEOUT")).toBe(false);
  });

  it("returns nothing for 204", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(apiRequest("/workspaces/w", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it.each([
    ["a body that is not JSON", respond(200, "<html>proxy error</html>", true)],
    ["JSON without the envelope", respond(200, { id: "w1" })],
    ["an unsuccessful status without an error envelope", respond(502, { detail: "bad gateway" })],
  ])("reports %s as a malformed response", async (_name, response) => {
    fetchMock.mockResolvedValue(response);

    expect((await failure(apiRequest("/workspaces"))).code).toBe("MALFORMED_RESPONSE");
  });

  it("reports an unreachable server as a network error", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

    const error = await failure(apiRequest("/workspaces"));

    expect(error.code).toBe("NETWORK_ERROR");
    expect(error.message).toMatch(/Could not reach the server/);
  });

  it("gives up after the timeout", async () => {
    fetchMock.mockImplementation(
      (_url, init) =>
        new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
        }),
    );

    const error = await failure(apiRequest("/ui/generate", { method: "POST", body: {}, timeoutMs: 20 }));

    expect(error.code).toBe("TIMEOUT");
  });
});

describe("session", () => {
  const signIn = () => useAuthStore.getState().signIn("token-abc", { id: "u1", email: "ana@example.com" });

  it("sends the access token once signed in, and nothing before", async () => {
    fetchMock.mockImplementation(async () => respond(200, { success: true, data: [] }));

    await apiRequest("/workspaces");
    signIn();
    await apiRequest("/workspaces");

    const headers = fetchMock.mock.calls.map(([, init]) => (init?.headers ?? {}) as Record<string, string>);
    expect(headers[0]!.Authorization).toBeUndefined();
    expect(headers[1]!.Authorization).toBe("Bearer token-abc");
  });

  it.each(["TOKEN_EXPIRED", "INVALID_TOKEN", "AUTHENTICATION_REQUIRED"])(
    "ends the session when the server answers %s",
    async (code) => {
      signIn();
      fetchMock.mockResolvedValue(respond(401, { success: false, error: { code, message: "no" } }));

      await failure(apiRequest("/workspaces"));

      expect(useAuthStore.getState().token).toBeNull();
    },
  );

  it("keeps the session on other errors, including wrong credentials", async () => {
    signIn();
    fetchMock.mockResolvedValue(
      respond(404, { success: false, error: { code: "RESOURCE_NOT_FOUND", message: "no" } }),
    );

    await failure(apiRequest("/workspaces/missing"));

    expect(useAuthStore.getState().token).toBe("token-abc");
  });
});

describe("proposal stream", () => {
  const sse = (...events: [string, unknown][]) =>
    events.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join("");

  function streamResponse(chunks: string[], status = 200): Response {
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        for (const chunk of chunks) controller.enqueue(new TextEncoder().encode(chunk));
        controller.close();
      },
    });
    return new Response(body, { status, headers: { "Content-Type": "text/event-stream" } });
  }

  it("parses complete events and keeps an unfinished tail", () => {
    const text = sse(["progress", { stage: "generating", characters: 5 }]) + "event: prop";

    expect(parseEvents(text)).toEqual({
      events: [{ event: "progress", data: { stage: "generating", characters: 5 } }],
      rest: "event: prop",
    });
  });

  it("reports progress and resolves with the proposal, even when events are split across chunks", async () => {
    const text = sse(
      ["progress", { stage: "understanding", characters: null }],
      ["progress", { stage: "generating", characters: 160 }],
      ["proposal", { success: true, data: { proposal_id: "p-1", kind: "mutate" } }],
    );
    const middle = Math.floor(text.length / 2);
    fetchMock.mockResolvedValue(streamResponse([text.slice(0, 17), text.slice(17, middle), text.slice(middle)]));
    const stages: string[] = [];

    const proposal = await requestProposalStream("/ui/mutate/stream", {}, (p) => stages.push(p.stage));

    expect(stages).toEqual(["understanding", "generating"]);
    expect(proposal).toEqual({ proposal_id: "p-1", kind: "mutate" });
    expect(fetchMock.mock.calls[0]![0]).toBe("http://localhost:8000/api/v1/ui/mutate/stream");
  });

  it("turns an error event into the same ApiError as a failed request", async () => {
    fetchMock.mockResolvedValue(
      streamResponse([
        sse(["error", { success: false, error: { code: "UI_SCHEMA_INVALID", message: "Generated UI schema is invalid." } }]),
      ]),
    );

    const error = await failure(requestProposalStream("/ui/generate/stream", {}, () => {}));

    expect(error.code).toBe("UI_SCHEMA_INVALID");
  });

  it("reports a rejection that happens before streaming starts", async () => {
    fetchMock.mockResolvedValue(
      respond(429, { success: false, error: { code: "RATE_LIMIT_EXCEEDED", message: "Too many requests." } }),
    );

    expect((await failure(requestProposalStream("/ui/mutate/stream", {}, () => {}))).code).toBe("RATE_LIMIT_EXCEEDED");
  });

  it.each([
    ["a stream that ends without a result", [sse(["progress", { stage: "generating", characters: 1 }])]],
    ["an unreadable event", ["event: progress\ndata: {not json\n\n"]],
  ])("treats %s as a malformed response", async (_name, chunks) => {
    fetchMock.mockResolvedValue(streamResponse(chunks));

    expect((await failure(requestProposalStream("/ui/mutate/stream", {}, () => {}))).code).toBe("MALFORMED_RESPONSE");
  });
});
