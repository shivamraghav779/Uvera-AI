/**
 * Opens every entry of the design vocabulary in a real browser and checks that
 * it works as a standalone page: it renders something, its script raises no
 * error, and none of its CSS rules is dead (a rule the browser dropped whole).
 *
 *   cd backend && poetry run python -m scripts.export_vocabulary /tmp/vocabulary
 *   cd frontend && node tests/e2e/vocabulary.mjs /tmp/vocabulary [--sheets DIR]
 *
 * With --sheets it also saves one contact sheet per section for a look by eye.
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

import { chromium } from "playwright-core";

const root = resolve(process.argv[2] ?? "");
const sheetsAt = process.argv.indexOf("--sheets");
const sheets = sheetsAt > 0 ? resolve(process.argv[sheetsAt + 1]) : null;
const index = JSON.parse(readFileSync(join(root, "index.json"), "utf8"));

const browser = await chromium.launch({ channel: "chrome" });
const context = await browser.newContext({ viewport: { width: 900, height: 620 }, acceptDownloads: true });
const failures = [];

async function check(entry) {
  const page = await context.newPage();
  const problems = [];
  page.on("pageerror", (error) => problems.push(`script error: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") problems.push(`console: ${message.text()}`);
  });
  // An entry may open a share sheet, a download or a dialog when used; none may hang the run.
  page.on("dialog", (dialog) => dialog.dismiss().catch(() => {}));
  await page.addInitScript(() => {
    if (navigator.share) navigator.share = () => Promise.reject(new DOMException("unavailable", "NotAllowedError"));
  });
  try {
    await page.goto(pathToFileURL(join(root, entry.slug, "index.html")).href);
    await page.waitForTimeout(60);
    const report = await page.evaluate(() => {
      const dead = [];
      const walk = (rules) => {
        for (const rule of rules) {
          if (rule.cssRules && rule.type !== CSSRule.STYLE_RULE) walk(rule.cssRules);
          else if (rule.type === CSSRule.STYLE_RULE && rule.style.length === 0) dead.push(rule.selectorText);
        }
      };
      for (const sheet of document.styleSheets) walk(sheet.cssRules);
      const visible = [...document.body.querySelectorAll("*")].some((element) => {
        const box = element.getBoundingClientRect();
        return box.width > 4 && box.height > 4 && !["SCRIPT", "STYLE"].includes(element.tagName);
      });
      return { dead, visible, sideways: document.documentElement.scrollWidth > innerWidth + 1 };
    });
    if (!report.visible) problems.push("renders nothing visible");
    if (report.sideways) problems.push("overflows the page sideways");
    for (const selector of report.dead) problems.push(`dead CSS rule: ${selector}`);
    // A light interaction: scripts that only fail when used should fail here.
    await page.mouse.move(450, 310);
    await page.mouse.click(450, 310);
    await page.keyboard.press("Tab");
    await page.waitForTimeout(40);
  } catch (error) {
    problems.push(`could not be exercised: ${error.message.split("\n")[0]}`);
  }
  await page.close().catch(() => {});
  if (problems.length > 0) failures.push({ slug: entry.slug, problems: [...new Set(problems)] });
}

for (const entry of index) await check(entry);

if (sheets) {
  mkdirSync(sheets, { recursive: true });
  const byCategory = Map.groupBy(index, (entry) => `${entry.slug.split("/")[0]}-${entry.category}`);
  const page = await context.newPage();
  // Twenty to a sheet: a browser does not paint frames far below the fold.
  const PER_SHEET = 20;
  await page.setViewportSize({ width: 1500, height: 990 });
  for (const [category, members] of byCategory) {
    for (let start = 0; start < members.length; start += PER_SHEET) {
      const cells = members
        .slice(start, start + PER_SHEET)
        .map(
          (entry) =>
            `<figure><iframe src="${pathToFileURL(join(root, entry.slug, "index.html")).href}"></iframe>` +
            `<figcaption>${entry.slug.split("/")[1]}</figcaption></figure>`,
        )
        .join("");
      const html =
        `<style>body{margin:0;background:#05060a;display:grid;grid-template-columns:repeat(5,1fr);gap:6px;padding:6px}` +
        `figure{margin:0}iframe{width:200%;height:440px;border:0;transform:scale(.5);transform-origin:0 0;margin-bottom:-220px;margin-right:-100%}` +
        `figcaption{font:11px system-ui;color:#9aa;padding:2px 4px;white-space:nowrap;overflow:hidden}</style>${cells}`;
      const name = `${category}-${1 + start / PER_SHEET}`;
      writeFileSync(join(sheets, `${name}.html`), html);
      await page.goto(pathToFileURL(join(sheets, `${name}.html`)).href);
      await page.waitForTimeout(900);
      await page.screenshot({ path: join(sheets, `${name}.png`) });
    }
  }
}

await browser.close();
for (const failure of failures) console.error(`FAIL ${failure.slug}\n     ${failure.problems.join("\n     ")}`);
console.log(`${index.length - failures.length} of ${index.length} entries pass.`);
process.exit(failures.length > 0 ? 1 : 0);
