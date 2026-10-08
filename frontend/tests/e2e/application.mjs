/**
 * End-to-end journey of a generated application, in a real browser.
 *
 *   one sentence -> a multi-screen application -> approve -> use it ->
 *   reload -> redesign a screen -> restyle the whole product -> restore the original
 *
 * Runs against the same three services as `journey.mjs` (see the README,
 * "End-to-end run"); the scripted model always builds the same recruitment product.
 *
 *   npm run e2e:app
 */
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright-core";

const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:5173";
const API_URL = `${process.env.E2E_API_URL ?? "http://localhost:8000"}/api/v1`;
const SHOTS = join(dirname(fileURLToPath(import.meta.url)), "screenshots");
const ONLY = Number(process.env.E2E_STOP_AFTER ?? Infinity);
mkdirSync(SHOTS, { recursive: true });

const browser = await chromium.launch({ channel: "chrome" });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const problems = [];
page.on("pageerror", (error) => problems.push(`pageerror: ${error.message}`));
page.on("console", (message) => {
  if (message.type() === "error") problems.push(`console: ${message.text()}`);
});

let step = 0;
const passed = [];
async function check(name, run) {
  step += 1;
  if (step > ONLY) return;
  const label = `${String(step).padStart(2, "0")} ${name}`;
  try {
    await run();
    passed.push(label);
    console.log(`  ok   ${label}`);
  } catch (error) {
    await page.screenshot({ path: join(SHOTS, `app-FAILED-${step}.png`) });
    console.error(`  FAIL ${label}\n       ${error.message.split("\n")[0]}`);
    await browser.close();
    process.exit(1);
  }
}

// Screens fade in; a picture is taken once they have settled.
const shot = async (name) => {
  await page.waitForTimeout(500);
  await page.screenshot({ path: join(SHOTS, `app-${name}.png`) });
};
const toolbar = page.getByRole("toolbar", { name: "Workspace" });
const proposal = page.getByRole("region", { name: "Proposal awaiting your decision" });
const canvas = page.locator(".g-root");
const nav = canvas.getByRole("navigation");
const expectScreen = (id) => canvas.locator(`[data-screen-id="${id}"]`).waitFor();
const expectVersion = (number) => toolbar.getByText(`v${number}`, { exact: true }).waitFor();
const column = (name) => canvas.getByRole("group", { name: new RegExp(`^${name}, `) });

async function ask(instruction) {
  const input = page.getByRole("textbox", { name: "Describe a change" });
  await input.fill(instruction);
  await input.press("Enter");
  await proposal.waitFor({ timeout: 120_000 });
}

async function apply(expectedVersion) {
  await proposal.getByRole("button", { name: /^(Apply|Restore)/ }).click();
  await expectVersion(expectedVersion);
  await proposal.waitFor({ state: "detached" });
}

const ACCOUNT = { email: `e2e-app-${Date.now()}@example.com`, password: "journey-password-1" };
let accessToken = null;

async function api(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  return (await response.json()).data;
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const workspaceId = () => new URL(page.url()).pathname.split("/")[2];
const versions = () => api(`/workspaces/${workspaceId()}/versions`);
const currentDocument = async () => {
  const workspace = await api(`/workspaces/${workspaceId()}`);
  return (await api(`/workspaces/${workspaceId()}/versions/${workspace.current_version_id}`)).document;
};
const screenOf = (document, id) => document.page.components.find((screen) => screen.id === id);

console.log(`Application journey against ${BASE_URL} (API ${API_URL})`);

await check("sign up and open an empty workspace", async () => {
  await page.goto(`${BASE_URL}/login`);
  await page.getByRole("button", { name: "Create an account" }).click();
  await page.getByLabel("Email").fill(ACCOUNT.email);
  await page.getByLabel(/^Password/).fill(ACCOUNT.password);
  await page.getByRole("button", { name: "Create account" }).click();
  await page.getByRole("heading", { name: "Workspaces", exact: true }).waitFor();
  accessToken = await page.evaluate(() => JSON.parse(localStorage.getItem("generative-ui.session")).state.token);
  await page.getByRole("button", { name: "New workspace" }).first().click();
  await page.waitForURL(/\/workspaces\/[0-9a-f-]{36}$/);
  await page.getByRole("heading", { name: "What do you want to build?" }).waitFor();
  await shot("01-empty");
});

await check("one sentence builds an application: a proposal, with real progress, nothing saved", async () => {
  const input = page.getByRole("textbox", { name: "Describe a change" });
  await input.fill("Build me a modern AI recruitment SaaS.");
  await input.press("Enter");
  await page.getByRole("heading", { name: "Building your application" }).waitFor();
  await shot("02-building");
  await proposal.waitFor({ timeout: 120_000 });
  await proposal.getByText("New application").waitFor();
  const job = await api(`/generation/jobs?workspace_id=${workspaceId()}`);
  assert(job.status === "ready" && job.stage === "ready" && job.progress === 100, "the job should have finished");
  assert((await versions()).length === 0, "a proposal must not create a version");
  // With nothing on the canvas yet, the draft is shown straight away, as a preview.
  await page.getByText("Nothing is saved until you apply it").waitFor();
  await expectScreen("dashboard");
  await shot("03-proposal");
});

await check("the summary describes the whole product and opens any of its screens", async () => {
  const screens = proposal.getByRole("list", { name: "Screens" });
  assert((await screens.getByRole("button").count()) === 7, "seven screens are proposed");
  await proposal.getByText("Premium SaaS").waitFor();
  await proposal.getByText("Sidebar navigation").waitFor();
  await proposal.getByText(/Candidates \(\d+\)/).waitFor();
  await screens.getByRole("button", { name: "Pipeline" }).click();
  await expectScreen("pipeline");
  await column("Interview").waitFor();
  await shot("04-preview-pipeline");
  // A preview can be explored, but it cannot change anything.
  await canvas.getByRole("button", { name: /^Move to / }).first().click();
  await page.getByText("Apply this version to use its actions.").waitFor();
});

await check("approve it: the application is version 1", async () => {
  await proposal.getByRole("button", { name: "Apply application" }).click();
  await expectVersion(1);
  const saved = await versions();
  assert(saved.length === 1 && saved[0].source === "ai_generation", "version 1 should exist");
  const application = await api(`/workspaces/${workspaceId()}/application`);
  assert(application.summary.screens.length === 7, "the saved application has seven screens");
  assert(application.unreachable_screen_ids.length === 0, "every screen can be reached");
  await expectScreen("dashboard");
  await shot("05-dashboard");
});

await check("screens are connected: navigation, a list, a record, and back", async () => {
  await nav.getByRole("button", { name: "Candidates" }).click();
  await expectScreen("candidates");
  await shot("06-candidates");
  await canvas.getByRole("button", { name: "Open Jonas Lindqvist" }).click();
  await expectScreen("candidate_detail");
  await canvas.getByRole("heading", { name: "Jonas Lindqvist" }).waitFor();
  assert(new URL(page.url()).searchParams.get("at") === "/candidates/cand-002", "the place is in the URL");
  await shot("07-candidate");
  await page.goBack();
  await expectScreen("candidates");
});

await check("acting on a record changes the data everywhere, without a new version", async () => {
  await nav.getByRole("button", { name: "Pipeline" }).click();
  await expectScreen("pipeline");
  const card = column("Screening").getByRole("article").filter({ hasText: "Jonas Lindqvist" });
  await card.getByRole("button", { name: "Move to Interview" }).click();
  await column("Interview").getByText("Jonas Lindqvist").waitFor();
  await shot("08-pipeline-moved");
  await nav.getByRole("button", { name: "Candidates" }).click();
  await canvas.getByRole("button", { name: "Open Jonas Lindqvist" }).click();
  await canvas.locator('[data-component-id="candidate_detail_header"]').getByText("Interview", { exact: true }).first().waitFor();
  assert((await versions()).length === 1, "using the application must not create versions");
});

await check("a form creates a record and returns to its list", async () => {
  await nav.getByRole("button", { name: "Jobs" }).click();
  await canvas.getByRole("button", { name: "Create job" }).click();
  await expectScreen("job_new");
  await canvas.getByLabel(/^Title/).fill("Staff Data Engineer");
  await canvas.getByLabel(/^Department/).fill("Data");
  await shot("09-new-job");
  await canvas.locator("form").getByRole("button").click();
  await expectScreen("jobs");
  await canvas.getByRole("cell", { name: "Staff Data Engineer" }).waitFor();
});

await check("reload: same version, same screen, same data", async () => {
  await nav.getByRole("button", { name: "Pipeline" }).click();
  await expectScreen("pipeline");
  await page.reload();
  await expectVersion(1);
  await expectScreen("pipeline");
  await column("Interview").getByText("Jonas Lindqvist").waitFor();
  const stored = await page.evaluate(() => Object.keys(localStorage));
  assert(
    stored.every((key) => ["generative-ui.preferences", "generative-ui.session"].includes(key)),
    `the browser keeps no application state, found ${stored}`,
  );
});

await check("screen-level edit: redesign the dashboard, and only the dashboard", async () => {
  await nav.getByRole("button", { name: "Dashboard" }).click();
  await expectScreen("dashboard");
  const before = await currentDocument();
  await ask("Redesign the dashboard");
  await proposal.getByRole("button", { name: /Preview/ }).click();
  await shot("10-dashboard-redesign-preview");
  await apply(2);
  const after = await currentDocument();
  assert(
    JSON.stringify(screenOf(before, "dashboard")) !== JSON.stringify(screenOf(after, "dashboard")),
    "the dashboard should have changed",
  );
  for (const id of ["jobs", "job_new", "candidates", "candidate_detail", "pipeline", "interviews"]) {
    assert(
      JSON.stringify(screenOf(before, id)) === JSON.stringify(screenOf(after, id)),
      `“${id}” must be untouched by a dashboard redesign`,
    );
  }
  assert(JSON.stringify(before.theme) === JSON.stringify(after.theme), "the look is unchanged");
  await shot("11-dashboard-v2");
});

await check("application-level edit: a more premium look, no screen regenerated", async () => {
  const before = await currentDocument();
  await ask("Make the entire application more premium");
  await proposal.getByRole("button", { name: /Preview/ }).click();
  await shot("12-premium-preview");
  await apply(3);
  const after = await currentDocument();
  assert(JSON.stringify(before.theme) !== JSON.stringify(after.theme), "the look should have changed");
  assert(JSON.stringify(before.page) === JSON.stringify(after.page), "no screen was regenerated to restyle");
  await nav.getByRole("button", { name: "Pipeline" }).click();
  await column("Interview").getByText("Jonas Lindqvist").waitFor();
  await shot("13-premium-pipeline");
});

await check("restore the original: version 1 comes back as version 4, history intact", async () => {
  await ask("Go back to the original version");
  await proposal.getByRole("button", { name: "Restore version 1" }).waitFor();
  await apply(4);
  const saved = await versions();
  assert(saved.length === 4, "history keeps every version");
  assert(saved[0].description === "Restored from Version 1", "version 4 is a restore of version 1");
  const first = (await api(`/workspaces/${workspaceId()}/versions/${saved.at(-1).id}`)).document;
  assert(JSON.stringify(first) === JSON.stringify(await currentDocument()), "the restored document equals version 1");
  // The data the user changed belongs to the workspace, not to a version.
  await column("Interview").getByText("Jonas Lindqvist").waitFor();
});

await check("direct editing works inside a screen and saves as a version", async () => {
  await nav.getByRole("button", { name: "Dashboard" }).click();
  await toolbar.getByRole("radio", { name: "Edit" }).click();
  await canvas.locator('[data-component-type="chart"]').first().click({ position: { x: 30, y: 12 } });
  const inspector = page.getByRole("complementary", { name: "Inspector" });
  await inspector.getByRole("button", { name: "Full", exact: true }).click();
  await toolbar.getByText("1 unsaved change").waitFor();
  await shot("14-edit-mode");
  await toolbar.getByRole("button", { name: "Save version" }).click();
  await expectVersion(5);
  await toolbar.getByRole("radio", { name: "View" }).click();
});

await check("the navigation style is a design choice, not a regeneration", async () => {
  const before = await currentDocument();
  await toolbar.getByRole("button", { name: "Design" }).click();
  await page.getByRole("radiogroup", { name: "Navigation" }).getByRole("radio", { name: "Top bar" }).click();
  await canvas.locator('.g-app[data-nav="topbar"]').waitFor();
  await page.keyboard.press("Escape");
  await toolbar.getByRole("button", { name: "Save version" }).click();
  await expectVersion(6);
  const after = await currentDocument();
  assert(after.application.navigation.style === "topbar", "the navigation style is saved");
  assert(JSON.stringify(before.page) === JSON.stringify(after.page), "screens are untouched");
  await shot("15-topbar");
});

await check("the screen menu reaches screens that are not in the navigation", async () => {
  await toolbar.getByRole("button", { name: /Dashboard|Screens/ }).click();
  await page.getByRole("listbox", { name: "Screens" }).getByRole("option", { name: /Candidate/ }).last().click();
  await expectScreen("candidate_detail");
  await canvas.locator('[data-component-id="candidate_detail_header"]').getByRole("heading").waitFor();
});

await check("responsive: the application works at mobile width", async () => {
  await nav.getByRole("button", { name: "Dashboard" }).click();
  await toolbar.getByRole("radio", { name: "Mobile width" }).click();
  await page.waitForFunction(() => document.querySelector(".g-root").getBoundingClientRect().width < 420);
  const overflow = await page.evaluate(() => {
    const root = document.querySelector(".g-root");
    return root.scrollWidth - root.clientWidth;
  });
  assert(overflow <= 1, `the mobile layout must not scroll sideways (overflow ${overflow}px)`);
  await shot("16-mobile");
  await toolbar.getByRole("radio", { name: "Desktop width" }).click();
});

await check("no script errors were reported by the browser", async () => {
  assert(problems.length === 0, problems.join(" | "));
});

await browser.close();
console.log(`\n${passed.length} steps passed. Screenshots: ${SHOTS}`);
