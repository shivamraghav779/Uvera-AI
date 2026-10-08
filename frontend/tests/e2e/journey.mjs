/**
 * End-to-end journey through the real stack, in a real browser.
 *
 *   browser -> Vite frontend -> FastAPI -> PostgreSQL
 *                                  \-> scripted LLM stand-in (backend/scripts/dev_llm.py)
 *
 * Start the three services first (see the README, "End-to-end run"), then:
 *
 *   npm run e2e
 *
 * Uses the Chrome already installed on the machine (no browser download).
 * Environment: E2E_BASE_URL (default http://localhost:5173),
 *              E2E_API_URL  (default http://localhost:8000).
 */
import { mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright-core";

const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:5173";
const API_URL = `${process.env.E2E_API_URL ?? "http://localhost:8000"}/api/v1`;
const SHOTS = join(dirname(fileURLToPath(import.meta.url)), "screenshots");
mkdirSync(SHOTS, { recursive: true });

const browser = await chromium.launch({ channel: "chrome" });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const problems = [];
page.on("pageerror", (error) => problems.push(`pageerror: ${error.message}`));
page.on("console", (message) => {
  // 409 (stale version) and 401 (wrong password) are expected answers in this journey.
  const expected = /\b(401|409)\b/.test(message.text());
  if (message.type() === "error" && !expected) problems.push(`console: ${message.text()}`);
});

let step = 0;
const passed = [];
async function check(name, run) {
  step += 1;
  const label = `${String(step).padStart(2, "0")} ${name}`;
  try {
    await run();
    passed.push(label);
    console.log(`  ok   ${label}`);
  } catch (error) {
    await page.screenshot({ path: join(SHOTS, `FAILED-${step}.png`) });
    console.error(`  FAIL ${label}\n       ${error.message.split("\n")[0]}`);
    await browser.close();
    process.exit(1);
  }
}

const shot = (name) => page.screenshot({ path: join(SHOTS, `${name}.png`) });
const toolbar = page.getByRole("toolbar", { name: "Workspace" });
const proposal = page.getByRole("region", { name: "Proposal awaiting your decision" });
const canvas = page.locator(".g-root");
const component = (id) => canvas.locator(`[data-component-id="${id}"]`);
const expectVersion = (number) => toolbar.getByText(`v${number}`, { exact: true }).waitFor();

async function ask(instruction) {
  const input = page.getByRole("textbox", { name: "Describe a change" });
  await input.fill(instruction);
  await input.press("Enter");
  await proposal.waitFor();
}

async function apply(expectedVersion) {
  await proposal.getByRole("button", { name: /^(Apply|Restore)/ }).click();
  await expectVersion(expectedVersion);
  await proposal.waitFor({ state: "detached" });
}

const ACCOUNT = { email: `e2e-${Date.now()}@example.com`, password: "journey-password-1" };
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
const metricOrder = () =>
  canvas.locator('[data-component-type="metric"]').evaluateAll((nodes) => nodes.map((n) => n.dataset.componentId));

console.log(`Journey against ${BASE_URL} (API ${API_URL})`);

await check("visitors are sent to sign in; creating an account opens the app", async () => {
  await page.goto(`${BASE_URL}/workspaces`);
  await page.waitForURL(/\/login$/);
  await page.getByRole("button", { name: "Create an account" }).click();
  await page.getByLabel("Email").fill(ACCOUNT.email);
  await page.getByLabel(/^Password/).fill(ACCOUNT.password);
  await shot("00-sign-up");
  await page.getByRole("button", { name: "Create account" }).click();
  await page.getByRole("heading", { name: "Workspaces", exact: true }).waitFor();
  accessToken = await page.evaluate(
    () => JSON.parse(localStorage.getItem("generative-ui.session")).state.token,
  );
  assert(accessToken, "a session token should be stored after signing up");
  const anonymous = await fetch(`${API_URL}/workspaces`);
  assert(anonymous.status === 401, "the API must refuse requests without a token");
});

await check("create a workspace and see the empty state", async () => {
  await page.goto(`${BASE_URL}/workspaces`);
  await page.getByRole("button", { name: "New workspace" }).first().click();
  await page.waitForURL(/\/workspaces\/[0-9a-f-]{36}$/);
  await page.getByRole("heading", { name: "What do you want to build?" }).waitFor();
  await shot("01-empty-workspace");
});

await check("generate a dashboard: shown as a preview, not saved", async () => {
  // Naming a look keeps the journey repeatable: an unspecified one gets a random palette.
  await ask("Create a light sales dashboard with revenue, orders and monthly sales.");
  await page.getByText("Nothing is saved until you apply it").waitFor();
  await canvas.getByRole("heading", { name: "Sales Dashboard" }).waitFor();
  await component("monthly_revenue_chart").locator("svg.recharts-surface").waitFor();
  const versions = await api(`/workspaces/${workspaceId()}/versions`);
  assert(versions.length === 0, "a proposal must not create a version");
  await shot("02-proposal-preview");
});

await check("approve it: version 1 is persisted", async () => {
  await apply(1);
  const versions = await api(`/workspaces/${workspaceId()}/versions`);
  assert(versions.length === 1 && versions[0].source === "ai_generation", "version 1 should exist");
  await shot("03-version-1");
});

await check("theme change by instruction: preview, then version 2", async () => {
  await ask("Make it dark");
  assert((await canvas.getAttribute("data-theme-mode")) === "light", "nothing changes before preview/apply");
  await proposal.getByRole("button", { name: "Preview" }).click();
  await page.locator('.g-root[data-theme-mode="dark"]').waitFor();
  await shot("04-dark-preview");
  await apply(2);
  assert((await canvas.getAttribute("data-theme-mode")) === "dark", "theme should be dark");
});

await check("move a component by instruction: version 3", async () => {
  await ask("Move the revenue card to the top right");
  await proposal.getByText("Move “Revenue” after “Top region”").waitFor();
  await apply(3);
  const order = await metricOrder();
  assert(order.at(-1) === "revenue_metric", `revenue should be last in its row, got ${order}`);
});

await check("replace the table with a bar chart: version 4", async () => {
  await ask("Replace the regional table with a bar chart");
  await apply(4);
  assert(
    (await component("regional_table").getAttribute("data-component-type")) === "chart",
    "the component should now be a chart with the same id",
  );
  await shot("05-version-4");
});

await check("reload the browser: version 4 comes back exactly", async () => {
  const before = await api(`/workspaces/${workspaceId()}`);
  await page.reload();
  await expectVersion(4);
  await page.locator('.g-root[data-theme-mode="dark"]').waitFor();
  assert((await metricOrder()).at(-1) === "revenue_metric", "layout should persist");
  assert(
    (await component("regional_table").getAttribute("data-component-type")) === "chart",
    "replacement should persist",
  );
  const stored = await page.evaluate(() =>
    Object.fromEntries(Object.entries(localStorage).map(([key, value]) => [key, value.length])),
  );
  const allowed = ["generative-ui.preferences", "generative-ui.session"];
  assert(
    Object.keys(stored).every((key) => allowed.includes(key)),
    `only preferences and the session may live in localStorage, found ${Object.keys(stored)}`,
  );
  assert(
    Object.values(stored).every((size) => size < 2000),
    "localStorage holds no workspace content",
  );
  assert(before.current_version_number === 4, "server should be at version 4");
});

await check("restore by instruction: preview version 3, approve, version 5 is a copy", async () => {
  await ask("Go back to the version before I replaced the table");
  await proposal.getByRole("button", { name: "Restore version 3" }).waitFor();
  await proposal.getByRole("button", { name: "Preview" }).click();
  await page.getByText("Version 3", { exact: true }).first().waitFor();
  await canvas.locator('[data-component-id="regional_table"][data-component-type="table"]').waitFor();
  await apply(5);
  const versions = await api(`/workspaces/${workspaceId()}/versions`);
  assert(versions.length === 5, "history must keep all versions");
  assert(versions[0].description === "Restored from Version 3", "version 5 should be a restore");
  assert(versions[1].description.startsWith("Replace"), "version 4 must be untouched");
});

await check("version history panel lists every version", async () => {
  await toolbar.getByRole("button", { name: "Version history" }).click();
  const history = page.getByRole("complementary", { name: "Version history" });
  await history.getByText("Version 5").waitFor();
  assert((await history.getByRole("listitem").count()) === 5, "five versions listed");
  await history.getByText("Restored from Version 3").waitFor();
  await shot("06-version-history");
});

await check("compare an old version with the current one", async () => {
  const history = page.getByRole("complementary", { name: "Version history" });
  await history.getByRole("listitem").filter({ hasText: "Version 1" }).getByRole("button", { name: "Compare" }).click();
  const dialog = page.getByRole("dialog", { name: /Version 1 → Version 5/ });
  await dialog.getByText("Theme changed from light to dark").waitFor();
  await shot("07-compare");
  await dialog.getByRole("button", { name: "Close" }).first().click();
});

await check("preview an old version read-only without changing the current one", async () => {
  const history = page.getByRole("complementary", { name: "Version history" });
  await history.getByRole("listitem").filter({ hasText: "Version 1" }).getByRole("button", { name: "Preview" }).click();
  await page.getByText("read-only. Your current version is unchanged.").waitFor();
  await page.locator('.g-root[data-theme-mode="light"]').waitFor();
  await page.getByRole("button", { name: "Back to current" }).click();
  await page.locator('.g-root[data-theme-mode="dark"]').waitFor();
  await expectVersion(5);
  await toolbar.getByRole("button", { name: "Version history" }).click();
});

await check("switch framework: same components, Material adapter, version 6", async () => {
  const before = await api(`/workspaces/${workspaceId()}`);
  const pageBefore = (await api(`/workspaces/${workspaceId()}/versions/${before.current_version_id}`)).document.page;
  await ask("Now make it use a Material UI style");
  await apply(6);
  await page.locator('.g-root[data-framework="material"]').waitFor();
  const after = await api(`/workspaces/${workspaceId()}`);
  const pageAfter = (await api(`/workspaces/${workspaceId()}/versions/${after.current_version_id}`)).document.page;
  assert(JSON.stringify(pageBefore) === JSON.stringify(pageAfter), "the semantic UI must be unchanged");
  await shot("08-material");
});

await check("edit mode: select, resize, undo/redo, save as version 7", async () => {
  await toolbar.getByRole("radio", { name: "Edit" }).click();
  await component("monthly_revenue_chart").click({ position: { x: 40, y: 20 } });
  const inspector = page.getByRole("complementary", { name: "Inspector" });
  await inspector.getByText("monthly_revenue_chart").first().waitFor();
  await shot("09-edit-mode");
  await inspector.getByRole("button", { name: "Full", exact: true }).click();
  await toolbar.getByText("1 unsaved change").waitFor();
  await toolbar.getByRole("button", { name: "Undo (unsaved edits)" }).click();
  await toolbar.getByText("1 unsaved change").waitFor({ state: "detached" });
  await toolbar.getByRole("button", { name: "Redo" }).click();
  await toolbar.getByText("1 unsaved change").waitFor();
  let versions = await api(`/workspaces/${workspaceId()}/versions`);
  assert(versions.length === 6, "local edits are not versions until saved");
  await toolbar.getByRole("button", { name: "Save version" }).click();
  await expectVersion(7);
  versions = await api(`/workspaces/${workspaceId()}/versions`);
  assert(versions[0].source === "manual_edit", "version 7 should be a manual edit");
});

await check("selection is sent as context; rejecting a proposal changes nothing", async () => {
  await component("regional_table").click({ position: { x: 40, y: 20 } });
  await page.getByText("About regional_table").waitFor();
  await ask("Make this half width");
  await proposal.getByText("Resize “Sales by region” to 6 of 12 columns wide").waitFor();
  await proposal.getByRole("button", { name: "Reject" }).click();
  await proposal.waitFor({ state: "detached" });
  await expectVersion(7);
  const versions = await api(`/workspaces/${workspaceId()}/versions`);
  assert(versions.length === 7, "a rejected proposal must not create a version");
});

await check("stale write is refused and the user can reload the latest version", async () => {
  const workspace = await api(`/workspaces/${workspaceId()}`);
  // Another client saves version 8 behind this browser's back.
  await api(`/workspaces/${workspaceId()}/versions`, {
    method: "POST",
    body: {
      base_version_id: workspace.current_version_id,
      operations: [{ type: "UPDATE", target: "page", props: { title: "Sales Dashboard (edited elsewhere)" } }],
    },
  });
  const inspector = page.getByRole("complementary", { name: "Inspector" });
  await inspector.getByRole("button", { name: "6/12", exact: true }).click();
  await toolbar.getByRole("button", { name: "Save version" }).click();
  const dialog = page.getByRole("dialog", { name: "Workspace changed" });
  await dialog.waitFor();
  await shot("10-conflict");
  const versions = await api(`/workspaces/${workspaceId()}/versions`);
  assert(versions.length === 8, "the stale write must not have been saved");
  await dialog.getByRole("button", { name: "Reload latest version" }).click();
  await expectVersion(8);
  await canvas.getByRole("heading", { name: "Sales Dashboard (edited elsewhere)" }).waitFor();
});

await check("view mode: a filter runs an allowlisted action and updates the table", async () => {
  await toolbar.getByRole("radio", { name: "View" }).click();
  const table = canvas.getByRole("table", { name: "Sales by region" });
  assert((await table.getByRole("row").count()) === 5, "four regions plus the header");
  await canvas.getByRole("combobox", { name: "Region" }).selectOption("South");
  await page.waitForFunction(
    () => document.querySelectorAll('[data-component-id="regional_table"] tbody tr').length === 1,
  );
});

await check("responsive: the layout collapses at mobile width", async () => {
  await toolbar.getByRole("radio", { name: "Mobile width" }).click();
  await page.waitForFunction(() => {
    const cells = [...document.querySelectorAll('[data-component-type="metric"]')];
    return cells.length > 1 && new Set(cells.map((cell) => cell.getBoundingClientRect().left)).size === 1;
  });
  await shot("11-mobile");
  await toolbar.getByRole("radio", { name: "Desktop width" }).click();
});

await check("an uploaded CSV becomes a dataset the workspace can use", async () => {
  await page.goto(`${BASE_URL}/settings`);
  await page.getByLabel("Name").fill("Support tickets");
  await page.getByLabel(/^Rows/).fill("status,hours\nopen,12\nclosed,30\n");
  await page.getByRole("button", { name: "Add dataset" }).click();
  await page.getByText("Dataset “support_tickets” is ready to use.").waitFor();
  const datasets = await api("/data-sources/datasets");
  assert(
    datasets.some((dataset) => dataset.name === "support_tickets"),
    "the uploaded dataset should be offered to the assistant",
  );
  await shot("12-data-sources");
});

await check("signing out locks the app; signing in again restores the same workspace", async () => {
  await page.getByRole("button", { name: "Sign out" }).click();
  await page.waitForURL(/\/login$/);
  await page.getByLabel("Email").fill(ACCOUNT.email);
  await page.getByLabel(/^Password/).fill("wrong-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.getByRole("alert").getByText("Incorrect email or password.").waitFor();
  await page.getByLabel(/^Password/).fill(ACCOUNT.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.getByRole("link", { name: /Sales Dashboard/ }).first().click();
  await expectVersion(8);
  await canvas.getByRole("heading", { name: "Sales Dashboard (edited elsewhere)" }).waitFor();
});

await check("no script errors were reported by the browser", async () => {
  assert(problems.length === 0, problems.join(" | "));
});

await browser.close();
console.log(`\n${passed.length} steps passed. Screenshots: ${SHOTS}`);
