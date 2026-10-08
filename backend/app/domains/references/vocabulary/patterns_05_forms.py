"""Patterns 151-190: forms and inputs."""

from app.domains.references.vocabulary.base import FIELD, Item, Section

HINT = ".hint { font-size: 12px; color: var(--muted); }\n.hint.bad { color: var(--danger); }\n"
ADORN = """\
.adorn { display: flex; align-items: center; height: 42px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface);
  transition: border-color .15s, box-shadow .15s; }
.adorn:focus-within { border-color: var(--primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 30%, transparent); }
.adorn input, .adorn select { flex: 1; min-width: 0; height: 100%; padding: 0 12px; border: 0; outline: 0; background: none; }
.adorn > span, .adorn > button { padding: 0 12px; color: var(--muted); border: 0; background: none; white-space: nowrap; }
"""
MENU = """\
.menu { position: absolute; inset: calc(100% + 6px) 0 auto; z-index: 3; max-height: 200px; overflow: auto; margin: 0; padding: 6px; list-style: none;
  border: 1px solid var(--border); border-radius: 10px; background: var(--surface-2); box-shadow: var(--shadow); }
.menu[hidden] { display: none; }
.menu li { padding: 7px 10px; border-radius: 7px; cursor: pointer; }
.menu li[aria-selected="true"], .menu li:hover { background: color-mix(in srgb, var(--primary) 22%, transparent); }
"""
EDITOR = """\
.ed { width: min(560px, 100%); border: 1px solid var(--border); border-radius: 12px; background: var(--surface); overflow: hidden; }
.ed .bar { display: flex; gap: 4px; padding: 6px; border-bottom: 1px solid var(--border); background: var(--surface-2); }
.ed .bar button { min-width: 32px; height: 30px; padding: 0 8px; border: 0; border-radius: 7px; background: none; color: var(--muted); }
.ed .bar button:hover, .ed .bar button[aria-pressed="true"] { background: var(--surface); color: var(--fg); }
.ed textarea, .ed .area { display: block; width: 100%; min-height: 150px; padding: 14px; border: 0; outline: 0; background: none; resize: vertical; }
.ed .foot { display: flex; justify-content: space-between; padding: 6px 12px; border-top: 1px solid var(--border); font-size: 12px; color: var(--muted); }
"""
CODE = ".code { font: 13px/1.6 var(--mono); tab-size: 2; white-space: pre; }\n"


def field(
    name: str, label: str, control: str, note: str, css: str = "", js: str = "", hint: str = ""
) -> Item:
    tail = f'<span class="hint" id="h">{hint}</span>' if hint else ""
    return Item(
        name,
        f'<div class="field"><label for="f">{label}</label>{control}{tail}</div>',
        FIELD + HINT + css,
        js,
        note,
    )


COMBO_JS = """\
const OPTIONS = __OPTIONS__;
const input = document.querySelector(".combo input");
const menu = document.querySelector(".menu");
let active = -1;
const visible = () => [...menu.children];
const render = () => {
  const query = input.value.trim().toLowerCase();
  const matches = OPTIONS.filter((option) => option.toLowerCase().includes(query));
  menu.replaceChildren(...matches.map((text, index) => Object.assign(document.createElement("li"), { textContent: text, id: `opt-${index}`, role: "option" })));
  if (__ALLOW_NEW__ && query && !matches.some((option) => option.toLowerCase() === query)) {
    menu.append(Object.assign(document.createElement("li"), { textContent: `Use “${input.value.trim()}”`, role: "option" }));
  }
  active = -1;
  menu.hidden = menu.children.length === 0;
  input.setAttribute("aria-expanded", String(!menu.hidden));
};
const mark = (index) => {
  const items = visible();
  active = (index + items.length) % items.length;
  items.forEach((item, i) => item.setAttribute("aria-selected", String(i === active)));
  input.setAttribute("aria-activedescendant", items[active]?.id ?? "");
  items[active]?.scrollIntoView({ block: "nearest" });
};
const choose = (item) => {
  input.value = item.textContent.replace(/^Use “(.*)”$/, "$1");
  menu.hidden = true;
  input.setAttribute("aria-expanded", "false");
};
input.addEventListener("input", render);
input.addEventListener("focus", render);
input.addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown") { event.preventDefault(); if (menu.hidden) render(); mark(active + 1); }
  else if (event.key === "ArrowUp") { event.preventDefault(); mark(active - 1); }
  else if (event.key === "Enter" && active >= 0) { event.preventDefault(); choose(visible()[active]); }
  else if (event.key === "Escape") menu.hidden = true;
});
menu.addEventListener("mousedown", (event) => { const item = event.target.closest("li"); if (item) { event.preventDefault(); choose(item); } });
input.addEventListener("blur", () => { menu.hidden = true; });
"""


def combo(name: str, label: str, options: list[str], allow_new: bool, note: str) -> Item:
    html = (
        f'<div class="field"><label for="f">{label}</label><div class="combo"><input id="f" class="input" role="combobox" autocomplete="off" '
        f'aria-expanded="false" aria-controls="lb" aria-autocomplete="list" placeholder="Start typing…"><ul class="menu" id="lb" role="listbox" hidden></ul></div></div>'
    )
    js = COMBO_JS.replace("__OPTIONS__", str(options).replace("'", '"')).replace(
        "__ALLOW_NEW__", "true" if allow_new else "false"
    )
    return Item(
        name,
        html,
        FIELD
        + MENU
        + ".combo { position: relative; }\n.field { height: 280px; align-content: start; }\n",
        js,
        note,
    )


TOKENS_CSS = """\
.tokens { display: flex; flex-wrap: wrap; gap: 6px; min-height: 42px; padding: 6px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); cursor: text; }
.tokens:focus-within { border-color: var(--primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 30%, transparent); }
.tokens span { display: inline-flex; align-items: center; gap: 4px; padding: 2px 4px 2px 10px; border-radius: 99px; background: color-mix(in srgb, var(--primary) 22%, transparent); font-size: 13px; }
.tokens span.bad { background: color-mix(in srgb, var(--danger) 22%, transparent); }
.tokens span button { width: 18px; height: 18px; padding: 0; border: 0; border-radius: 50%; background: none; color: var(--muted); line-height: 1; }
.tokens input { flex: 1; min-width: 80px; border: 0; outline: 0; background: none; height: 28px; }
"""
TOKENS_JS = """\
const box = document.querySelector(".tokens");
const input = box.querySelector("input");
const valid = __VALID__;
const add = (raw) => {
  const text = raw.trim().replace(/,$/, "");
  if (!text || [...box.querySelectorAll("span")].some((chip) => chip.dataset.value === text.toLowerCase())) return;
  const chip = document.createElement("span");
  chip.dataset.value = text.toLowerCase();
  if (!valid(text)) chip.className = "bad";
  const remove = Object.assign(document.createElement("button"), { type: "button", textContent: "×" });
  remove.setAttribute("aria-label", `Remove ${text}`);
  remove.addEventListener("click", () => { chip.remove(); input.focus(); });
  chip.append(text, remove);
  box.insertBefore(chip, input);
};
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" || event.key === "," || event.key === "Tab" && input.value) { if (input.value) event.preventDefault(); add(input.value); input.value = ""; }
  else if (event.key === "Backspace" && !input.value) box.querySelector("span:last-of-type")?.remove();
});
// Pasting a list adds every item.
input.addEventListener("paste", (event) => {
  event.preventDefault();
  event.clipboardData.getData("text").split(/[,;\\s]+/).forEach(add);
});
box.addEventListener("click", () => input.focus());
__SEED__.forEach(add);
"""


def tokens(name: str, label: str, seed: list[str], valid: str, note: str) -> Item:
    html = f'<div class="field"><label for="f">{label}</label><div class="tokens"><input id="f" placeholder="Add…"></div></div>'
    js = TOKENS_JS.replace("__VALID__", valid).replace("__SEED__", str(seed).replace("'", '"'))
    return Item(name, html, FIELD + TOKENS_CSS, js, note)


SECTION = Section(
    "patterns",
    "Forms & Inputs",
    151,
    (
        field(
            "Text input",
            "Full name",
            '<input id="f" class="input" placeholder="Dana Whitfield" autocomplete="name">',
            "A visible label above, placeholder as an example only.",
        ),
        field(
            "Textarea",
            "Message",
            '<textarea id="f" class="input ta" rows="3" maxlength="280" aria-describedby="h"></textarea>',
            "Grows with its content up to a limit and counts what is left.",
            ".ta { height: auto; min-height: 84px; max-height: 220px; padding: 10px 12px; resize: none; field-sizing: content; }\n",
            'const area = document.querySelector(".ta");\nconst hint = document.getElementById("h");\nconst update = () => { hint.textContent = `${area.maxLength - area.value.length} characters left`; };\narea.addEventListener("input", update);\nupdate();\n',
            "280 characters left",
        ),
        Item(
            "Search input",
            '<form class="search" role="search"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.500-3.500"/></svg><input type="search" placeholder="Search projects" aria-label="Search projects"><button type="reset" aria-label="Clear search" hidden>×</button></form>',
            ".search { display: flex; align-items: center; gap: 8px; width: min(340px, 100%); height: 42px; padding: 0 12px; border: 1px solid var(--border); border-radius: 999px; background: var(--surface); color: var(--muted); }\n.search:focus-within { border-color: var(--primary); }\n.search input { flex: 1; min-width: 0; border: 0; outline: 0; background: none; color: var(--fg); }\n.search input::-webkit-search-cancel-button { display: none; }\n.search button { border: 0; background: none; color: var(--muted); font-size: 18px; }\n",
            'const form = document.querySelector(".search");\nconst input = form.querySelector("input");\nconst clear = form.querySelector("button");\ninput.addEventListener("input", () => { clear.hidden = input.value === ""; });\nform.addEventListener("reset", () => { clear.hidden = true; input.focus(); });\nform.addEventListener("submit", (event) => event.preventDefault());\n',
            "role=search, a leading icon and a clear button that appears with text.",
        ),
        Item(
            "Password input",
            '<div class="field"><label for="f">Password</label><div class="adorn"><input id="f" type="password" autocomplete="new-password" aria-describedby="h"><button type="button" aria-pressed="false">Show</button></div><div class="meter"><i></i></div><span class="hint" id="h">Use 12 or more characters.</span></div>',
            FIELD
            + HINT
            + ADORN
            + ".meter { height: 4px; border-radius: 99px; background: var(--surface-2); overflow: hidden; }\n.meter i { display: block; height: 100%; width: 0; background: var(--danger); transition: width .25s var(--ease), background .25s; }\n",
            """\
const input = document.getElementById("f");
const reveal = document.querySelector(".adorn button");
const bar = document.querySelector(".meter i");
const hint = document.getElementById("h");
reveal.addEventListener("click", () => {
  const show = input.type === "password";
  input.type = show ? "text" : "password";
  reveal.textContent = show ? "Hide" : "Show";
  reveal.setAttribute("aria-pressed", String(show));
});
// Length dominates; variety adds a little. This is a hint, not a policy check.
const score = (value) => Math.min(4, Math.floor(value.length / 4) + (/[^a-zA-Z]/.test(value) && value.length >= 8 ? 1 : 0));
input.addEventListener("input", () => {
  const level = score(input.value);
  bar.style.width = `${level * 25}%`;
  bar.style.background = ["var(--danger)", "var(--danger)", "var(--warning)", "var(--accent)", "var(--success)"][level];
  hint.textContent = ["Use 12 or more characters.", "Too short.", "Getting there.", "Good.", "Strong."][level];
});
""",
            "Show/hide toggle and a strength hint driven mostly by length.",
        ),
        field(
            "Email input",
            "Work email",
            '<input id="f" class="input" type="email" inputmode="email" autocomplete="email" placeholder="you@company.com" aria-describedby="h">',
            "Validated on blur, not on every keystroke; the message says how to fix it.",
            '.input[aria-invalid="true"] { border-color: var(--danger); }\n',
            'const input = document.getElementById("f");\nconst hint = document.getElementById("h");\ninput.addEventListener("blur", () => {\n  const bad = input.value !== "" && !input.checkValidity();\n  input.setAttribute("aria-invalid", String(bad));\n  hint.textContent = bad ? "Enter an address like name@company.com." : "We only use this to sign you in.";\n  hint.classList.toggle("bad", bad);\n});\ninput.addEventListener("input", () => { if (input.checkValidity()) { input.setAttribute("aria-invalid", "false"); hint.classList.remove("bad"); } });\n',
            "We only use this to sign you in.",
        ),
        Item(
            "Number input",
            '<div class="field"><label for="f">Seats</label><div class="adorn num"><button type="button" aria-label="Decrease">−</button><input id="f" inputmode="numeric" value="5" aria-describedby="h"><button type="button" aria-label="Increase">+</button></div><span class="hint" id="h">Between 1 and 50.</span></div>',
            FIELD
            + HINT
            + ADORN
            + ".num input { text-align: center; font-variant-numeric: tabular-nums; }\n.num button { font-size: 18px; color: var(--fg); }\n.num button:disabled { opacity: .3; }\n",
            """\
const MIN = 1, MAX = 50;
const input = document.getElementById("f");
const [minus, plus] = document.querySelectorAll(".num button");
const set = (value) => {
  const next = Math.min(MAX, Math.max(MIN, Number.isFinite(value) ? Math.round(value) : MIN));
  input.value = String(next);
  minus.disabled = next <= MIN;
  plus.disabled = next >= MAX;
};
minus.addEventListener("click", () => set(Number(input.value) - 1));
plus.addEventListener("click", () => set(Number(input.value) + 1));
input.addEventListener("blur", () => set(Number(input.value)));
input.addEventListener("keydown", (event) => {
  if (event.key === "ArrowUp") { event.preventDefault(); set(Number(input.value) + 1); }
  if (event.key === "ArrowDown") { event.preventDefault(); set(Number(input.value) - 1); }
});
set(Number(input.value));
""",
            "Stepper buttons, arrow keys, and clamping to the allowed range on blur.",
        ),
        Item(
            "Currency input",
            '<div class="field"><label for="f">Budget</label><div class="adorn"><span>$</span><input id="f" inputmode="decimal" placeholder="0.00"><span>USD</span></div></div>',
            FIELD
            + ADORN
            + ".adorn input { text-align: right; font-variant-numeric: tabular-nums; }\n",
            """\
const input = document.getElementById("f");
const format = new Intl.NumberFormat("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
// Let people type freely; tidy the figure when they leave the field.
input.addEventListener("input", () => { input.value = input.value.replace(/[^0-9.,]/g, ""); });
input.addEventListener("blur", () => {
  const value = Number(input.value.replaceAll(",", ""));
  input.value = input.value && Number.isFinite(value) ? format.format(value) : "";
});
input.addEventListener("focus", () => { input.value = input.value.replaceAll(",", ""); });
""",
            "Symbol and code as adornments; formatted with Intl on blur, raw while editing.",
        ),
        Item(
            "Phone input",
            '<div class="field"><label for="f">Phone</label><div class="adorn"><select aria-label="Country code"><option value="+1">🇺🇸 +1</option><option value="+44">🇬🇧 +44</option><option value="+49">🇩🇪 +49</option><option value="+91">🇮🇳 +91</option></select><input id="f" type="tel" inputmode="tel" autocomplete="tel-national" placeholder="555 010 1234"></div></div>',
            FIELD
            + ADORN
            + ".adorn select { flex: none; width: 92px; border-right: 1px solid var(--border); }\n",
            'const input = document.getElementById("f");\ninput.addEventListener("input", () => {\n  const digits = input.value.replace(/\\D/g, "").slice(0, 12);\n  input.value = digits.replace(/(\\d{3})(?=\\d)/g, "$1 ").trim();\n});\n',
            "Country code beside the number; digits are grouped as they are typed.",
        ),
        Item(
            "URL input",
            '<div class="field"><label for="f">Website</label><div class="adorn"><span>https://</span><input id="f" inputmode="url" autocomplete="url" placeholder="northwind.io" aria-describedby="h"></div><span class="hint" id="h"></span></div>',
            FIELD + HINT + ADORN,
            """\
const input = document.getElementById("f");
const hint = document.getElementById("h");
input.addEventListener("input", () => { input.value = input.value.replace(/^https?:\\/\\//i, ""); });  // the scheme is already shown
input.addEventListener("blur", () => {
  if (!input.value) { hint.textContent = ""; return; }
  let ok = false;
  try { ok = new URL(`https://${input.value}`).hostname.includes("."); } catch { ok = false; }
  hint.textContent = ok ? "" : "That does not look like a web address.";
  hint.classList.toggle("bad", !ok);
});
""",
            "The scheme is fixed as a prefix; a pasted scheme is stripped, the rest parsed with URL.",
        ),
        field(
            "Date input",
            "Start date",
            '<input id="f" class="input" type="date">',
            "The native picker: accessible, localised and right on phones.",
            ".input { color-scheme: dark; }\n",
            'const input = document.getElementById("f");\ninput.min = new Date().toISOString().slice(0, 10);  // no dates in the past\n',
        ),
        field(
            "Time input",
            "Meeting time",
            '<input id="f" class="input" type="time" step="900" value="09:30">',
            "Native time control stepping in quarter hours.",
            ".input { color-scheme: dark; }\n",
        ),
        field(
            "Date-time picker",
            "Publish at",
            '<input id="f" class="input" type="datetime-local" aria-describedby="h">',
            "One native control for date and time, with the zone stated next to it.",
            ".input { color-scheme: dark; }\n",
            'document.getElementById("h").textContent = `Times are in ${Intl.DateTimeFormat().resolvedOptions().timeZone}.`;\n',
            "Times are local.",
        ),
        Item(
            "Date range picker",
            '<div class="range"><header><button aria-label="Previous month">‹</button><strong></strong><button aria-label="Next month">›</button></header><div class="dow"></div><div class="days" role="grid"></div><footer></footer></div>',
            """\
.range { width: 300px; padding: 14px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }
.range header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.range header button { width: 28px; height: 28px; border: 0; border-radius: 8px; background: var(--surface-2); }
.dow, .days { display: grid; grid-template-columns: repeat(7, 1fr); }
.dow span { text-align: center; font-size: 11px; color: var(--muted); padding: 4px 0; }
.days button { aspect-ratio: 1; border: 0; background: none; border-radius: 8px; font-variant-numeric: tabular-nums; }
.days button:hover { background: var(--surface-2); }
.days .in { background: color-mix(in srgb, var(--primary) 20%, transparent); border-radius: 0; }
.days .edge { background: var(--primary); color: #fff; border-radius: 8px; }
.range footer { margin-top: 10px; font-size: 13px; color: var(--muted); min-height: 20px; }
""",
            """\
const root = document.querySelector(".range");
const title = root.querySelector("strong");
const grid = root.querySelector(".days");
const footer = root.querySelector("footer");
const view = new Date(); view.setDate(1);
let start = null, end = null;
const sameDay = (a, b) => a && b && a.toDateString() === b.toDateString();
const label = (date) => date.toLocaleDateString(undefined, { day: "numeric", month: "short" });
root.querySelector(".dow").append(...["M", "T", "W", "T", "F", "S", "S"].map((day) => Object.assign(document.createElement("span"), { textContent: day })));
const render = () => {
  title.textContent = view.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  grid.replaceChildren();
  const offset = (view.getDay() + 6) % 7;  // weeks start on Monday
  for (let i = 0; i < offset; i += 1) grid.append(document.createElement("span"));
  const days = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
  for (let day = 1; day <= days; day += 1) {
    const date = new Date(view.getFullYear(), view.getMonth(), day);
    const button = Object.assign(document.createElement("button"), { textContent: String(day), type: "button" });
    if (sameDay(date, start) || sameDay(date, end)) button.className = "edge";
    else if (start && end && date > start && date < end) button.className = "in";
    button.addEventListener("click", () => {
      // First click starts a range, the second closes it (in either order), a third starts over.
      if (!start || end) { start = date; end = null; }
      else if (date < start) { end = start; start = date; }
      else end = date;
      render();
    });
    grid.append(button);
  }
  footer.textContent = start && end ? `${label(start)} – ${label(end)}` : start ? `${label(start)} – choose an end date` : "Choose a start date";
};
const [previous, next] = root.querySelectorAll("header button");
previous.addEventListener("click", () => { view.setMonth(view.getMonth() - 1); render(); });
next.addEventListener("click", () => { view.setMonth(view.getMonth() + 1); render(); });
render();
""",
            note="A month grid where two clicks set a range in either order; the days between are tinted.",
        ),
        Item(
            "Color picker",
            '<div class="field"><label for="f">Brand colour</label><div class="adorn"><input type="color" id="pick" value="#7c5cff" aria-label="Pick a colour"><input id="f" value="#7C5CFF" maxlength="7" spellcheck="false"></div><div class="sw"></div></div>',
            FIELD
            + ADORN
            + '.adorn input[type=color] { flex: none; width: 44px; padding: 4px; border: 0; background: none; cursor: pointer; }\n.adorn #f { font-family: var(--mono); text-transform: uppercase; }\n.sw { display: flex; gap: 6px; }\n.sw button { width: 24px; height: 24px; border-radius: 7px; border: 2px solid transparent; }\n.sw button[aria-pressed="true"] { border-color: var(--fg); }\n',
            """\
const picker = document.getElementById("pick");
const text = document.getElementById("f");
const swatches = document.querySelector(".sw");
const set = (hex) => {
  picker.value = hex;
  text.value = hex.toUpperCase();
  swatches.querySelectorAll("button").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.hex === hex.toLowerCase())));
};
for (const hex of ["#7c5cff", "#22d3ee", "#34d399", "#fbbf24", "#f87171", "#f472b6"]) {
  const button = Object.assign(document.createElement("button"), { type: "button" });
  button.dataset.hex = hex;
  button.style.background = hex;
  button.setAttribute("aria-label", hex);
  button.addEventListener("click", () => set(hex));
  swatches.append(button);
}
picker.addEventListener("input", () => set(picker.value));
text.addEventListener("change", () => { if (/^#[0-9a-f]{6}$/i.test(text.value)) set(text.value.toLowerCase()); else set(picker.value); });
set(picker.value);
""",
            "Native colour well, a hex field that only accepts #RRGGBB, and preset swatches kept in step.",
        ),
        Item(
            "File input",
            '<div class="field"><label for="f">Attachment</label><label class="filebtn"><input id="f" type="file" accept=".pdf,.png,.jpg"><span>Choose a file</span><em>No file chosen</em></label><span class="hint">PDF, PNG or JPG, up to 10 MB.</span></div>',
            FIELD
            + HINT
            + ".filebtn { display: flex; align-items: center; gap: 12px; height: 42px; padding: 4px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); cursor: pointer; }\n.filebtn input { position: absolute; opacity: 0; width: 1px; }\n.filebtn span { padding: 6px 12px; border-radius: 7px; background: var(--surface-2); font-weight: 600; font-size: 14px; }\n.filebtn em { font-style: normal; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.filebtn:focus-within { border-color: var(--primary); }\n",
            """\
const input = document.getElementById("f");
const name = document.querySelector(".filebtn em");
const hint = document.querySelector(".hint");
const LIMIT = 10 * 1024 * 1024;
input.addEventListener("change", () => {
  const file = input.files[0];
  if (!file) { name.textContent = "No file chosen"; return; }
  if (file.size > LIMIT) {
    input.value = "";
    name.textContent = "No file chosen";
    hint.textContent = `${file.name} is larger than 10 MB.`;
    hint.classList.add("bad");
    return;
  }
  hint.classList.remove("bad");
  hint.textContent = "PDF, PNG or JPG, up to 10 MB.";
  name.textContent = `${file.name} · ${(file.size / 1024).toFixed(0)} KB`;
});
""",
            "The real file input stays in the label (keyboard and screen readers work); size is checked before accepting.",
        ),
        Item(
            "Image uploader",
            '<label class="imgup"><input type="file" accept="image/*"><span class="ph">Upload a photo</span><img alt="" hidden></label><button class="rm" hidden>Remove</button>',
            ".imgup { position: relative; display: grid; place-items: center; width: 160px; height: 160px; border: 2px dashed var(--border); border-radius: 50%; overflow: hidden; cursor: pointer; background: var(--surface); }\n.imgup:focus-within, .imgup:hover { border-color: var(--primary); }\n.imgup input { position: absolute; opacity: 0; }\n.ph { color: var(--muted); font-size: 13px; }\n.imgup img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }\n.rm { margin-top: 12px; border: 0; background: none; color: var(--danger); }\nbody { grid-auto-flow: row; align-content: center; justify-items: center; }\n",
            """\
const input = document.querySelector(".imgup input");
const image = document.querySelector(".imgup img");
const remove = document.querySelector(".rm");
let url = null;
const clear = () => { if (url) URL.revokeObjectURL(url); url = null; image.hidden = true; remove.hidden = true; input.value = ""; };
input.addEventListener("change", () => {
  const file = input.files[0];
  if (!file || !file.type.startsWith("image/")) { clear(); return; }
  if (url) URL.revokeObjectURL(url);
  url = URL.createObjectURL(file);  // a local preview; nothing is uploaded yet
  image.src = url;
  image.hidden = false;
  remove.hidden = false;
});
remove.addEventListener("click", clear);
""",
            "Previews the chosen image from an object URL and releases it when replaced or removed.",
        ),
        Item(
            "Drag-and-drop uploader",
            '<label class="drop"><input type="file"><strong>Drop a file here</strong><span>or click to browse</span></label>',
            ".drop { display: grid; place-items: center; align-content: center; gap: 4px; width: min(420px, 100%); height: 180px; border: 2px dashed var(--border); border-radius: 16px; background: var(--surface); cursor: pointer; transition: border-color .15s, background .15s; }\n.drop.over { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 12%, var(--surface)); }\n.drop input { position: absolute; opacity: 0; }\n.drop span { color: var(--muted); font-size: 13px; }\n.drop:focus-within { border-color: var(--primary); }\n",
            """\
const zone = document.querySelector(".drop");
const input = zone.querySelector("input");
const title = zone.querySelector("strong");
const show = (file) => { title.textContent = file ? file.name : "Drop a file here"; };
for (const type of ["dragenter", "dragover"]) zone.addEventListener(type, (event) => { event.preventDefault(); zone.classList.add("over"); });
for (const type of ["dragleave", "drop"]) zone.addEventListener(type, (event) => { event.preventDefault(); zone.classList.remove("over"); });
zone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (!file) return;
  // Put the dropped file into the real input so the form submits it like a chosen one.
  const transfer = new DataTransfer();
  transfer.items.add(file);
  input.files = transfer.files;
  show(file);
});
input.addEventListener("change", () => show(input.files[0]));
""",
            "A drop zone that is also a normal file input; a dropped file is assigned to the input.",
        ),
        Item(
            "Multi-file uploader",
            '<div class="mf"><label class="add"><input type="file" multiple>Add files</label><ul></ul><p class="sum"></p></div>',
            ".mf { width: min(420px, 100%); display: grid; gap: 10px; }\n.add { justify-self: start; padding: 8px 14px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface-2); font-weight: 600; cursor: pointer; }\n.add input { position: absolute; opacity: 0; width: 1px; }\n.mf ul { margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; }\n.mf li { display: grid; grid-template-columns: 1fr auto auto; gap: 10px; align-items: center; padding: 8px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); font-size: 14px; }\n.mf li span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.mf li small { color: var(--muted); }\n.mf li button { border: 0; background: none; color: var(--muted); }\n.sum { margin: 0; font-size: 13px; color: var(--muted); }\n",
            """\
const input = document.querySelector(".mf input");
const list = document.querySelector(".mf ul");
const summary = document.querySelector(".sum");
const files = new Map();  // keyed by name+size so the same file is not listed twice
const size = (bytes) => bytes > 1048576 ? `${(bytes / 1048576).toFixed(1)} MB` : `${Math.ceil(bytes / 1024)} KB`;
const render = () => {
  list.replaceChildren(...[...files].map(([key, file]) => {
    const row = document.createElement("li");
    const remove = Object.assign(document.createElement("button"), { type: "button", textContent: "×" });
    remove.setAttribute("aria-label", `Remove ${file.name}`);
    remove.addEventListener("click", () => { files.delete(key); render(); });
    row.append(Object.assign(document.createElement("span"), { textContent: file.name }), Object.assign(document.createElement("small"), { textContent: size(file.size) }), remove);
    return row;
  }));
  const total = [...files.values()].reduce((sum, file) => sum + file.size, 0);
  summary.textContent = files.size ? `${files.size} file${files.size === 1 ? "" : "s"}, ${size(total)}` : "No files added.";
};
input.addEventListener("change", () => {
  for (const file of input.files) files.set(`${file.name}:${file.size}`, file);
  input.value = "";  // so choosing the same file again fires change
  render();
});
render();
""",
            "Accumulates files across several picks, de-duplicates, and lets each be removed.",
        ),
        combo(
            "Autocomplete",
            "City",
            [
                "Amsterdam",
                "Berlin",
                "Bristol",
                "Lisbon",
                "London",
                "Madrid",
                "Paris",
                "Porto",
                "Stockholm",
            ],
            True,
            "Suggests as you type but accepts any text.",
        ),
        combo(
            "Combobox",
            "Assignee",
            ["Dana Whitfield", "Mika Tanaka", "Ravi Shah", "Sam Okafor", "Zoe Lindqvist"],
            False,
            "Filterable choice from a fixed list, with the ARIA combobox pattern.",
        ),
        field(
            "Select dropdown",
            "Plan",
            '<div class="sel"><select id="f" class="input"><option>Free</option><option selected>Team</option><option>Enterprise</option></select></div>',
            "The native select, restyled: it is the most robust dropdown there is.",
            '.sel { position: relative; }\n.sel select { appearance: none; padding-right: 36px; }\n.sel::after { content: ""; position: absolute; right: 14px; top: 50%; width: 8px; height: 8px; border: solid var(--muted); border-width: 0 2px 2px 0; translate: 0 -70%; rotate: 45deg; pointer-events: none; }\n',
        ),
        Item(
            "Multi-select",
            '<div class="field ms"><span id="l">Notify</span><button class="input trig" aria-haspopup="listbox" aria-expanded="false" aria-labelledby="l v"><span id="v">Choose…</span></button><ul class="menu" role="listbox" aria-multiselectable="true" hidden>'
            + "".join(
                f'<li role="option" aria-selected="{"true" if i < 2 else "false"}" tabindex="-1">{n}</li>'
                for i, n in enumerate(["Email", "Slack", "SMS", "Push", "Webhook"])
            )
            + "</ul></div>",
            FIELD
            + MENU
            + '.ms { position: relative; height: 280px; align-content: start; }\n.ms > span { font-size: 13px; color: var(--muted); }\n.trig { text-align: left; }\n.menu li[aria-selected="true"]::before { content: "✓ "; color: var(--success); }\n.menu li[aria-selected="false"]::before { content: "✓ "; visibility: hidden; }\n.menu li:focus { outline: 2px solid var(--accent); }\n',
            """\
const trigger = document.querySelector(".trig");
const menu = document.querySelector(".menu");
const value = document.getElementById("v");
const options = [...menu.children];
const update = () => {
  const chosen = options.filter((option) => option.getAttribute("aria-selected") === "true").map((option) => option.textContent);
  value.textContent = chosen.length === 0 ? "Choose…" : chosen.length <= 2 ? chosen.join(", ") : `${chosen.length} selected`;
};
const set = (open) => { menu.hidden = !open; trigger.setAttribute("aria-expanded", String(open)); if (open) options[0].focus(); };
const flip = (option) => { option.setAttribute("aria-selected", String(option.getAttribute("aria-selected") !== "true")); update(); };
trigger.addEventListener("click", () => set(menu.hidden));
menu.addEventListener("click", (event) => { const option = event.target.closest("li"); if (option) flip(option); });  // stays open: more than one can be picked
menu.addEventListener("keydown", (event) => {
  const index = options.indexOf(document.activeElement);
  if (event.key === "ArrowDown") options[(index + 1) % options.length].focus();
  else if (event.key === "ArrowUp") options[(index - 1 + options.length) % options.length].focus();
  else if (event.key === " " || event.key === "Enter") flip(options[index]);
  else if (event.key === "Escape") { set(false); trigger.focus(); }
  else return;
  event.preventDefault();
});
document.addEventListener("click", (event) => { if (!event.target.closest(".ms")) set(false); });
update();
""",
            "The list stays open while options are toggled; the trigger summarises the choice.",
        ),
        tokens(
            "Tag input",
            "Labels",
            ["design", "q3"],
            "() => true",
            "Enter or comma adds a tag, Backspace removes the last, pasting a list adds them all.",
        ),
        tokens(
            "Token input",
            "Recipients",
            ["dana@northwind.io"],
            "(text) => /^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(text)",
            "Each token is validated on its own; invalid ones stay visible and marked.",
        ),
        Item(
            "OTP input",
            '<fieldset class="otp"><legend>Enter the 6-digit code</legend><div>'
            + "".join(
                f'<input inputmode="numeric" maxlength="1" aria-label="Digit {i}" {'autocomplete="one-time-code"' if i == 1 else ""}>'
                for i in range(1, 7)
            )
            + '</div><p role="status"></p></fieldset>',
            ".otp { border: 0; padding: 0; display: grid; gap: 12px; justify-items: center; }\n.otp legend { color: var(--muted); margin-bottom: 12px; }\n.otp div { display: flex; gap: 8px; }\n.otp input { width: 46px; height: 54px; text-align: center; font-size: 22px; font-weight: 700; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.otp input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 30%, transparent); }\n.otp input:nth-child(3) { margin-right: 10px; }\n.otp p { margin: 0; min-height: 20px; color: var(--success); font-size: 14px; }\n",
            """\
const cells = [...document.querySelectorAll(".otp input")];
const status = document.querySelector(".otp p");
const done = () => { const code = cells.map((cell) => cell.value).join(""); status.textContent = code.length === cells.length ? `Code ${code} entered.` : ""; };
cells.forEach((cell, index) => {
  cell.addEventListener("input", () => {
    cell.value = cell.value.replace(/\\D/g, "").slice(-1);
    if (cell.value && cells[index + 1]) cells[index + 1].focus();
    done();
  });
  cell.addEventListener("keydown", (event) => {
    if (event.key === "Backspace" && !cell.value && cells[index - 1]) cells[index - 1].focus();
    if (event.key === "ArrowLeft") cells[index - 1]?.focus();
    if (event.key === "ArrowRight") cells[index + 1]?.focus();
  });
  // A pasted (or auto-filled) code is spread across the cells.
  cell.addEventListener("paste", (event) => {
    event.preventDefault();
    const digits = event.clipboardData.getData("text").replace(/\\D/g, "").slice(0, cells.length);
    [...digits].forEach((digit, i) => { cells[i].value = digit; });
    cells[Math.min(digits.length, cells.length - 1)].focus();
    done();
  });
});
""",
            "One cell per digit with auto-advance, Backspace to go back, and paste filling every cell.",
        ),
        field(
            "Code input",
            "Invite code",
            '<input id="f" class="input codei" maxlength="14" placeholder="XXXX-XXXX-XXXX" autocapitalize="characters" spellcheck="false">',
            "Uppercases and inserts the dashes while typing.",
            ".codei { font-family: var(--mono); letter-spacing: .12em; text-transform: uppercase; }\n",
            'const input = document.getElementById("f");\ninput.addEventListener("input", () => {\n  const raw = input.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 12);\n  input.value = raw.replace(/(.{4})(?=.)/g, "$1-");\n});\n',
        ),
        Item(
            "Markdown editor",
            '<div class="ed md"><div class="bar"><button data-wrap="**" aria-label="Bold"><b>B</b></button><button data-wrap="_" aria-label="Italic"><i>I</i></button><button data-wrap="`" aria-label="Code">&lt;/&gt;</button><button data-line="- " aria-label="List">•</button><button data-line="# " aria-label="Heading">H</button></div><textarea aria-label="Markdown"># Release notes\n\nAdded **bulk export** and _faster_ search.\n\n- Fix `login` redirect</textarea><div class="foot"><span>Markdown</span><span class="count"></span></div></div>',
            EDITOR + ".md textarea { font: 14px/1.6 var(--mono); }\n",
            """\
const area = document.querySelector(".md textarea");
const count = document.querySelector(".count");
const update = () => { count.textContent = `${area.value.trim().split(/\\s+/).filter(Boolean).length} words`; };
document.querySelector(".md .bar").addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  const { selectionStart: from, selectionEnd: to, value } = area;
  if (button.dataset.wrap) {
    const mark = button.dataset.wrap;
    area.setRangeText(`${mark}${value.slice(from, to) || "text"}${mark}`, from, to, "select");
  } else {
    const lineStart = value.lastIndexOf("\\n", from - 1) + 1;  // prefix the line the caret is on
    area.setRangeText(button.dataset.line, lineStart, lineStart, "end");
  }
  area.focus();
  update();
});
area.addEventListener("input", update);
update();
""",
            "A plain textarea plus buttons that wrap the selection or prefix the line with Markdown.",
        ),
        Item(
            "Rich text editor",
            '<div class="ed rt"><div class="bar"><button data-cmd="bold" aria-label="Bold" aria-pressed="false"><b>B</b></button><button data-cmd="italic" aria-label="Italic" aria-pressed="false"><i>I</i></button><button data-cmd="underline" aria-label="Underline" aria-pressed="false"><u>U</u></button><button data-cmd="insertUnorderedList" aria-label="Bulleted list">•</button></div><div class="area" contenteditable="true" role="textbox" aria-multiline="true" aria-label="Rich text"><p>Select some of this text and <b>format</b> it.</p></div></div>',
            EDITOR + ".rt .area p { margin: 0 0 8px; }\n",
            """\
const area = document.querySelector(".rt .area");
const buttons = [...document.querySelectorAll(".rt .bar button")];
// execCommand is deprecated but remains the only built-in way to format a contenteditable;
// swap this layer for an editor library when the document model matters.
const reflect = () => buttons.forEach((button) => {
  if (button.hasAttribute("aria-pressed")) button.setAttribute("aria-pressed", String(document.queryCommandState(button.dataset.cmd)));
});
buttons.forEach((button) => {
  button.addEventListener("mousedown", (event) => event.preventDefault());  // keep the selection
  button.addEventListener("click", () => { document.execCommand(button.dataset.cmd); area.focus(); reflect(); });
});
document.addEventListener("selectionchange", reflect);
// Paste as plain text so foreign styles never enter the document.
area.addEventListener("paste", (event) => {
  event.preventDefault();
  document.execCommand("insertText", false, event.clipboardData.getData("text/plain"));
});
""",
            "contenteditable with a toolbar that reflects the selection; pastes are reduced to plain text.",
        ),
        Item(
            "WYSIWYG editor",
            '<div class="ed wy"><div class="bar"><select aria-label="Block style"><option value="p">Paragraph</option><option value="h2">Heading</option><option value="blockquote">Quote</option></select><button data-cmd="bold" aria-label="Bold"><b>B</b></button><button data-cmd="italic" aria-label="Italic"><i>I</i></button><button data-link aria-label="Link">🔗</button><button data-cmd="removeFormat" aria-label="Clear formatting">⌫</button></div><div class="area" contenteditable="true" role="textbox" aria-multiline="true" aria-label="Document"><h2>Weekly update</h2><p>What shipped, what slipped, what is next.</p></div><div class="foot"><span>Rich text</span><span class="out"></span></div></div>',
            EDITOR
            + ".wy .bar select { height: 30px; border: 1px solid var(--border); border-radius: 7px; background: var(--surface); }\n.wy .area h2 { margin: 0 0 8px; font-size: 20px; }\n.wy .area p, .wy .area blockquote { margin: 0 0 8px; }\n.wy .area blockquote { padding-left: 12px; border-left: 3px solid var(--primary); color: var(--muted); }\n.wy .area a { color: var(--accent); }\n",
            """\
const area = document.querySelector(".wy .area");
const out = document.querySelector(".out");
const ALLOWED = new Set(["P", "H2", "BLOCKQUOTE", "B", "STRONG", "I", "EM", "A", "BR", "UL", "OL", "LI"]);
// What gets saved is cleaned: only known tags, and links only to http(s).
const clean = (node) => {
  for (const child of [...node.children]) {
    clean(child);
    if (!ALLOWED.has(child.tagName)) { child.replaceWith(...child.childNodes); continue; }
    for (const attribute of [...child.attributes]) {
      const keep = child.tagName === "A" && attribute.name === "href" && /^https?:\\/\\//i.test(attribute.value);
      if (!keep) child.removeAttribute(attribute.name);
    }
  }
  return node;
};
const serialise = () => { out.textContent = `${clean(area.cloneNode(true)).innerHTML.length} characters of HTML`; };
document.querySelector(".wy select").addEventListener("change", (event) => { document.execCommand("formatBlock", false, event.target.value); area.focus(); serialise(); });
document.querySelectorAll(".wy .bar button").forEach((button) => {
  button.addEventListener("mousedown", (event) => event.preventDefault());
  button.addEventListener("click", () => {
    if (button.hasAttribute("data-link")) {
      const url = window.prompt("Link address (https://…)");
      if (url && /^https?:\\/\\//i.test(url)) document.execCommand("createLink", false, url);
    } else document.execCommand(button.dataset.cmd);
    serialise();
  });
});
area.addEventListener("input", serialise);
serialise();
""",
            "Block styles, inline marks and links, with the saved HTML reduced to an allowlist of tags.",
        ),
        Item(
            "JSON editor",
            '<div class="ed js"><textarea class="code" spellcheck="false" aria-label="JSON" aria-describedby="jm">{\n  "name": "northwind",\n  "seats": 12,\n  "features": ["sso", "audit"]\n}</textarea><div class="foot"><span id="jm"></span><button class="fmt">Format</button></div></div>',
            EDITOR
            + CODE
            + ".js .foot button { border: 0; background: none; color: var(--primary); font-weight: 600; }\n.js .foot .bad { color: var(--danger); }\n.js .foot .ok { color: var(--success); }\n",
            """\
const area = document.querySelector(".js textarea");
const message = document.getElementById("jm");
const check = () => {
  try {
    JSON.parse(area.value);
    message.textContent = "Valid JSON";
    message.className = "ok";
    return true;
  } catch (error) {
    message.textContent = error.message;  // the parser's own position is the most useful hint
    message.className = "bad";
    return false;
  }
};
document.querySelector(".fmt").addEventListener("click", () => { if (check()) area.value = JSON.stringify(JSON.parse(area.value), null, 2); });
area.addEventListener("input", check);
area.addEventListener("keydown", (event) => {
  if (event.key !== "Tab") return;
  event.preventDefault();  // Tab indents instead of leaving; Escape then Tab leaves
  area.setRangeText("  ", area.selectionStart, area.selectionEnd, "end");
});
check();
""",
            "Validates on every change, shows the parser's message, formats on request.",
        ),
        Item(
            "Code editor",
            '<div class="ed ce"><div class="wrap"><pre class="nums" aria-hidden="true"></pre><textarea class="code" spellcheck="false" aria-label="Code">function total(items) {\n  return items.reduce((sum, item) =&gt; sum + item.price, 0);\n}</textarea></div><div class="foot"><span>JavaScript</span><span class="pos"></span></div></div>',
            EDITOR
            + CODE
            + ".wrap { display: grid; grid-template-columns: auto 1fr; }\n.nums { margin: 0; padding: 14px 10px 14px 14px; text-align: right; color: var(--muted); font: 13px/1.6 var(--mono); user-select: none; border-right: 1px solid var(--border); }\n.ce textarea { resize: none; overflow: auto; }\n",
            """\
const area = document.querySelector(".ce textarea");
const nums = document.querySelector(".nums");
const pos = document.querySelector(".pos");
const update = () => {
  const lines = area.value.split("\\n").length;
  nums.textContent = Array.from({ length: lines }, (_, i) => i + 1).join("\\n");
  const before = area.value.slice(0, area.selectionStart).split("\\n");
  pos.textContent = `Ln ${before.length}, Col ${before.at(-1).length + 1}`;
};
area.addEventListener("keydown", (event) => {
  if (event.key === "Tab") { event.preventDefault(); area.setRangeText("  ", area.selectionStart, area.selectionEnd, "end"); update(); }
  if (event.key === "Enter") {
    // Carry the current line's indentation onto the new line.
    event.preventDefault();
    const line = area.value.slice(0, area.selectionStart).split("\\n").at(-1);
    area.setRangeText(`\\n${line.match(/^\\s*/)[0]}`, area.selectionStart, area.selectionEnd, "end");
    update();
  }
});
for (const type of ["input", "click", "keyup"]) area.addEventListener(type, update);
update();
""",
            "Line numbers, caret position, Tab to indent and indentation carried onto new lines.",
        ),
        Item(
            "Query editor",
            '<div class="ed qe"><textarea class="code" spellcheck="false" aria-label="SQL query">SELECT region, SUM(revenue)\nFROM orders\nWHERE created_at &gt;= \'2026-01-01\'\nGROUP BY region;</textarea><div class="foot"><span class="info"></span><button class="run">Run ⌘↵</button></div></div>',
            EDITOR
            + CODE
            + ".qe .run { padding: 4px 12px; border: 0; border-radius: 7px; background: var(--primary); color: #fff; font-weight: 600; }\n.qe .info.bad { color: var(--danger); }\n",
            """\
const area = document.querySelector(".qe textarea");
const info = document.querySelector(".qe .info");
const WRITES = /\\b(insert|update|delete|drop|alter|truncate|create|grant)\\b/i;
const run = () => {
  const sql = area.value.trim();
  // A reporting console runs single read-only statements; say so instead of failing later.
  const problem = !sql ? "Write a query first." : WRITES.test(sql) ? "Only SELECT statements can be run here."
    : sql.replace(/;\\s*$/, "").includes(";") ? "Run one statement at a time." : "";
  info.textContent = problem || `Ready to run (${sql.split("\\n").length} lines).`;
  info.classList.toggle("bad", Boolean(problem));
};
document.querySelector(".run").addEventListener("click", run);
area.addEventListener("keydown", (event) => { if ((event.metaKey || event.ctrlKey) && event.key === "Enter") { event.preventDefault(); run(); } });
""",
            "A SQL box with ⌘/Ctrl+Enter to run and client-side guards for read-only, single statements.",
        ),
        Item(
            "Prompt editor",
            '<div class="ed pe"><textarea aria-label="Prompt template">Summarise {{document}} for {{audience}} in {{length}} bullet points.</textarea><div class="vars" aria-live="polite"></div></div>',
            EDITOR
            + ".pe textarea { min-height: 96px; }\n.vars { display: flex; flex-wrap: wrap; gap: 6px; padding: 10px 12px; border-top: 1px solid var(--border); min-height: 44px; }\n.vars span { padding: 2px 10px; border-radius: 99px; background: color-mix(in srgb, var(--accent) 20%, transparent); color: var(--accent); font: 12px var(--mono); }\n.vars em { color: var(--muted); font-size: 13px; font-style: normal; }\n",
            """\
const area = document.querySelector(".pe textarea");
const vars = document.querySelector(".vars");
const update = () => {
  const names = [...new Set([...area.value.matchAll(/\\{\\{\\s*([a-z_][a-z0-9_]*)\\s*\\}\\}/gi)].map((match) => match[1]))];
  vars.replaceChildren(...(names.length
    ? names.map((name) => Object.assign(document.createElement("span"), { textContent: name }))
    : [Object.assign(document.createElement("em"), { textContent: "No variables. Write {{name}} to add one." })]));
};
area.addEventListener("input", update);
update();
""",
            "A template with {{variables}}; the editor lists the variables it finds as you type.",
        ),
        Item(
            "AI prompt box",
            '<form class="pb"><textarea rows="1" placeholder="Ask anything…" aria-label="Message"></textarea><div class="tools"><button type="button" aria-label="Attach file">＋</button><span class="model">sonnet</span><button class="send" aria-label="Send" disabled>↑</button></div></form>',
            ".pb { width: min(560px, 100%); padding: 12px; border: 1px solid var(--border); border-radius: 20px; background: var(--surface); box-shadow: var(--shadow); transition: border-color .15s; }\n.pb:focus-within { border-color: var(--primary); }\n.pb textarea { display: block; width: 100%; max-height: 180px; border: 0; outline: 0; background: none; resize: none; padding: 4px 6px 10px; }\n.tools { display: flex; align-items: center; gap: 8px; }\n.tools button { width: 32px; height: 32px; border: 1px solid var(--border); border-radius: 50%; background: var(--surface-2); }\n.model { margin-right: auto; padding: 3px 10px; border-radius: 99px; background: var(--surface-2); font: 12px var(--mono); color: var(--muted); }\n.send { border: 0 !important; background: var(--primary) !important; color: #fff; }\n.send:disabled { opacity: .35; }\n",
            """\
const form = document.querySelector(".pb");
const area = form.querySelector("textarea");
const send = form.querySelector(".send");
const fit = () => { area.style.height = "auto"; area.style.height = `${area.scrollHeight}px`; send.disabled = area.value.trim() === ""; };
area.addEventListener("input", fit);
area.addEventListener("keydown", (event) => {
  // Enter sends, Shift+Enter makes a new line; never send while an IME is composing.
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); form.requestSubmit(); }
});
form.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!area.value.trim()) return;
  area.value = "";
  fit();
});
fit();
""",
            "Grows with the text, Enter sends, Shift+Enter breaks the line, composition is respected.",
        ),
        Item(
            "Smart input",
            '<div class="field"><label for="f">Quick add</label><input id="f" class="input" placeholder="Lunch with Mika tomorrow 12:30 #team"><div class="parsed" aria-live="polite"></div></div>',
            FIELD
            + ".parsed { display: flex; flex-wrap: wrap; gap: 6px; min-height: 24px; }\n.parsed span { padding: 2px 10px; border-radius: 99px; font-size: 12px; background: var(--surface-2); }\n.parsed .when { background: color-mix(in srgb, var(--accent) 20%, transparent); color: var(--accent); }\n.parsed .tag { background: color-mix(in srgb, var(--primary) 22%, transparent); color: var(--primary); }\n",
            """\
const input = document.getElementById("f");
const parsed = document.querySelector(".parsed");
const chip = (cls, text) => Object.assign(document.createElement("span"), { className: cls, textContent: text });
input.addEventListener("input", () => {
  let rest = input.value;
  const chips = [];
  const take = (pattern, cls, label) => { rest = rest.replace(pattern, (match) => { chips.push(chip(cls, label(match))); return ""; }); };
  take(/\\b(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\\b/i, "when", (m) => `Day: ${m}`);
  take(/\\b\\d{1,2}:\\d{2}\\b/, "when", (m) => `Time: ${m}`);
  take(/#\\w+/g, "tag", (m) => m);
  const title = rest.replace(/\\s+/g, " ").trim();
  parsed.replaceChildren(...(title ? [chip("", `Title: ${title}`)] : []), ...chips);
});
""",
            "Free text is parsed into structured parts (day, time, tags) shown back as chips before saving.",
        ),
        Item(
            "Voice input",
            '<div class="voice"><button class="mic" aria-pressed="false" aria-label="Start recording"><i></i></button><div class="lvl"><span></span><span></span><span></span><span></span><span></span></div><p role="status">Press the microphone to record.</p></div>',
            '.voice { display: grid; justify-items: center; gap: 14px; }\n.mic { display: grid; place-items: center; width: 68px; height: 68px; border: 0; border-radius: 50%; background: var(--surface-2); transition: background .2s, box-shadow .2s; }\n.mic i { width: 16px; height: 26px; border-radius: 8px; background: var(--fg); }\n.mic[aria-pressed="true"] { background: var(--danger); box-shadow: 0 0 0 8px color-mix(in srgb, var(--danger) 25%, transparent); }\n.lvl { display: flex; gap: 4px; align-items: center; height: 36px; }\n.lvl span { width: 5px; height: 6px; border-radius: 3px; background: var(--accent); transition: height .08s; }\n.voice p { margin: 0; color: var(--muted); font-size: 14px; }\n',
            """\
const mic = document.querySelector(".mic");
const bars = [...document.querySelectorAll(".lvl span")];
const status = document.querySelector(".voice p");
let stream = null, context = null, frame = 0;
const stop = () => {
  cancelAnimationFrame(frame);
  stream?.getTracks().forEach((track) => track.stop());
  context?.close();
  stream = context = null;
  bars.forEach((bar) => { bar.style.height = "6px"; });
  mic.setAttribute("aria-pressed", "false");
  mic.setAttribute("aria-label", "Start recording");
};
mic.addEventListener("click", async () => {
  if (stream) { stop(); status.textContent = "Recording stopped."; return; }
  if (!navigator.mediaDevices?.getUserMedia) { status.textContent = "This browser cannot record audio."; return; }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    status.textContent = "Microphone access was not allowed.";
    return;
  }
  context = new AudioContext();
  const analyser = context.createAnalyser();
  analyser.fftSize = 64;
  context.createMediaStreamSource(stream).connect(analyser);
  const data = new Uint8Array(analyser.frequencyBinCount);
  const draw = () => {
    analyser.getByteFrequencyData(data);
    bars.forEach((bar, i) => { bar.style.height = `${6 + (data[i * 3] / 255) * 30}px`; });
    frame = requestAnimationFrame(draw);
  };
  draw();
  mic.setAttribute("aria-pressed", "true");
  mic.setAttribute("aria-label", "Stop recording");
  status.textContent = "Listening…";
});
""",
            "Asks for the microphone on press, shows a live level, and releases the device on stop.",
        ),
        Item(
            "Speech-to-text input",
            '<div class="field"><label for="f">Dictate a note</label><div class="adorn"><input id="f" placeholder="Press the button and speak"><button type="button" aria-pressed="false">Dictate</button></div><span class="hint" role="status"></span></div>',
            FIELD + HINT + ADORN + '.adorn button[aria-pressed="true"] { color: var(--danger); }\n',
            """\
const input = document.getElementById("f");
const button = document.querySelector(".adorn button");
const hint = document.querySelector(".hint");
const Recognition = window.SpeechRecognition ?? window.webkitSpeechRecognition;
if (!Recognition) {
  button.disabled = true;
  hint.textContent = "Dictation is not supported in this browser; type instead.";
} else {
  const recognition = new Recognition();
  recognition.interimResults = true;
  recognition.lang = navigator.language;
  let base = "";
  recognition.addEventListener("result", (event) => {
    const spoken = [...event.results].map((result) => result[0].transcript).join("");
    input.value = `${base}${spoken}`;  // interim words are shown, then replaced by the final ones
  });
  const end = () => { button.setAttribute("aria-pressed", "false"); button.textContent = "Dictate"; };
  recognition.addEventListener("end", end);
  recognition.addEventListener("error", (event) => { hint.textContent = event.error === "not-allowed" ? "Microphone access was not allowed." : "Dictation stopped."; end(); });
  button.addEventListener("click", () => {
    if (button.getAttribute("aria-pressed") === "true") { recognition.stop(); return; }
    base = input.value ? `${input.value} ` : "";
    recognition.start();
    button.setAttribute("aria-pressed", "true");
    button.textContent = "Stop";
    hint.textContent = "Listening…";
  });
}
""",
            "Uses the Web Speech API where it exists and degrades to plain typing where it does not.",
        ),
        Item(
            "Mention input",
            '<div class="field mi"><label for="f">Comment</label><textarea id="f" class="input" rows="3" placeholder="Type @ to mention someone"></textarea><ul class="menu" role="listbox" hidden></ul></div>',
            FIELD
            + MENU
            + ".mi { position: relative; height: 300px; align-content: start; }\n.mi textarea { height: auto; padding: 10px 12px; resize: none; }\n.mi .menu { inset: 110px auto auto 0; width: 220px; }\n",
            """\
const PEOPLE = ["dana", "mika", "ravi", "sam", "zoe"];
const area = document.getElementById("f");
const menu = document.querySelector(".mi .menu");
let active = 0;
// The mention being typed: "@" followed by letters, ending at the caret.
const current = () => area.value.slice(0, area.selectionStart).match(/(^|\\s)@(\\w*)$/);
const render = () => {
  const match = current();
  const names = match ? PEOPLE.filter((name) => name.startsWith(match[2].toLowerCase())) : [];
  active = 0;
  menu.replaceChildren(...names.map((name, i) => { const item = Object.assign(document.createElement("li"), { textContent: `@${name}` }); item.setAttribute("aria-selected", String(i === 0)); return item; }));
  menu.hidden = names.length === 0;
};
const insert = (text) => {
  const match = current();
  if (!match) return;
  const from = area.selectionStart - match[2].length - 1;
  area.setRangeText(`${text} `, from, area.selectionStart, "end");
  menu.hidden = true;
};
area.addEventListener("input", render);
area.addEventListener("keydown", (event) => {
  if (menu.hidden) return;
  const items = [...menu.children];
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    active = (active + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
    items.forEach((item, i) => item.setAttribute("aria-selected", String(i === active)));
  } else if (event.key === "Enter" || event.key === "Tab") { event.preventDefault(); insert(items[active].textContent); }
  else if (event.key === "Escape") menu.hidden = true;
});
menu.addEventListener("mousedown", (event) => { const item = event.target.closest("li"); if (item) { event.preventDefault(); insert(item.textContent); } });
""",
            "Typing @ opens a filtered list at the caret's word; Enter or Tab completes it.",
        ),
        Item(
            "Emoji picker",
            '<div class="ep"><button class="open" aria-haspopup="dialog" aria-expanded="false" aria-label="Add emoji">🙂</button><output></output><div class="sheet" role="dialog" aria-label="Emoji" hidden><input placeholder="Search" aria-label="Search emoji"><div class="grid"></div></div></div>',
            ".ep { position: relative; display: flex; gap: 10px; align-items: center; height: 300px; align-self: start; }\n.ep .open { width: 40px; height: 40px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); font-size: 18px; }\n.ep output { font-size: 24px; }\n.sheet { position: absolute; top: 48px; left: 0; width: 240px; padding: 10px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface-2); box-shadow: var(--shadow); }\n.sheet[hidden] { display: none; }\n.sheet input { width: 100%; height: 34px; margin-bottom: 8px; padding: 0 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); }\n.grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 2px; }\n.grid button { aspect-ratio: 1; border: 0; border-radius: 8px; background: none; font-size: 18px; }\n.grid button:hover, .grid button:focus { background: var(--surface); outline: none; }\n",
            """\
const EMOJI = [["🙂", "smile"], ["😂", "laugh joy"], ["😍", "love heart eyes"], ["🤔", "think"], ["👍", "thumbs up yes"], ["👎", "thumbs down no"], ["🎉", "party celebrate"], ["🔥", "fire hot"], ["✅", "check done"], ["❌", "cross no"], ["🚀", "rocket ship launch"], ["💡", "idea light"], ["👀", "eyes look"], ["🙏", "thanks please"], ["💯", "hundred"], ["⚠️", "warning"], ["❤️", "heart love"], ["⭐", "star"]];
const root = document.querySelector(".ep");
const opener = root.querySelector(".open");
const sheet = root.querySelector(".sheet");
const search = sheet.querySelector("input");
const grid = sheet.querySelector(".grid");
const render = () => {
  const query = search.value.trim().toLowerCase();
  grid.replaceChildren(...EMOJI.filter(([, words]) => words.includes(query)).map(([emoji, words]) => {
    const button = Object.assign(document.createElement("button"), { type: "button", textContent: emoji });
    button.setAttribute("aria-label", words.split(" ")[0]);
    return button;
  }));
};
const set = (open) => { sheet.hidden = !open; opener.setAttribute("aria-expanded", String(open)); if (open) { search.value = ""; render(); search.focus(); } };
opener.addEventListener("click", () => set(sheet.hidden));
search.addEventListener("input", render);
grid.addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  root.querySelector("output").textContent += button.textContent;
  set(false);
  opener.focus();
});
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !sheet.hidden) { set(false); opener.focus(); } });
document.addEventListener("click", (event) => { if (!root.contains(event.target)) set(false); });
""",
            "A searchable grid in a popover; every emoji button has a spoken name.",
        ),
        Item(
            "Command input",
            '<div class="ci"><label><span>&gt;</span><input placeholder="Type a command" aria-label="Command" aria-controls="cl" autocomplete="off"></label><ul id="cl" role="listbox"></ul></div>',
            '.ci { width: min(460px, 100%); border: 1px solid var(--border); border-radius: 14px; background: var(--surface); overflow: hidden; box-shadow: var(--shadow); }\n.ci label { display: flex; align-items: center; gap: 10px; padding: 0 14px; height: 48px; border-bottom: 1px solid var(--border); }\n.ci label span { color: var(--primary); font: 700 15px var(--mono); }\n.ci input { flex: 1; border: 0; outline: 0; background: none; }\n.ci ul { margin: 0; padding: 6px; list-style: none; max-height: 220px; overflow: auto; }\n.ci li { display: flex; justify-content: space-between; padding: 8px 10px; border-radius: 8px; cursor: pointer; }\n.ci li[aria-selected="true"] { background: color-mix(in srgb, var(--primary) 22%, transparent); }\n.ci li kbd { font: 11px var(--mono); color: var(--muted); }\n.ci li.none { color: var(--muted); cursor: default; }\n',
            """\
const COMMANDS = [["New project", "N"], ["Invite teammate", "I"], ["Open settings", ","], ["Toggle theme", "T"], ["Export as CSV", "E"], ["Sign out", "Q"]];
const input = document.querySelector(".ci input");
const list = document.getElementById("cl");
let active = 0;
// Every typed letter must appear in order: "nwp" finds "New project".
const fuzzy = (text, query) => { let i = 0; for (const char of text.toLowerCase()) if (char === query[i]) i += 1; return i === query.length; };
const render = () => {
  const query = input.value.trim().toLowerCase().replace(/\\s/g, "");
  const found = COMMANDS.filter(([name]) => fuzzy(name, query));
  active = 0;
  list.replaceChildren(...(found.length ? found.map(([name, key], i) => {
    const item = document.createElement("li");
    item.setAttribute("role", "option");
    item.setAttribute("aria-selected", String(i === 0));
    item.append(name, Object.assign(document.createElement("kbd"), { textContent: key }));
    return item;
  }) : [Object.assign(document.createElement("li"), { className: "none", textContent: "No matching command" })]));
};
input.addEventListener("input", render);
input.addEventListener("keydown", (event) => {
  const items = [...list.querySelectorAll('[role="option"]')];
  if (!items.length) return;
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    active = (active + (event.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
    items.forEach((item, i) => item.setAttribute("aria-selected", String(i === active)));
    items[active].scrollIntoView({ block: "nearest" });
  } else if (event.key === "Enter") { input.value = items[active].firstChild.textContent; render(); }
});
render();
""",
            "Fuzzy-matches commands as you type; arrows move the highlight, Enter runs it.",
        ),
    ),
)
