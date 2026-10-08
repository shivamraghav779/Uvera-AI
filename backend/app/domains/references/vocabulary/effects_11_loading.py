"""Effects 271-300: loading."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import REPLAY_BTN, REPLAY_CSS, STAGE

CALM = 'const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\n'
TURN = "@keyframes turn { to { rotate: 360deg; } }\n"


def load(
    name: str,
    inner: str,
    css: str,
    note: str,
    js: str = "",
    label: str = "Loading",
    replay: bool = False,
) -> Item:
    """A loader announced to assistive technology as a status, whatever it looks like."""
    html = f'<div class="stage"><div class="ld" role="status" aria-label="{label}">{inner}</div>{REPLAY_BTN if replay else ""}</div>'
    return Item(
        name,
        html,
        STAGE
        + ".ld { position: relative; display: grid; place-items: center; }\n"
        + (REPLAY_CSS if replay else "")
        + css,
        js,
        note,
    )


def pieces(count: int) -> str:
    return "".join(f'<i style="--i: {index}"></i>' for index in range(count))


# Feeds a fixed answer into the page a few characters at a time, as a model's stream would.
STREAM_JS = (
    CALM
    + """\
const ANSWER = "Streaming shows the answer as it is produced, so the wait feels shorter and the reader can begin at once.";
// Calls `onToken(text)` for each small chunk, then `onDone()`; returns a function that cancels.
const stream = (onToken, onDone = () => {}) => {
  const tokens = ANSWER.match(/\\s*\\S{1,4}/g);
  if (calm) { onToken(ANSWER); onDone(); return () => {}; }
  let index = 0;
  const timer = setInterval(() => {
    onToken(tokens[index++]);
    if (index === tokens.length) { clearInterval(timer); onDone(); }
  }, 55);
  return () => clearInterval(timer);
};
"""
)
STREAM_CSS = ".ld { width: 340px; min-height: 96px; place-items: start; text-align: left; line-height: 1.6; }\n.out { margin: 0; }\n"
STREAM_LOOP = """\
let cancel = () => {};
const start = () => { cancel(); output.textContent = ""; cancel = run(); };
document.querySelector(".replay").addEventListener("click", start);
start();
"""

SECTION = Section(
    "effects",
    "Loading Effects",
    271,
    (
        load(
            "Spinner",
            "",
            ".ld { width: 40px; height: 40px; border: 4px solid var(--surface-2); border-top-color: var(--primary); border-radius: 50%; animation: turn .8s linear infinite; }\n"
            + TURN,
            "A ring with one coloured quarter, turning at constant speed.",
        ),
        load(
            "Dotted spinner",
            pieces(8),
            """\
.ld { width: 48px; height: 48px; }
.ld i { position: absolute; width: 7px; height: 7px; border-radius: 50%; background: var(--fg); transform: rotate(calc(var(--i) * 45deg)) translateY(-19px); animation: fade .8s linear infinite; animation-delay: calc(var(--i) * .1s - .8s); }
@keyframes fade { from { opacity: 1; } to { opacity: .12; } }
""",
            "Eight fixed dots; brightness passes round them in turn, so nothing actually rotates.",
        ),
        load(
            "Ring spinner",
            '<svg viewBox="0 0 50 50" aria-hidden="true"><circle cx="25" cy="25" r="20"/></svg>',
            """\
.ld svg { width: 46px; height: 46px; animation: turn 1.6s linear infinite; }
.ld circle { fill: none; stroke: var(--primary); stroke-width: 4; stroke-linecap: round; animation: stretch 1.4s ease-in-out infinite; }
/* The arc grows from the head, then shrinks from the tail, while the whole ring turns. */
@keyframes stretch { 0% { stroke-dasharray: 1 126; stroke-dashoffset: 0; } 50% { stroke-dasharray: 90 126; stroke-dashoffset: -30; } 100% { stroke-dasharray: 90 126; stroke-dashoffset: -124; } }
"""
            + TURN,
            "An arc that lengthens and shortens as it rotates: the Material-style spinner.",
        ),
        load(
            "Dual-ring spinner",
            "<i></i><i></i>",
            """\
.ld { width: 52px; height: 52px; }
.ld i { position: absolute; border: 3px solid transparent; border-radius: 50%; }
.ld i:nth-child(1) { inset: 0; border-top-color: var(--primary); border-bottom-color: var(--primary); animation: turn 1.1s linear infinite; }
.ld i:nth-child(2) { inset: 9px; border-left-color: var(--accent); border-right-color: var(--accent); animation: turn .8s linear infinite reverse; }
"""
            + TURN,
            "Two rings, one inside the other, turning in opposite directions at different speeds.",
        ),
        load(
            "Pulse loader",
            "<i></i><i></i>",
            """\
.ld { width: 56px; height: 56px; }
.ld i { position: absolute; inset: 0; border-radius: 50%; background: var(--primary); animation: pulse 1.6s ease-out infinite; }
.ld i:nth-child(2) { animation-delay: -.8s; }
@keyframes pulse { from { scale: 0; opacity: .9; } to { scale: 1; opacity: 0; } }
""",
            "Discs grow from the centre and fade; a second one, half a cycle behind, keeps it continuous.",
        ),
        load(
            "Wave loader",
            pieces(5),
            """\
.ld { display: flex; gap: 5px; height: 40px; }
.ld i { width: 6px; height: 100%; border-radius: 3px; background: var(--primary); animation: wave 1s ease-in-out infinite; animation-delay: calc(var(--i) * .1s); }
@keyframes wave { 0%, 100% { scale: 1 .3; } 50% { scale: 1 1; } }
""",
            "Bars rise and fall one after another, so a wave appears to pass along the row.",
        ),
        load(
            "Bar loader",
            "",
            """\
.ld { width: 220px; height: 5px; overflow: hidden; border-radius: 99px; background: var(--surface-2); }
.ld::before { content: ""; position: absolute; inset: 0; width: 40%; border-radius: inherit; background: var(--primary); animation: slide 1.3s ease-in-out infinite; }
@keyframes slide { from { translate: -100% 0; } to { translate: 250% 0; } }
""",
            "An indeterminate bar: a segment crosses a track repeatedly when the amount of work is unknown.",
        ),
        load(
            "Shimmer loader",
            "",
            """\
.ld { width: 260px; height: 90px; border-radius: 14px; background: linear-gradient(100deg, var(--surface) 30%, var(--surface-2) 50%, var(--surface) 70%) 0 0 / 250% 100%; animation: shimmer 1.4s linear infinite; }
@keyframes shimmer { from { background-position: 150% 0; } to { background-position: -100% 0; } }
""",
            "A placeholder block with a lighter band sliding across it.",
        ),
        load(
            "Skeleton shimmer",
            '<i class="avatar"></i><i class="line" style="width: 60%"></i><i class="line"></i><i class="line" style="width: 80%"></i>',
            """\
.ld { grid-template-columns: 48px 1fr; gap: 10px 14px; width: 300px; place-items: center start; }
.ld i { border-radius: 6px; background: linear-gradient(100deg, var(--surface) 30%, var(--surface-2) 50%, var(--surface) 70%) fixed 0 0 / 250% 100%; animation: shimmer 1.4s linear infinite; }
/* `fixed` ties every piece to one shared gradient, so the band crosses the whole skeleton as a single sweep. */
.avatar { grid-row: span 2; width: 48px; height: 48px; border-radius: 50% !important; }
.line { width: 100%; height: 12px; }
.line:nth-child(n + 3) { grid-column: 1 / -1; }
@keyframes shimmer { from { background-position: 150% 0; } to { background-position: -100% 0; } }
""",
            "The outline of the content to come, with one highlight sweeping across all of its pieces together.",
            label="Loading content",
        ),
        load(
            "Skeleton pulse",
            '<i class="avatar"></i><i class="line" style="width: 60%"></i><i class="line"></i><i class="line" style="width: 80%"></i>',
            """\
.ld { grid-template-columns: 48px 1fr; gap: 10px 14px; width: 300px; place-items: center start; animation: dim 1.4s ease-in-out infinite alternate; }
.ld i { border-radius: 6px; background: var(--surface-2); }
.avatar { grid-row: span 2; width: 48px; height: 48px; border-radius: 50% !important; }
.line { width: 100%; height: 12px; }
.line:nth-child(n + 3) { grid-column: 1 / -1; }
@keyframes dim { to { opacity: .4; } }
""",
            "The same skeleton, fading in and out as a whole: quieter than a shimmer, and cheaper to render.",
            label="Loading content",
        ),
        load(
            "Gradient loader",
            "",
            """\
.ld { width: 52px; height: 52px; border-radius: 50%; background: conic-gradient(transparent 10%, var(--primary), var(--accent)); mask: radial-gradient(farthest-side, transparent calc(100% - 6px), #000 calc(100% - 5px)); animation: turn 1s linear infinite; }
"""
            + TURN,
            "A conic gradient cut into a ring by a mask: the arc fades out along its own tail.",
        ),
        load(
            "Liquid loader",
            "",
            """\
.ld { width: 86px; height: 86px; overflow: hidden; border: 3px solid var(--accent); border-radius: 50%; background: var(--surface); }
/* Two large rounded squares turn slowly; their edges, seen through the circle, look like a liquid surface. */
.ld::before, .ld::after { content: ""; position: absolute; left: -50%; width: 200%; aspect-ratio: 1; border-radius: 42%; background: var(--accent); animation: turn 5s linear infinite, fill 5s ease-in-out infinite alternate; }
.ld::after { border-radius: 38%; opacity: .45; animation-duration: 7s, 5s; }
@keyframes fill { from { top: 85%; } to { top: 15%; } }
"""
            + TURN,
            "A vessel that fills and drains, with a surface that sloshes as it goes.",
        ),
        load(
            "Orb loader",
            "",
            """\
.ld { width: 64px; height: 64px; border-radius: 50%; background: conic-gradient(from 0deg, #7c5cff, #22d3ee, #f472b6, #7c5cff); filter: blur(3px); box-shadow: 0 0 30px rgb(124 92 255 / .7); animation: turn 2.4s linear infinite, swell 2.4s ease-in-out infinite alternate; }
.ld::after { content: ""; position: absolute; inset: 22%; border-radius: 50%; background: radial-gradient(circle at 35% 30%, #fff, transparent 70%); mix-blend-mode: soft-light; }
@keyframes swell { from { scale: .88; } to { scale: 1.08; } }
"""
            + TURN,
            "A glowing sphere of turning colour that swells and settles: the assistant-is-busy orb.",
        ),
        load(
            "Particle loader",
            pieces(12),
            """\
.ld { width: 90px; height: 90px; }
.ld i { position: absolute; width: 5px; height: 5px; border-radius: 50%; background: var(--accent); rotate: calc(var(--i) * 30deg); animation: gather 1.5s ease-in infinite; animation-delay: calc(var(--i) * -.125s); }
@keyframes gather { from { transform: translateY(-44px) scale(1); opacity: 0; } 25% { opacity: 1; } to { transform: translateY(0) scale(.2); opacity: 0; } }
""",
            "Particles are drawn in from a ring to the centre one after another, round and round.",
        ),
        load(
            "Orbital loader",
            '<b></b><i style="--r: 20px; --t: 1.1s"></i><i style="--r: 30px; --t: 1.7s"></i><i style="--r: 40px; --t: 2.6s"></i>',
            """\
.ld { width: 90px; height: 90px; }
.ld b { width: 12px; height: 12px; border-radius: 50%; background: var(--primary); box-shadow: 0 0 12px var(--primary); }
.ld i { position: absolute; width: calc(var(--r) * 2); height: calc(var(--r) * 2); border: 1px solid var(--border); border-radius: 50%; animation: turn var(--t) linear infinite; }
.ld i::after { content: ""; position: absolute; top: -4px; left: calc(50% - 3px); width: 7px; height: 7px; border-radius: 50%; background: var(--accent); }
"""
            + TURN,
            "Satellites on three orbits, the nearer ones faster, around a fixed core.",
        ),
        load(
            "Rotating loader",
            "",
            """\
.ld { width: 38px; height: 38px; border-radius: 6px; background: var(--primary); animation: tumble 1.6s var(--ease) infinite; }
@keyframes tumble { 0% { transform: perspective(120px) rotateX(0) rotateY(0); } 50% { transform: perspective(120px) rotateX(-180deg) rotateY(0); } 100% { transform: perspective(120px) rotateX(-180deg) rotateY(-180deg); } }
""",
            "A tile that flips over one axis, then the other, pausing flat between turns.",
        ),
        load(
            "Morphing loader",
            "",
            """\
.ld { width: 44px; height: 44px; background: var(--primary); animation: morph 3s ease-in-out infinite; }
@keyframes morph { 0%, 100% { border-radius: 50%; rotate: 0deg; background: #7c5cff; } 33% { border-radius: 8px; rotate: 90deg; background: #22d3ee; } 66% { border-radius: 50% 50% 8px 50%; rotate: 225deg; background: #f472b6; } }
""",
            "One shape passing through circle, square and teardrop while it turns and changes colour.",
        ),
        load(
            "Breathing loader",
            "",
            """\
.ld { width: 60px; height: 60px; border-radius: 50%; background: radial-gradient(circle, var(--accent), transparent 70%); animation: breathe 3s ease-in-out infinite alternate; }
@keyframes breathe { from { scale: .6; opacity: .45; } to { scale: 1.15; opacity: 1; } }
""",
            "A slow swell and release at about the pace of a resting breath: calm, for long waits.",
        ),
        load(
            "Elastic loader",
            "",
            """\
.ld { width: 120px; height: 16px; }
.ld::before { content: ""; position: absolute; left: 0; width: 16px; height: 16px; border-radius: 8px; background: var(--primary); animation: snap 1.4s cubic-bezier(.6, 0, .4, 1) infinite alternate; }
/* It stretches out toward the far side first, then the back end catches up. */
@keyframes snap { 0% { left: 0; width: 16px; } 50% { left: 0; width: 120px; } 100% { left: 104px; width: 16px; } }
""",
            "A dot that stretches across the track and snaps to the other side, like a rubber band.",
        ),
        load(
            "AI thinking animation",
            '<span class="dots">' + pieces(3) + '</span><span class="word">Thinking</span>',
            """\
.ld { display: flex; gap: 12px; padding: 12px 18px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface); }
.dots { display: flex; gap: 4px; }
.dots i { width: 7px; height: 7px; border-radius: 50%; background: var(--primary); animation: hop 1.2s ease-in-out infinite; animation-delay: calc(var(--i) * .15s); }
.word { color: transparent; background: linear-gradient(100deg, var(--muted) 35%, #fff 50%, var(--muted) 65%) 0 0 / 250% 100%; -webkit-background-clip: text; background-clip: text; animation: sweep 2s linear infinite; }
@keyframes hop { 0%, 60%, 100% { translate: 0 0; opacity: .4; } 30% { translate: 0 -6px; opacity: 1; } }
@keyframes sweep { from { background-position: 150% 0; } to { background-position: -100% 0; } }
""",
            "Three hopping dots beside a word with a highlight passing through it: the model has started but has nothing to show yet.",
            label="Thinking",
        ),
        load(
            "AI processing pulse",
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2l2.2 6.8L21 11l-6.8 2.2L12 20l-2.2-6.8L3 11l6.8-2.2z"/></svg><i></i><i></i>',
            """\
.ld { width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, #7c5cff, #22d3ee); }
.ld svg { position: relative; z-index: 1; width: 28px; fill: #fff; animation: twinkle 1.6s ease-in-out infinite alternate; }
.ld i { position: absolute; inset: 0; border-radius: 50%; border: 2px solid var(--primary); animation: ripple 2s ease-out infinite; }
.ld i:last-child { animation-delay: -1s; border-color: var(--accent); }
@keyframes ripple { to { scale: 2; opacity: 0; } }
@keyframes twinkle { from { scale: .8; rotate: -12deg; } to { scale: 1.1; rotate: 12deg; } }
""",
            "The assistant's mark with rings radiating from it while a request is being processed.",
            label="Processing",
        ),
        load(
            "Neural activity animation",
            '<svg viewBox="0 0 300 150" aria-hidden="true"></svg>',
            """\
.ld svg { width: 320px; overflow: visible; }
.ld line { stroke: var(--border); stroke-width: 1; transition: stroke .5s; }
.ld line.fire { stroke: var(--accent); transition: none; }
.ld circle { fill: var(--surface-2); stroke: var(--border); transition: fill .6s; }
.ld circle.fire { fill: var(--accent); filter: drop-shadow(0 0 6px var(--accent)); transition: none; }
""",
            "A small layered network: signals start at an input and hop forward along random connections, lighting each node as they arrive.",
            CALM
            + """\
const svg = document.querySelector("svg");
const make = (tag, attrs) => { const node = document.createElementNS("http://www.w3.org/2000/svg", tag); for (const key in attrs) node.setAttribute(key, attrs[key]); return node; };
const SIZES = [3, 5, 5, 2];
const layers = SIZES.map((size, column) => Array.from({ length: size }, (_, row) => ({ x: 30 + column * 80, y: 75 + (row - (size - 1) / 2) * 30 })));
// Every node is joined to every node of the next layer; each link remembers its line.
const links = new Map();
layers.slice(0, -1).forEach((layer, column) => layer.forEach((from) => layers[column + 1].forEach((to) => {
  const line = svg.appendChild(make("line", { x1: from.x, y1: from.y, x2: to.x, y2: to.y }));
  links.set(`${from.x},${from.y}>${to.x},${to.y}`, line);
})));
layers.flat().forEach((point) => { point.dot = svg.appendChild(make("circle", { cx: point.x, cy: point.y, r: 6 })); });
const flash = (element) => { element.classList.add("fire"); setTimeout(() => element.classList.remove("fire"), 160); };
const pick = (list) => list[Math.floor(Math.random() * list.length)];
const signal = (node, column) => {
  flash(node.dot);
  if (column === layers.length - 1) return;
  const next = pick(layers[column + 1]);
  flash(links.get(`${node.x},${node.y}>${next.x},${next.y}`));
  setTimeout(() => signal(next, column + 1), 140);
};
if (calm) layers[1].forEach((node) => node.dot.classList.add("fire"));
else setInterval(() => signal(pick(layers[0]), 0), 260);
""",
            label="Model is working",
        ),
        load(
            "Token generation animation",
            '<p class="out"></p>',
            """\
.ld { width: 340px; min-height: 110px; place-items: start; }
.out { display: flex; flex-wrap: wrap; gap: 5px; margin: 0; }
.out span { padding: 2px 7px; border-radius: 6px; font: 13px var(--mono); background: var(--surface-2); animation: token .7s ease-out both; }
@keyframes token { from { background: var(--primary); color: #fff; scale: .8; opacity: 0; } }
""",
            "Output shown as the discrete tokens it is made of: each chip arrives highlighted and cools to the resting colour.",
            STREAM_JS
            + """\
const output = document.querySelector(".out");
const run = () => stream((token) => {
  if (calm) { output.textContent = token; return; }
  output.append(Object.assign(document.createElement("span"), { textContent: token.trim() }));
});
"""
            + STREAM_LOOP,
            label="Generating",
            replay=True,
        ),
        load(
            "Streaming cursor",
            '<p class="out"></p>',
            STREAM_CSS
            + """\
.out::after { content: ""; display: inline-block; width: 8px; height: 1.05em; margin-left: 2px; vertical-align: text-bottom; border-radius: 2px; background: var(--accent); animation: blink 1s steps(2) infinite; }
.out.done::after { display: none; }
@keyframes blink { 50% { opacity: 0; } }
""",
            "A block caret stays at the end of the text while it is still arriving, and goes when the stream ends.",
            STREAM_JS
            + """\
const output = document.querySelector(".out");
const run = () => { output.classList.remove("done"); return stream((token) => { output.textContent += token; }, () => output.classList.add("done")); };
"""
            + STREAM_LOOP,
            label="Generating",
            replay=True,
        ),
        load(
            "Streaming glow",
            '<p class="out"></p>',
            STREAM_CSS
            + ".out span { animation: cool 1s ease-out both; }\n@keyframes cool { from { color: #fff; text-shadow: 0 0 10px var(--accent), 0 0 22px var(--accent); } }\n",
            "The newest words are lit and cool down over a second, so the eye always knows where the writing is happening.",
            STREAM_JS
            + """\
const output = document.querySelector(".out");
const run = () => stream((token) => {
  if (calm) { output.textContent = token; return; }
  output.append(Object.assign(document.createElement("span"), { textContent: token }));
});
"""
            + STREAM_LOOP,
            label="Generating",
            replay=True,
        ),
        load(
            "Streaming gradient",
            '<p class="out"></p>',
            STREAM_CSS
            + """\
/* Each chunk starts as a blurred wash of the accent colour and clears to plain text. */
.out span { animation: appear .7s ease-out both; }
@keyframes appear { from { opacity: 0; filter: blur(4px); color: var(--accent); } 60% { color: var(--primary); } }
""",
            "Words do not pop in: each resolves from a blurred tint through the brand colours to plain text, so the stream has a soft coloured leading edge.",
            STREAM_JS
            + """\
const output = document.querySelector(".out");
const run = () => stream((token) => {
  if (calm) { output.textContent = token; return; }
  output.append(Object.assign(document.createElement("span"), { textContent: token }));
});
"""
            + STREAM_LOOP,
            label="Generating",
            replay=True,
        ),
        load(
            "Progress morph",
            '<button class="pm" type="button"><span class="text">Upload</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></button>',
            """\
.pm { position: relative; display: grid; place-items: center; width: 150px; height: 44px; overflow: hidden; border: 0; border-radius: 22px; background: var(--primary); color: #fff; font-weight: 600; transition: width .4s var(--ease), height .4s var(--ease), background .3s; }
.pm::before { content: ""; position: absolute; inset: 0; width: calc(var(--done, 0) * 100%); background: var(--accent); opacity: 0; }
.pm svg { position: absolute; width: 22px; fill: none; stroke: #fff; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 24; stroke-dashoffset: 24; }
/* 1: the button flattens into a track. 2: the track rounds up into a badge with a tick. */
.pm[data-state="busy"] { width: 220px; height: 8px; background: var(--surface-2); }
.pm[data-state="busy"] .text, .pm[data-state="done"] .text { opacity: 0; }
.pm[data-state="busy"]::before { opacity: 1; }
.pm[data-state="done"] { width: 44px; background: var(--success); }
.pm[data-state="done"] svg { stroke-dashoffset: 0; transition: stroke-dashoffset .35s .3s ease-out; }
""",
            "One element is the button, then the progress bar, then the confirmation: it changes shape instead of being swapped out. Click to run it.",
            """\
const button = document.querySelector(".pm");
const status = document.querySelector(".ld");
const run = () => {
  if (button.dataset.state === "busy") return;
  button.dataset.state = "busy";
  status.setAttribute("aria-label", "Uploading");
  let done = 0;
  const timer = setInterval(() => {
    done = Math.min(1, done + 0.04 + Math.random() * 0.06);
    button.style.setProperty("--done", done.toFixed(3));
    if (done < 1) return;
    clearInterval(timer);
    button.dataset.state = "done";
    status.setAttribute("aria-label", "Upload complete");
    setTimeout(() => { delete button.dataset.state; button.style.removeProperty("--done"); status.setAttribute("aria-label", "Ready"); }, 1800);
  }, 120);
};
button.addEventListener("click", run);
run();
""",
            label="Ready",
        ),
        load(
            "Loading percentage animation",
            '<b class="pct">0%</b><i class="track"></i>',
            """\
.ld { gap: 12px; width: 240px; }
.pct { font-size: 46px; font-weight: 800; font-variant-numeric: tabular-nums; }
.track { width: 100%; height: 6px; border-radius: 99px; background: linear-gradient(90deg, var(--primary), var(--accent)) 0 0 / calc(var(--done, 0) * 100%) 100% no-repeat, var(--surface-2); }
""",
            "A figure that counts up alongside its bar. Tabular numerals keep the digits from shifting as they change.",
            CALM
            + """\
const status = document.querySelector(".ld");
const figure = status.querySelector(".pct");
const DURATION = 2600;
const show = (done) => { figure.textContent = `${Math.round(done * 100)}%`; status.style.setProperty("--done", done.toFixed(4)); };
const run = () => {
  const started = performance.now();
  const frame = (now) => {
    const t = Math.min(1, Math.max(0, (now - started) / DURATION));
    show(1 - Math.pow(1 - t, 3));  // fast at first, slowing toward the end
    if (t < 1) requestAnimationFrame(frame);
  };
  if (calm) show(1); else requestAnimationFrame(frame);
};
document.querySelector(".replay").addEventListener("click", run);
run();
""",
            replay=True,
        ),
        load(
            "Step progress animation",
            '<ol class="steps"><li>Upload</li><li>Scan</li><li>Index</li><li>Done</li></ol>',
            """\
.steps { display: flex; margin: 0; padding: 0; list-style: none; counter-reset: step; }
.steps li { position: relative; display: grid; justify-items: center; gap: 8px; width: 88px; font-size: 12px; color: var(--muted); counter-increment: step; transition: color .3s; }
.steps li::before { content: counter(step); position: relative; z-index: 1; display: grid; place-items: center; width: 28px; height: 28px; border: 2px solid var(--border); border-radius: 50%; background: var(--bg); font-weight: 700; transition: all .3s var(--ease); }
/* The connector to the previous step fills as this step is reached. */
.steps li + li::after { content: ""; position: absolute; top: 13px; right: 50%; width: 100%; height: 2px; background: linear-gradient(var(--primary), var(--primary)) 0 0 / 0% 100% no-repeat, var(--border); transition: background-size .5s var(--ease); }
.steps li.active, .steps li.done { color: var(--fg); }
.steps li.active::before { border-color: var(--primary); box-shadow: 0 0 0 4px rgb(124 92 255 / .25); }
.steps li.done::before { content: "✓"; border-color: var(--primary); background: var(--primary); color: #fff; }
.steps li.active::after, .steps li.done::after { background-size: 100% 100%; }
""",
            "Stages complete in order: the line fills up to a step, the step lights, and then it turns to a tick as the next begins.",
            """\
const status = document.querySelector(".ld");
const steps = [...status.querySelectorAll("li")];
let current = 0;
const show = () => {
  steps.forEach((step, index) => { step.classList.toggle("done", index < current); step.classList.toggle("active", index === current); });
  status.setAttribute("aria-label", current < steps.length ? `Step ${current + 1} of ${steps.length}: ${steps[current].textContent}` : "All steps complete");
};
show();
setInterval(() => { current = current === steps.length ? 0 : current + 1; show(); }, 1100);
""",
        ),
        load(
            "Indeterminate wave",
            '<svg viewBox="0 0 240 24" preserveAspectRatio="none" aria-hidden="true"><path d="M-48 12 q 12 -14 24 0 t 24 0 t 24 0 t 24 0 t 24 0 t 24 0 t 24 0 t 24 0 t 24 0 t 24 0 t 24 0 t 24 0 t 24 0"/></svg>',
            """\
.ld { width: 240px; height: 24px; overflow: hidden; mask: linear-gradient(90deg, transparent, #000 20% 80%, transparent); }
.ld svg { width: 100%; height: 100%; overflow: visible; }
.ld path { fill: none; stroke: var(--primary); stroke-width: 3; stroke-linecap: round; animation: flow .9s linear infinite; }
/* Shifting by exactly one wavelength (48 units) makes the loop seamless. */
@keyframes flow { to { translate: 48px 0; } }
""",
            "A sine wave travelling along a line, faded at both ends: an indeterminate bar with more character.",
        ),
    ),
)
