/**
 * Builds applications from prompts with whatever model the backend is configured
 * with, applies them, and photographs every screen. For judging design quality
 * with real models; nothing is asserted beyond "it built and rendered".
 *
 *   npm run e2e:showcase -- "Build a premium website for an architecture studio."
 *
 * Environment: E2E_BASE_URL, E2E_API_URL (as for the journeys),
 *              SHOWCASE_DIR (default tests/e2e/screenshots/showcase).
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright-core";

const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:5173";
const API_URL = `${process.env.E2E_API_URL ?? "http://localhost:8000"}/api/v1`;
const OUT = process.env.SHOWCASE_DIR ?? join(dirname(fileURLToPath(import.meta.url)), "screenshots", "showcase");
const PROMPTS = process.argv.slice(2);
if (PROMPTS.length === 0) {
  console.error('Give at least one prompt, e.g. "Build me a modern AI recruitment SaaS."');
  process.exit(2);
}
mkdirSync(OUT, { recursive: true });

const account = { email: `showcase-${Date.now()}@example.com`, password: "showcase-password-1" };
let token = null;

async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const payload = await response.json();
  if (!payload.success) throw new Error(`${path}: ${payload.error?.code} ${payload.error?.message}`);
  return payload.data;
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const slug = (text) => text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40);

const session = await api("/auth/register", { method: "POST", body: account });
token = session.access_token;

const browser = await chromium.launch({ channel: "chrome" });
const context = await browser.newContext({ viewport: { width: 1440, height: 1500 } });
await context.addInitScript(
  ([value]) => localStorage.setItem("generative-ui.session", value),
  [JSON.stringify({ state: { token, user: session.user }, version: 1 })],
);
const page = await context.newPage();

for (const prompt of PROMPTS) {
  const name = slug(prompt);
  console.log(`\n${prompt}`);
  const workspace = await api("/workspaces", { method: "POST", body: {} });
  let job = await api("/generation/jobs", { method: "POST", body: { workspace_id: workspace.id, instruction: prompt } });
  const started = Date.now();
  let last = "";
  while (job.status === "queued" || job.status === "running") {
    await wait(2000);
    job = await api(`/generation/jobs/${job.id}`);
    const line = `${job.stage} ${job.progress}% ${job.detail ?? ""}`;
    if (line !== last) console.log(`  ${line}`);
    last = line;
  }
  const seconds = Math.round((Date.now() - started) / 1000);
  if (job.status !== "ready") {
    console.error(`  ${job.status} after ${seconds}s: ${job.error?.code} ${job.error?.message}`);
    continue;
  }
  const proposal = job.proposal;
  writeFileSync(join(OUT, `${name}.json`), JSON.stringify(proposal.document, null, 2));
  if (!proposal.application) {
    console.log(`  built a single view in ${seconds}s`);
  } else {
    const { application: summary, quality } = proposal;
    console.log(
      `  ${summary.name}: ${summary.screens.length} screens, ${summary.design.style_name}/${summary.design.palette}, ` +
        `${summary.navigation_style} navigation, ${summary.asset_count} images, review ${quality?.score}/100, ${seconds}s`,
    );
    for (const screen of summary.screens.filter((item) => item.failed)) console.log(`  failed: ${screen.title}`);
  }
  await api(`/workspaces/${workspace.id}/versions`, {
    method: "POST",
    body: { base_version_id: null, source: "ai_generation", proposal_id: proposal.proposal_id, document: proposal.document },
  });

  const screens = proposal.application?.screens ?? [{ id: "view", route: "/" }];
  for (const [index, screen] of screens.entries()) {
    await page.goto(`${BASE_URL}/workspaces/${workspace.id}?at=${encodeURIComponent(screen.route)}`);
    const root = page.locator(".g-root");
    await root.waitFor();
    // Let images arrive (they are generated or searched for on demand) and animations settle.
    await page.waitForLoadState("networkidle").catch(() => {});
    await wait(900);
    await page.screenshot({ path: join(OUT, `${name}-${String(index + 1).padStart(2, "0")}-${screen.id}.png`) });
  }
}

await browser.close();
console.log(`\nScreenshots and documents: ${OUT}`);
