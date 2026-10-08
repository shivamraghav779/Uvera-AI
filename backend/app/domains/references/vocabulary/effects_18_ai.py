"""Effects 451-480: AI and agents."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import BURST_JS, REPLAY_BTN, REPLAY_CSS, STAGE

CALM = 'const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\n'
SPARK = '<svg class="mark" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l2.2 6.8L21 11l-6.8 2.2L12 20l-2.2-6.8L3 11l6.8-2.2z"/></svg>'
AVATAR = ".ai { position: relative; display: grid; place-items: center; width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #7c5cff, #22d3ee); }\n.mark { position: relative; width: 28px; fill: #fff; }\n"
BUBBLE = ".bubble { position: relative; width: 340px; padding: 14px 16px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); line-height: 1.6; }\n.bubble p { margin: 0; }\n"
ANSWER = "Retrieval adds your own documents to the prompt, so the model answers from them instead of from memory."
RESTART = 'const root = document.querySelector(".fx");\nconst play = () => { root.classList.remove("go"); void root.offsetWidth; root.classList.add("go"); };\ndocument.querySelector(".replay").addEventListener("click", play);\nplay();\n'
NS = 'const NS = "http://www.w3.org/2000/svg";\nconst make = (tag, attrs = {}, parent) => { const node = document.createElementNS(NS, tag); for (const key in attrs) node.setAttribute(key, attrs[key]); parent?.append(node); return node; };\n'
STEP_LOOP = "let timers = [];\nconst later = (ms, action) => timers.push(setTimeout(action, calm ? 0 : ms));\nconst reset = () => { timers.forEach(clearTimeout); timers = []; };\n"
GRAPH = ".graph { width: 380px; overflow: visible; }\n.graph text { fill: var(--fg); font: 600 11px var(--font); text-anchor: middle; }\n"


def ai(
    name: str, inner: str, css: str, note: str, js: str = "", replay: bool = False, label: str = ""
) -> Item:
    status = f' role="status" aria-label="{label}"' if label else ""
    html = f'<div class="stage"><div class="fx"{status}>{inner}</div>{REPLAY_BTN if replay else ""}</div>'
    return Item(
        name,
        html,
        STAGE
        + ".fx { position: relative; display: grid; place-items: center; }\n"
        + (REPLAY_CSS if replay else "")
        + css,
        js,
        note,
    )


def node(x: int, y: int, label: str, cls: str = "") -> str:
    return f'<g class="node {cls}" transform="translate({x} {y})"><rect x="-44" y="-18" width="88" height="36" rx="10"/><text y="4">{label}</text></g>'


NODE_CSS = ".node rect { fill: var(--surface); stroke: var(--border); stroke-width: 1.5; transition: all .3s; }\n.wire { fill: none; stroke: var(--border); stroke-width: 2; }\n"

SECTION = Section(
    "effects",
    "AI / Agent Effects",
    451,
    (
        ai(
            "AI thinking pulse",
            SPARK,
            AVATAR
            + ".fx { width: 64px; height: 64px; }\n.fx { border-radius: 50%; background: linear-gradient(135deg, #7c5cff, #22d3ee); animation: think 1.4s ease-in-out infinite; }\n@keyframes think { 0%, 100% { scale: 1; box-shadow: 0 0 0 0 rgb(124 92 255 / .6); } 50% { scale: 1.08; box-shadow: 0 0 0 16px rgb(124 92 255 / 0); } }\n",
            "The assistant's mark swells and releases a ring on each beat while it works.",
            label="Thinking",
        ),
        ai(
            "AI breathing glow",
            SPARK,
            AVATAR
            + '.fx { width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #7c5cff, #22d3ee); }\n.fx::before { content: ""; position: absolute; inset: -18px; border-radius: 50%; background: radial-gradient(circle, rgb(124 92 255 / .8), rgb(34 211 238 / .4) 50%, transparent 70%); filter: blur(10px); animation: breathe 4s ease-in-out infinite alternate; z-index: -1; }\n.stage { isolation: isolate; }\n@keyframes breathe { from { opacity: .3; scale: .8; } to { opacity: 1; scale: 1.25; } }\n',
            "A halo behind the mark rises and falls slowly: present and listening, not busy.",
            label="Assistant ready",
        ),
        ai(
            "AI neural pulse",
            '<svg class="graph" viewBox="0 0 380 160" aria-hidden="true"></svg>',
            GRAPH
            + ".edge { stroke: var(--border); stroke-width: 1; }\n.cell { fill: var(--surface-2); stroke: var(--border); }\n.spike { fill: var(--accent); filter: drop-shadow(0 0 5px var(--accent)); }\n.cell.lit { fill: var(--accent); transition: none; }\n.cell { transition: fill .7s; }\n",
            "Pulses travel along the connections of a small network from left to right, and each node flashes as a pulse reaches it.",
            CALM
            + NS
            + """\
const svg = document.querySelector(".graph");
const SIZES = [3, 4, 4, 2];
const layers = SIZES.map((size, column) => Array.from({ length: size }, (_, row) => ({ x: 40 + column * 100, y: 80 + (row - (size - 1) / 2) * 38 })));
layers.slice(0, -1).forEach((layer, column) => layer.forEach((from) => layers[column + 1].forEach((to) => make("line", { x1: from.x, y1: from.y, x2: to.x, y2: to.y, class: "edge" }, svg))));
layers.flat().forEach((cell) => { cell.dot = make("circle", { cx: cell.x, cy: cell.y, r: 7, class: "cell" }, svg); });
const pick = (list) => list[Math.floor(Math.random() * list.length)];
const flash = (cell) => { cell.dot.classList.add("lit"); setTimeout(() => cell.dot.classList.remove("lit"), 120); };
// One pulse: a dot that travels an edge, then hands over to a random edge of the next layer.
const fire = (from, column) => {
  flash(from);
  if (column === layers.length - 1) return;
  const to = pick(layers[column + 1]);
  const spike = make("circle", { r: 3.5, class: "spike" }, svg);
  const travel = spike.animate([{ transform: `translate(${from.x}px, ${from.y}px)` }, { transform: `translate(${to.x}px, ${to.y}px)` }], { duration: 380, easing: "ease-in-out" });
  travel.onfinish = () => { spike.remove(); fire(to, column + 1); };
};
if (calm) layers[1].forEach(flash); else setInterval(() => fire(pick(layers[0]), 0), 320);
""",
            label="Model is working",
        ),
        ai(
            "AI token stream",
            '<div class="lane" aria-hidden="true"></div>',
            ".lane { position: relative; width: 380px; height: 120px; overflow: hidden; mask: linear-gradient(90deg, transparent, #000 15% 85%, transparent); }\n.lane span { position: absolute; left: 0; top: var(--row); padding: 3px 9px; border-radius: 7px; background: color-mix(in srgb, var(--tint) 22%, var(--surface)); border: 1px solid color-mix(in srgb, var(--tint) 50%, transparent); font: 12px var(--mono); white-space: nowrap; animation: pass var(--time) linear forwards; }\n@keyframes pass { from { translate: -80px 0; } to { translate: 400px 0; } }\n",
            "Tokens as a flow: chips enter on the left in several lanes at slightly different speeds and leave on the right.",
            CALM
            + """\
const lane = document.querySelector(".lane");
const TOKENS = ["The", " model", " predicts", " one", " token", " at", " a", " time", ",", " then", " feeds", " it", " back", " in", "."];
const TINTS = ["#7c5cff", "#22d3ee", "#f472b6"];
let index = 0;
const emit = () => {
  const chip = Object.assign(document.createElement("span"), { textContent: TOKENS[index % TOKENS.length].trim() });
  chip.style.setProperty("--row", `${8 + (index % 4) * 28}px`);
  chip.style.setProperty("--time", `${2.6 + (index % 3) * 0.5}s`);
  chip.style.setProperty("--tint", TINTS[index % TINTS.length]);
  chip.addEventListener("animationend", () => chip.remove());
  lane.append(chip);
  index += 1;
};
if (calm) { lane.textContent = TOKENS.join(""); } else { emit(); setInterval(emit, 240); }
""",
            label="Generating tokens",
        ),
        ai(
            "AI cursor blink",
            f'<p>{ANSWER[:38]}<i class="caret"></i></p>',
            BUBBLE.replace(".bubble", ".fx")
            + ".caret { display: inline-block; width: 2px; height: 1.15em; margin-left: 2px; vertical-align: text-bottom; background: var(--accent); box-shadow: 0 0 8px var(--accent); animation: blink 1.1s ease-in-out infinite; }\n@keyframes blink { 0%, 45% { opacity: 1; } 55%, 100% { opacity: 0; } }\n.fx { display: block; }\n",
            "A thin glowing caret at the end of unfinished text. It fades between on and off instead of switching, which reads as softer than a terminal cursor.",
        ),
        ai(
            "AI response reveal",
            f"<p>{ANSWER}</p>",
            BUBBLE.replace(".bubble", ".fx")
            + '.fx { display: block; }\n@property --edge { syntax: "<percentage>"; inherits: false; initial-value: 130%; }\n.fx p { mask: linear-gradient(180deg, #000 calc(var(--edge) - 35%), transparent var(--edge)); }\n.fx.go { animation: rise .5s var(--ease) both; }\n.fx.go p { animation: unveil 1.4s ease-out both; }\n@keyframes rise { from { opacity: 0; translate: 0 10px; } }\n@keyframes unveil { from { --edge: 0%; } }\n',
            "A finished answer is uncovered from the top down behind a soft edge, as the bubble rises into place.",
            RESTART,
            replay=True,
        ),
        ai(
            "AI response shimmer",
            '<i style="width: 92%"></i><i style="width: 100%"></i><i style="width: 64%"></i>',
            BUBBLE.replace(".bubble", ".fx")
            + ".fx { gap: 10px; place-items: start; }\n.fx i { height: 11px; border-radius: 6px; background: linear-gradient(100deg, var(--surface-2) 30%, color-mix(in srgb, var(--primary) 60%, var(--surface-2)) 50%, var(--surface-2) 70%) fixed 0 0 / 250% 100%; animation: sweep 1.6s linear infinite; }\n@keyframes sweep { from { background-position: 150% 0; } to { background-position: -100% 0; } }\n",
            "Placeholder lines where the answer will be, with a tinted highlight crossing all of them at once.",
            label="Writing a response",
        ),
        ai(
            "AI response gradient",
            f"<p>{ANSWER}</p>",
            BUBBLE.replace(".bubble", ".fx")
            + '.fx { display: block; border-color: transparent; background: linear-gradient(var(--surface), var(--surface)) padding-box, conic-gradient(from var(--a), #7c5cff, #22d3ee, #f472b6, #7c5cff) border-box; animation: turn 4s linear infinite; }\n@property --a { syntax: "<angle>"; inherits: false; initial-value: 0deg; }\n@keyframes turn { to { --a: 360deg; } }\n',
            "The answer's border is a slowly turning gradient: a quiet mark that this text was generated.",
        ),
        ai(
            "AI source highlight",
            '<p>Retrieval adds <mark id="m1">your own documents</mark> to the prompt, so the model <mark id="m2">answers from them</mark> instead of from memory.</p><div class="sources"><button data-for="m1">1 · handbook.pdf</button><button data-for="m2">2 · policy.md</button></div>',
            BUBBLE.replace(".bubble", ".fx")
            + ".fx { display: block; }\nmark { padding: 1px 2px; border-radius: 4px; color: inherit; background: linear-gradient(rgb(34 211 238 / .3), rgb(34 211 238 / .3)) 0 0 / 0% 100% no-repeat; transition: background-size .45s var(--ease); }\nmark.on { background-size: 100% 100%; }\n.sources { display: flex; gap: 8px; margin-top: 12px; }\n.sources button { padding: 4px 10px; border: 1px solid var(--border); border-radius: 99px; background: none; font-size: 12px; }\n.sources button:hover, .sources button:focus-visible { border-color: var(--accent); outline: none; }\n",
            "Pointing at a source sweeps a highlight across exactly the passage that came from it.",
            'document.querySelectorAll(".sources button").forEach((source) => {\n  const passage = document.getElementById(source.dataset.for);\n  const set = (on) => passage.classList.toggle("on", on);\n  source.addEventListener("pointerenter", () => set(true));\n  source.addEventListener("pointerleave", () => set(false));\n  source.addEventListener("focus", () => set(true));\n  source.addEventListener("blur", () => set(false));\n});\ndocument.getElementById("m1").classList.add("on");\n',
        ),
        ai(
            "AI citation glow",
            '<p>Retrieval adds your own documents to the prompt<a class="cite" href="#s1" aria-label="Source 1">1</a>, so the model answers from them<a class="cite" href="#s2" aria-label="Source 2">2</a> instead of from memory.</p>',
            BUBBLE.replace(".bubble", ".fx")
            + ".fx { display: block; }\n.cite { display: inline-grid; place-items: center; width: 17px; height: 17px; margin-left: 3px; border-radius: 50%; background: var(--surface-2); color: var(--accent); font-size: 10px; font-weight: 700; text-decoration: none; vertical-align: super; transition: all .25s; animation: arrive 1.8s ease-out both; }\n.cite:nth-of-type(2) { animation-delay: .5s; }\n.cite:hover, .cite:focus-visible { background: var(--accent); color: #06202a; box-shadow: 0 0 12px var(--accent); outline: none; }\n@keyframes arrive { 0% { box-shadow: 0 0 0 0 rgb(34 211 238 / .9); background: var(--accent); color: #06202a; } 100% { box-shadow: 0 0 0 10px rgb(34 211 238 / 0); } }\n",
            "Citation markers flare once as they appear, so the reader notices the claim is sourced, and glow again on hover.",
        ),
        ai(
            "AI confidence pulse",
            '<span class="conf"><i></i>Confidence <b>62%</b></span>',
            ".conf { display: flex; align-items: center; gap: 10px; padding: 9px 16px 9px 12px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface); }\n.conf i { width: 12px; height: 12px; border-radius: 50%; background: var(--tone); animation: beat var(--pace) ease-in-out infinite; }\n@keyframes beat { 50% { scale: 1.5; box-shadow: 0 0 12px var(--tone); } }\n.dial { display: block; width: 200px; margin-top: 14px; accent-color: var(--primary); }\n",
            "The indicator beats faster and turns from green through amber to red as confidence falls: uncertainty that is felt as well as read. Drag the slider.",
            'const badge = document.querySelector(".conf");\nconst slider = Object.assign(document.createElement("input"), { type: "range", min: 0, max: 100, value: 62, className: "dial" });\nslider.setAttribute("aria-label", "Confidence");\nbadge.after(slider);\nconst show = () => {\n  const value = Number(slider.value);\n  badge.querySelector("b").textContent = `${value}%`;\n  badge.style.setProperty("--tone", value >= 75 ? "var(--success)" : value >= 45 ? "var(--warning)" : "var(--danger)");\n  badge.style.setProperty("--pace", `${(0.5 + (value / 100) * 2).toFixed(2)}s`);  // less sure, faster pulse\n};\nslider.addEventListener("input", show);\nshow();\n',
        ),
        ai(
            "AI reasoning timeline",
            '<ol class="steps"><li>Read the question</li><li>Search the handbook</li><li>Compare two policies</li><li>Draft the answer</li></ol>',
            '.fx { place-items: start; }\n.steps { display: grid; gap: 0; margin: 0; padding: 0; list-style: none; }\n.steps li { position: relative; padding: 0 0 16px 28px; color: var(--muted); opacity: 0; translate: 0 8px; transition: all .4s var(--ease); }\n.steps li.shown { opacity: 1; translate: 0 0; }\n.steps li::before { content: ""; position: absolute; left: 0; top: 3px; width: 12px; height: 12px; border: 2px solid var(--border); border-radius: 50%; background: var(--bg); transition: all .3s; }\n.steps li::after { content: ""; position: absolute; left: 7px; top: 19px; bottom: -3px; width: 2px; background: var(--primary); scale: 1 0; transform-origin: 50% 0; transition: scale .5s var(--ease); }\n.steps li:last-child::after { display: none; }\n.steps li.active { color: var(--fg); }\n.steps li.active::before { border-color: var(--primary); box-shadow: 0 0 0 4px rgb(124 92 255 / .25); animation: busy 1s ease-in-out infinite alternate; }\n.steps li.done::before { border-color: var(--primary); background: var(--primary); }\n.steps li.done::after { scale: 1 1; }\n@keyframes busy { to { box-shadow: 0 0 0 7px rgb(124 92 255 / .1); } }\n',
            "Steps of the model's work appear one by one: each is shown as active, then marked done as a line grows down to the next.",
            CALM
            + STEP_LOOP
            + 'const steps = [...document.querySelectorAll(".steps li")];\nconst play = () => {\n  reset();\n  steps.forEach((step) => step.classList.remove("shown", "active", "done"));\n  steps.forEach((step, index) => {\n    later(300 + index * 900, () => step.classList.add("shown", "active"));\n    later(300 + (index + 1) * 900, () => { step.classList.remove("active"); step.classList.add("done"); });\n  });\n};\ndocument.querySelector(".replay").addEventListener("click", play);\nplay();\n',
            replay=True,
        ),
        ai(
            "Agent activation pulse",
            SPARK + "<span>Research agent</span>",
            ".fx { display: flex; gap: 10px; padding: 12px 18px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); font-weight: 600; }\n.mark { width: 20px; fill: var(--muted); transition: fill .3s; }\n.fx.go { animation: wake 1s ease-out both; border-color: var(--primary); }\n.fx.go .mark { fill: var(--primary); animation: spin .8s var(--ease); }\n@keyframes wake { 0% { box-shadow: 0 0 0 0 rgb(124 92 255 / .8); scale: .96; } 40% { scale: 1.04; } 100% { box-shadow: 0 0 0 22px rgb(124 92 255 / 0); scale: 1; } }\n@keyframes spin { from { rotate: -180deg; scale: .4; } }\n",
            "An agent coming online: the card kicks, a ring leaves it, and its icon spins up into the active colour.",
            RESTART,
            replay=True,
        ),
        ai(
            "Agent handoff animation",
            '<div class="agent a">Planner</div><i class="parcel" aria-hidden="true"></i><div class="agent b">Coder</div>',
            ".fx { display: flex; gap: 110px; }\n.agent { padding: 12px 18px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); font-weight: 600; transition: all .3s; }\n.parcel { position: absolute; left: 50%; top: 50%; width: 16px; height: 16px; margin: -8px; border-radius: 5px; background: var(--accent); box-shadow: 0 0 14px var(--accent); opacity: 0; }\n"
            ".go .a { animation: give 2.2s both; }\n.go .b { animation: take 2.2s both; }\n.go .parcel { animation: carry 2.2s var(--ease) both; }\n"
            "@keyframes give { 0%, 25% { border-color: var(--primary); box-shadow: 0 0 20px rgb(124 92 255 / .5); } 50%, 100% { border-color: var(--border); box-shadow: none; opacity: .55; } }\n"
            "@keyframes take { 0%, 55% { opacity: .55; } 70% { scale: 1.08; } 75%, 100% { opacity: 1; border-color: var(--accent); box-shadow: 0 0 20px rgb(34 211 238 / .5); } }\n"
            "@keyframes carry { 0%, 20% { translate: -70px 0; opacity: 0; scale: .4; } 30% { opacity: 1; scale: 1; } 50% { translate: 0 -22px; rotate: 180deg; } 68% { translate: 70px 0; opacity: 1; scale: 1; } 78%, 100% { translate: 70px 0; opacity: 0; scale: .4; } }\n",
            "Work passes between agents as a visible parcel: it leaves the first, which dims, arcs across, and the second lights up as it lands.",
            RESTART,
            replay=True,
        ),
        ai(
            "Agent connection pulse",
            '<svg class="graph" viewBox="0 0 380 120" aria-hidden="true"><path class="wire" d="M82 60 C150 10, 230 110, 298 60"/><path class="flow" d="M82 60 C150 10, 230 110, 298 60"/>'
            + node(44, 60, "Agent")
            + node(336, 60, "Service")
            + "</svg>",
            GRAPH
            + NODE_CSS
            + ".flow { fill: none; stroke: var(--accent); stroke-width: 2.5; stroke-linecap: round; stroke-dasharray: 14 240; animation: send 1.6s linear infinite; filter: drop-shadow(0 0 5px var(--accent)); }\n@keyframes send { from { stroke-dashoffset: 14; } to { stroke-dashoffset: -240; } }\n",
            "A bright dash runs along the line between two nodes, again and again: data is moving across this connection.",
        ),
        ai(
            "Agent node glow",
            '<svg class="graph" viewBox="0 0 380 120" aria-hidden="true">'
            + node(70, 60, "Plan", "done")
            + node(190, 60, "Search", "active")
            + node(310, 60, "Write")
            + "</svg>",
            GRAPH
            + NODE_CSS
            + ".node.done rect { stroke: var(--success); }\n.node.active rect { stroke: var(--primary); fill: color-mix(in srgb, var(--primary) 18%, var(--surface)); animation: aura 1.6s ease-in-out infinite alternate; }\n.node:not(.done):not(.active) { opacity: .5; }\n@keyframes aura { from { filter: drop-shadow(0 0 2px var(--primary)); } to { filter: drop-shadow(0 0 14px var(--primary)); } }\n",
            "The running node carries a breathing glow; finished nodes keep a steady outline and those still waiting are dimmed.",
        ),
        ai(
            "Agent workflow flow",
            '<svg class="graph" viewBox="0 0 380 120" aria-hidden="true"><path class="wire" id="w1" pathLength="1" d="M114 60 H146"/><path class="wire" id="w2" pathLength="1" d="M234 60 H266"/>'
            + node(70, 60, "Plan")
            + node(190, 60, "Search")
            + node(310, 60, "Write")
            + "</svg>",
            GRAPH
            + NODE_CSS
            + ".wire { stroke: var(--primary); stroke-dasharray: 1; stroke-dashoffset: 1; transition: stroke-dashoffset .4s ease-in-out; }\n.wire.on { stroke-dashoffset: 0; }\n.node { opacity: .45; transition: opacity .3s; }\n.node.active, .node.done { opacity: 1; }\n.node.active rect { stroke: var(--primary); filter: drop-shadow(0 0 8px var(--primary)); }\n.node.done rect { stroke: var(--success); fill: color-mix(in srgb, var(--success) 14%, var(--surface)); }\n",
            "The run advances through the graph: a node works, completes, the connector to the next one fills, and the next node lights.",
            CALM
            + STEP_LOOP
            + 'const nodes = [...document.querySelectorAll(".node")];\nconst wires = [...document.querySelectorAll(".wire")];\nconst play = () => {\n  reset();\n  nodes.forEach((item) => item.classList.remove("active", "done"));\n  wires.forEach((wire) => wire.classList.remove("on"));\n  nodes.forEach((item, index) => {\n    later(200 + index * 1100, () => item.classList.add("active"));\n    later(200 + index * 1100 + 700, () => { item.classList.remove("active"); item.classList.add("done"); wires[index]?.classList.add("on"); });\n  });\n};\ndocument.querySelector(".replay").addEventListener("click", play);\nplay();\n',
            replay=True,
        ),
        ai(
            "Agent tool-call animation",
            '<div class="call"><header><i class="state"></i><code>search_docs</code><span class="took"></span></header><pre class="args"></pre><pre class="result" hidden></pre></div>',
            ".call { width: 320px; overflow: hidden; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); font-size: 13px; }\n.call header { display: flex; align-items: center; gap: 10px; padding: 10px 14px; }\n.call code { font-family: var(--mono); font-weight: 600; }\n.took { margin-left: auto; color: var(--muted); font-size: 12px; }\n.state { width: 14px; height: 14px; border: 2px solid var(--surface-2); border-top-color: var(--accent); border-radius: 50%; animation: turn .7s linear infinite; }\n.call.done .state { border-color: var(--success); background: var(--success); animation: none; }\n.call pre { margin: 0; padding: 10px 14px; border-top: 1px solid var(--border); font: 12px var(--mono); white-space: pre-wrap; min-height: 1.5em; }\n.result { color: var(--success); animation: open .35s var(--ease); }\n@keyframes turn { to { rotate: 360deg; } }\n@keyframes open { from { opacity: 0; translate: 0 -6px; } }\n",
            "A tool call plays out in three beats: its arguments are typed in, a spinner runs while it executes, and the result drops open below.",
            CALM
            + STEP_LOOP
            + """\
const call = document.querySelector(".call");
const args = call.querySelector(".args"), result = call.querySelector(".result"), took = call.querySelector(".took");
const ARGS = '{ "query": "refund policy", "top_k": 3 }';
const play = () => {
  reset();
  call.classList.remove("done"); result.hidden = true; args.textContent = ""; took.textContent = "running";
  [...ARGS].forEach((char, index) => later(200 + index * 22, () => { args.textContent = ARGS.slice(0, index + 1); }));
  later(200 + ARGS.length * 22 + 900, () => { call.classList.add("done"); took.textContent = "0.9s"; result.textContent = "3 passages found"; result.hidden = false; });
};
document.querySelector(".replay").addEventListener("click", play);
play();
""",
            replay=True,
        ),
        ai(
            "Tool execution pulse",
            '<i class="gear" aria-hidden="true">⚙</i><span>Running <code>run_tests</code></span>',
            '.fx { display: flex; gap: 12px; padding: 12px 18px; overflow: hidden; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.fx code { font-family: var(--mono); color: var(--accent); }\n.gear { font-style: normal; font-size: 18px; animation: turn 2s linear infinite; }\n.fx::after { content: ""; position: absolute; left: 0; bottom: 0; width: 40%; height: 2px; background: linear-gradient(90deg, transparent, var(--accent), transparent); animation: scan 1.4s ease-in-out infinite; }\n@keyframes turn { to { rotate: 360deg; } }\n@keyframes scan { from { translate: -100% 0; } to { translate: 250% 0; } }\n',
            "A tool in the middle of running: its gear turns and a light scans back and forth along the bottom edge of the chip.",
            label="Running run_tests",
        ),
        ai(
            "Tool completion burst",
            '<button class="chip"><i class="state" aria-hidden="true">✓</i><span>Tests passed</span></button>',
            ".stage { overflow: hidden; }\n.chip { display: flex; align-items: center; gap: 10px; padding: 12px 18px; border: 1px solid var(--success); border-radius: 14px; background: color-mix(in srgb, var(--success) 12%, var(--surface)); font-weight: 600; }\n.state { display: grid; place-items: center; width: 20px; height: 20px; border-radius: 50%; background: var(--success); color: #06281a; font-style: normal; font-size: 12px; }\n.chip.hit { animation: land .45s var(--ease); }\n@keyframes land { 30% { scale: 1.1; } }\n.bit { position: absolute; width: 6px; height: 6px; margin: -3px; border-radius: 50%; background: var(--tint); animation: fly .8s cubic-bezier(.15, .7, .3, 1) forwards; pointer-events: none; }\n@keyframes fly { to { translate: var(--dx) var(--dy); scale: 0; opacity: 0; } }\n",
            "The moment a tool finishes: the chip bumps and throws off a ring of sparks. Click to replay.",
            BURST_JS
            + 'const stage = document.querySelector(".stage");\nconst chip = stage.querySelector(".chip");\nconst TINTS = ["#34d399", "#22d3ee", "#ffffff"];\nconst finish = () => {\n  chip.classList.remove("hit"); void chip.offsetWidth; chip.classList.add("hit");\n  const box = chip.getBoundingClientRect(), frame = stage.getBoundingClientRect();\n  burst(stage, box.left - frame.left + box.width / 2, box.top - frame.top + box.height / 2, 18, (piece, i, count) => {\n    const angle = (i / count) * Math.PI * 2, reach = 70 + Math.random() * 40;\n    piece.style.setProperty("--dx", `${Math.cos(angle) * reach * 1.4}px`);\n    piece.style.setProperty("--dy", `${Math.sin(angle) * reach * 0.7}px`);\n    piece.style.setProperty("--tint", TINTS[i % TINTS.length]);\n  });\n};\nchip.addEventListener("click", finish);\nfinish();\n',
        ),
        ai(
            "Retrieval animation",
            '<div class="shelf">'
            + "".join(f'<i class="doc" style="--i: {i}"></i>' for i in range(8))
            + '</div><div class="slot">Context</div>',
            ".fx { gap: 26px; }\n.shelf { display: grid; grid-template-columns: repeat(8, 30px); gap: 8px; }\n.doc { height: 40px; border: 1px solid var(--border); border-radius: 5px; background: repeating-linear-gradient(var(--surface-2) 0 3px, transparent 3px 7px) 5px 6px / 18px 26px no-repeat, var(--surface); }\n.slot { display: grid; place-items: center; width: 180px; height: 46px; border: 1px dashed var(--border); border-radius: 12px; color: var(--muted); font-size: 13px; }\n"
            "/* Every document is scanned in turn; the matching ones are then lifted out and dropped into the context. */\n"
            ".go .doc { animation: scan .35s ease-in-out both; animation-delay: calc(var(--i) * .09s); }\n.go .doc.match { animation: scan .35s ease-in-out both, fetch .8s var(--ease) forwards; animation-delay: calc(var(--i) * .09s), calc(1s + var(--order) * .2s); }\n.go .slot { animation: fill .4s 2s both; }\n"
            "@keyframes scan { 50% { border-color: var(--accent); translate: 0 -4px; } }\n@keyframes fetch { 30% { border-color: var(--primary); box-shadow: 0 0 12px var(--primary); translate: 0 -10px; } 100% { border-color: var(--primary); translate: var(--tx) 78px; scale: .7; opacity: 0; } }\n@keyframes fill { to { border-style: solid; border-color: var(--primary); color: var(--fg); background: color-mix(in srgb, var(--primary) 14%, transparent); } }\n",
            "Retrieval made visible: a ripple scans every document, the relevant few light up, and they fly down into the context slot.",
            'const docs = [...document.querySelectorAll(".doc")];\n[1, 4, 6].forEach((index, order) => {\n  const doc = docs[index];\n  doc.classList.add("match");\n  doc.style.setProperty("--order", order);\n  doc.style.setProperty("--tx", `${(3.5 - index) * 38}px`);  // toward the centre, where the slot is\n});\n'
            + RESTART,
            replay=True,
        ),
        ai(
            "Vector search visualization",
            '<svg class="graph" viewBox="0 0 380 200" role="img" aria-label="Points in a vector space; the five nearest to the query are highlighted"></svg>',
            GRAPH
            + ".pt { fill: var(--muted); opacity: .5; transition: all .3s; }\n.pt.near { fill: var(--accent); opacity: 1; r: 5; filter: drop-shadow(0 0 5px var(--accent)); }\n.query { fill: var(--primary); }\n.reach { fill: rgb(124 92 255 / .08); stroke: var(--primary); stroke-dasharray: 4 4; }\n.link { stroke: var(--accent); stroke-width: 1; opacity: .6; }\n.graph { cursor: crosshair; }\n",
            "Documents as points in space, and a query as one more point: the search radius grows until it has caught the five nearest. Click anywhere to ask from there.",
            CALM
            + NS
            + """\
const svg = document.querySelector(".graph");
let seed = 11;
const rand = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const points = Array.from({ length: 70 }, () => ({ x: 14 + rand() * 352, y: 12 + rand() * 176 }));
const reach = make("circle", { class: "reach", r: 0 }, svg);
const links = make("g", {}, svg);
points.forEach((point) => { point.dot = make("circle", { cx: point.x, cy: point.y, r: 3, class: "pt" }, svg); });
const query = make("circle", { class: "query", r: 6 }, svg);
const K = 5;
let frame;
const search = (qx, qy) => {
  cancelAnimationFrame(frame);
  query.setAttribute("cx", qx); query.setAttribute("cy", qy);
  reach.setAttribute("cx", qx); reach.setAttribute("cy", qy);
  links.replaceChildren();
  const ranked = points.map((point) => ({ point, distance: Math.hypot(point.x - qx, point.y - qy) })).sort((a, b) => a.distance - b.distance);
  ranked.forEach(({ point }) => point.dot.classList.remove("near"));
  const limit = ranked[K - 1].distance + 4;
  let radius = 0;
  // The circle grows; each point is marked the moment the circle reaches it.
  const grow = () => {
    radius = calm ? limit : Math.min(limit, radius + 1.6);
    reach.setAttribute("r", radius);
    ranked.slice(0, K).forEach(({ point, distance }) => {
      if (distance > radius || point.dot.classList.contains("near")) return;
      point.dot.classList.add("near");
      make("line", { x1: qx, y1: qy, x2: point.x, y2: point.y, class: "link" }, links);
    });
    if (radius < limit) frame = requestAnimationFrame(grow);
  };
  grow();
};
svg.addEventListener("click", (event) => {
  const box = svg.getBoundingClientRect();
  search(((event.clientX - box.left) / box.width) * 380, ((event.clientY - box.top) / box.height) * 200);
});
search(190, 100);
""",
        ),
        ai(
            "Embedding particle flow",
            '<span class="text">“refund policy”</span><canvas width="200" height="120" aria-hidden="true"></canvas><span class="vec">[0.12, −0.48, 0.91, …]</span>',
            ".fx { display: flex; gap: 6px; font-size: 13px; }\n.text { font-weight: 600; }\n.vec { font-family: var(--mono); color: var(--accent); }\ncanvas { width: 200px; height: 120px; }\n",
            "Text becomes a vector: particles leave the words scattered, and are drawn together into ordered streams as they cross to the numbers.",
            CALM
            + """\
const canvas = document.querySelector("canvas");
const context = canvas.getContext("2d");
const W = canvas.width, H = canvas.height, LANES = 5;
const spawn = () => ({ x: 0, y: H / 2 + (Math.random() - 0.5) * 20, wobble: Math.random() * Math.PI * 2, lane: Math.floor(Math.random() * LANES), speed: 0.8 + Math.random() * 0.9 });
const particles = Array.from({ length: 70 }, () => Object.assign(spawn(), { x: Math.random() * W }));
const draw = () => {
  context.clearRect(0, 0, W, H);
  for (const particle of particles) {
    particle.x += particle.speed;
    if (particle.x > W) Object.assign(particle, spawn());
    const progress = particle.x / W;
    // Early on a particle wanders widely; further along it is pulled onto its lane.
    const scatter = Math.sin(particle.wobble + particle.x / 14) * 46 * (1 - progress) ** 2;
    const lane = H / 2 + (particle.lane - (LANES - 1) / 2) * 14;
    const py = (H / 2 + scatter) * (1 - progress) + lane * progress;
    context.fillStyle = `hsl(${255 - progress * 70} 90% 68% / ${0.35 + progress * 0.65})`;
    context.beginPath(); context.arc(particle.x, py, 1.8, 0, Math.PI * 2); context.fill();
  }
  if (!calm) requestAnimationFrame(draw);
};
draw();
""",
        ),
        ai(
            "Knowledge graph pulse",
            '<svg class="graph" viewBox="0 0 380 200" aria-hidden="true"></svg>',
            GRAPH
            + ".edge { stroke: var(--border); stroke-width: 1.5; transition: stroke .6s; }\n.edge.hot { stroke: var(--accent); transition: none; }\n.ent circle { fill: var(--surface-2); stroke: var(--border); stroke-width: 1.5; transition: all .8s; }\n.ent.hot circle { fill: color-mix(in srgb, var(--accent) 40%, var(--surface)); stroke: var(--accent); filter: drop-shadow(0 0 8px var(--accent)); transition: none; }\n.ent text { font-size: 10px; }\n",
            "Activation spreads outward through the graph from one entity: its neighbours light a moment later, then theirs, each fading as the wave moves on.",
            CALM
            + NS
            + """\
const svg = document.querySelector(".graph");
const ENTITIES = [["Refund", 190, 100], ["Order", 100, 50], ["Policy", 280, 50], ["Customer", 60, 140], ["Invoice", 150, 170], ["Legal", 330, 130], ["Region", 250, 165]];
const EDGES = [[0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [0, 6], [5, 6], [3, 4]];
const lines = EDGES.map(([a, b]) => make("line", { x1: ENTITIES[a][1], y1: ENTITIES[a][2], x2: ENTITIES[b][1], y2: ENTITIES[b][2], class: "edge" }, svg));
const groups = ENTITIES.map(([label, x, y]) => {
  const group = make("g", { class: "ent", transform: `translate(${x} ${y})` }, svg);
  make("circle", { r: 20 }, group);
  make("text", { y: 3 }, group).textContent = label;
  return group;
});
const flash = (element) => { element.classList.add("hot"); setTimeout(() => element.classList.remove("hot"), 260); };
// Breadth-first: every hop outward from the source is one step later.
const pulse = (source) => {
  const seen = new Set([source]);
  let frontier = [source], hop = 0;
  while (frontier.length) {
    const wave = frontier, next = [];
    setTimeout(() => wave.forEach((index) => flash(groups[index])), hop * 320);
    for (const index of wave) EDGES.forEach(([a, b], edge) => {
      const other = a === index ? b : b === index ? a : -1;
      if (other < 0 || seen.has(other)) return;
      seen.add(other); next.push(other);
      setTimeout(() => flash(lines[edge]), hop * 320 + 160);
    });
    frontier = next; hop += 1;
  }
};
if (calm) groups[0].classList.add("hot"); else { pulse(0); setInterval(() => pulse(Math.floor(Math.random() * ENTITIES.length)), 2200); }
""",
        ),
        ai(
            "Context loading animation",
            '<div class="meter"><div class="bar"><i class="seg s"></i><i class="seg h"></i><i class="seg d"></i><i class="seg q"></i></div><ul><li class="s">System</li><li class="h">History</li><li class="d">Documents</li><li class="q">Question</li></ul><small class="count"></small></div>',
            '.meter { display: grid; gap: 10px; width: 340px; }\n.bar { display: flex; height: 14px; overflow: hidden; border-radius: 99px; background: var(--surface-2); }\n.seg { width: 0; transition: width .6s var(--ease); }\n.s { --c: #7c5cff; } .h { --c: #22d3ee; } .d { --c: #f472b6; } .q { --c: #fbbf24; }\n.seg { background: var(--c); }\n.meter ul { display: flex; gap: 14px; margin: 0; padding: 0; list-style: none; font-size: 12px; }\n.meter li { display: flex; align-items: center; gap: 6px; opacity: .35; transition: opacity .3s; }\n.meter li.in { opacity: 1; }\n.meter li::before { content: ""; width: 8px; height: 8px; border-radius: 2px; background: var(--c); }\n.count { color: var(--muted); font-variant-numeric: tabular-nums; }\n',
            "The context window fills piece by piece — system prompt, history, documents, question — each a coloured segment, with the token count rising.",
            CALM
            + STEP_LOOP
            + """\
const PARTS = [["s", 800], ["h", 2400], ["d", 5200], ["q", 300]];
const LIMIT = 12000;
const count = document.querySelector(".count");
const play = () => {
  reset();
  let used = 0;
  PARTS.forEach(([key]) => { document.querySelector(`.seg.${key}`).style.width = "0"; document.querySelector(`li.${key}`).classList.remove("in"); });
  count.textContent = `0 / ${LIMIT.toLocaleString("en-US")} tokens`;
  PARTS.forEach(([key, tokens], index) => later(300 + index * 700, () => {
    used += tokens;
    document.querySelector(`.seg.${key}`).style.width = `${(tokens / LIMIT) * 100}%`;
    document.querySelector(`li.${key}`).classList.add("in");
    count.textContent = `${used.toLocaleString("en-US")} / ${LIMIT.toLocaleString("en-US")} tokens`;
  }));
};
document.querySelector(".replay").addEventListener("click", play);
play();
""",
            replay=True,
        ),
        ai(
            "Context expansion",
            '<button class="ctx" aria-expanded="false"><span class="pill">3 sources</span><span class="more"><span>handbook.pdf · policy.md · faq.html</span></span></button>',
            ".ctx { display: flex; align-items: center; gap: 0; padding: 6px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface); color: inherit; transition: border-radius .4s var(--ease), gap .4s var(--ease); }\n.pill { padding: 5px 12px; border-radius: 99px; background: var(--primary); color: #fff; font-weight: 600; font-size: 13px; white-space: nowrap; }\n.more { display: grid; grid-template-columns: 0fr; transition: grid-template-columns .45s var(--ease); }\n"
            "/* The hidden part is one grid column animated from 0fr to 1fr, so its natural width is reached without measuring. */\n"
            '.more > span { min-width: 0; overflow: hidden; white-space: nowrap; font-size: 13px; color: var(--muted); opacity: 0; transition: opacity .3s; }\n.ctx[aria-expanded="true"] { gap: 10px; }\n.ctx[aria-expanded="true"] .more { grid-template-columns: 1fr; padding-right: 10px; }\n.ctx[aria-expanded="true"] .more > span { opacity: 1; transition-delay: .15s; }\n',
            "A compact 'sources' pill widens in place to list what the answer drew on, and closes back to the pill. Click to toggle.",
            'const chip = document.querySelector(".ctx");\nconst toggle = () => chip.setAttribute("aria-expanded", chip.getAttribute("aria-expanded") !== "true");\nchip.addEventListener("click", toggle);\nsetTimeout(toggle, 500);\n',
        ),
        ai(
            "Prompt enhancement animation",
            '<p class="prompt"></p>',
            ".prompt { width: 340px; min-height: 96px; margin: 0; padding: 14px 16px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); line-height: 1.6; }\n.prompt ins { text-decoration: none; border-radius: 4px; animation: added 1.6s ease-out both; }\n@keyframes added { 0% { background: rgb(124 92 255 / .6); color: #fff; opacity: 0; filter: blur(4px); } 25% { opacity: 1; filter: none; } 100% { background: rgb(124 92 255 / 0); } }\n",
            "A short prompt is improved where it stands: the added detail is typed into place between the original words, highlighted, and the highlight fades.",
            CALM
            + STEP_LOOP
            + """\
const prompt = document.querySelector(".prompt");
// The original words stay; the additions are inserted between them, one phrase at a time.
const PARTS = [["Write a summary", false], [" of the attached report", true], [" for executives", true], [", in five bullet points", true], [", citing page numbers", true], [".", false]];
const play = () => {
  reset();
  prompt.replaceChildren(...PARTS.filter(([, added]) => !added).map(([text]) => document.createTextNode(text)));
  let anchor = prompt.firstChild;
  PARTS.filter(([, added]) => added).forEach(([text], index) => later(700 + index * 650, () => {
    const piece = Object.assign(document.createElement("ins"), { textContent: text });
    anchor.after(piece);
    anchor = piece;
  }));
};
document.querySelector(".replay").addEventListener("click", play);
play();
""",
            replay=True,
        ),
        ai(
            "Prompt transformation",
            '<div class="was">make this sound better</div><i class="arrow" aria-hidden="true">↓</i><div class="now">Rewrite the paragraph below in a confident, plain tone. Keep it under 80 words.</div>',
            ".fx { gap: 8px; width: 340px; }\n.was, .now { width: 100%; padding: 12px 14px; border-radius: 12px; font-size: 13px; line-height: 1.5; }\n.was { border: 1px dashed var(--border); color: var(--muted); }\n.now { border: 1px solid var(--primary); background: color-mix(in srgb, var(--primary) 12%, var(--surface)); }\n.arrow { font-style: normal; color: var(--primary); }\n"
            ".go .was { animation: fade-back 1.8s both; }\n.go .arrow { animation: drop .5s .5s var(--ease) both; }\n.go .now { animation: form .8s .8s var(--ease) both; }\n"
            "@keyframes fade-back { 0%, 30% { opacity: 1; scale: 1; } 100% { opacity: .5; scale: .96; } }\n@keyframes drop { from { opacity: 0; translate: 0 -10px; } }\n@keyframes form { from { opacity: 0; filter: blur(8px); scale: .96; letter-spacing: .08em; } }\n",
            "Before and after: the rough prompt recedes, and the structured version condenses out of a blur beneath it.",
            RESTART,
            replay=True,
        ),
        ai(
            "Response regeneration",
            '<p class="text" aria-live="polite"></p><button class="regen"><i aria-hidden="true">↻</i> Regenerate</button>',
            BUBBLE.replace(".bubble", ".fx")
            + ".fx { display: grid; gap: 12px; place-items: start; }\n.text { min-height: 4.8em; transition: opacity .25s, filter .25s; }\n.fx.busy .text { opacity: .25; filter: blur(3px); }\n.regen { display: flex; align-items: center; gap: 6px; padding: 5px 12px; border: 1px solid var(--border); border-radius: 99px; background: none; font-size: 12px; }\n.regen i { display: inline-block; font-style: normal; }\n.fx.busy .regen i { animation: turn .7s linear infinite; }\n@keyframes turn { to { rotate: 360deg; } }\n",
            "Asking again: the old answer blurs and fades back while the button's icon spins, then the new answer streams in over it.",
            CALM
            + """\
const bubble = document.querySelector(".fx");
const text = bubble.querySelector(".text");
const VERSIONS = ["Retrieval adds your documents to the prompt, so answers come from them instead of from memory.", "The model looks up relevant passages first, then writes its answer using only what it found.", "Think of it as an open-book exam: the model reads the right pages before it replies."];
let version = 0, timer;
const stream = (answer) => {
  const words = answer.split(" ");
  let shown = 0;
  text.textContent = "";
  timer = setInterval(() => { shown += 1; text.textContent = words.slice(0, shown).join(" "); if (shown === words.length) clearInterval(timer); }, calm ? 0 : 55);
};
const regenerate = () => {
  clearInterval(timer);
  bubble.classList.add("busy");
  version = (version + 1) % VERSIONS.length;
  setTimeout(() => { bubble.classList.remove("busy"); stream(VERSIONS[version]); }, calm ? 0 : 700);
};
bubble.querySelector(".regen").addEventListener("click", regenerate);
stream(VERSIONS[0]);
""",
        ),
        ai(
            "Conversation branching animation",
            '<svg class="graph" viewBox="0 0 380 190" aria-hidden="true"><path class="wire trunk" d="M190 26 V78"/><path class="wire branch" pathLength="1" d="M190 78 C190 110, 100 100, 100 140"/><path class="wire branch" pathLength="1" d="M190 78 C190 110, 280 100, 280 140"/>'
            + node(190, 26, "Question")
            + node(190, 78, "Answer")
            + node(100, 150, "Shorter", "leaf")
            + node(280, 150, "More formal", "leaf")
            + "</svg>",
            GRAPH
            + NODE_CSS
            + ".branch { stroke: var(--primary); stroke-dasharray: 1; stroke-dashoffset: 1; }\n.leaf { opacity: 0; }\n.go .branch { animation: grow .6s .3s var(--ease) forwards; }\n.go .leaf { animation: bud .4s .8s var(--ease) both; }\n.go .leaf:last-of-type { animation-delay: .95s; }\n.go .branch:nth-of-type(3) { animation-delay: .45s; }\n@keyframes grow { to { stroke-dashoffset: 0; } }\n@keyframes bud { from { opacity: 0; scale: .6; } to { opacity: 1; scale: 1; } }\n.leaf { transform-box: fill-box; transform-origin: center; }\n.leaf rect { stroke: var(--primary); }\n",
            "One conversation becomes two: lines grow out of an answer in different directions and an alternative reply forms at the end of each.",
            RESTART,
            replay=True,
        ),
    ),
)
