"""Recipes 1-6: effects combined on one component.

Each recipe layers four entries from the lists above. The comments in the CSS
name which declaration belongs to which effect, so one can be removed without
disturbing the others.
"""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import BURST_JS, REPLAY_BTN, REPLAY_CSS, STAGE, pointer_js

CALM = 'const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\n'

CARD = Item(
    "Card: hover lift + 3D tilt + cursor spotlight + dynamic shadow",
    '<div class="stage"><article class="card" tabindex="0"><div class="art"></div><div class="body"><h3>Aurora plan</h3><p>Everything a small team needs.</p></div></article></div>',
    STAGE
    + """\
.stage { perspective: 900px; }
.card { --px: .5; --py: .5; --lift: 0; position: relative; width: 240px; overflow: hidden; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); outline: none; cursor: pointer;
  /* 3D tilt: lean toward the pointer on both axes. Hover lift: come forward along z. */
  transform: translateZ(calc(var(--lift) * 30px)) rotateX(calc((.5 - var(--py)) * 18deg * var(--lift))) rotateY(calc((var(--px) - .5) * 18deg * var(--lift)));
  /* Dynamic shadow: thrown away from the pointer, longer and softer as the card lifts. */
  box-shadow: calc((.5 - var(--px)) * 36px * var(--lift)) calc((.5 - var(--py)) * 36px * var(--lift) + 8px + var(--lift) * 14px) calc(18px + var(--lift) * 30px) rgb(0 0 0 / calc(.3 + var(--lift) * .25));
  transition: transform .18s ease-out, box-shadow .18s ease-out; }
.card:hover, .card:focus-visible { --lift: 1; }
/* Cursor spotlight: a pool of light on the surface, under the pointer. */
.card::after { content: ""; position: absolute; inset: 0; background: radial-gradient(180px circle at calc(var(--px) * 100%) calc(var(--py) * 100%), rgb(255 255 255 / .2), transparent 70%); opacity: var(--lift); transition: opacity .3s; pointer-events: none; }
.art { height: 96px; background: radial-gradient(circle at 30% 30%, #f472b6, transparent 45%), radial-gradient(circle at 75% 65%, #22d3ee, transparent 50%), linear-gradient(135deg, #312e81, #7c5cff); }
.body { padding: 14px 16px 16px; }
.card h3 { margin: 0 0 4px; font-size: 15px; }
.card p { margin: 0; color: var(--muted); font-size: 13px; }
@media (prefers-reduced-motion: reduce) { .card { transform: none; } }
""",
    pointer_js(".card", ".card"),
    "All four effects read the same two numbers, the pointer's position over the card, and one switch for hover. That shared input is why they feel like a single response.",
)

AI_RESPONSE = Item(
    "AI response: streaming text + subtle shimmer + citation glow + source reveal",
    '<div class="stage"><article class="answer" aria-live="polite" aria-busy="true"><div class="waiting" aria-hidden="true"><i style="width: 90%"></i><i style="width: 100%"></i><i style="width: 60%"></i></div><p class="text"></p>'
    '<ul class="sources" aria-label="Sources"><li><a href="#">1 · handbook.pdf</a></li><li><a href="#">2 · policy.md</a></li></ul></article>'
    + REPLAY_BTN
    + "</div>",
    STAGE
    + REPLAY_CSS
    + """\
.answer { position: relative; width: 360px; min-height: 150px; padding: 16px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); line-height: 1.6; }
.text { margin: 0; }
/* Subtle shimmer: placeholder lines while nothing has arrived yet. */
.waiting { display: grid; gap: 10px; }
.waiting i { height: 11px; border-radius: 6px; background: linear-gradient(100deg, var(--surface-2) 30%, color-mix(in srgb, var(--primary) 45%, var(--surface-2)) 50%, var(--surface-2) 70%) fixed 0 0 / 250% 100%; animation: sweep 1.6s linear infinite; }
.answer:not([data-phase="waiting"]) .waiting { display: none; }
/* Streaming text: each chunk fades in; a caret marks the end while the stream is open. */
.text span { animation: appear .35s ease-out both; }
.answer[data-phase="streaming"] .text::after { content: ""; display: inline-block; width: 2px; height: 1.1em; margin-left: 2px; vertical-align: text-bottom; background: var(--accent); animation: blink 1s steps(2) infinite; }
/* Citation glow: a marker flares once as it lands. */
.cite { display: inline-grid; place-items: center; width: 17px; height: 17px; margin-left: 3px; border-radius: 50%; background: var(--surface-2); color: var(--accent); font-size: 10px; font-weight: 700; vertical-align: super; animation: flare 1.4s ease-out both; }
/* Source reveal: the list is held back until the answer is complete, then rises in, one item after another. */
.sources { display: flex; gap: 8px; margin: 12px 0 0; padding: 0; list-style: none; }
.sources li { opacity: 0; translate: 0 8px; transition: all .4s var(--ease); }
.sources li:nth-child(2) { transition-delay: .12s; }
.answer[data-phase="done"] .sources li { opacity: 1; translate: 0 0; }
.sources a { display: block; padding: 4px 10px; border: 1px solid var(--border); border-radius: 99px; color: inherit; font-size: 12px; text-decoration: none; }
@keyframes sweep { from { background-position: 150% 0; } to { background-position: -100% 0; } }
@keyframes appear { from { opacity: 0; filter: blur(3px); } }
@keyframes blink { 50% { opacity: 0; } }
@keyframes flare { 0% { background: var(--accent); color: #06202a; box-shadow: 0 0 0 0 rgb(34 211 238 / .9); } 100% { box-shadow: 0 0 0 10px rgb(34 211 238 / 0); } }
""",
    CALM
    + """\
const answer = document.querySelector(".answer");
const text = answer.querySelector(".text");
// The reply as a model would send it: text chunks, with a citation number wherever a source is used.
const CHUNKS = ["Retrieval ", "adds ", "your own ", "documents ", "to the ", "prompt", 1, ", so the ", "model ", "answers ", "from them", 2, " instead ", "of from ", "memory."];
let timers = [];
const phase = (name) => { answer.dataset.phase = name; answer.setAttribute("aria-busy", name !== "done"); };
const write = (chunk) => {
  const piece = document.createElement("span");
  if (typeof chunk === "number") { piece.className = "cite"; piece.textContent = chunk; piece.setAttribute("aria-label", `Source ${chunk}`); } else piece.textContent = chunk;
  text.append(piece);
};
const play = () => {
  timers.forEach(clearTimeout); timers = [];
  text.replaceChildren();
  phase("waiting");
  const wait = calm ? 0 : 1100, gap = calm ? 0 : 90;
  timers.push(setTimeout(() => phase("streaming"), wait));
  CHUNKS.forEach((chunk, index) => timers.push(setTimeout(() => write(chunk), wait + index * gap)));
  timers.push(setTimeout(() => phase("done"), wait + CHUNKS.length * gap + 150));
};
document.querySelector(".replay").addEventListener("click", play);
play();
""",
    "One state attribute drives the sequence: waiting shows the shimmer, streaming shows text and caret, done reveals the sources. Each effect belongs to exactly one phase, so they never compete.",
)

CTA = Item(
    "Primary CTA: magnetic pull + gradient shift + press compression + success burst",
    '<div class="stage"><button class="cta"><span class="label">Start free trial</span></button></div>',
    STAGE
    + """\
.stage { overflow: hidden; }
.cta { --mx: 0px; --my: 0px; position: relative; padding: 15px 30px; border: 0; border-radius: 14px; color: #fff; font-size: 16px; font-weight: 700;
  /* Gradient shift: an oversized gradient that slides on hover. */
  background: linear-gradient(110deg, #7c5cff, #22d3ee, #f472b6, #7c5cff) 0 0 / 300% 100%;
  /* Magnetic pull: the button is drawn toward the pointer by the offsets the script supplies. */
  translate: var(--mx) var(--my);
  box-shadow: 0 10px 30px rgb(124 92 255 / .45);
  transition: translate .2s ease-out, scale .12s ease-out, background-position .8s var(--ease), box-shadow .2s; }
.cta:hover, .cta:focus-visible { background-position: 100% 0; box-shadow: 0 14px 40px rgb(34 211 238 / .45); }
/* Press compression: squashed while held. */
.cta:active { scale: .94; box-shadow: 0 4px 12px rgb(124 92 255 / .4); }
.cta .label { display: inline-block; transition: translate .2s ease-out; translate: calc(var(--mx) * .35) calc(var(--my) * .35); }
.cta.done { background: var(--success); color: #06281a; }
/* Success burst: pieces thrown out from the button on completion. */
.bit { position: absolute; width: 8px; height: 8px; margin: -4px; border-radius: 2px; background: var(--tint); animation: fly .9s cubic-bezier(.15, .7, .3, 1) forwards; pointer-events: none; }
@keyframes fly { to { translate: var(--dx) var(--dy); rotate: var(--spin); scale: 0; opacity: 0; } }
""",
    CALM
    + BURST_JS
    + """\
const stage = document.querySelector(".stage");
const button = stage.querySelector(".cta");
const label = button.querySelector(".label");
const RANGE = 90, PULL = 0.35;
// Magnetic pull: within RANGE of the centre, the button moves a fraction of the way toward the pointer.
stage.addEventListener("pointermove", (event) => {
  if (calm) return;
  const box = button.getBoundingClientRect();
  // Measured from where the button rests, not where it has been pulled to.
  const cx = box.left + box.width / 2 - parseFloat(button.style.getPropertyValue("--mx") || 0);
  const cy = box.top + box.height / 2 - parseFloat(button.style.getPropertyValue("--my") || 0);
  const dx = event.clientX - cx, dy = event.clientY - cy;
  const near = Math.hypot(dx, dy) < RANGE + box.width / 2;
  button.style.setProperty("--mx", `${near ? dx * PULL : 0}px`);
  button.style.setProperty("--my", `${near ? dy * PULL : 0}px`);
});
stage.addEventListener("pointerleave", () => { button.style.setProperty("--mx", "0px"); button.style.setProperty("--my", "0px"); });
const TINTS = ["#7c5cff", "#22d3ee", "#f472b6", "#fbbf24", "#34d399"];
button.addEventListener("click", () => {
  if (button.classList.contains("done")) return;
  button.classList.add("done");
  label.textContent = "You're in ✓";
  const box = button.getBoundingClientRect(), frame = stage.getBoundingClientRect();
  burst(stage, box.left - frame.left + box.width / 2, box.top - frame.top + box.height / 2, 26, (piece, i, count) => {
    const angle = (i / count) * Math.PI * 2, reach = 80 + Math.random() * 70;
    piece.style.setProperty("--dx", `${Math.cos(angle) * reach}px`);
    piece.style.setProperty("--dy", `${Math.sin(angle) * reach}px`);
    piece.style.setProperty("--spin", `${(Math.random() - 0.5) * 540}deg`);
    piece.style.setProperty("--tint", TINTS[i % TINTS.length]);
  });
  setTimeout(() => { button.classList.remove("done"); label.textContent = "Start free trial"; }, 2200);
});
""",
    "The four effects are spread over the life of one click: pull as the pointer approaches, shift on hover, compress on press, burst on success. Nothing overlaps, so the button never feels busy.",
)

DASHBOARD = Item(
    "Dashboard: bento layout + scroll reveal + metric count-up + chart draw animation",
    '<div class="board" tabindex="0"><p class="hint">Scroll down</p><div class="bento">'
    '<section class="tile wide"><small>Revenue</small><b data-to="48210" data-prefix="$">$0</b><svg class="line" viewBox="0 0 300 70" preserveAspectRatio="none" aria-hidden="true"><path pathLength="1" d="M0 58 L40 46 L80 50 L120 30 L160 36 L200 18 L240 22 L300 6"/></svg></section>'
    '<section class="tile"><small>Active users</small><b data-to="1284">0</b></section>'
    '<section class="tile"><small>Conversion</small><b data-to="4.8" data-suffix="%" data-decimals="1">0%</b></section>'
    '<section class="tile tall"><small>By plan</small><div class="bars" aria-hidden="true"><i style="--h: 45%"></i><i style="--h: 80%"></i><i style="--h: 60%"></i><i style="--h: 95%"></i></div></section>'
    '<section class="tile wide"><small>Churn</small><b data-to="1.9" data-suffix="%" data-decimals="1">0%</b></section>'
    '</div><p class="hint">End</p></div>',
    """\
.board { width: min(480px, 100%); height: 320px; overflow-y: auto; padding: 0 14px; border: 1px solid var(--border); border-radius: 20px; background: var(--bg); outline: none; }
.hint { display: grid; place-items: center; height: 120px; margin: 0; color: var(--muted); font-size: 13px; }
/* Bento layout: a three-column grid in which tiles span different numbers of cells. */
.bento { display: grid; grid-template-columns: repeat(3, 1fr); grid-auto-rows: 104px; gap: 12px; }
.wide { grid-column: span 2; }
.tall { grid-row: span 2; }
.tile { position: relative; display: grid; align-content: start; gap: 4px; padding: 14px; overflow: hidden; border: 1px solid var(--border); border-radius: 16px; background: var(--surface);
  /* Scroll reveal: hidden until the tile enters the scroller, then it rises in. */
  opacity: 0; translate: 0 24px; scale: .97; transition: opacity .6s var(--ease), translate .6s var(--ease), scale .6s var(--ease); }
.tile.seen { opacity: 1; translate: 0 0; scale: 1; }
.tile small { color: var(--muted); }
.tile b { font-size: 26px; font-weight: 800; font-variant-numeric: tabular-nums; }
/* Chart draw: the line and the bars are drawn only once their tile has been revealed. */
.line { position: absolute; left: 0; right: 0; bottom: 0; width: 100%; height: 46px; }
.line path { fill: none; stroke: var(--accent); stroke-width: 2.5; vector-effect: non-scaling-stroke; stroke-dasharray: 1; stroke-dashoffset: 1; transition: stroke-dashoffset 1.4s var(--ease) .3s; }
.seen .line path { stroke-dashoffset: 0; }
.bars { display: flex; align-items: end; gap: 8px; height: 150px; margin-top: 8px; }
.bars i { flex: 1; height: var(--h); border-radius: 6px 6px 2px 2px; background: var(--primary); transform-origin: 50% 100%; scale: 1 0; transition: scale .7s var(--ease); }
.bars i:nth-child(2) { transition-delay: .1s; } .bars i:nth-child(3) { transition-delay: .2s; } .bars i:nth-child(4) { transition-delay: .3s; }
.seen .bars i { scale: 1 1; }
@media (prefers-reduced-motion: reduce) { .tile { opacity: 1; translate: 0 0; scale: 1; transition: none; } }
""",
    CALM
    + """\
const board = document.querySelector(".board");
// Metric count-up: runs once, when the tile holding the figure is revealed.
const countUp = (figure) => {
  const to = Number(figure.dataset.to), decimals = Number(figure.dataset.decimals || 0);
  const show = (value) => { figure.textContent = `${figure.dataset.prefix || ""}${value.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}${figure.dataset.suffix || ""}`; };
  if (calm) { show(to); return; }
  const start = performance.now();
  const frame = (now) => {
    const t = Math.min(1, Math.max(0, (now - start) / 1200));
    show(to * (1 - Math.pow(1 - t, 3)));
    if (t < 1) requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
};
// One observer starts everything: reveal, count and chart all key off the same `seen` class.
const observer = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;
    entry.target.classList.add("seen");
    entry.target.querySelectorAll("b[data-to]").forEach(countUp);
    observer.unobserve(entry.target);  // once only: scrolling back does not replay it
  }
}, { root: board, threshold: 0.35 });
board.querySelectorAll(".tile").forEach((tile, index) => { tile.style.transitionDelay = `${(index % 3) * 70}ms`; observer.observe(tile); });
""",
    "Scroll is the single trigger. A tile entering the view is revealed, and that same moment starts its number counting and its chart drawing, so data is never animated off-screen where nobody sees it.",
)

WORKFLOW = Item(
    "AI agent workflow: node glow + connection pulse + tool execution animation + completion burst",
    '<div class="stage"><div class="flow" role="status" aria-label="Agent run"><svg viewBox="0 0 420 150" aria-hidden="true">'
    '<path class="wire" id="wire-0" d="M104 50 H158"/><path class="wire" id="wire-1" d="M262 50 H316"/>'
    '<path class="pulse" id="pulse-0" d="M104 50 H158"/><path class="pulse" id="pulse-1" d="M262 50 H316"/>'
    + "".join(
        f'<g class="node" id="node-{i}" transform="translate({54 + i * 158} 50)"><rect x="-50" y="-22" width="100" height="44" rx="12"/><text y="4">{label}</text></g>'
        for i, label in enumerate(("Plan", "Search", "Answer"))
    )
    + '</svg><div class="tool"><i class="state"></i><code></code><span class="took"></span></div></div>'
    + REPLAY_BTN
    + "</div>",
    STAGE
    + REPLAY_CSS
    + """\
.stage { overflow: hidden; }
.flow { position: relative; width: 420px; }
.flow svg { display: block; width: 100%; overflow: visible; }
.flow text { fill: var(--fg); font: 600 13px var(--font); text-anchor: middle; }
.node rect { fill: var(--surface); stroke: var(--border); stroke-width: 1.5; transition: all .3s; }
.node { opacity: .45; transition: opacity .3s; }
.node.active, .node.done { opacity: 1; }
/* Node glow: the running node breathes in the brand colour. */
.node.active rect { stroke: var(--primary); fill: color-mix(in srgb, var(--primary) 18%, var(--surface)); animation: aura 1.2s ease-in-out infinite alternate; }
.node.done rect { stroke: var(--success); }
.wire { fill: none; stroke: var(--border); stroke-width: 2; }
/* Connection pulse: a dash that crosses the connector once, when work is handed on. */
.pulse { fill: none; stroke: var(--accent); stroke-width: 3; stroke-linecap: round; stroke-dasharray: 16 60; stroke-dashoffset: 16; opacity: 0; filter: drop-shadow(0 0 5px var(--accent)); }
.pulse.go { animation: send .6s ease-in-out; }
/* Tool execution: a chip under the graph shows the call in progress, then its duration. */
.tool { display: flex; align-items: center; gap: 10px; width: 250px; margin: -30px auto 0; padding: 9px 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); font-size: 13px; opacity: 0; translate: 0 6px; transition: all .3s var(--ease); }
.tool.on { opacity: 1; translate: 0 0; }
.tool code { font-family: var(--mono); }
.took { margin-left: auto; color: var(--muted); font-size: 12px; }
.state { width: 13px; height: 13px; border: 2px solid var(--surface-2); border-top-color: var(--accent); border-radius: 50%; animation: turn .7s linear infinite; }
.tool.ok .state { border-color: var(--success); background: var(--success); animation: none; }
/* Completion burst: sparks from the last node when the whole run has finished. */
.bit { position: absolute; width: 6px; height: 6px; margin: -3px; border-radius: 50%; background: var(--tint); animation: fly .9s cubic-bezier(.15, .7, .3, 1) forwards; pointer-events: none; }
@keyframes aura { from { filter: drop-shadow(0 0 2px var(--primary)); } to { filter: drop-shadow(0 0 14px var(--primary)); } }
@keyframes send { 0% { opacity: 1; stroke-dashoffset: 16; } 100% { opacity: 1; stroke-dashoffset: -60; } }
@keyframes turn { to { rotate: 360deg; } }
@keyframes fly { to { translate: var(--dx) var(--dy); scale: 0; opacity: 0; } }
""",
    CALM
    + BURST_JS
    + """\
const flow = document.querySelector(".flow");
const nodes = [...flow.querySelectorAll(".node")];
const tool = flow.querySelector(".tool");
// The run, as the orchestrator would report it: each step is a node and the tool it calls.
const RUN = [{ tool: "make_plan", seconds: 0.6 }, { tool: "search_docs", seconds: 1.2 }, { tool: "write_answer", seconds: 0.9 }];
let timers = [];
const later = (ms, action) => timers.push(setTimeout(action, calm ? 0 : ms));
const start = (index) => {
  nodes[index].classList.add("active");
  tool.classList.remove("ok"); tool.classList.add("on");
  tool.querySelector("code").textContent = RUN[index].tool;
  tool.querySelector(".took").textContent = "running";
  flow.setAttribute("aria-label", `Agent run: ${nodes[index].textContent}, calling ${RUN[index].tool}`);
};
const finish = (index) => {
  nodes[index].classList.remove("active"); nodes[index].classList.add("done");
  tool.classList.add("ok");
  tool.querySelector(".took").textContent = `${RUN[index].seconds}s`;
  const pulse = flow.querySelector(`#pulse-${index}`);
  if (pulse) { pulse.classList.remove("go"); void pulse.getBoundingClientRect(); pulse.classList.add("go"); }
};
const celebrate = () => {
  flow.setAttribute("aria-label", "Agent run complete");
  const box = nodes.at(-1).getBoundingClientRect(), frame = flow.getBoundingClientRect();
  burst(flow, box.left - frame.left + box.width / 2, box.top - frame.top + box.height / 2, 20, (piece, i, count) => {
    const angle = (i / count) * Math.PI * 2, reach = 46 + Math.random() * 40;
    piece.style.setProperty("--dx", `${Math.cos(angle) * reach}px`);
    piece.style.setProperty("--dy", `${Math.sin(angle) * reach}px`);
    piece.style.setProperty("--tint", ["#34d399", "#22d3ee", "#ffffff"][i % 3]);
  });
};
const play = () => {
  timers.forEach(clearTimeout); timers = [];
  nodes.forEach((item) => item.classList.remove("active", "done"));
  tool.classList.remove("on", "ok");
  let at = 300;
  RUN.forEach((step, index) => {
    later(at, () => start(index));
    at += step.seconds * 1000 + 300;
    later(at, () => finish(index));
    at += 500;  // time for the pulse to cross to the next node
  });
  later(at - 300, celebrate);
};
document.querySelector(".replay").addEventListener("click", play);
play();
""",
    "Each effect answers a different question about the run: the glow says where it is, the pulse says control has moved, the tool chip says what is being done, and the burst says it is over.",
)

SIDEBAR = Item(
    "Glass sidebar: backdrop blur + translucent gradient + edge illumination + active-pill morph",
    '<div class="stage scene"><i class="blob a"></i><i class="blob b"></i><i class="blob c"></i><nav class="glass" aria-label="Main"><i class="pill" aria-hidden="true"></i>'
    + "".join(
        f'<a href="#"{' aria-current="page"' if index == 0 else ""}><i aria-hidden="true">{icon}</i>{label}</a>'
        for index, (icon, label) in enumerate(
            (("⌂", "Home"), ("◔", "Reports"), ("☰", "Projects"), ("✉", "Inbox"), ("⚙", "Settings"))
        )
    )
    + "</nav></div>",
    STAGE
    + """\
.scene { place-items: center start; padding-left: 26px; overflow: hidden; border-radius: 18px; background: #0b1020; }
.blob { position: absolute; border-radius: 50%; animation: drift 9s ease-in-out infinite alternate; }
.blob.a { left: -6%; top: -20%; width: 200px; height: 200px; background: #f472b6; }
.blob.b { left: 22%; bottom: -30%; width: 220px; height: 220px; background: #22d3ee; animation-delay: -3s; }
.blob.c { right: 8%; top: 12%; width: 150px; height: 150px; background: #7c5cff; animation-delay: -6s; }
@keyframes drift { to { translate: 30px 18px; } }
.glass { --px: .5; --py: .5; position: relative; display: grid; gap: 2px; width: 190px; padding: 10px; border-radius: 20px; border: 1px solid transparent; color: #fff;
  /* Backdrop blur: what is behind the panel is blurred and slightly intensified. */
  backdrop-filter: blur(18px) saturate(160%);
  /* Translucent gradient: a tint that is denser at the top than the bottom, in the padding box.
     Edge illumination: the border box holds a light that sits where the pointer is nearest. */
  background: linear-gradient(rgb(255 255 255 / .16), rgb(255 255 255 / .05)) padding-box,
    radial-gradient(160px circle at calc(var(--px) * 100%) calc(var(--py) * 100%), rgb(255 255 255 / .9), rgb(255 255 255 / .14) 70%) border-box;
  box-shadow: 0 20px 50px rgb(0 0 0 / .35), inset 0 1px 0 rgb(255 255 255 / .25); }
.glass a { position: relative; z-index: 1; display: flex; align-items: center; gap: 12px; height: 38px; padding: 0 12px; border-radius: 12px; color: rgb(255 255 255 / .75); font-weight: 600; font-size: 14px; text-decoration: none; transition: color .25s; }
.glass a i { width: 18px; text-align: center; font-style: normal; }
.glass a[aria-current="page"] { color: #fff; }
/* Active-pill morph: one pill for all items. The edge facing the direction of travel moves first, so it stretches and then contracts. */
.pill { position: absolute; left: 10px; right: 10px; top: var(--top, 10px); bottom: var(--bottom, 0px); border-radius: 12px; background: rgb(255 255 255 / .2); box-shadow: inset 0 1px 0 rgb(255 255 255 / .35); }
.glass[data-direction="down"] .pill { transition: bottom .25s var(--ease), top .25s var(--ease) .12s; }
.glass[data-direction="up"] .pill { transition: top .25s var(--ease), bottom .25s var(--ease) .12s; }
""",
    pointer_js(".stage", ".glass")
    + """\
const nav = target;
const items = [...nav.querySelectorAll("a")];
let current = 0;
const select = (index) => {
  const item = items[index];
  nav.dataset.direction = index >= current ? "down" : "up";
  nav.style.setProperty("--top", `${item.offsetTop}px`);
  nav.style.setProperty("--bottom", `${nav.clientHeight - item.offsetTop - item.offsetHeight}px`);
  items.forEach((other, i) => { if (i === index) other.setAttribute("aria-current", "page"); else other.removeAttribute("aria-current"); });
  current = index;
};
items.forEach((item, index) => item.addEventListener("click", (event) => { event.preventDefault(); select(index); }));
select(0);
""",
    "The first three effects are all one `background` declaration plus a backdrop-filter, layered by box: tint in the padding box, light in the border box. The pill is the only moving part.",
)

SECTION = Section(
    "recipes", "Effect Combinations", 1, (CARD, AI_RESPONSE, CTA, DASHBOARD, WORKFLOW, SIDEBAR)
)
