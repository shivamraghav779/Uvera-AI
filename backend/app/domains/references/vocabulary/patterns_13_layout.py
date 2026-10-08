"""Patterns 421-450: advanced layout and interaction."""

from app.domains.references.vocabulary.base import BTN, Item, Section

WS = """\
.ws { position: relative; width: min(680px, 100%); height: 360px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); overflow: hidden; }
.pane { padding: 16px; overflow: auto; min-width: 0; min-height: 0; }
.pane h4 { margin: 0 0 8px; font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.pane p { margin: 0 0 10px; color: var(--muted); }
.tb { display: flex; align-items: center; gap: 6px; padding: 8px 10px; border-bottom: 1px solid var(--border); background: var(--surface-2); font-size: 13px; }
.tb button { height: 28px; padding: 0 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); font-size: 13px; }
.tb button[aria-pressed="true"] { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 20%, transparent); }
.tb .sp { flex: 1; }
.tb output { color: var(--muted); font-variant-numeric: tabular-nums; }
.bx { position: absolute; display: grid; place-items: center; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2);
  font-size: 13px; font-weight: 600; touch-action: none; user-select: none; cursor: grab; }
.bx.sel { border-color: var(--primary); box-shadow: 0 0 0 2px color-mix(in srgb, var(--primary) 40%, transparent); }
.dots { background: radial-gradient(var(--border) 1px, transparent 1px) 0 0 / 20px 20px, var(--bg); }
"""
# One pointer-drag helper used across this section.
DRAG = r"""const drag = (element, onStart, onMove, onEnd) => element.addEventListener("pointerdown", (event) => {
  if (event.button !== 0) return;
  const context = onStart(event);
  if (context === false) return;
  event.preventDefault();
  element.setPointerCapture(event.pointerId);
  const x0 = event.clientX, y0 = event.clientY;
  const move = (e) => onMove(e.clientX - x0, e.clientY - y0, context, e);
  element.addEventListener("pointermove", move);
  element.addEventListener("pointerup", (e) => { element.removeEventListener("pointermove", move); onEnd?.(context, e); }, { once: true });
});
"""
LOREM = "<p>Notes for the quarterly review. Revenue is ahead of plan in two regions.</p><p>The third needs a closer look at renewals and at the pricing change in March.</p><p>Next steps are listed at the end.</p>"
PANZOOM = (
    DRAG
    + r"""const view = document.querySelector(".view");
const world = view.querySelector(".world");
const readout = document.querySelector(".tb output");
let scale = 1, tx = 0, ty = 0;
const MIN = 0.25, MAX = 4;
const apply = () => {
  world.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
  // The dotted background moves and scales with the world, so the canvas never seems to end.
  view.style.backgroundSize = `${20 * scale}px ${20 * scale}px`;
  view.style.backgroundPosition = `${tx}px ${ty}px`;
  if (readout) readout.textContent = `${Math.round(scale * 100)}%`;
  onView?.();
};
const zoomAt = (factor, cx, cy) => {
  const next = Math.min(MAX, Math.max(MIN, scale * factor));
  tx = cx - ((cx - tx) / scale) * next;
  ty = cy - ((cy - ty) / scale) * next;
  scale = next;
  apply();
};
let onView = null;
view.addEventListener("wheel", (event) => {
  event.preventDefault();
  const box = view.getBoundingClientRect();
  // Pinch or Ctrl+wheel zooms about the pointer; a plain wheel pans.
  if (event.ctrlKey || event.metaKey) zoomAt(Math.exp(-event.deltaY * 0.01), event.clientX - box.left, event.clientY - box.top);
  else { tx -= event.deltaX; ty -= event.deltaY; apply(); }
}, { passive: false });
drag(view, (event) => (event.target === view || event.target === world) && { tx, ty }, (dx, dy, start) => { tx = start.tx + dx; ty = start.ty + dy; apply(); });
view.addEventListener("keydown", (event) => {
  const step = { ArrowLeft: [40, 0], ArrowRight: [-40, 0], ArrowUp: [0, 40], ArrowDown: [0, -40] }[event.key];
  if (step) { tx += step[0]; ty += step[1]; apply(); }
  else if (event.key === "+" || event.key === "=") zoomAt(1.2, view.clientWidth / 2, view.clientHeight / 2);
  else if (event.key === "-") zoomAt(1 / 1.2, view.clientWidth / 2, view.clientHeight / 2);
  else if (event.key === "0") { scale = 1; tx = ty = 0; apply(); }
});
"""
)
CANVAS_CSS = (
    WS
    + ".view { position: relative; height: calc(100% - 45px); overflow: hidden; cursor: grab; touch-action: none; outline: none; }\n.view:focus-visible { box-shadow: inset 0 0 0 2px var(--accent); }\n.world { position: absolute; left: 0; top: 0; transform-origin: 0 0; }\n"
)
GRAPH_CSS = (
    WS
    + ".g { position: relative; height: 100%; }\n.g svg { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }\n.g path { fill: none; stroke: var(--muted); stroke-width: 2; }\n.nd { position: absolute; min-width: 110px; padding: 8px 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); font-size: 13px; font-weight: 600; cursor: grab; touch-action: none; user-select: none; }\n.nd.sel { border-color: var(--primary); }\n"
)
# Nodes that can be dragged, with curved edges redrawn between them.
GRAPH_JS = (
    DRAG
    + r"""const NS = "http://www.w3.org/2000/svg";
const stage = document.querySelector(".g");
const svg = stage.querySelector("svg");
const nodes = new Map();
const edges = [];
const centreOf = (element, side) => ({ x: element.offsetLeft + (side === "out" ? element.offsetWidth : 0), y: element.offsetTop + element.offsetHeight / 2 });
const curve = (a, b) => { const bend = Math.max(40, Math.abs(b.x - a.x) / 2); return `M${a.x} ${a.y}C${a.x + bend} ${a.y} ${b.x - bend} ${b.y} ${b.x} ${b.y}`; };
const redraw = () => edges.forEach((edge) => edge.path.setAttribute("d", curve(centreOf(nodes.get(edge.from), "out"), centreOf(nodes.get(edge.to), "in"))));
const addNode = (id, label, x, y) => {
  const node = Object.assign(document.createElement("div"), { className: "nd", textContent: label });
  node.dataset.id = id;
  node.style.left = `${x}px`; node.style.top = `${y}px`;
  node.tabIndex = 0;
  stage.append(node);
  nodes.set(id, node);
  drag(node, (event) => event.target === node && { x: node.offsetLeft, y: node.offsetTop }, (dx, dy, start) => {
    node.style.left = `${Math.max(0, Math.min(stage.clientWidth - node.offsetWidth, start.x + dx))}px`;
    node.style.top = `${Math.max(0, Math.min(stage.clientHeight - node.offsetHeight, start.y + dy))}px`;
    redraw();
  });
  return node;
};
const addEdge = (from, to) => {
  if (from === to || edges.some((edge) => edge.from === from && edge.to === to)) return;
  const path = document.createElementNS(NS, "path");
  svg.append(path);
  edges.push({ from, to, path });
  redraw();
};
"""
)


def ws(name: str, body: str, css: str, js: str, note: str) -> Item:
    return Item(name, body, WS + css, js, note)


SECTION = Section(
    "patterns",
    "Advanced Layout & Interaction",
    421,
    (
        ws(
            "Split pane",
            f'<div class="ws sp2"><section class="pane"><h4>Editor</h4>{LOREM}</section><section class="pane two"><h4>Preview <button aria-pressed="false">Hide</button></h4>{LOREM}</section></div>',
            ".sp2 { display: grid; grid-template-columns: 1fr 1fr; transition: grid-template-columns .3s var(--ease); }\n.sp2.one { grid-template-columns: 1fr 44px; }\n.two { border-left: 1px solid var(--border); background: var(--bg); }\n.two h4 { display: flex; justify-content: space-between; align-items: center; }\n.two button { border: 0; background: none; color: var(--primary); font-size: 12px; }\n.sp2.one .two p { display: none; }\n.sp2.one .two h4 { writing-mode: vertical-rl; gap: 10px; }\n",
            'const split = document.querySelector(".sp2");\nconst button = split.querySelector("button");\nbutton.addEventListener("click", () => {\n  const hidden = split.classList.toggle("one");\n  button.setAttribute("aria-pressed", String(hidden));\n  button.textContent = hidden ? "Show" : "Hide";\n});\n',
            "Two panes side by side with independent scrolling; the second collapses to a strip.",
        ),
        ws(
            "Resizable pane",
            f'<div class="ws rz"><section class="pane">{LOREM}</section><div class="sep" role="separator" aria-orientation="vertical" aria-label="Resize panes" aria-valuemin="20" aria-valuemax="80" aria-valuenow="50" tabindex="0"></div><section class="pane">{LOREM}</section></div>',
            ".rz { display: grid; grid-template-columns: var(--left, 50%) 9px 1fr; }\n.sep { cursor: col-resize; background: var(--border); background-clip: content-box; padding: 0 4px; transition: background-color .15s; touch-action: none; }\n.sep:hover, .sep:focus-visible, .sep.on { background-color: var(--primary); outline: none; }\n",
            DRAG
            + 'const root = document.querySelector(".rz");\nconst separator = root.querySelector(".sep");\nconst MIN = 20, MAX = 80;\nconst set = (percent) => {\n  const value = Math.min(MAX, Math.max(MIN, percent));\n  root.style.setProperty("--left", `${value}%`);\n  separator.setAttribute("aria-valuenow", String(Math.round(value)));\n};\nconst current = () => Number(separator.getAttribute("aria-valuenow"));\ndrag(separator, () => { separator.classList.add("on"); return current(); }, (dx, _dy, start) => set(start + (dx / root.clientWidth) * 100), () => separator.classList.remove("on"));\nseparator.addEventListener("keydown", (event) => {\n  if (event.key === "ArrowLeft") set(current() - 2); else if (event.key === "ArrowRight") set(current() + 2);\n  else if (event.key === "Home") set(MIN); else if (event.key === "End") set(MAX);\n});\nseparator.addEventListener("dblclick", () => set(50));\n',
            "A separator with role=separator: drag it, use the arrow keys, or double-click to reset; both panes keep a minimum.",
        ),
        ws(
            "Master-detail layout",
            '<div class="ws mdl" data-view="list"><nav class="pane" aria-label="Messages">'
            + "".join(
                f'<button data-t="{t}" data-b="{b}"><b>{t}</b><small>{b}</small></button>'
                for t, b in [
                    ("Launch plan", "Thursday at 10:00 UTC."),
                    ("Budget review", "Two lines need sign-off."),
                    ("Hiring update", "Three offers are out."),
                ]
            )
            + '</nav><article class="pane"><button class="back">← Back</button><h3>Select a message</h3><p></p></article></div>',
            '.mdl { display: grid; grid-template-columns: 230px 1fr; container-type: inline-size; }\n.mdl nav { display: grid; align-content: start; gap: 4px; border-right: 1px solid var(--border); }\n.mdl nav button { text-align: left; padding: 10px; border: 0; border-radius: 10px; background: none; }\n.mdl nav button:hover, .mdl nav button[aria-current="true"] { background: var(--surface-2); }\n.mdl small { display: block; color: var(--muted); }\n.mdl h3 { margin: 0 0 8px; }\n.back { display: none; margin-bottom: 12px; border: 0; background: none; color: var(--primary); padding: 0; }\n@container (max-width: 480px) {\n  .mdl > nav, .mdl > article { grid-column: 1 / -1; grid-row: 1; }\n  .mdl[data-view=list] > article, .mdl[data-view=detail] > nav { display: none; }\n  .back { display: block; }\n}\n',
            'const root = document.querySelector(".mdl");\nconst detail = root.querySelector("article");\nconst items = [...root.querySelectorAll("nav button")];\nitems.forEach((item) => item.addEventListener("click", () => {\n  items.forEach((other) => other.setAttribute("aria-current", String(other === item)));\n  detail.querySelector("h3").textContent = item.dataset.t;\n  detail.querySelector("p").textContent = item.dataset.b;\n  root.dataset.view = "detail";  // on a narrow container the detail replaces the list\n}));\nroot.querySelector(".back").addEventListener("click", () => { root.dataset.view = "list"; });\n',
            "List and detail side by side; in a narrow container they become two screens with a back button (container query).",
        ),
        ws(
            "Multi-column workspace",
            '<div class="ws mcw"><nav class="pane a"><h4>Folders</h4><p>Inbox</p><p>Drafts</p><p>Archive</p></nav><section class="pane b"><h4>Inbox</h4>'
            + "<p>Message subject line</p>" * 9
            + f'</section><article class="pane c"><h4>Message</h4>{LOREM * 2}</article></div>',
            ".mcw { display: grid; grid-template-columns: 150px 220px 1fr; }\n.mcw .pane + .pane { border-left: 1px solid var(--border); }\n.mcw .a { background: var(--bg); }\n.mcw .b p { padding-bottom: 10px; border-bottom: 1px solid var(--border); }\n@media (max-width: 560px) { .mcw { grid-template-columns: 0 200px 1fr; } .mcw .a { padding: 0; } }\n",
            "",
            "Navigation, list and content as three columns that each scroll on their own; the first gives way when space is short.",
        ),
        ws(
            "Full-screen workspace",
            f'<div class="ws fsw"><div class="tb"><b>Canvas</b><span class="sp"></span><button aria-pressed="false">Enter full screen</button></div><div class="pane">{LOREM}</div></div><p class="msg" role="status"></p>',
            ".fsw:fullscreen { width: 100%; height: 100%; border: 0; border-radius: 0; }\n.fsw:fullscreen .pane { max-width: 70ch; margin: 0 auto; font-size: 18px; }\n.msg { position: fixed; bottom: 14px; margin: 0; font-size: 13px; color: var(--muted); }\n",
            'const workspace = document.querySelector(".fsw");\nconst button = workspace.querySelector("button");\nconst message = document.querySelector(".msg");\nbutton.addEventListener("click", async () => {\n  try {\n    if (document.fullscreenElement) await document.exitFullscreen(); else await workspace.requestFullscreen();\n  } catch {\n    message.textContent = "Full screen is not available here.";  // refused by the browser or an embedding page\n  }\n});\n// The button follows the real state, including leaving with Escape.\ndocument.addEventListener("fullscreenchange", () => {\n  const on = document.fullscreenElement === workspace;\n  button.setAttribute("aria-pressed", String(on));\n  button.textContent = on ? "Exit full screen" : "Enter full screen";\n});\n',
            "The Fullscreen API on one region; the control mirrors the actual state and failure is reported.",
        ),
        ws(
            "Focus mode",
            '<article class="ws fm pane"><div class="tb2"><button aria-pressed="false">Focus mode</button></div><p tabindex="0">Revenue grew across every region this quarter, with EMEA furthest ahead of plan.</p><p tabindex="0">Renewals in APAC slipped six points, mostly among customers on the old pricing.</p><p tabindex="0">We recommend moving those accounts to the new plan before their anniversaries.</p><p tabindex="0">Hiring is on track: three offers are out and two have been accepted.</p></article>',
            '.fm { height: auto; padding: 18px 22px; }\n.tb2 { margin-bottom: 14px; }\n.tb2 button { padding: 5px 12px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface-2); font-size: 13px; }\n.tb2 button[aria-pressed="true"] { border-color: var(--primary); }\n.fm p { color: var(--fg); line-height: 1.7; transition: opacity .25s; outline: none; border-radius: 6px; }\n.fm.on p { opacity: .25; }\n.fm.on p.cur { opacity: 1; }\n',
            'const article = document.querySelector(".fm");\nconst toggle = article.querySelector("button");\nconst blocks = [...article.querySelectorAll("p")];\nlet current = 0;\nconst mark = (index) => { current = Math.min(blocks.length - 1, Math.max(0, index)); blocks.forEach((block, i) => block.classList.toggle("cur", i === current)); };\ntoggle.addEventListener("click", () => toggle.setAttribute("aria-pressed", String(article.classList.toggle("on"))));\nblocks.forEach((block, i) => { block.addEventListener("click", () => mark(i)); block.addEventListener("focus", () => mark(i)); });\narticle.addEventListener("keydown", (event) => {\n  if (event.key === "ArrowDown") blocks[Math.min(blocks.length - 1, current + 1)].focus();\n  else if (event.key === "ArrowUp") blocks[Math.max(0, current - 1)].focus();\n});\nmark(0);\n',
            "Everything but the block being read is dimmed; arrow keys and clicks move the focus.",
        ),
        ws(
            "Distraction-free mode",
            f'<div class="ws dfm"><div class="tb"><b>Draft</b><span class="sp"></span><button aria-pressed="false">Hide interface</button></div><div class="body"><aside class="pane"><h4>Outline</h4><p>Intro</p><p>Results</p></aside><div class="pane doc" contenteditable="true" role="textbox" aria-multiline="true" aria-label="Document">{LOREM}</div></div></div>',
            ".dfm { display: grid; grid-template-rows: auto 1fr; }\n.dfm .tb, .dfm aside { transition: translate .3s var(--ease), opacity .3s; }\n.dfm .body { display: grid; grid-template-columns: 160px 1fr; min-height: 0; transition: grid-template-columns .3s var(--ease); }\n.dfm aside { border-right: 1px solid var(--border); }\n.doc { outline: none; max-width: 60ch; margin: 0 auto; }\n.doc p { color: var(--fg); }\n.dfm.quiet .body { grid-template-columns: 0 1fr; }\n.dfm.quiet aside { opacity: 0; padding: 0; border: 0; }\n.dfm.quiet .tb { opacity: 0; }\n.dfm.quiet.peek .tb, .dfm.quiet .tb:focus-within { opacity: 1; }\n",
            'const root = document.querySelector(".dfm");\nconst button = root.querySelector(".tb button");\nconst set = (quiet) => { root.classList.toggle("quiet", quiet); button.setAttribute("aria-pressed", String(quiet)); button.textContent = quiet ? "Show interface" : "Hide interface"; };\nbutton.addEventListener("click", () => set(!root.classList.contains("quiet")));\n// The toolbar comes back when the pointer reaches the top edge, and on Escape.\nroot.addEventListener("pointermove", (event) => root.classList.toggle("peek", event.clientY - root.getBoundingClientRect().top < 48));\ndocument.addEventListener("keydown", (event) => { if (event.key === "Escape") set(false); });\n',
            "Chrome fades away while writing and returns at the top edge, on focus, or with Escape.",
        ),
        ws(
            "Zen mode",
            '<div class="ws zen"><div class="page" contenteditable="true" role="textbox" aria-multiline="true" aria-label="Write">Start writing. Nothing else is on the screen.</div><footer><span class="count"></span><span>Esc to leave</span></footer></div>',
            ".zen { display: grid; grid-template-rows: 1fr auto; background: #0a0b0f; }\n.page { width: min(56ch, 100% - 48px); margin: 0 auto; padding: 120px 0 140px; overflow: auto; outline: none; font: 19px/1.8 Georgia, serif; color: #e6e1d6; caret-color: var(--accent); scrollbar-width: none; }\n.zen footer { display: flex; justify-content: space-between; padding: 8px 16px; font-size: 12px; color: var(--muted); opacity: 0; transition: opacity .4s; }\n.zen.idle footer { opacity: .8; }\n",
            'const zen = document.querySelector(".zen");\nconst page = zen.querySelector(".page");\nconst count = zen.querySelector(".count");\nlet timer = null;\nconst update = () => {\n  count.textContent = `${page.textContent.trim().split(/\\s+/).filter(Boolean).length} words`;\n  // Typewriter scrolling: the line being written stays at the same height.\n  const selection = document.getSelection();\n  if (selection.rangeCount) {\n    const caret = selection.getRangeAt(0).getBoundingClientRect(), box = page.getBoundingClientRect();\n    if (caret.height) page.scrollTop += caret.top - (box.top + box.height * 0.45);\n  }\n  zen.classList.remove("idle");\n  clearTimeout(timer);\n  timer = setTimeout(() => zen.classList.add("idle"), 1500);  // details reappear only when typing stops\n};\npage.addEventListener("input", update);\npage.addEventListener("keydown", (event) => { if (event.key === "Escape") page.blur(); });\nupdate();\n',
            "One column of text, the caret line held in place, and a word count that shows only when typing pauses.",
        ),
        ws(
            "Picture-in-picture panel",
            '<div class="ws pipw"><div class="pane"><h4>Document</h4>'
            + LOREM
            + '</div><div class="pip" tabindex="0" role="group" aria-label="Video, drag to move"><span>▶ Live</span></div></div>',
            ".pip { position: absolute; left: 0; top: 0; display: grid; place-items: center; width: 170px; aspect-ratio: 16 / 9; border-radius: 12px; background: linear-gradient(135deg, #1e1b4b, #7c5cff); color: #fff; font-size: 13px; font-weight: 700; box-shadow: 0 14px 30px -10px rgb(0 0 0 / .8); cursor: grab; touch-action: none; }\n.pip.settle { transition: translate .3s var(--ease); }\n",
            DRAG
            + 'const area = document.querySelector(".pipw");\nconst pip = area.querySelector(".pip");\nconst GAP = 12;\nlet corner = 3;  // 0 top-left, 1 top-right, 2 bottom-left, 3 bottom-right\nconst spot = (index) => [index % 2 ? area.clientWidth - pip.offsetWidth - GAP : GAP, index > 1 ? area.clientHeight - pip.offsetHeight - GAP : GAP];\nconst place = (x, y) => { pip.style.translate = `${x}px ${y}px`; };\nconst snap = (index) => { corner = index; pip.classList.add("settle"); place(...spot(index)); };\ndrag(pip, () => { pip.classList.remove("settle"); return spot(corner); }, (dx, dy, [x, y]) => place(x + dx, y + dy), () => {\n  // On release it goes to whichever corner is nearest.\n  const box = pip.getBoundingClientRect(), frame = area.getBoundingClientRect();\n  const right = box.left + box.width / 2 - frame.left > frame.width / 2, bottom = box.top + box.height / 2 - frame.top > frame.height / 2;\n  snap((bottom ? 2 : 0) + (right ? 1 : 0));\n});\npip.addEventListener("keydown", (event) => {\n  const move = { ArrowLeft: corner & 2, ArrowRight: corner | 1, ArrowUp: corner & 1, ArrowDown: corner | 2 }[event.key];\n  if (move !== undefined) snap(move);\n});\nplace(...spot(corner));\n',
            "A small media panel over the content that can be dragged and snaps to the nearest corner; arrows move it between corners.",
        ),
        ws(
            "Floating panel",
            '<div class="ws fpw dots"><section class="fp" role="dialog" aria-label="Inspector"><header><b>Inspector</b><button class="min" aria-label="Minimise" aria-expanded="true">–</button><button class="x" aria-label="Close">×</button></header><div class="in"><label>Width <input value="320"></label><label>Height <input value="200"></label></div></section><button class="btn reopen" hidden>Open inspector</button></div>',
            BTN
            + ".fp { position: absolute; left: 40px; top: 40px; width: 220px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface-2); box-shadow: var(--shadow); }\n.fp header { display: flex; align-items: center; gap: 4px; padding: 8px 8px 8px 12px; cursor: grab; touch-action: none; user-select: none; border-bottom: 1px solid var(--border); }\n.fp header b { flex: 1; font-size: 13px; }\n.fp header button { width: 24px; height: 24px; border: 0; border-radius: 6px; background: none; color: var(--muted); }\n.fp header button:hover { background: var(--surface); }\n.fp .in { display: grid; gap: 8px; padding: 12px; }\n.fp .in[hidden] { display: none; }\n.fp label { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: var(--muted); }\n.fp input { width: 90px; height: 28px; padding: 0 8px; border: 1px solid var(--border); border-radius: 7px; background: var(--bg); }\n.reopen { position: absolute; left: 16px; bottom: 16px; }\n",
            DRAG
            + 'const area = document.querySelector(".fpw");\nconst panel = area.querySelector(".fp");\nconst body = panel.querySelector(".in");\nconst reopen = area.querySelector(".reopen");\ndrag(panel.querySelector("header"), (event) => !event.target.closest("button") && { x: panel.offsetLeft, y: panel.offsetTop }, (dx, dy, start) => {\n  // The panel can never be dragged out of reach.\n  panel.style.left = `${Math.min(area.clientWidth - panel.offsetWidth, Math.max(0, start.x + dx))}px`;\n  panel.style.top = `${Math.min(area.clientHeight - 40, Math.max(0, start.y + dy))}px`;\n});\npanel.querySelector(".min").addEventListener("click", (event) => { body.hidden = !body.hidden; event.target.setAttribute("aria-expanded", String(!body.hidden)); });\npanel.querySelector(".x").addEventListener("click", () => { panel.hidden = true; reopen.hidden = false; reopen.focus(); });\nreopen.addEventListener("click", () => { panel.hidden = false; reopen.hidden = true; });\n',
            "A panel dragged by its title bar within the workspace, with minimise, close and a way to bring it back.",
        ),
        ws(
            "Sticky panel",
            '<div class="ws stp"><article class="pane">'
            + LOREM * 5
            + '</article><aside><div class="card"><h4>On this page</h4><p>Summary</p><p>Results</p><p>Next steps</p></div></aside></div>',
            ".stp { display: grid; grid-template-columns: 1fr 200px; overflow: auto; }\n.stp article { overflow: visible; }\n.stp aside { padding: 16px 16px 16px 0; }\n.stp .card { position: sticky; top: 16px; padding: 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); }\n.stp h4 { margin: 0 0 8px; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }\n.stp .card p { margin: 0 0 6px; }\n",
            "",
            "position: sticky inside the scrolling area: the side card rides along while the article scrolls.",
        ),
        ws(
            "Dockable panel",
            '<div class="ws dk" data-dock="right"><main class="pane dots"><div class="tb"><span>Dock:</span>'
            + "".join(
                f'<button data-d="{d}" aria-pressed="{"true" if d == "right" else "false"}">{d.title()}</button>'
                for d in ["left", "right", "bottom", "float"]
            )
            + '</div></main><aside class="pane"><h4>Console</h4><p>Ready.</p></aside></div>',
            '.dk { display: grid; grid-template: "main side" 1fr / 1fr 200px; }\n.dk main { grid-area: main; padding: 0; }\n.dk aside { grid-area: side; border-left: 1px solid var(--border); background: var(--surface-2); }\n.dk[data-dock=left] { grid-template: "side main" 1fr / 200px 1fr; }\n.dk[data-dock=left] aside { border-left: 0; border-right: 1px solid var(--border); }\n.dk[data-dock=bottom] { grid-template: "main" 1fr "side" 120px / 1fr; }\n.dk[data-dock=bottom] aside { border-left: 0; border-top: 1px solid var(--border); }\n.dk[data-dock=float] { grid-template: "main" 1fr / 1fr; }\n.dk[data-dock=float] aside { position: absolute; right: 20px; bottom: 20px; width: 200px; height: 130px; border: 1px solid var(--border); border-radius: 12px; box-shadow: var(--shadow); }\n',
            'const root = document.querySelector(".dk");\nconst buttons = [...root.querySelectorAll("[data-d]")];\nconst KEY = "panel.dock";\nconst set = (dock) => {\n  root.dataset.dock = dock;\n  buttons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.d === dock)));\n  try { localStorage.setItem(KEY, dock); } catch { /* the choice lasts for this visit */ }\n};\nbuttons.forEach((button) => button.addEventListener("click", () => set(button.dataset.d)));\ntry { const saved = localStorage.getItem(KEY); if (saved && buttons.some((button) => button.dataset.d === saved)) set(saved); } catch { /* default dock */ }\n',
            "One panel, four homes: left, right, bottom or floating. Only grid areas change, and the choice is remembered.",
        ),
        ws(
            "Expandable workspace",
            f'<div class="ws ew"><aside class="pane l"><h4>Files</h4><p>index.ts</p><p>app.tsx</p></aside><main class="pane"><div class="tb"><button data-s="l" aria-pressed="true">Files</button><button data-s="r" aria-pressed="true">Details</button><span class="sp"></span><button class="max" aria-pressed="false">Maximise</button></div>{LOREM}</main><aside class="pane r"><h4>Details</h4><p>2 KB · today</p></aside></div>',
            ".ew { display: grid; grid-template-columns: var(--l, 150px) 1fr var(--r, 170px); transition: grid-template-columns .3s var(--ease); }\n.ew main { padding: 0; border-inline: 1px solid var(--border); }\n.ew main p { padding: 0 16px; margin-top: 12px; }\n.ew aside { overflow: hidden; white-space: nowrap; }\n",
            'const root = document.querySelector(".ew");\nconst sides = { l: "150px", r: "170px" };\nconst toggles = [...root.querySelectorAll("[data-s]")];\nconst max = root.querySelector(".max");\nconst show = (side, on) => { root.style.setProperty(`--${side}`, on ? sides[side] : "0px"); toggles.find((toggle) => toggle.dataset.s === side).setAttribute("aria-pressed", String(on)); };\ntoggles.forEach((toggle) => toggle.addEventListener("click", () => { show(toggle.dataset.s, toggle.getAttribute("aria-pressed") !== "true"); sync(); }));\nconst sync = () => max.setAttribute("aria-pressed", String(toggles.every((toggle) => toggle.getAttribute("aria-pressed") === "false")));\n// Maximise hides both sides; pressing it again brings both back.\nmax.addEventListener("click", () => { const open = max.getAttribute("aria-pressed") === "true"; show("l", open); show("r", open); sync(); });\n',
            "Side panels that slide shut one at a time, or both at once to give the centre the whole width.",
        ),
        Item(
            "Canvas workspace",
            '<div class="ws"><div class="tb"><button data-z="out" aria-label="Zoom out">−</button><output>100%</output><button data-z="in" aria-label="Zoom in">+</button><button data-z="reset">Reset</button><span class="sp"></span><span>Drag to pan · Ctrl+wheel to zoom</span></div><div class="view dots" tabindex="0" aria-label="Canvas"><div class="world"><div class="bx" style="left:60px;top:50px;width:150px;height:90px">Frame A</div><div class="bx" style="left:280px;top:120px;width:170px;height:110px">Frame B</div></div></div></div>',
            CANVAS_CSS,
            PANZOOM
            + 'document.querySelectorAll("[data-z]").forEach((button) => button.addEventListener("click", () => {\n  const centre = [view.clientWidth / 2, view.clientHeight / 2];\n  if (button.dataset.z === "reset") { scale = 1; tx = ty = 0; apply(); } else zoomAt(button.dataset.z === "in" ? 1.25 : 0.8, ...centre);\n}));\napply();\n',
            "A pannable, zoomable surface: one transform on a world layer, zoom anchored at the pointer, keys for all of it.",
        ),
        Item(
            "Infinite canvas",
            '<div class="ws"><div class="tb"><output>100%</output><span class="sp"></span><span class="pos"></span></div><div class="view dots" tabindex="0" aria-label="Infinite canvas. Double-click to add a note."><div class="world"><div class="bx note" style="left:120px;top:90px">Double-click anywhere</div></div></div></div>',
            CANVAS_CSS
            + ".note { padding: 10px 14px; background: #fde68a; color: #1b1505; border: 0; border-radius: 4px; box-shadow: 0 6px 14px -6px rgb(0 0 0 / .6); cursor: default; white-space: nowrap; }\n.pos { color: var(--muted); font: 12px var(--mono); }\n",
            PANZOOM
            + 'const position = document.querySelector(".pos");\n// Screen position to world position: undo the pan, then the zoom.\nconst toWorld = (event) => { const box = view.getBoundingClientRect(); return [(event.clientX - box.left - tx) / scale, (event.clientY - box.top - ty) / scale]; };\nview.addEventListener("pointermove", (event) => { const [x, y] = toWorld(event); position.textContent = `${Math.round(x)}, ${Math.round(y)}`; });\nlet count = 0;\nview.addEventListener("dblclick", (event) => {\n  const [x, y] = toWorld(event);\n  count += 1;\n  const note = Object.assign(document.createElement("div"), { className: "bx note", textContent: `Note ${count}` });\n  note.style.left = `${x}px`; note.style.top = `${y}px`;\n  world.append(note);  // there is no edge: any coordinate is valid\n});\napply();\n',
            "No bounds: the grid tiles with the pan, coordinates are shown, and anything can be placed anywhere.",
        ),
        Item(
            "Spatial workspace",
            '<div class="ws"><div class="tb"><button class="fit">Zoom to fit</button><output>100%</output></div><div class="view dots" tabindex="0" aria-label="Workspace"><div class="world">'
            + "".join(
                f'<div class="bx" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{n}</div>'
                for n, x, y, w, h in [
                    ("Research", 40, 30, 150, 90),
                    ("Design", 420, 60, 170, 100),
                    ("Build", 760, 260, 180, 110),
                    ("Launch", 260, 420, 160, 90),
                ]
            )
            + '</div><div class="mini" aria-hidden="true"><i></i></div></div></div>',
            CANVAS_CSS
            + ".mini { position: absolute; right: 10px; bottom: 10px; width: 140px; height: 84px; border: 1px solid var(--border); border-radius: 8px; background: color-mix(in srgb, var(--surface) 90%, transparent); overflow: hidden; }\n.mini b { position: absolute; border-radius: 2px; background: var(--muted); }\n.mini i { position: absolute; border: 1.5px solid var(--primary); background: color-mix(in srgb, var(--primary) 15%, transparent); }\n",
            PANZOOM
            + 'const mini = document.querySelector(".mini");\nconst lens = mini.querySelector("i");\nconst boxes = [...world.querySelectorAll(".bx")];\n// The extent of everything on the canvas.\nconst bounds = () => {\n  const xs = boxes.flatMap((box) => [box.offsetLeft, box.offsetLeft + box.offsetWidth]), ys = boxes.flatMap((box) => [box.offsetTop, box.offsetTop + box.offsetHeight]);\n  return { x: Math.min(...xs) - 60, y: Math.min(...ys) - 60, w: Math.max(...xs) - Math.min(...xs) + 120, h: Math.max(...ys) - Math.min(...ys) + 120 };\n};\nconst all = bounds();\nconst ratio = Math.min(mini.clientWidth / all.w, mini.clientHeight / all.h);\nboxes.forEach((box) => { const dot = document.createElement("b"); Object.assign(dot.style, { left: `${(box.offsetLeft - all.x) * ratio}px`, top: `${(box.offsetTop - all.y) * ratio}px`, width: `${box.offsetWidth * ratio}px`, height: `${box.offsetHeight * ratio}px` }); mini.append(dot); });\n// The minimap shows where the viewport sits within the whole.\nonView = () => Object.assign(lens.style, { left: `${(-tx / scale - all.x) * ratio}px`, top: `${(-ty / scale - all.y) * ratio}px`, width: `${(view.clientWidth / scale) * ratio}px`, height: `${(view.clientHeight / scale) * ratio}px` });\ndocument.querySelector(".fit").addEventListener("click", () => {\n  scale = Math.min(view.clientWidth / all.w, view.clientHeight / all.h);\n  tx = -all.x * scale + (view.clientWidth - all.w * scale) / 2;\n  ty = -all.y * scale + (view.clientHeight - all.h * scale) / 2;\n  apply();\n});\napply();\n',
            "A canvas larger than the screen with a minimap of the whole and the viewport, and a zoom-to-fit.",
        ),
        Item(
            "Whiteboard",
            '<div class="ws wb"><div class="tb"><span role="radiogroup" aria-label="Colour">'
            + "".join(
                f'<button role="radio" aria-checked="{"true" if i == 0 else "false"}" data-c="{c}" aria-label="{n}" style="background:{c}"></button>'
                for i, (n, c) in enumerate(
                    [
                        ("White", "#e8ebf2"),
                        ("Violet", "#7c5cff"),
                        ("Cyan", "#22d3ee"),
                        ("Rose", "#f472b6"),
                    ]
                )
            )
            + '</span><button class="er" aria-pressed="false">Eraser</button><span class="sp"></span><button class="un">Undo</button><button class="cl">Clear</button></div><canvas aria-label="Drawing surface"></canvas></div>',
            WS
            + '.wb canvas { display: block; width: 100%; height: calc(100% - 45px); touch-action: none; cursor: crosshair; background: var(--bg); }\n.wb [role=radio] { width: 22px; height: 22px; padding: 0; border-radius: 50%; margin-right: 4px; }\n.wb [role=radio][aria-checked="true"] { box-shadow: 0 0 0 2px var(--surface-2), 0 0 0 4px var(--fg); }\n',
            'const canvas = document.querySelector(".wb canvas");\nconst context = canvas.getContext("2d");\nconst strokes = [];  // every stroke is kept as data, so undo and redraw are exact\nlet colour = "#e8ebf2", erasing = false, current = null;\nconst resize = () => {\n  const ratio = devicePixelRatio || 1;\n  canvas.width = canvas.clientWidth * ratio;\n  canvas.height = canvas.clientHeight * ratio;\n  context.setTransform(ratio, 0, 0, ratio, 0, 0);  // sharp lines on dense screens\n  redraw();\n};\nconst redraw = () => {\n  context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);\n  context.lineCap = context.lineJoin = "round";\n  for (const stroke of strokes) {\n    context.globalCompositeOperation = stroke.erase ? "destination-out" : "source-over";\n    context.strokeStyle = stroke.colour;\n    context.lineWidth = stroke.erase ? 18 : 3;\n    context.beginPath();\n    stroke.points.forEach(([x, y], i) => (i ? context.lineTo(x, y) : context.moveTo(x, y)));\n    if (stroke.points.length === 1) context.lineTo(stroke.points[0][0] + 0.1, stroke.points[0][1]);\n    context.stroke();\n  }\n};\nconst point = (event) => { const box = canvas.getBoundingClientRect(); return [event.clientX - box.left, event.clientY - box.top]; };\ncanvas.addEventListener("pointerdown", (event) => { canvas.setPointerCapture(event.pointerId); current = { colour, erase: erasing, points: [point(event)] }; strokes.push(current); redraw(); });\ncanvas.addEventListener("pointermove", (event) => { if (current) { current.points.push(point(event)); redraw(); } });\ncanvas.addEventListener("pointerup", () => { current = null; });\nconst swatches = [...document.querySelectorAll(".wb [role=radio]")];\nswatches.forEach((swatch) => swatch.addEventListener("click", () => { colour = swatch.dataset.c; erasing = false; eraser.setAttribute("aria-pressed", "false"); swatches.forEach((other) => other.setAttribute("aria-checked", String(other === swatch))); }));\nconst eraser = document.querySelector(".er");\neraser.addEventListener("click", () => { erasing = !erasing; eraser.setAttribute("aria-pressed", String(erasing)); });\ndocument.querySelector(".un").addEventListener("click", () => { strokes.pop(); redraw(); });\ndocument.querySelector(".cl").addEventListener("click", () => { strokes.length = 0; redraw(); });\nnew ResizeObserver(resize).observe(canvas);\n',
            "Freehand drawing on a canvas with colours, an eraser, undo and clear; strokes are stored, so nothing is lost on resize.",
        ),
        Item(
            "Diagram canvas",
            '<div class="ws dots"><div class="g"><svg aria-hidden="true"></svg></div></div>',
            GRAPH_CSS,
            GRAPH_JS
            + 'addNode("user", "User", 30, 60);\naddNode("api", "API gateway", 220, 140);\naddNode("db", "Database", 450, 60);\naddNode("cache", "Cache", 450, 230);\naddEdge("user", "api"); addEdge("api", "db"); addEdge("api", "cache");\n',
            "Boxes joined by curves that follow as the boxes are dragged.",
        ),
        Item(
            "Workflow canvas",
            '<div class="ws wfc pane"><ol></ol></div>',
            WS
            + '.wfc { display: grid; justify-items: center; }\n.wfc ol { display: grid; justify-items: center; margin: 0; padding: 0; list-style: none; }\n.wfc li { display: grid; justify-items: center; }\n.wfc .step { display: flex; align-items: center; gap: 10px; width: 260px; padding: 10px 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); }\n.wfc .step b { flex: 1; font-size: 14px; }\n.wfc .step i { display: grid; place-items: center; width: 24px; height: 24px; border-radius: 7px; background: color-mix(in srgb, var(--primary) 25%, transparent); font-style: normal; font-size: 12px; }\n.wfc .step button { border: 0; background: none; color: var(--muted); }\n.wfc .add { position: relative; width: 22px; height: 22px; margin: 16px 0; padding: 0; border: 1px solid var(--border); border-radius: 50%; background: var(--surface); color: var(--muted); line-height: 1; }\n.wfc .add::before, .wfc .add::after { content: ""; position: absolute; left: 50%; width: 1px; height: 16px; background: var(--border); }\n.wfc .add::before { bottom: 100%; }\n.wfc .add::after { top: 100%; }\n.wfc .add:hover { border-color: var(--primary); color: var(--primary); }\n',
            'const list = document.querySelector(".wfc ol");\nlet steps = ["When a form is submitted", "Add a row to the sheet", "Send a Slack message"];\nconst LIBRARY = ["Wait 5 minutes", "Send an email", "Create a task", "Call a webhook"];\nlet next = 0;\nconst render = () => {\n  list.replaceChildren();\n  steps.forEach((name, index) => {\n    const item = document.createElement("li");\n    const step = Object.assign(document.createElement("div"), { className: "step" });\n    const remove = Object.assign(document.createElement("button"), { textContent: "×" });\n    remove.setAttribute("aria-label", `Remove step: ${name}`);\n    remove.hidden = index === 0;  // the trigger stays\n    remove.addEventListener("click", () => { steps.splice(index, 1); render(); });\n    step.append(Object.assign(document.createElement("i"), { textContent: String(index + 1) }), Object.assign(document.createElement("b"), { textContent: name }), remove);\n    // A step can be inserted after any existing one.\n    const add = Object.assign(document.createElement("button"), { className: "add", textContent: "+" });\n    add.setAttribute("aria-label", `Add a step after: ${name}`);\n    add.addEventListener("click", () => { steps.splice(index + 1, 0, LIBRARY[next++ % LIBRARY.length]); render(); });\n    item.append(step, add);\n    list.append(item);\n  });\n};\nrender();\n',
            "A top-to-bottom automation: numbered steps with an insert button on every connector.",
        ),
        Item(
            "Node editor",
            '<div class="ws dots"><div class="g ne"><svg aria-hidden="true"><path class="ghost"></path></svg></div></div><p class="hint">Drag from a right-hand port to a left-hand port to connect.</p>',
            GRAPH_CSS
            + ".ne .nd { padding: 8px 18px; }\n.port { position: absolute; top: 50%; width: 12px; height: 12px; margin-top: -6px; border-radius: 50%; border: 2px solid var(--surface); background: var(--accent); cursor: crosshair; }\n.port.in { left: -6px; background: var(--primary); }\n.port.out { right: -6px; }\n.ghost { stroke: var(--accent) !important; stroke-dasharray: 5 4; }\n.hint { margin: 10px 0 0; font-size: 13px; color: var(--muted); }\nbody { align-content: center; justify-items: center; }\n",
            GRAPH_JS
            + 'const ghost = svg.querySelector(".ghost");\nconst withPorts = (id, label, x, y) => {\n  const node = addNode(id, label, x, y);\n  for (const side of ["in", "out"]) {\n    const port = Object.assign(document.createElement("span"), { className: `port ${side}` });\n    port.dataset.node = id;\n    node.append(port);\n    if (side === "in") continue;\n    // Dragging from an output draws a provisional wire; releasing on an input makes it real.\n    drag(port, () => centreOf(node, "out"), (dx, dy, from) => ghost.setAttribute("d", curve(from, { x: from.x + dx, y: from.y + dy })), (_from, event) => {\n      ghost.setAttribute("d", "");\n      const target = document.elementFromPoint(event.clientX, event.clientY)?.closest(".port.in");\n      if (target) addEdge(id, target.dataset.node);\n    });\n  }\n};\nwithPorts("in", "Input", 30, 50);\nwithPorts("blur", "Blur", 230, 30);\nwithPorts("mix", "Mix", 230, 180);\nwithPorts("out", "Output", 450, 110);\naddEdge("in", "blur");\n',
            "Nodes with input and output ports; wires are made by dragging from one port to another.",
        ),
        Item(
            "Flow editor",
            '<div class="ws"><div class="tb"><button class="add">Add step</button><button class="del" disabled>Delete</button><button class="lay">Tidy up</button><span class="sp"></span><output></output></div><div class="g fe dots" style="height:calc(100% - 45px)"><svg aria-hidden="true"></svg></div></div>',
            GRAPH_CSS,
            GRAPH_JS
            + 'const count = document.querySelector(".tb output");\nconst remove = document.querySelector(".del");\nlet selected = null, serial = 0;\nconst select = (id) => { selected = id; nodes.forEach((node, key) => node.classList.toggle("sel", key === id)); remove.disabled = id === null; };\nconst refresh = () => { count.textContent = `${nodes.size} steps · ${edges.length} links`; };\nconst create = (label, x, y, after) => {\n  const id = `n${serial++}`;\n  const node = addNode(id, label, x, y);\n  node.addEventListener("pointerdown", () => select(id));\n  node.addEventListener("focus", () => select(id));\n  if (after) addEdge(after, id);\n  refresh();\n  return id;\n};\nconst first = create("Start", 30, 110);\nconst second = create("Review", 220, 40, first);\ncreate("Approve", 420, 110, second);\n// A new step follows the selected one, or the last one made.\ndocument.querySelector(".add").addEventListener("click", () => select(create(`Step ${serial}`, 60 + (serial * 70) % 380, 200, selected ?? [...nodes.keys()].at(-1))));\nconst erase = () => {\n  if (!selected) return;\n  nodes.get(selected).remove();\n  nodes.delete(selected);\n  // Links to a removed step go with it.\n  for (let i = edges.length - 1; i >= 0; i -= 1) if (edges[i].from === selected || edges[i].to === selected) { edges[i].path.remove(); edges.splice(i, 1); }\n  select(null);\n  refresh();\n};\nremove.addEventListener("click", erase);\nstage.addEventListener("keydown", (event) => { if (event.key === "Delete" || event.key === "Backspace") erase(); });\n// Tidy up: columns by distance from a step with nothing before it.\ndocument.querySelector(".lay").addEventListener("click", () => {\n  const depth = new Map();\n  const walk = (id, level) => { if ((depth.get(id) ?? -1) >= level) return; depth.set(id, level); edges.filter((edge) => edge.from === id).forEach((edge) => walk(edge.to, level + 1)); };\n  [...nodes.keys()].filter((id) => !edges.some((edge) => edge.to === id)).forEach((id) => walk(id, 0));\n  const rows = new Map();\n  for (const [id, node] of nodes) {\n    const level = depth.get(id) ?? 0, row = rows.get(level) ?? 0;\n    rows.set(level, row + 1);\n    node.style.left = `${30 + level * 170}px`; node.style.top = `${30 + row * 70}px`;\n  }\n  redraw();\n});\n',
            "Add, select, delete and connect steps, and lay them out in columns by their order.",
        ),
        Item(
            "Drag handles",
            '<ul class="dh" aria-label="Reorderable list">'
            + "".join(
                f'<li><button class="h" aria-label="Reorder {t}">⠿</button><span>{t}</span></li>'
                for t in [
                    "Write launch post",
                    "Update pricing page",
                    "Fix checkout bug",
                    "Plan next sprint",
                ]
            )
            + '</ul><p class="say" role="status"></p>',
            ".dh { width: min(360px, 100%); margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; }\n.dh li { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.dh li.lift { position: relative; z-index: 2; box-shadow: var(--shadow); border-color: var(--primary); }\n.h { width: 26px; height: 26px; border: 0; border-radius: 6px; background: none; color: var(--muted); cursor: grab; touch-action: none; }\n.h:hover, .h:focus-visible { background: var(--surface-2); color: var(--fg); }\n.say { margin: 10px 0 0; font-size: 13px; color: var(--muted); min-height: 20px; }\nbody { align-content: center; justify-items: center; }\n",
            DRAG
            + 'const list = document.querySelector(".dh");\nconst say = document.querySelector(".say");\nconst announce = (item) => { say.textContent = `${item.querySelector("span").textContent}: position ${[...list.children].indexOf(item) + 1} of ${list.children.length}.`; };\nlist.querySelectorAll(".h").forEach((handle) => {\n  const item = handle.closest("li");\n  // Only the handle starts a drag, so the rest of the row stays selectable and scrollable.\n  drag(handle, () => { item.classList.add("lift"); return { y: 0 }; }, (_dx, dy, state) => {\n    const offset = dy - state.y;\n    const previous = item.previousElementSibling, next = item.nextElementSibling;\n    const step = item.offsetHeight + 6;\n    if (next && offset > step / 2) { list.insertBefore(next, item); state.y += step; }\n    else if (previous && offset < -step / 2) { list.insertBefore(item, previous); state.y -= step; }\n    item.style.translate = `0 ${dy - state.y}px`;\n  }, () => { item.classList.remove("lift"); item.style.translate = ""; announce(item); });\n  handle.addEventListener("keydown", (event) => {\n    if (event.key === "ArrowUp" && item.previousElementSibling) list.insertBefore(item, item.previousElementSibling);\n    else if (event.key === "ArrowDown" && item.nextElementSibling) list.insertBefore(item.nextElementSibling, item);\n    else return;\n    event.preventDefault();\n    handle.focus();\n    announce(item);\n  });\n});\n',
            "A grip on each row is the only thing that drags; arrow keys on the grip do the same and the new position is announced.",
        ),
        Item(
            "Resize handles",
            '<div class="ws dots rh"><div class="bx sel" style="left:150px;top:80px;width:220px;height:140px"><span></span></div></div>',
            WS
            + ".rh .bx { cursor: move; }\n.rh .hd { position: absolute; width: 12px; height: 12px; margin: -6px; border: 2px solid var(--primary); border-radius: 3px; background: var(--bg); touch-action: none; }\n.rh span { font: 12px var(--mono); color: var(--muted); }\n",
            DRAG
            + 'const box = document.querySelector(".rh .bx");\nconst area = box.parentElement;\nconst label = box.querySelector("span");\nconst MIN = 60;\nconst rect = () => ({ x: box.offsetLeft, y: box.offsetTop, w: box.offsetWidth, h: box.offsetHeight });\nconst set = ({ x, y, w, h }) => { Object.assign(box.style, { left: `${x}px`, top: `${y}px`, width: `${w}px`, height: `${h}px` }); label.textContent = `${Math.round(w)} × ${Math.round(h)}`; };\n// Eight handles: each names the edges it moves.\nfor (const edges of ["n", "s", "e", "w", "ne", "nw", "se", "sw"]) {\n  const handle = Object.assign(document.createElement("i"), { className: "hd" });\n  handle.style.left = edges.includes("w") ? "0" : edges.includes("e") ? "100%" : "50%";\n  handle.style.top = edges.includes("n") ? "0" : edges.includes("s") ? "100%" : "50%";\n  handle.style.cursor = `${edges}-resize`;\n  box.append(handle);\n  drag(handle, rect, (dx, dy, start) => {\n    const next = { ...start };\n    if (edges.includes("e")) next.w = Math.max(MIN, start.w + dx);\n    if (edges.includes("s")) next.h = Math.max(MIN, start.h + dy);\n    if (edges.includes("w")) { next.w = Math.max(MIN, start.w - dx); next.x = start.x + start.w - next.w; }  // the opposite edge stays put\n    if (edges.includes("n")) { next.h = Math.max(MIN, start.h - dy); next.y = start.y + start.h - next.h; }\n    set(next);\n  });\n}\ndrag(box, (event) => event.target === box || event.target === label ? rect() : false, (dx, dy, start) => set({ ...start, x: Math.min(area.clientWidth - start.w, Math.max(0, start.x + dx)), y: Math.min(area.clientHeight - start.h, Math.max(0, start.y + dy)) }));\nset(rect());\n',
            "Eight handles around a selection; dragging one moves only its edges, the opposite side stays fixed, and there is a minimum size.",
        ),
        Item(
            "Snap-to-grid",
            '<div class="ws"><div class="tb"><button aria-pressed="true">Snap to grid</button><span class="sp"></span><output></output></div><div class="g dots" style="height:calc(100% - 45px)"><div class="bx" style="left:80px;top:60px;width:120px;height:80px">Drag me</div></div></div>',
            WS + ".g { position: relative; }\n",
            DRAG
            + 'const GRID = 20;\nconst box = document.querySelector(".bx");\nconst area = box.parentElement;\nconst toggle = document.querySelector(".tb button");\nconst readout = document.querySelector(".tb output");\nlet snapping = true;\nconst snap = (value) => (snapping ? Math.round(value / GRID) * GRID : value);\nconst place = (x, y) => {\n  box.style.left = `${Math.min(area.clientWidth - box.offsetWidth, Math.max(0, snap(x)))}px`;\n  box.style.top = `${Math.min(area.clientHeight - box.offsetHeight, Math.max(0, snap(y)))}px`;\n  readout.textContent = `${box.offsetLeft}, ${box.offsetTop}`;\n};\ndrag(box, () => ({ x: box.offsetLeft, y: box.offsetTop }), (dx, dy, start, event) => { snapping = toggle.getAttribute("aria-pressed") === "true" && !event.altKey; place(start.x + dx, start.y + dy); });  // Alt turns snapping off for one drag\ntoggle.addEventListener("click", () => toggle.setAttribute("aria-pressed", String(toggle.getAttribute("aria-pressed") !== "true")));\nbox.tabIndex = 0;\nbox.addEventListener("keydown", (event) => {\n  const step = { ArrowLeft: [-GRID, 0], ArrowRight: [GRID, 0], ArrowUp: [0, -GRID], ArrowDown: [0, GRID] }[event.key];\n  if (step) { event.preventDefault(); snapping = true; place(box.offsetLeft + step[0], box.offsetTop + step[1]); }\n});\nplace(box.offsetLeft, box.offsetTop);\n',
            "Positions round to a 20px grid while dragging; Alt suspends it, and the arrow keys move one cell.",
        ),
        Item(
            "Alignment guides",
            '<div class="ws"><div class="g ag dots" style="height:100%"><div class="bx" style="left:60px;top:50px;width:110px;height:70px">A</div><div class="bx" style="left:380px;top:200px;width:140px;height:90px">B</div><div class="bx mv" style="left:210px;top:120px;width:120px;height:80px">Drag me</div><i class="gv"></i><i class="gh"></i></div></div>',
            WS
            + ".g { position: relative; }\n.ag i { position: absolute; background: #f43f5e; pointer-events: none; display: none; z-index: 3; }\n.gv { top: 0; bottom: 0; width: 1px; }\n.gh { left: 0; right: 0; height: 1px; }\n.mv { border-color: var(--primary); }\n",
            DRAG
            + 'const THRESHOLD = 6;\nconst mover = document.querySelector(".mv");\nconst others = [...document.querySelectorAll(".ag .bx:not(.mv)")];\nconst vertical = document.querySelector(".gv"), horizontal = document.querySelector(".gh");\n// Left, centre and right (or top, middle, bottom) of a box along one axis.\nconst lines = (start, size) => [start, start + size / 2, start + size];\nconst nearest = (position, size, targets) => {\n  let best = null;\n  lines(position, size).forEach((line, i) => targets.forEach((target) => {\n    const gap = target - line;\n    if (Math.abs(gap) <= THRESHOLD && (!best || Math.abs(gap) < Math.abs(best.gap))) best = { gap, at: target, i };\n  }));\n  return best;\n};\ndrag(mover, () => ({ x: mover.offsetLeft, y: mover.offsetTop }), (dx, dy, start) => {\n  let x = start.x + dx, y = start.y + dy;\n  const snapX = nearest(x, mover.offsetWidth, others.flatMap((box) => lines(box.offsetLeft, box.offsetWidth)));\n  const snapY = nearest(y, mover.offsetHeight, others.flatMap((box) => lines(box.offsetTop, box.offsetHeight)));\n  if (snapX) x += snapX.gap;  // close enough: snap, and show the line it snapped to\n  if (snapY) y += snapY.gap;\n  vertical.style.display = snapX ? "block" : "none";\n  horizontal.style.display = snapY ? "block" : "none";\n  if (snapX) vertical.style.left = `${snapX.at}px`;\n  if (snapY) horizontal.style.top = `${snapY.at}px`;\n  mover.style.left = `${x}px`; mover.style.top = `${y}px`;\n}, () => { vertical.style.display = horizontal.style.display = "none"; });\n',
            "While dragging, edges and centres are compared with the other boxes; within six pixels it snaps and a guide appears.",
        ),
        Item(
            "Selection marquee",
            '<div class="ws"><div class="g sm" style="height:100%" tabindex="0" aria-label="Drag to select items">'
            + "".join(
                f'<div class="bx" style="left:{40 + (i % 5) * 120}px;top:{40 + (i // 5) * 100}px;width:90px;height:64px">{i + 1}</div>'
                for i in range(15)
            )
            + '<i class="mq"></i></div></div><p class="cnt" role="status">Nothing selected</p>',
            WS
            + ".g { position: relative; cursor: crosshair; touch-action: none; }\n.sm .bx { cursor: default; pointer-events: none; }\n.mq { position: absolute; display: none; border: 1px solid var(--primary); background: color-mix(in srgb, var(--primary) 15%, transparent); pointer-events: none; }\n.cnt { margin: 10px 0 0; font-size: 13px; color: var(--muted); }\nbody { align-content: center; justify-items: center; }\n",
            DRAG
            + 'const area = document.querySelector(".sm");\nconst marquee = area.querySelector(".mq");\nconst items = [...area.querySelectorAll(".bx")];\nconst count = document.querySelector(".cnt");\nconst report = () => { const n = items.filter((item) => item.classList.contains("sel")).length; count.textContent = n ? `${n} selected` : "Nothing selected"; };\ndrag(area, (event) => {\n  const box = area.getBoundingClientRect();\n  // Shift keeps what was selected and adds to it.\n  return { x: event.clientX - box.left, y: event.clientY - box.top, kept: event.shiftKey ? items.filter((item) => item.classList.contains("sel")) : [] };\n}, (dx, dy, start) => {\n  const left = Math.min(start.x, start.x + dx), top = Math.min(start.y, start.y + dy), width = Math.abs(dx), height = Math.abs(dy);\n  Object.assign(marquee.style, { display: "block", left: `${left}px`, top: `${top}px`, width: `${width}px`, height: `${height}px` });\n  for (const item of items) {\n    const hit = item.offsetLeft < left + width && item.offsetLeft + item.offsetWidth > left && item.offsetTop < top + height && item.offsetTop + item.offsetHeight > top;\n    item.classList.toggle("sel", hit || start.kept.includes(item));\n  }\n  report();\n}, () => { marquee.style.display = "none"; });\narea.addEventListener("keydown", (event) => {\n  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "a") { event.preventDefault(); items.forEach((item) => item.classList.add("sel")); report(); }\n  if (event.key === "Escape") { items.forEach((item) => item.classList.remove("sel")); report(); }\n});\n',
            "A rubber-band rectangle selects everything it touches; Shift adds, ⌘/Ctrl+A selects all, Escape clears.",
        ),
        Item(
            "Multi-select toolbar",
            '<div class="ws"><div class="g mst" style="height:100%">'
            + "".join(
                f'<button class="bx" aria-pressed="false" style="left:{40 + (i % 4) * 150}px;top:{50 + (i // 4) * 120}px;width:110px;height:80px">Item {i + 1}</button>'
                for i in range(8)
            )
            + '<div class="bar" role="toolbar" aria-label="Selection actions" hidden><b></b><button data-a="dup">Duplicate</button><button data-a="del">Delete</button><button data-a="none">Clear</button></div></div></div>',
            WS
            + '.g { position: relative; }\n.mst .bx { cursor: pointer; color: var(--fg); }\n.mst .bx[aria-pressed="true"] { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 18%, var(--surface-2)); }\n.bar { position: absolute; left: 50%; bottom: 16px; translate: -50% 0; display: flex; align-items: center; gap: 6px; padding: 6px 6px 6px 14px; border-radius: 12px; background: var(--fg); color: var(--bg); box-shadow: var(--shadow); white-space: nowrap; animation: up .2s var(--ease); }\n.bar[hidden] { display: none; }\n.bar button { height: 30px; padding: 0 10px; border: 0; border-radius: 8px; background: rgb(0 0 0 / .1); color: inherit; font-weight: 600; }\n@keyframes up { from { translate: -50% 16px; opacity: 0; } }\n',
            'const area = document.querySelector(".mst");\nconst bar = area.querySelector(".bar");\nlet last = null;\nconst items = () => [...area.querySelectorAll(".bx")];\nconst chosen = () => items().filter((item) => item.getAttribute("aria-pressed") === "true");\nconst update = () => { const n = chosen().length; bar.hidden = n === 0; bar.querySelector("b").textContent = `${n} selected`; };\narea.addEventListener("click", (event) => {\n  const item = event.target.closest(".bx");\n  if (!item) return;\n  const all = items();\n  if (event.shiftKey && last) {\n    // Shift extends the selection from the last item clicked to this one.\n    const [from, to] = [all.indexOf(last), all.indexOf(item)].sort((a, b) => a - b);\n    all.slice(from, to + 1).forEach((other) => other.setAttribute("aria-pressed", "true"));\n  } else item.setAttribute("aria-pressed", String(item.getAttribute("aria-pressed") !== "true"));\n  last = item;\n  update();\n});\nbar.addEventListener("click", (event) => {\n  const action = event.target.dataset.a;\n  if (!action) return;\n  if (action === "del") chosen().forEach((item) => item.remove());\n  if (action === "dup") chosen().forEach((item) => { const copy = item.cloneNode(true); copy.style.left = `${item.offsetLeft + 16}px`; copy.style.top = `${item.offsetTop + 16}px`; copy.textContent = `${item.textContent} copy`; copy.setAttribute("aria-pressed", "false"); area.insertBefore(copy, bar); });\n  if (action !== "dup") items().forEach((item) => item.setAttribute("aria-pressed", "false"));\n  update();\n});\n',
            "Click toggles, Shift-click extends a range; a toolbar with the count appears while anything is selected.",
        ),
        Item(
            "Undo/redo history",
            '<div class="ur"><div class="row"><button class="btn add">Add shape</button><button class="un" disabled>Undo</button><button class="re" disabled>Redo</button></div><div class="board"></div><ol class="hist" aria-label="History"></ol></div>',
            BTN
            + ".ur { display: grid; gap: 12px; width: min(460px, 100%); }\n.row { display: flex; gap: 8px; }\n.row button:not(.btn) { height: 40px; padding: 0 14px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }\n.row button:disabled { opacity: .35; }\n.board { display: flex; flex-wrap: wrap; gap: 8px; min-height: 76px; padding: 12px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.board i { width: 50px; height: 50px; border-radius: 12px; cursor: pointer; }\n.hist { margin: 0; padding: 0 0 0 20px; font-size: 13px; color: var(--muted); max-height: 110px; overflow: auto; }\n.hist li.now { color: var(--fg); font-weight: 600; }\n.hist li.future { opacity: .4; text-decoration: line-through; }\n",
            '// Every change is a command that knows how to do and undo itself.\nlet shapes = [];\nconst done = [], undone = [];\nconst board = document.querySelector(".board");\nconst history = document.querySelector(".hist");\nconst [undoButton, redoButton] = [document.querySelector(".un"), document.querySelector(".re")];\nconst render = () => {\n  board.replaceChildren(...shapes.map((shape) => { const tile = document.createElement("i"); tile.style.background = shape.colour; tile.title = "Click to remove"; tile.addEventListener("click", () => run(removeCommand(shape))); return tile; }));\n  history.replaceChildren(...[...done, ...[...undone].reverse()].map((command, i) => Object.assign(document.createElement("li"), { textContent: command.label, className: i === done.length - 1 ? "now" : i >= done.length ? "future" : "" })));\n  undoButton.disabled = done.length === 0;\n  redoButton.disabled = undone.length === 0;\n};\nconst run = (command) => { command.do(); done.push(command); undone.length = 0; render(); };  // a new action discards the redo branch\nconst undo = () => { const command = done.pop(); if (command) { command.undo(); undone.push(command); render(); } };\nconst redo = () => { const command = undone.pop(); if (command) { command.do(); done.push(command); render(); } };\nlet serial = 0;\nconst addCommand = () => { const shape = { id: ++serial, colour: `hsl(${(serial * 47) % 360} 70% 55%)` }; return { label: `Add shape ${shape.id}`, do: () => shapes.push(shape), undo: () => { shapes = shapes.filter((other) => other !== shape); } }; };\nconst removeCommand = (shape) => { let index = 0; return { label: `Remove shape ${shape.id}`, do: () => { index = shapes.indexOf(shape); shapes.splice(index, 1); }, undo: () => shapes.splice(index, 0, shape) }; };\ndocument.querySelector(".add").addEventListener("click", () => run(addCommand()));\nundoButton.addEventListener("click", undo);\nredoButton.addEventListener("click", redo);\ndocument.addEventListener("keydown", (event) => {\n  if (!(event.metaKey || event.ctrlKey) || event.key.toLowerCase() !== "z") return;\n  event.preventDefault();\n  if (event.shiftKey) redo(); else undo();\n});\nrender();\n',
            "The command pattern: each action can undo itself, two stacks hold past and future, and a new action clears redo.",
        ),
        Item(
            "Command history",
            '<div class="chs"><ol aria-label="Command history" aria-live="polite"></ol><form><span>›</span><input placeholder="Try: add 3, list, clear" aria-label="Command" autocomplete="off" spellcheck="false"></form></div>',
            ".chs { width: min(480px, 100%); border: 1px solid var(--border); border-radius: 14px; background: #06080c; font: 13px/1.6 var(--mono); overflow: hidden; }\n.chs ol { margin: 0; padding: 12px 14px; list-style: none; height: 220px; overflow: auto; }\n.chs li { display: grid; grid-template-columns: auto 1fr auto; gap: 10px; }\n.chs li time { color: var(--muted); }\n.chs li .c { color: var(--accent); cursor: pointer; }\n.chs li .c:hover { text-decoration: underline; }\n.chs li .o { grid-column: 2 / -1; color: #b8c0d4; margin-bottom: 4px; }\n.chs li .o.bad { color: var(--danger); }\n.chs form { display: flex; gap: 8px; padding: 10px 14px; border-top: 1px solid var(--border); }\n.chs form span { color: var(--success); }\n.chs input { flex: 1; border: 0; outline: 0; background: none; font: inherit; }\n",
            'const log = document.querySelector(".chs ol");\nconst form = document.querySelector(".chs form");\nconst input = form.querySelector("input");\nconst entered = [];\nlet cursor = 0, total = 0;\n// A small set of known commands; anything else is reported, never evaluated.\nconst COMMANDS = {\n  add: (argument) => { const n = Number(argument); if (!Number.isFinite(n)) throw new Error("add needs a number"); total += n; return `total is ${total}`; },\n  list: () => `${entered.length} commands so far`,\n  help: () => `commands: ${Object.keys(COMMANDS).join(", ")}`,\n  clear: () => { log.replaceChildren(); return null; },\n};\nconst execute = (text) => {\n  const [name, argument] = text.trim().split(/\\s+/);\n  let output, failed = false;\n  try { if (!COMMANDS[name]) throw new Error(`unknown command: ${name}`); output = COMMANDS[name](argument); } catch (error) { output = error.message; failed = true; }\n  if (output === null) return;\n  const item = document.createElement("li");\n  const command = Object.assign(document.createElement("span"), { className: "c", textContent: text, title: "Run again" });\n  command.addEventListener("click", () => execute(text));  // any earlier command can be run again\n  item.append(Object.assign(document.createElement("time"), { textContent: new Date().toLocaleTimeString([], { hour12: false }) }), command, document.createElement("span"), Object.assign(document.createElement("span"), { className: `o ${failed ? "bad" : ""}`, textContent: output }));\n  log.append(item);\n  log.scrollTop = log.scrollHeight;\n};\nform.addEventListener("submit", (event) => {\n  event.preventDefault();\n  const text = input.value.trim();\n  if (!text) return;\n  entered.push(text);\n  cursor = entered.length;\n  input.value = "";\n  execute(text);\n});\ninput.addEventListener("keydown", (event) => {\n  if (event.key === "ArrowUp" && cursor > 0) cursor -= 1; else if (event.key === "ArrowDown" && cursor < entered.length) cursor += 1; else return;\n  event.preventDefault();\n  input.value = entered[cursor] ?? "";\n});\nexecute("help");\n',
            "A log of what was run, when and with what result; earlier commands can be recalled with the arrows or re-run by clicking.",
        ),
        Item(
            "Keyboard shortcut overlay",
            '<p class="lead">Press <kbd>?</kbd> to see keyboard shortcuts.</p><dialog class="ks" aria-labelledby="kt"><header><h2 id="kt">Keyboard shortcuts</h2><input type="search" placeholder="Filter" aria-label="Filter shortcuts"></header><div class="cols"></div></dialog>',
            "kbd { display: inline-block; min-width: 22px; padding: 1px 6px; border: 1px solid var(--border); border-bottom-width: 2px; border-radius: 6px; background: var(--surface-2); font: 12px var(--mono); text-align: center; }\n.lead { color: var(--muted); }\n.ks { width: min(600px, calc(100% - 32px)); padding: 0; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); color: var(--fg); }\n.ks::backdrop { background: rgb(4 6 10 / .6); backdrop-filter: blur(3px); }\n.ks header { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 16px 18px; border-bottom: 1px solid var(--border); }\n.ks h2 { margin: 0; font-size: 18px; }\n.ks input { height: 34px; padding: 0 12px; border: 1px solid var(--border); border-radius: 9px; background: var(--bg); color: var(--fg); }\n.cols { columns: 2 220px; column-gap: 28px; padding: 16px 18px; max-height: 60vh; overflow: auto; }\n.cols section { break-inside: avoid; margin-bottom: 16px; }\n.cols h3 { margin: 0 0 8px; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }\n.cols dl { margin: 0; }\n.cols div { display: flex; justify-content: space-between; gap: 12px; padding: 5px 0; font-size: 14px; }\n.cols dd { margin: 0; display: flex; gap: 4px; }\n",
            'const SHORTCUTS = { General: [["Open command palette", "⌘ K"], ["Show shortcuts", "?"], ["Search", "/"]], Editing: [["Undo", "⌘ Z"], ["Redo", "⇧ ⌘ Z"], ["Duplicate", "⌘ D"], ["Delete", "⌫"]], Navigation: [["Go to dashboard", "G D"], ["Go to settings", "G S"], ["Next item", "J"], ["Previous item", "K"]] };\nconst dialog = document.querySelector(".ks");\nconst columns = dialog.querySelector(".cols");\nconst filter = dialog.querySelector("input");\nconst render = () => {\n  const query = filter.value.trim().toLowerCase();\n  columns.replaceChildren();\n  for (const [group, rows] of Object.entries(SHORTCUTS)) {\n    const shown = rows.filter(([name]) => name.toLowerCase().includes(query));\n    if (shown.length === 0) continue;\n    const section = document.createElement("section");\n    const list = document.createElement("dl");\n    for (const [name, keys] of shown) {\n      const row = document.createElement("div");\n      const combo = document.createElement("dd");\n      combo.append(...keys.split(" ").map((key) => Object.assign(document.createElement("kbd"), { textContent: key })));\n      row.append(Object.assign(document.createElement("dt"), { textContent: name }), combo);\n      list.append(row);\n    }\n    section.append(Object.assign(document.createElement("h3"), { textContent: group }), list);\n    columns.append(section);\n  }\n};\nfilter.addEventListener("input", render);\ndocument.addEventListener("keydown", (event) => {\n  // "?" opens it, but never while someone is typing in a field.\n  if (event.key !== "?" || event.target.closest("input, textarea, [contenteditable]")) return;\n  event.preventDefault();\n  filter.value = "";\n  render();\n  if (!dialog.open) dialog.showModal();\n});\ndialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });\n',
            "Pressing ? opens a searchable, grouped sheet of shortcuts, unless the person is typing in a field.",
        ),
    ),
)
