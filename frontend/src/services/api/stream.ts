/**
 * Proposal requests with live progress (server-sent events over fetch).
 *
 * The server sends `progress` events while the model works, then exactly one
 * `proposal` or `error`. Only progress *counts* are streamed: the proposal
 * arrives whole and already validated, so nothing partial is ever rendered.
 */
import {
  AI_TIMEOUT_MS,
  ApiError,
  buildUrl,
  errorFromEnvelope,
  requestHeaders,
} from "./client";
import type { ProposalRead } from "./types";

export interface ProposalProgress {
  stage: "understanding" | "planning" | "generating" | "validating" | "repairing" | "finishing";
  characters: number | null;
}

interface ServerEvent {
  event: string;
  data: unknown;
}

/** Split a chunk of an event stream into complete events, returning the unfinished tail. */
export function parseEvents(buffer: string): { events: ServerEvent[]; rest: string } {
  const blocks = buffer.split("\n\n");
  const rest = blocks.pop() ?? "";
  const events: ServerEvent[] = [];
  for (const block of blocks) {
    let event = "message";
    const data: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trim());
    }
    if (data.length === 0) continue;
    try {
      events.push({ event, data: JSON.parse(data.join("\n")) });
    } catch {
      throw new ApiError("MALFORMED_RESPONSE", "The server sent an unreadable progress event.");
    }
  }
  return { events, rest };
}

export async function requestProposalStream(
  path: string,
  body: unknown,
  onProgress: (progress: ProposalProgress) => void,
  timeoutMs: number = AI_TIMEOUT_MS,
): Promise<ProposalRead> {
  const timeout = AbortSignal.timeout(timeoutMs);
  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      method: "POST",
      headers: { ...requestHeaders(true), Accept: "text/event-stream" },
      body: JSON.stringify(body),
      signal: timeout,
    });
  } catch {
    if (timeout.aborted) throw new ApiError("TIMEOUT", "The request took too long. Please try again.");
    throw new ApiError("NETWORK_ERROR", "Could not reach the server. Check that the backend is running.");
  }

  if (!response.ok || !response.body) {
    // Rejected before streaming began (validation, authentication, rate limit).
    const payload: unknown = await response.json().catch(() => null);
    throw (
      errorFromEnvelope(payload, response.status) ??
      new ApiError("MALFORMED_RESPONSE", "The server sent a response in an unexpected format.", response.status)
    );
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      const parsed = parseEvents(buffer + value);
      buffer = parsed.rest;
      for (const { event, data } of parsed.events) {
        if (event === "progress") {
          onProgress(data as ProposalProgress);
        } else if (event === "proposal") {
          return (data as { data: ProposalRead }).data;
        } else if (event === "error") {
          throw errorFromEnvelope(data, response.status) ?? new ApiError("MALFORMED_RESPONSE", "Unreadable error.");
        }
      }
    }
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (timeout.aborted) throw new ApiError("TIMEOUT", "The assistant took too long to answer.");
    throw new ApiError("NETWORK_ERROR", "The connection was lost while the assistant was working.");
  } finally {
    void reader.cancel().catch(() => undefined);
  }
  throw new ApiError("MALFORMED_RESPONSE", "The server ended the stream without a result.");
}
