"""Patterns 41-80: buttons and actions."""

from app.domains.references.vocabulary.base import BTN, Item, Section

ROW = ".row { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; }\n"


def variant(name: str, label: str, css: str, note: str, attrs: str = "") -> Item:
    """A button that differs from the base only in its look."""
    return Item(name, f'<button class="btn v"{attrs}>{label}</button>', BTN + css, note=note)


COPY_JS = """\
const button = document.querySelector(".copy");
const label = button.querySelector("span");
button.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(button.dataset.value);
    label.textContent = "Copied";
  } catch {
    // Clipboard access can be refused (permissions, insecure context): say so.
    label.textContent = "Press Ctrl+C";
  }
  button.classList.add("done");
  setTimeout(() => { label.textContent = "Copy"; button.classList.remove("done"); }, 1600);
});
"""
BUSY_JS = """\
const button = document.querySelector(".btn");
const label = button.querySelector(".label");
const idle = label.textContent;
// Stand-in for a request; replace with the real call and keep the three states.
const work = () => new Promise((resolve, reject) => setTimeout(Math.random() > 0.25 ? resolve : reject, 1100));
button.addEventListener("click", async () => {
  if (button.dataset.state === "busy") return;
  button.dataset.state = "busy";
  button.setAttribute("aria-busy", "true");
  label.textContent = button.dataset.busy;
  try {
    await work();
    button.dataset.state = "done";
    label.textContent = button.dataset.done;
  } catch {
    button.dataset.state = "failed";
    label.textContent = button.dataset.failed;
  }
  button.removeAttribute("aria-busy");
  setTimeout(() => { button.dataset.state = "idle"; label.textContent = idle; }, 1500);
});
"""
BUSY_CSS = (
    BTN
    + """\
.btn { min-width: 150px; }
.spin { width: 15px; height: 15px; border: 2px solid rgb(255 255 255 / .35); border-top-color: #fff; border-radius: 50%;
  display: none; animation: spin .7s linear infinite; }
.btn[data-state="busy"] { cursor: progress; opacity: .85; }
.btn[data-state="busy"] .spin { display: block; }
.btn[data-state="done"] { background: var(--success); }
.btn[data-state="failed"] { background: var(--danger); }
@keyframes spin { to { rotate: 360deg; } }
"""
)


def busy(name: str, label: str, working: str, done: str, failed: str, note: str) -> Item:
    html = (
        f'<button class="btn" data-state="idle" data-busy="{working}" data-done="{done}" data-failed="{failed}">'
        f'<i class="spin"></i><span class="label">{label}</span></button>'
    )
    return Item(name, html, BUSY_CSS, BUSY_JS, note)


SECTION = Section(
    "patterns",
    "Buttons & Actions",
    41,
    (
        variant(
            "Primary button",
            "Create project",
            ".v:hover { background: color-mix(in srgb, var(--primary) 88%, white); }\n.v:active { transform: scale(.98); }\n",
            "One per view: the action the screen exists for.",
        ),
        variant(
            "Secondary button",
            "Save draft",
            ".v { background: var(--surface-2); color: var(--fg); border-color: var(--border); }\n.v:hover { background: color-mix(in srgb, var(--surface-2) 80%, white 8%); }\n",
            "A real alternative to the primary action, visibly quieter.",
        ),
        variant(
            "Tertiary button",
            "Learn more",
            ".v { background: none; color: var(--primary); padding: 0 6px; }\n.v:hover { text-decoration: underline; text-underline-offset: 4px; }\n",
            "Text-weight action for optional paths.",
        ),
        variant(
            "Ghost button",
            "Cancel",
            ".v { background: transparent; color: var(--fg); }\n.v:hover { background: var(--surface-2); }\n",
            "No surface until hovered; for toolbars and dismissals.",
        ),
        variant(
            "Outline button",
            "Add filter",
            ".v { background: transparent; color: var(--fg); border-color: var(--border); }\n.v:hover { border-color: var(--fg); }\n",
            "A border instead of a fill; sits well on busy surfaces.",
        ),
        variant(
            "Destructive button",
            "Delete workspace",
            ".v { background: var(--danger); color: #1a0606; }\n.v:hover { background: color-mix(in srgb, var(--danger) 85%, white); }\n",
            "Reserved for irreversible actions; pair with a confirmation.",
        ),
        variant(
            "Icon button",
            '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
            ".v { width: 40px; padding: 0; background: var(--surface-2); color: var(--fg); border-color: var(--border); }\n.v:hover { background: var(--surface); }\n",
            "Square, icon only; always carries an aria-label.",
            ' aria-label="Add item"',
        ),
        Item(
            "Floating action button",
            '<div class="canvas"><button class="fab" aria-label="Compose">+</button></div>',
            """\
.canvas { position: relative; width: 320px; height: 300px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }
.fab { position: absolute; right: 18px; bottom: 18px; width: 56px; height: 56px; border: 0; border-radius: 18px; font-size: 26px;
  background: var(--primary); color: var(--primary-fg); box-shadow: 0 10px 24px -6px color-mix(in srgb, var(--primary) 70%, transparent);
  transition: transform .2s var(--ease), box-shadow .2s; }
.fab:hover { transform: translateY(-2px) scale(1.04); box-shadow: 0 16px 30px -8px color-mix(in srgb, var(--primary) 80%, transparent); }
.fab:active { transform: scale(.96); }
""",
            note="Pinned to a corner of its surface for the single most common creation action.",
        ),
        Item(
            "Split button",
            '<div class="splitbtn"><button class="btn main">Merge pull request</button><button class="btn more" aria-haspopup="menu" aria-expanded="false" aria-label="More merge options">▾</button>'
            '<ul role="menu" hidden><li role="menuitem" tabindex="-1">Squash and merge</li><li role="menuitem" tabindex="-1">Rebase and merge</li></ul></div>',
            BTN
            + """\
.splitbtn { position: relative; display: inline-flex; height: 120px; align-items: flex-start; }
.main { border-radius: 10px 0 0 10px; }
.more { border-radius: 0 10px 10px 0; padding: 0 12px; border-left: 1px solid rgb(255 255 255 / .25); }
.splitbtn ul { position: absolute; top: 46px; right: 0; margin: 0; padding: 6px; min-width: 200px; list-style: none;
  border: 1px solid var(--border); border-radius: 10px; background: var(--surface-2); box-shadow: var(--shadow); }
.splitbtn ul[hidden] { display: none; }
.splitbtn li { padding: 8px 10px; border-radius: 7px; cursor: pointer; }
.splitbtn li:hover, .splitbtn li:focus { background: var(--surface); outline: none; }
""",
            """\
const more = document.querySelector(".more");
const menu = document.querySelector('[role="menu"]');
const main = document.querySelector(".main");
const set = (open) => { menu.hidden = !open; more.setAttribute("aria-expanded", String(open)); if (open) menu.firstElementChild.focus(); };
more.addEventListener("click", () => set(menu.hidden));
menu.addEventListener("click", (event) => {
  const item = event.target.closest("li");
  if (!item) return;
  main.textContent = item.textContent;  // the chosen variant becomes the default action
  set(false);
});
document.addEventListener("keydown", (event) => { if (event.key === "Escape") set(false); });
document.addEventListener("click", (event) => { if (!event.target.closest(".splitbtn")) set(false); });
""",
            "The default action plus a caret for its variants; picking one makes it the default.",
        ),
        Item(
            "Dropdown button",
            '<div class="dd"><button class="btn" aria-haspopup="menu" aria-expanded="false">Actions ▾</button>'
            '<ul role="menu" hidden><li role="menuitem" tabindex="-1">Duplicate</li><li role="menuitem" tabindex="-1">Rename</li><li role="menuitem" tabindex="-1">Archive</li></ul></div>',
            BTN
            + """\
.dd { position: relative; height: 170px; }
.dd ul { position: absolute; top: 46px; left: 0; margin: 0; padding: 6px; min-width: 170px; list-style: none; border: 1px solid var(--border);
  border-radius: 10px; background: var(--surface-2); box-shadow: var(--shadow); transform-origin: top left; animation: pop .16s var(--ease); }
.dd ul[hidden] { display: none; }
.dd li { padding: 8px 10px; border-radius: 7px; cursor: pointer; }
.dd li:hover, .dd li:focus { background: var(--surface); outline: none; }
@keyframes pop { from { opacity: 0; scale: .96; } }
""",
            """\
const button = document.querySelector(".dd .btn");
const menu = document.querySelector(".dd ul");
const items = [...menu.children];
const set = (open) => { menu.hidden = !open; button.setAttribute("aria-expanded", String(open)); if (open) items[0].focus(); else button.focus(); };
button.addEventListener("click", () => set(menu.hidden));
menu.addEventListener("keydown", (event) => {
  const index = items.indexOf(document.activeElement);
  if (event.key === "ArrowDown") items[(index + 1) % items.length].focus();
  else if (event.key === "ArrowUp") items[(index - 1 + items.length) % items.length].focus();
  else if (event.key === "Escape" || event.key === "Enter") set(false);
  else return;
  event.preventDefault();
});
menu.addEventListener("click", () => set(false));
document.addEventListener("click", (event) => { if (!event.target.closest(".dd") && !menu.hidden) { menu.hidden = true; button.setAttribute("aria-expanded", "false"); } });
""",
            "A button that only opens a menu; arrow keys move, Escape closes and returns focus.",
        ),
        busy(
            "Loading button",
            "Save changes",
            "Saving…",
            "Saved",
            "Try again",
            "Keeps its width while busy so the layout does not jump; ignores repeat clicks.",
        ),
        busy(
            "Async action button",
            "Deploy",
            "Deploying…",
            "Deployed",
            "Deploy failed",
            "Idle, busy, then success or failure, each with its own colour and label.",
        ),
        Item(
            "Toggle button",
            '<button class="btn tg" aria-pressed="false"><span class="dot"></span>Notifications</button>',
            BTN
            + """\
.tg { background: var(--surface-2); color: var(--muted); border-color: var(--border); }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); transition: background .15s, box-shadow .15s; }
.tg[aria-pressed="true"] { color: var(--fg); border-color: var(--primary); background: color-mix(in srgb, var(--primary) 18%, transparent); }
.tg[aria-pressed="true"] .dot { background: var(--success); box-shadow: 0 0 0 3px color-mix(in srgb, var(--success) 30%, transparent); }
""",
            """\
const toggle = document.querySelector(".tg");
toggle.addEventListener("click", () => toggle.setAttribute("aria-pressed", String(toggle.getAttribute("aria-pressed") !== "true")));
""",
            "aria-pressed carries the state; the label never changes between on and off.",
        ),
        Item(
            "Toggle group",
            '<div class="group" role="group" aria-label="Text style"><button aria-pressed="true"><b>B</b></button><button aria-pressed="false"><i>I</i></button>'
            '<button aria-pressed="false"><u>U</u></button><button aria-pressed="false"><s>S</s></button></div>',
            """\
.group { display: inline-flex; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; background: var(--surface); }
.group button { width: 42px; height: 38px; border: 0; border-right: 1px solid var(--border); background: none; color: var(--muted); }
.group button:last-child { border-right: 0; }
.group button:hover { background: var(--surface-2); }
.group button[aria-pressed="true"] { background: color-mix(in srgb, var(--primary) 22%, transparent); color: var(--fg); }
""",
            """\
document.querySelectorAll(".group button").forEach((button) => button.addEventListener("click", () =>
  button.setAttribute("aria-pressed", String(button.getAttribute("aria-pressed") !== "true"))));
""",
            "Independent toggles joined into one control; any number can be on.",
        ),
        Item(
            "Segmented control",
            '<div class="segc" role="radiogroup" aria-label="View"><label><input type="radio" name="view" checked><span>List</span></label>'
            '<label><input type="radio" name="view"><span>Board</span></label><label><input type="radio" name="view"><span>Calendar</span></label></div>',
            """\
.segc { display: inline-flex; padding: 3px; border-radius: 11px; background: var(--surface-2); }
.segc input { position: absolute; opacity: 0; pointer-events: none; }
.segc span { display: block; padding: 7px 16px; border-radius: 8px; color: var(--muted); font-weight: 600; cursor: pointer; transition: background .15s, color .15s; }
.segc input:checked + span { background: var(--surface); color: var(--fg); box-shadow: 0 1px 3px rgb(0 0 0 / .4); }
.segc input:focus-visible + span { outline: 2px solid var(--accent); }
""",
            note="Exactly one option on; real radio inputs give arrow-key behaviour for free.",
        ),
        Item(
            "Magnetic button",
            '<div class="field"><button class="btn mag"><span>Get started</span></button></div>',
            BTN
            + """\
.field { display: grid; place-items: center; width: 320px; height: 220px; }
.mag { height: 52px; padding: 0 28px; border-radius: 999px; transition: transform .25s var(--ease); will-change: transform; }
.mag span { display: block; transition: transform .25s var(--ease); pointer-events: none; }
""",
            """\
const area = document.querySelector(".field");
const button = area.querySelector(".mag");
const label = button.querySelector("span");
const PULL = 0.35;  // how far the button follows the pointer
area.addEventListener("pointermove", (event) => {
  const box = button.getBoundingClientRect();
  const x = event.clientX - (box.left + box.width / 2);
  const y = event.clientY - (box.top + box.height / 2);
  button.style.transform = `translate(${x * PULL}px, ${y * PULL}px)`;
  label.style.transform = `translate(${x * PULL * 0.4}px, ${y * PULL * 0.4}px)`;
});
area.addEventListener("pointerleave", () => { button.style.transform = label.style.transform = ""; });
""",
            "The button leans toward the pointer within a zone around it and springs back on leave.",
        ),
        variant(
            "Gradient button",
            "Upgrade to Pro",
            ".v { background: linear-gradient(120deg, var(--primary), var(--accent), var(--primary)); background-size: 200% 100%; transition: background-position .5s var(--ease), transform .15s; }\n.v:hover { background-position: 100% 0; }\n",
            "The gradient is twice the width and slides on hover.",
        ),
        Item(
            "Glass button",
            '<div class="bg"><button class="btn gl">Explore</button></div>',
            BTN
            + """\
.bg { display: grid; place-items: center; width: 320px; height: 180px; border-radius: var(--radius);
  background: conic-gradient(from 120deg, #7c5cff, #22d3ee, #f472b6, #7c5cff); }
.gl { background: rgb(255 255 255 / .14); border-color: rgb(255 255 255 / .35); color: #fff; backdrop-filter: blur(12px) saturate(1.4);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / .4); }
.gl:hover { background: rgb(255 255 255 / .24); }
""",
            note="Translucent fill, light inner edge, blur of whatever is behind.",
        ),
        variant(
            "Neon button",
            "Launch",
            ".v { background: transparent; color: var(--accent); border-color: var(--accent); text-shadow: 0 0 8px var(--accent); box-shadow: 0 0 12px color-mix(in srgb, var(--accent) 60%, transparent), inset 0 0 12px color-mix(in srgb, var(--accent) 30%, transparent); }\n.v:hover { background: var(--accent); color: #04121a; text-shadow: none; box-shadow: 0 0 28px var(--accent); }\n",
            "Glowing outline that fills on hover; for dark, high-contrast themes only.",
        ),
        variant(
            "Pill button",
            "Follow",
            ".v { border-radius: 999px; padding: 0 22px; }\n",
            "Fully rounded ends; friendlier, good for tags and social actions.",
        ),
        variant(
            "Circular action button",
            "▶",
            ".v { width: 56px; height: 56px; padding: 0; border-radius: 50%; font-size: 18px; }\n.v:hover { transform: scale(1.06); }\n",
            "A single glyph in a circle for media and primary canvas actions.",
            ' aria-label="Play"',
        ),
        variant(
            "Compact action button",
            "Edit",
            ".v { height: 28px; padding: 0 10px; border-radius: 7px; font-size: 13px; background: var(--surface-2); color: var(--fg); border-color: var(--border); }\n",
            "Dense size for table rows and toolbars.",
        ),
        Item(
            "Expandable action button",
            '<button class="btn exp" aria-label="Add to cart"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg><span>Add to cart</span></button>',
            BTN
            + """\
.exp { padding: 0 11px; gap: 0; border-radius: 999px; }
.exp span { max-width: 0; overflow: hidden; opacity: 0; transition: max-width .3s var(--ease), opacity .2s, margin .3s var(--ease); }
.exp:hover span, .exp:focus-visible span { max-width: 120px; opacity: 1; margin-left: 8px; }
""",
            note="An icon that widens to reveal its label on hover or focus.",
        ),
        Item(
            "Hover-reveal action",
            '<ul class="rows"><li>Design review notes<span class="acts"><button>Open</button><button>Share</button></span></li><li>Launch checklist<span class="acts"><button>Open</button><button>Share</button></span></li></ul>',
            """\
.rows { width: min(420px, 100%); margin: 0; padding: 0; list-style: none; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }
.rows li { display: flex; align-items: center; justify-content: space-between; height: 48px; padding: 0 14px; border-bottom: 1px solid var(--border); }
.rows li:last-child { border: 0; }
.acts { display: flex; gap: 6px; opacity: 0; translate: 6px 0; transition: opacity .15s, translate .15s; }
.rows li:hover .acts, .rows li:focus-within .acts { opacity: 1; translate: 0 0; }
.acts button { padding: 4px 10px; border: 1px solid var(--border); border-radius: 7px; background: var(--surface-2); font-size: 13px; }
""",
            note="Row actions appear on hover and on keyboard focus within the row.",
        ),
        Item(
            "Swipe action",
            '<div class="swipe"><div class="under"><span>Archive</span></div><div class="top" tabindex="0">Drag me left · Invoice #2041</div></div>',
            """\
.swipe { position: relative; width: min(380px, 100%); height: 60px; border-radius: 12px; overflow: hidden; }
.under { position: absolute; inset: 0; display: flex; justify-content: flex-end; align-items: center; padding: 0 20px; background: var(--danger); color: #1a0606; font-weight: 700; }
.top { position: absolute; inset: 0; display: flex; align-items: center; padding: 0 16px; background: var(--surface-2); border: 1px solid var(--border);
  border-radius: 12px; touch-action: pan-y; cursor: grab; user-select: none; }
.top.settle { transition: translate .25s var(--ease); }
""",
            """\
const top = document.querySelector(".top");
const THRESHOLD = 110;
let startX = null;
let offset = 0;
const move = (value) => { offset = Math.min(0, value); top.style.translate = `${offset}px 0`; };
top.addEventListener("pointerdown", (event) => { startX = event.clientX - offset; top.classList.remove("settle"); top.setPointerCapture(event.pointerId); });
top.addEventListener("pointermove", (event) => { if (startX !== null) move(event.clientX - startX); });
const release = () => {
  if (startX === null) return;
  startX = null;
  top.classList.add("settle");
  // Past the threshold the action commits; otherwise the row returns.
  move(offset < -THRESHOLD ? -top.offsetWidth : 0);
};
top.addEventListener("pointerup", release);
top.addEventListener("pointercancel", release);
top.addEventListener("keydown", (event) => { if (event.key === "Delete") { top.classList.add("settle"); move(-top.offsetWidth); } });
""",
            "Drag past a threshold to commit; Delete is the keyboard equivalent.",
        ),
        Item(
            "Context action",
            '<div class="zone" tabindex="0">Right-click (or press the menu key) here</div><ul class="ctxmenu" role="menu" hidden><li role="menuitem" tabindex="-1">Open</li><li role="menuitem" tabindex="-1">Rename</li><li role="menuitem" tabindex="-1">Delete</li></ul>',
            """\
.zone { display: grid; place-items: center; width: 360px; height: 200px; border: 1px dashed var(--border); border-radius: var(--radius); color: var(--muted); }
.ctxmenu { position: fixed; margin: 0; padding: 6px; min-width: 160px; list-style: none; border: 1px solid var(--border); border-radius: 10px;
  background: var(--surface-2); box-shadow: var(--shadow); z-index: 10; }
.ctxmenu[hidden] { display: none; }
.ctxmenu li { padding: 7px 10px; border-radius: 7px; cursor: pointer; }
.ctxmenu li:hover, .ctxmenu li:focus { background: var(--surface); outline: none; }
""",
            """\
const zone = document.querySelector(".zone");
const menu = document.querySelector(".ctxmenu");
const openAt = (x, y) => {
  menu.hidden = false;
  // Keep the menu inside the viewport.
  menu.style.left = `${Math.min(x, innerWidth - menu.offsetWidth - 8)}px`;
  menu.style.top = `${Math.min(y, innerHeight - menu.offsetHeight - 8)}px`;
  menu.firstElementChild.focus();
};
zone.addEventListener("contextmenu", (event) => { event.preventDefault(); openAt(event.clientX, event.clientY); });
zone.addEventListener("keydown", (event) => {
  if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) {
    event.preventDefault();
    const box = zone.getBoundingClientRect();
    openAt(box.left + 24, box.top + 24);
  }
});
const close = () => { menu.hidden = true; };
document.addEventListener("click", close);
document.addEventListener("keydown", (event) => { if (event.key === "Escape") { close(); zone.focus(); } });
""",
            "A menu at the pointer for the thing under it, clamped to the viewport.",
        ),
        Item(
            "Bulk action bar",
            '<div class="bulk"><label><input type="checkbox" checked> Report A</label><label><input type="checkbox" checked> Report B</label><label><input type="checkbox"> Report C</label>'
            '<div class="barx" role="region" aria-label="Bulk actions"><strong></strong><button>Export</button><button>Move</button><button class="d">Delete</button></div></div>',
            """\
.bulk { position: relative; display: grid; gap: 10px; width: min(420px, 100%); height: 240px; align-content: start; padding: 16px;
  border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); overflow: hidden; }
.bulk label { display: flex; gap: 10px; align-items: center; }
.barx { position: absolute; left: 50%; bottom: 14px; display: flex; align-items: center; gap: 8px; padding: 8px 8px 8px 16px; border-radius: 999px;
  background: var(--fg); color: var(--bg); translate: -50% 140%; transition: translate .3s var(--ease); white-space: nowrap; }
.barx.show { translate: -50% 0; }
.barx button { padding: 6px 12px; border: 0; border-radius: 999px; background: rgb(0 0 0 / .1); color: inherit; font-weight: 600; }
.barx .d { background: var(--danger); }
""",
            """\
const boxes = [...document.querySelectorAll('.bulk input[type="checkbox"]')];
const bar = document.querySelector(".barx");
const update = () => {
  const count = boxes.filter((box) => box.checked).length;
  bar.classList.toggle("show", count > 0);
  bar.inert = count === 0;
  bar.querySelector("strong").textContent = `${count} selected`;
};
boxes.forEach((box) => box.addEventListener("change", update));
update();
""",
            "Rises from the bottom while anything is selected and says how many.",
        ),
        Item(
            "Sticky action bar",
            '<form class="sheetform"><div class="body"><p>Long form content…</p></div><footer><span class="muted">Unsaved changes</span><button type="button" class="btn g">Discard</button><button class="btn" type="button">Save</button></footer></form>',
            BTN
            + """\
.sheetform { width: min(460px, 100%); height: 280px; overflow: auto; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }
.body { height: 520px; padding: 18px; color: var(--muted); }
.sheetform footer { position: sticky; bottom: 0; display: flex; align-items: center; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--border);
  background: color-mix(in srgb, var(--surface) 90%, transparent); backdrop-filter: blur(10px); }
.muted { flex: 1; color: var(--warning); font-size: 13px; }
.g { background: transparent; color: var(--fg); border-color: var(--border); }
""",
            note="The form's actions stay in reach at the bottom of its scroll area.",
        ),
        Item(
            "Bottom action bar",
            '<div class="phone2"><main>Order summary</main><footer><div><small>Total</small><strong>$128.00</strong></div><button class="btn">Checkout</button></footer></div>',
            BTN
            + """\
.phone2 { display: grid; grid-template-rows: 1fr auto; width: 320px; height: 420px; border: 1px solid var(--border); border-radius: 26px; overflow: hidden; background: var(--surface); }
.phone2 main { display: grid; place-items: center; color: var(--muted); }
.phone2 footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  border-top: 1px solid var(--border); background: var(--surface-2); }
.phone2 small { display: block; color: var(--muted); font-size: 12px; }
.phone2 .btn { flex: 1; height: 46px; }
""",
            note="Full-width commit area on phones, with the figure that the action commits to.",
        ),
        Item(
            "Inline action",
            '<p class="inline">Your trial ends in 3 days. <button>Upgrade now</button> or <button>remind me later</button>.</p>',
            """\
.inline { max-width: 420px; color: var(--muted); }
.inline button { padding: 0; border: 0; background: none; color: var(--primary); font-weight: 600; text-decoration: underline;
  text-decoration-color: color-mix(in srgb, var(--primary) 40%, transparent); text-underline-offset: 3px; }
.inline button:hover { text-decoration-color: currentColor; }
""",
            note="An action inside a sentence: a button styled as a link, never a link that acts.",
        ),
        Item(
            "Quick action",
            '<div class="quick"><button><b>N</b>New note</button><button><b>U</b>Upload</button><button><b>I</b>Invite</button><button><b>S</b>Search</button></div>',
            """\
.quick { display: grid; grid-template-columns: repeat(4, 96px); gap: 10px; }
.quick button { display: grid; justify-items: center; gap: 8px; padding: 14px 6px; border: 1px solid var(--border); border-radius: 14px;
  background: var(--surface); font-size: 13px; transition: translate .15s var(--ease), border-color .15s; }
.quick button:hover { translate: 0 -2px; border-color: var(--primary); }
.quick b { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; background: color-mix(in srgb, var(--primary) 22%, transparent); color: var(--primary); }
""",
            note="A row of the few things people do most, one click each.",
        ),
        Item(
            "Smart action",
            '<div class="smart"><span class="hint">Looks like a date range</span><button class="btn">Create a chart for Mar – Jun</button><button class="dismiss" aria-label="Dismiss suggestion">×</button></div>',
            BTN
            + """\
.smart { display: flex; align-items: center; gap: 10px; padding: 8px 8px 8px 14px; border: 1px dashed color-mix(in srgb, var(--primary) 60%, transparent);
  border-radius: 14px; background: color-mix(in srgb, var(--primary) 8%, transparent); }
.hint { color: var(--muted); font-size: 13px; }
.dismiss { width: 28px; height: 28px; border: 0; border-radius: 8px; background: none; color: var(--muted); }
.dismiss:hover { background: var(--surface-2); }
""",
            'document.querySelector(".dismiss").addEventListener("click", (event) => event.target.closest(".smart").remove());\n',
            "A suggested action derived from context, with the reason shown and an easy way to dismiss it.",
        ),
        Item(
            "AI action button",
            '<button class="btn ai"><svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M12 2l2.2 6.8L21 11l-6.8 2.2L12 20l-2.2-6.8L3 11l6.8-2.2z"/></svg>Ask AI</button>',
            BTN
            + """\
.ai { position: relative; background: var(--surface); color: var(--fg); isolation: isolate; }
.ai::before { content: ""; position: absolute; inset: -1px; z-index: -2; border-radius: inherit;
  background: conic-gradient(from var(--turn, 0deg), var(--primary), var(--accent), #f472b6, var(--primary)); animation: turn 4s linear infinite; }
.ai::after { content: ""; position: absolute; inset: 1px; z-index: -1; border-radius: 9px; background: var(--surface); }
.ai svg { color: var(--accent); }
@property --turn { syntax: "<angle>"; inherits: false; initial-value: 0deg; }
@keyframes turn { to { --turn: 360deg; } }
""",
            note="A slowly rotating gradient border marks AI-powered actions without shouting.",
        ),
        busy(
            "Generate button",
            "Generate",
            "Generating…",
            "Done",
            "Failed, retry",
            "Starts a generation; the busy state is the cue that work has begun.",
        ),
        Item(
            "Regenerate button",
            '<button class="btn regen"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/></svg>Regenerate</button>',
            BTN
            + """\
.regen { background: var(--surface-2); color: var(--fg); border-color: var(--border); }
.regen svg { transition: rotate .6s var(--ease); }
.regen.turning svg { rotate: 360deg; }
""",
            """\
const button = document.querySelector(".regen");
button.addEventListener("click", () => {
  button.classList.remove("turning");
  void button.offsetWidth;  // restart the transition
  button.classList.add("turning");
});
""",
            "The arrow makes one turn per press: feedback that a new attempt started.",
        ),
        Item(
            "Retry button",
            '<div class="retry" role="alert"><span>Could not reach the server.</span><button class="btn">Retry</button><small></small></div>',
            BTN
            + """\
.retry { display: grid; grid-template-columns: 1fr auto; gap: 6px 12px; align-items: center; width: min(380px, 100%); padding: 14px 16px;
  border: 1px solid color-mix(in srgb, var(--danger) 50%, transparent); border-radius: var(--radius); background: color-mix(in srgb, var(--danger) 10%, transparent); }
.retry small { grid-column: 1 / -1; color: var(--muted); }
.retry .btn { height: 34px; }
""",
            """\
const button = document.querySelector(".retry .btn");
const status = document.querySelector(".retry small");
let attempt = 0;
button.addEventListener("click", () => {
  attempt += 1;
  // Back off between attempts so a failing service is not hammered.
  let wait = Math.min(2 ** attempt, 16);
  button.disabled = true;
  const tick = () => {
    status.textContent = `Attempt ${attempt} failed. You can retry in ${wait}s.`;
    if (wait === 0) { button.disabled = false; status.textContent = `Attempt ${attempt} failed.`; return; }
    wait -= 1;
    setTimeout(tick, 1000);
  };
  tick();
});
""",
            "Retry with exponential back-off, counting down until the next attempt is allowed.",
        ),
        Item(
            "Copy action",
            '<div class="snippet"><code>npm install @northwind/sdk</code><button class="copy" data-value="npm install @northwind/sdk"><span>Copy</span></button></div>',
            """\
.snippet { display: flex; align-items: center; gap: 12px; padding: 8px 8px 8px 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }
.snippet code { font: 13px var(--mono); }
.copy { min-width: 76px; padding: 6px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); transition: background .15s, color .15s; }
.copy.done { background: color-mix(in srgb, var(--success) 20%, transparent); color: var(--success); border-color: transparent; }
""",
            COPY_JS,
            "Confirms in place, then reverts; falls back to an instruction if the clipboard is refused.",
        ),
        Item(
            "Share action",
            '<button class="btn share">Share</button><p class="said" role="status"></p>',
            BTN
            + ".said { position: fixed; bottom: 24px; margin: 0; color: var(--muted); font-size: 13px; }\n",
            """\
const button = document.querySelector(".share");
const said = document.querySelector(".said");
button.addEventListener("click", async () => {
  const data = { title: document.title, url: location.href };
  try {
    if (navigator.share) await navigator.share(data);          // the system share sheet where there is one
    else { await navigator.clipboard.writeText(data.url); said.textContent = "Link copied to clipboard."; }
  } catch (error) {
    if (error.name !== "AbortError") said.textContent = "Sharing is not available here.";
  }
});
""",
            "Uses the native share sheet when the platform has one, otherwise copies the link.",
        ),
        Item(
            "Export action",
            '<button class="btn exportb">Export CSV</button>',
            BTN,
            """\
const rows = [["Month", "Revenue"], ["January", 12400], ["February", 13950], ["March", 15120]];
const escape = (cell) => `"${String(cell).replaceAll('"', '""')}"`;
document.querySelector(".exportb").addEventListener("click", () => {
  const csv = rows.map((row) => row.map(escape).join(",")).join("\\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  const link = Object.assign(document.createElement("a"), { href: url, download: "revenue.csv" });
  link.click();
  URL.revokeObjectURL(url);
});
""",
            "Builds the file in the browser and downloads it; cells are quoted and escaped.",
        ),
        Item(
            "Favorite action",
            '<button class="fav" aria-pressed="false" aria-label="Add to favourites"><svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M12 21s-7.5-4.6-9.6-9.2C.9 8.400 2.900 4.500 6.700 4.500c2 0 3.700 1.100 5.300 3 1.600-1.900 3.300-3 5.300-3 3.800 0 5.800 3.900 4.300 7.300C19.500 16.400 12 21 12 21z"/></svg></button>',
            """\
.fav { display: grid; place-items: center; width: 52px; height: 52px; border: 1px solid var(--border); border-radius: 50%; background: var(--surface); }
.fav svg { fill: none; stroke: var(--muted); stroke-width: 2; transition: fill .2s, stroke .2s; }
.fav[aria-pressed="true"] svg { fill: #f43f5e; stroke: #f43f5e; animation: beat .45s var(--ease); }
@keyframes beat { 30% { scale: 1.35; } 60% { scale: .92; } }
""",
            """\
const fav = document.querySelector(".fav");
fav.addEventListener("click", () => {
  const on = fav.getAttribute("aria-pressed") !== "true";
  fav.setAttribute("aria-pressed", String(on));
  fav.setAttribute("aria-label", on ? "Remove from favourites" : "Add to favourites");
});
""",
            "A heart that fills with a single beat; the label says what pressing will do next.",
        ),
    ),
)
