"""Effects 421-450: data visualisation."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import STAGE
from app.domains.references.vocabulary.patterns_10_dataviz import CH, KIT

AGAIN_CSS = ".again { position: absolute; top: 12px; right: 14px; padding: 4px 12px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface-2); font-size: 12px; }\n"
CALM = 'const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\n'
# Calls `step(t)` with eased t from 0 to 1 over `ms`. Reduced motion jumps straight to the end.
TWEEN = (
    CALM
    + """\
const ease = (t) => 1 - Math.pow(1 - t, 3);
const tween = (ms, step, done = () => {}) => {
  if (calm) { step(1); done(); return; }
  const start = performance.now();
  const frame = (now) => {
    const t = Math.min(1, Math.max(0, (now - start) / ms));  // a frame's timestamp can precede `start`
    step(ease(t));
    if (t < 1) requestAnimationFrame(frame); else done();
  };
  requestAnimationFrame(frame);
};
const mix = (from, to, t) => from + (to - from) * t;
"""
)
# Scales and axes for the shared monthly series, redrawn from scratch on each replay.
SCENE = """\
const max = niceMax(Math.max(...SERIES));
const x = linear(0, SERIES.length - 1, M.left + 10, W - M.right - 10);
const y = linear(0, max, H - M.bottom, M.top);
const points = SERIES.map((value, i) => [x(i), y(value)]);
const axes = () => { svg.replaceChildren(); yAxis(y, max); xLabels(MONTHS, x); };
"""
BARS = """\
const max = niceMax(Math.max(...SERIES));
const y = linear(0, max, H - M.bottom, M.top);
const band = (W - M.left - M.right) / MONTHS.length;
const centre = (i) => M.left + band * (i + 0.5);
const axes = () => { svg.replaceChildren(); yAxis(y, max); MONTHS.forEach((label, i) => el("text", { x: centre(i), y: H - 10, class: "tick mid" }, label)); };
const bar = (i, value, extra = {}) => el("rect", { x: centre(i) - band * 0.3, width: band * 0.6, y: y(value), height: y(0) - y(value), rx: 4, class: "fill s0", ...extra });
"""
RESTART = 'const restart = () => { svg.classList.remove("go"); void svg.getBoundingClientRect(); svg.classList.add("go"); };\n'
WIRE = 'document.querySelector(".again").addEventListener("click", play);\nplay();\n'


def viz(
    name: str,
    js: str,
    note: str,
    css: str = "",
    replay: bool = True,
    extra: str = "",
    sub: str = "",
) -> Item:
    """A chart effect. With ``replay`` the script defines ``play()``, which draws and animates from scratch."""
    small = f"<small>{sub}</small>" if sub else ""
    button = '<button class="again">Replay</button>' if replay else ""
    html = f'<figure class="ch"><figcaption>{name}{small}</figcaption><svg class="plot" viewBox="0 0 480 260" role="img" aria-label="{name}"></svg>{extra}{button}</figure>'
    return Item(name, html, CH + AGAIN_CSS + css, KIT + js + (WIRE if replay else ""), note)


KPI_CSS = (
    STAGE
    + ".kpi { position: relative; display: grid; gap: 4px; min-width: 220px; padding: 18px 22px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n"
    ".kpi small { color: var(--muted); }\n.kpi b { font-size: 40px; font-weight: 800; font-variant-numeric: tabular-nums; line-height: 1.1; }\n"
    ".again { padding: 4px 12px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface-2); font-size: 12px; justify-self: start; margin-top: 8px; }\n"
)


def kpi(name: str, inner: str, css: str, js: str, note: str, button: str = "Replay") -> Item:
    html = f'<div class="stage"><div class="kpi"><small>Monthly revenue</small>{inner}<button class="again">{button}</button></div></div>'
    return Item(name, html, KPI_CSS + css, js, note)


# A value that changes every time the button is pressed (and once on load).
LIVE = """\
const NEXT = [48210, 51940, 49875, 56320, 60105];
let turn = 0, value = NEXT[0];
const format = (number) => `$${Math.round(number).toLocaleString("en-US")}`;
"""

SECTION = Section(
    "effects",
    "Data Visualization Effects",
    421,
    (
        viz(
            "Chart draw animation",
            SCENE
            + RESTART
            + """\
const play = () => {
  axes();
  el("path", { d: `${path(points)}L${points.at(-1)[0]} ${y(0)}L${points[0][0]} ${y(0)}Z`, class: "soft s0 area" });
  el("path", { d: path(points), class: "stroke s0 line", pathLength: 1 });
  points.forEach(([px, py], i) => el("circle", { cx: px, cy: py, r: 4, class: "fill s0 dot", style: `--i: ${i}` }));
  restart();
};
""",
            "The whole chart assembles in order: the line is drawn, each point pops in as the line reaches it, and the area fades in last.",
            ".line { stroke-dasharray: 1; stroke-dashoffset: 1; }\n.dot { transform-box: fill-box; transform-origin: center; scale: 0; }\n.area { opacity: 0; }\n"
            ".go .line { animation: draw 1.2s var(--ease) forwards; }\n.go .dot { animation: pop .35s var(--ease) forwards; animation-delay: calc(var(--i) * .15s + .1s); }\n.go .area { animation: show .6s 1.1s ease-out forwards; }\n"
            "@keyframes draw { to { stroke-dashoffset: 0; } }\n@keyframes pop { to { scale: 1; } }\n@keyframes show { to { opacity: 1; } }\n",
        ),
        viz(
            "Line growth",
            SCENE
            + TWEEN
            + """\
const play = () => {
  axes();
  const line = el("path", { class: "stroke s0" });
  // Every point starts on the baseline and rises to its value.
  tween(900, (t) => line.setAttribute("d", path(SERIES.map((value, i) => [x(i), y(value * t)]))));
};
""",
            "The line starts flat on the baseline and every point rises to its value together: growth read as height.",
        ),
        viz(
            "Bar growth",
            BARS
            + RESTART
            + "const play = () => { axes(); SERIES.forEach((value, i) => bar(i, value, { style: `--i: ${i}` })); restart(); };\n",
            "Bars grow up from the axis one after another. The transform origin is each bar's own bottom edge.",
            "rect.fill { transform-box: fill-box; transform-origin: 50% 100%; scale: 1 0; }\n.go rect.fill { animation: grow .6s var(--ease) forwards; animation-delay: calc(var(--i) * 60ms); }\n@keyframes grow { to { scale: 1 1; } }\n",
        ),
        viz(
            "Area reveal",
            SCENE
            + TWEEN
            + """\
const play = () => {
  axes();
  const defs = el("defs");
  const gradient = el("linearGradient", { id: "fade", x1: 0, y1: 0, x2: 0, y2: 1 }, undefined, defs);
  el("stop", { offset: 0, "stop-color": "#7c5cff", "stop-opacity": 0.55 }, undefined, gradient);
  el("stop", { offset: 1, "stop-color": "#7c5cff", "stop-opacity": 0 }, undefined, gradient);
  const window = el("rect", { x: 0, y: 0, width: 0, height: H }, undefined, el("clipPath", { id: "reveal" }, undefined, defs));
  const group = el("g", { "clip-path": "url(#reveal)" });
  el("path", { d: `${path(points)}L${points.at(-1)[0]} ${y(0)}L${points[0][0]} ${y(0)}Z`, fill: "url(#fade)" }, undefined, group);
  el("path", { d: path(points), class: "stroke s0" }, undefined, group);
  tween(1100, (t) => window.setAttribute("width", W * t));  // the clipping window opens from the left
};
""",
            "A clipping window widens from the left, uncovering the line and its gradient fill together.",
        ),
        viz(
            "Pie expansion",
            TWEEN
            + """\
const PARTS = [["Direct", 42], ["Search", 28], ["Social", 18], ["Email", 12]];
const total = PARTS.reduce((sum, [, value]) => sum + value, 0);
const wedge = (cx, cy, r, a0, a1) => `${arc(cx, cy, r, a0, a1)}L${cx} ${cy}Z`;
const play = () => {
  svg.replaceChildren();
  const slices = PARTS.map((part, i) => el("path", { class: `fill s${i}` }));
  PARTS.forEach(([label], i) => { el("rect", { x: 330, y: 80 + i * 26, width: 12, height: 12, rx: 3, class: `fill s${i}` }); el("text", { x: 350, y: 91 + i * 26, class: "lbl" }, label); });
  // The whole pie opens like a fan: every slice's angles are scaled by the same t.
  tween(1000, (t) => {
    let from = 0;
    PARTS.forEach(([, value], i) => {
      const to = from + (value / total) * Math.PI * 2 * t;
      slices[i].setAttribute("d", wedge(170, 130, 100, from, Math.max(to, from + 0.0001)));
      from = to;
    });
  });
};
""",
            "The pie opens like a fan from twelve o'clock: all slices sweep out together, keeping their proportions the whole way.",
        ),
        viz(
            "Donut progress",
            TWEEN
            + """\
const TARGET = 0.72, R = 84, LENGTH = 2 * Math.PI * R;
const play = () => {
  svg.replaceChildren();
  el("circle", { cx: 240, cy: 130, r: R, fill: "none", stroke: "var(--surface-2)", "stroke-width": 18 });
  const ring = el("circle", { cx: 240, cy: 130, r: R, fill: "none", stroke: "var(--primary)", "stroke-width": 18, "stroke-linecap": "round", "stroke-dasharray": LENGTH, transform: "rotate(-90 240 130)" });
  const figure = el("text", { x: 240, y: 142, class: "lbl mid", style: "font-size: 34px" });
  tween(1200, (t) => {
    ring.setAttribute("stroke-dashoffset", LENGTH * (1 - TARGET * t));
    figure.textContent = `${Math.round(TARGET * t * 100)}%`;
  });
};
""",
            "The ring fills clockwise to its value while the figure in the middle counts up in step with it.",
        ),
        viz(
            "Gauge sweep",
            CALM
            + """\
const VALUE = 0.68, CX = 240, CY = 200, R = 130;
const angle = (share) => -Math.PI / 2 + share * Math.PI;  // 0..1 across the top half
const play = () => {
  svg.replaceChildren();
  el("path", { d: arc(CX, CY, R, angle(0), angle(1)), fill: "none", stroke: "var(--surface-2)", "stroke-width": 20, "stroke-linecap": "round" });
  [["var(--success)", 0, 0.5], ["var(--warning)", 0.5, 0.8], ["var(--danger)", 0.8, 1]].forEach(([colour, a, b]) => el("path", { d: arc(CX, CY, R, angle(a), angle(b)), fill: "none", stroke: colour, "stroke-width": 6 }));
  const needle = el("line", { x1: CX, y1: CY, x2: CX, y2: CY - R + 24, stroke: "var(--fg)", "stroke-width": 4, "stroke-linecap": "round", class: "needle" });
  el("circle", { cx: CX, cy: CY, r: 9, class: "fill s0" });
  el("text", { x: CX, y: CY + 40, class: "lbl mid", style: "font-size: 20px" }, `${Math.round(VALUE * 100)}%`);
  needle.style.rotate = "-90deg";
  void needle.getBoundingClientRect();
  needle.style.rotate = `${-90 + VALUE * 180}deg`;  // the transition, with its overshoot, does the rest
};
""",
            "The needle swings from zero to its reading and wobbles to rest, as a physical needle with some mass would.",
            ".needle { transform-box: view-box; transform-origin: 240px 200px; transition: rotate 1.4s linear(0, .5 14%, .94 27%, 1.12 38%, 1.04 50%, .97 62%, 1.01 78%, 1); }\n@media (prefers-reduced-motion: reduce) { .needle { transition: none; } }\n",
        ),
        kpi(
            "Counter animation",
            '<b class="value">$0</b>',
            "",
            TWEEN
            + 'const figure = document.querySelector(".value");\nconst TARGET = 48210;\nconst play = () => tween(1400, (t) => { figure.textContent = `$${Math.round(TARGET * t).toLocaleString("en-US")}`; });\ndocument.querySelector(".again").addEventListener("click", play);\nplay();\n',
            "The figure counts up from zero, fast at first and slowing as it nears the value. Tabular numerals stop the width from jittering.",
        ),
        kpi(
            "Number rolling",
            '<b class="reel" aria-label="48,210"></b>',
            ".reel { display: flex; height: 1.1em; overflow: hidden; }\n.reel span { display: grid; transition: translate 1.2s cubic-bezier(.2, .8, .2, 1); transition-delay: calc(var(--i) * 80ms); translate: 0 calc(var(--digit) * -1.1em); }\n.reel span i { height: 1.1em; font-style: normal; }\n",
            """\
const reel = document.querySelector(".reel");
const VALUES = ["48,210", "51,940", "49,875"];
let turn = 0;
// Each digit is a column of 0-9; showing a digit means sliding the column up to it.
const build = (text) => reel.replaceChildren(...[...text].map((char, i) => {
  const column = document.createElement("span");
  column.style.setProperty("--i", i);
  column.style.setProperty("--digit", 0);
  if (/\\d/.test(char)) for (let digit = 0; digit <= 9; digit += 1) column.append(Object.assign(document.createElement("i"), { textContent: digit }));
  else column.append(Object.assign(document.createElement("i"), { textContent: char }));
  column.setAttribute("aria-hidden", "true");
  return column;
}));
const show = (text) => {
  reel.setAttribute("aria-label", text);
  [...reel.children].forEach((column, i) => { if (/\\d/.test(text[i])) column.style.setProperty("--digit", text[i]); });
};
build(VALUES[0]);
requestAnimationFrame(() => requestAnimationFrame(() => show(VALUES[0])));
document.querySelector(".again").addEventListener("click", () => { turn = (turn + 1) % VALUES.length; show(VALUES[turn]); });
""",
            "An odometer: every digit is a strip of 0 to 9 that rolls to the right number, the digits finishing one after another.",
            button="Next value",
        ),
        kpi(
            "Number morphing",
            '<b class="value" aria-live="polite"></b>',
            ".value { display: flex; }\n.value span { display: inline-block; }\n.value span.new { animation: swap-in .45s var(--ease) both; }\n@keyframes swap-in { from { opacity: 0; translate: 0 .5em; filter: blur(6px); } }\n",
            LIVE
            + """\
const figure = document.querySelector(".value");
// Only the characters that differ from the previous value are animated.
const show = (text) => {
  const before = figure.textContent;
  figure.replaceChildren(...[...text].map((char, i) => Object.assign(document.createElement("span"), { textContent: char, className: before[i] === char ? "" : "new" })));
};
show(format(value));
document.querySelector(".again").addEventListener("click", () => { turn = (turn + 1) % NEXT.length; show(format(NEXT[turn])); });
""",
            "When the value changes, only the digits that differ are replaced: each dissolves up into its new form while the rest stay still.",
            button="Next value",
        ),
        kpi(
            "Metric pulse",
            '<b class="value" aria-live="polite"></b>',
            ".value.hit { animation: thump .5s var(--ease); }\n@keyframes thump { 30% { scale: 1.12; color: var(--accent); } }\n.value { transform-origin: 0 50%; }\n",
            LIVE
            + 'const figure = document.querySelector(".value");\nconst show = () => { figure.textContent = format(NEXT[turn]); figure.classList.remove("hit"); void figure.offsetWidth; figure.classList.add("hit"); };\nshow();\ndocument.querySelector(".again").addEventListener("click", () => { turn = (turn + 1) % NEXT.length; show(); });\n',
            "Each update makes the figure swell and flash once: enough to catch the eye on a live dashboard.",
            button="Update",
        ),
        kpi(
            "Metric highlight",
            '<b class="value" aria-live="polite"></b>',
            '.kpi { overflow: hidden; }\n.kpi::before { content: ""; position: absolute; inset: 0; background: var(--tone, transparent); opacity: 0; pointer-events: none; }\n.kpi.hit::before { animation: flash 1.2s ease-out; }\n@keyframes flash { from { opacity: .35; } }\n',
            LIVE
            + 'const card = document.querySelector(".kpi");\nconst figure = card.querySelector(".value");\nconst show = (previous) => {\n  figure.textContent = format(NEXT[turn]);\n  // Green for a rise, red for a fall: the direction is in the colour.\n  card.style.setProperty("--tone", NEXT[turn] >= previous ? "var(--success)" : "var(--danger)");\n  card.classList.remove("hit"); void card.offsetWidth; card.classList.add("hit");\n};\nshow(0);\ndocument.querySelector(".again").addEventListener("click", () => { const previous = NEXT[turn]; turn = (turn + 1) % NEXT.length; show(previous); });\n',
            "The card's background flashes green or red when the value moves, then fades: the trading-screen convention for 'this just changed, and which way'.",
            button="Update",
        ),
        kpi(
            "Trend animation",
            '<b class="value"></b><span class="trend" aria-live="polite"><i aria-hidden="true">↑</i><em></em></span>',
            ".trend { display: flex; align-items: center; gap: 6px; font-weight: 700; color: var(--success); transition: color .4s; }\n.trend i { display: inline-block; font-style: normal; transition: rotate .5s var(--ease); }\n.trend em { font-style: normal; }\n.trend.down { color: var(--danger); }\n.trend.down i { rotate: 180deg; }\n",
            LIVE
            + TWEEN
            + """\
const figure = document.querySelector(".value");
const trend = document.querySelector(".trend");
const delta = trend.querySelector("em");
let shown = 0;
const show = (previous) => {
  const change = previous ? ((NEXT[turn] - previous) / previous) * 100 : 4.2;
  figure.textContent = format(NEXT[turn]);
  trend.classList.toggle("down", change < 0);  // the arrow turns over and the colour follows
  const from = shown;
  tween(600, (t) => { shown = mix(from, change, t); delta.textContent = `${shown >= 0 ? "+" : ""}${shown.toFixed(1)}%`; });
};
show(0);
document.querySelector(".again").addEventListener("click", () => { const previous = NEXT[turn]; turn = (turn + 1) % NEXT.length; show(previous); });
""",
            "The trend arrow rotates between up and down, its colour changes with it, and the percentage runs to its new value.",
            button="Update",
        ),
        kpi(
            "Sparkline draw",
            '<b class="value">$48,210</b><svg class="spark" viewBox="0 0 180 44" aria-hidden="true"><path pathLength="1" d="M2 34 L24 28 L46 31 L68 18 L90 22 L112 10 L134 14 L156 6 L176 9"/><circle cx="176" cy="9" r="4"/></svg>',
            ".spark { width: 180px; overflow: visible; }\n.spark path { fill: none; stroke: var(--accent); stroke-width: 2.5; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1; stroke-dashoffset: 1; }\n.spark circle { fill: var(--accent); scale: 0; transform-box: fill-box; transform-origin: center; }\n.go path { animation: draw 1s var(--ease) forwards; }\n.go circle { animation: pop .3s 1s var(--ease) forwards; }\n@keyframes draw { to { stroke-dashoffset: 0; } }\n@keyframes pop { to { scale: 1; } }\n",
            'const spark = document.querySelector(".spark");\nconst play = () => { spark.classList.remove("go"); void spark.getBoundingClientRect(); spark.classList.add("go"); };\ndocument.querySelector(".again").addEventListener("click", play);\nplay();\n',
            "A sparkline is drawn in one stroke, and a dot lands on its latest value when the line arrives.",
        ),
        viz(
            "Tooltip follow",
            SCENE
            + CALM
            + """\
axes();
el("path", { d: path(points), class: "stroke s0" });
const marker = el("circle", { r: 5, class: "fill s0", visibility: "hidden" });
const tip = document.querySelector(".tip");
const figure = document.querySelector(".ch");
let at = null, goal = null, nearest = 0;
// The tooltip chases its goal a fraction of the way each frame, so it glides instead of jumping between points.
const chase = () => {
  if (!goal) return;
  at = at && !calm ? [at[0] + (goal[0] - at[0]) * 0.22, at[1] + (goal[1] - at[1]) * 0.22] : goal;
  const box = svg.getBoundingClientRect(), frame = figure.getBoundingClientRect();
  tip.style.left = `${box.left - frame.left + (at[0] / W) * box.width}px`;
  tip.style.top = `${box.top - frame.top + (at[1] / H) * box.height}px`;
  marker.setAttribute("cx", at[0]); marker.setAttribute("cy", at[1]);
  requestAnimationFrame(chase);
};
svg.addEventListener("pointermove", (event) => {
  const box = svg.getBoundingClientRect();
  const px = ((event.clientX - box.left) / box.width) * W;
  nearest = points.reduce((best, point, i) => (Math.abs(point[0] - px) < Math.abs(points[best][0] - px) ? i : best), 0);
  const starting = !goal;
  goal = points[nearest];
  tip.textContent = `${MONTHS[nearest]}: ${SERIES[nearest]}`;
  tip.hidden = false; marker.setAttribute("visibility", "visible");
  if (starting) chase();
});
svg.addEventListener("pointerleave", () => { goal = null; at = null; tip.hidden = true; marker.setAttribute("visibility", "hidden"); });
""",
            "The tooltip snaps to the nearest data point but glides there, easing a fraction of the remaining distance each frame.",
            replay=False,
            extra='<div class="tip" hidden></div>',
            sub="Move across the chart",
        ),
        viz(
            "Data-point pulse",
            SCENE
            + 'axes();\nel("path", { d: path(points), class: "stroke s0" });\nconst [lx, ly] = points.at(-1);\nel("circle", { cx: lx, cy: ly, r: 5, class: "ping" });\nel("circle", { cx: lx, cy: ly, r: 5, class: "fill s0" });\n',
            "The newest point sends out rings: the line is live and this is where it is growing.",
            ".ping { fill: none; stroke: var(--primary); stroke-width: 2; transform-box: fill-box; transform-origin: center; animation: ping 1.6s ease-out infinite; }\n@keyframes ping { to { scale: 4; opacity: 0; } }\n",
            replay=False,
        ),
        viz(
            "Data-point glow",
            SCENE
            + 'axes();\nel("path", { d: path(points), class: "stroke s1" });\npoints.forEach(([px, py], i) => el("circle", { cx: px, cy: py, r: 5, class: "fill s1 dot", tabindex: 0, role: "img", "aria-label": `${MONTHS[i]}: ${SERIES[i]}` }));\n',
            "Hovering or focusing a point lights it: a drop-shadow in the series colour, with no change of size.",
            ".dot { outline: none; cursor: pointer; transition: filter .25s; }\n.dot:hover, .dot:focus-visible { filter: drop-shadow(0 0 4px var(--accent)) drop-shadow(0 0 12px var(--accent)); }\n",
            replay=False,
            sub="Hover a point",
        ),
        viz(
            "Data-point expansion",
            SCENE
            + 'axes();\nel("path", { d: path(points), class: "stroke s0" });\npoints.forEach(([px, py], i) => {\n  const group = el("g", { class: "pt", tabindex: 0, role: "img", "aria-label": `${MONTHS[i]}: ${SERIES[i]}` });\n  el("circle", { cx: px, cy: py, r: 16, fill: "transparent" }, undefined, group);  // a larger target than the visible dot\n  el("circle", { cx: px, cy: py, r: 4, class: "fill s0 dot" }, undefined, group);\n  el("text", { x: px, y: py - 16, class: "lbl mid" }, SERIES[i], group);\n});\n',
            "A point grows when approached and its value appears above it. The invisible hit area is much larger than the dot.",
            ".pt { outline: none; cursor: pointer; }\n.pt .dot { transform-box: fill-box; transform-origin: center; transition: scale .25s var(--ease); stroke: var(--surface); stroke-width: 0; }\n.pt text { opacity: 0; translate: 0 6px; transition: all .25s var(--ease); }\n.pt:hover .dot, .pt:focus-visible .dot { scale: 2; stroke-width: 1.5; }\n.pt:hover text, .pt:focus-visible text { opacity: 1; translate: 0 0; }\n",
            replay=False,
            sub="Hover a point",
        ),
        viz(
            "Chart zoom",
            TWEEN
            + """\
const DATA = Array.from({ length: 60 }, (_, i) => 50 + Math.sin(i / 4) * 22 + Math.sin(i / 1.3) * 8 + rand() * 8);
const y = linear(0, 100, H - M.bottom, M.top);
let view = [0, DATA.length - 1];
const render = ([from, to]) => {
  svg.replaceChildren();
  yAxis(y, 100);
  const x = linear(from, to, M.left, W - M.right);
  const clip = el("clipPath", { id: "plot" });
  el("rect", { x: M.left, y: 0, width: W - M.left - M.right, height: H }, undefined, clip);
  el("path", { d: path(DATA.map((value, i) => [x(i), y(value)])), class: "stroke s0", "clip-path": "url(#plot)" });
  for (let i = Math.ceil(from / 10) * 10; i <= to; i += 10) el("text", { x: x(i), y: H - 10, class: "tick mid" }, `d${i}`);
};
// Zooming changes the visible domain; the tween interpolates both ends so the chart scales smoothly.
const zoom = (factor) => {
  const [from, to] = view, middle = (from + to) / 2;
  const half = Math.min((DATA.length - 1) / 2, Math.max(4, ((to - from) / 2) * factor));
  const goal = [Math.max(0, middle - half), Math.min(DATA.length - 1, middle + half)];
  tween(350, (t) => render([mix(from, goal[0], t), mix(to, goal[1], t)]), () => { view = goal; });
};
document.querySelector(".in").addEventListener("click", () => zoom(0.5));
document.querySelector(".out").addEventListener("click", () => zoom(2));
svg.addEventListener("wheel", (event) => { event.preventDefault(); zoom(event.deltaY < 0 ? 0.7 : 1.4); }, { passive: false });
render(view);
""",
            "Zooming narrows the range of x shown. The change of range is animated, so the line stretches instead of jumping. Buttons or the wheel.",
            ".zoomer { position: absolute; top: 12px; right: 14px; display: flex; gap: 6px; }\n.zoomer button { width: 28px; height: 28px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); }\n",
            replay=False,
            extra='<div class="zoomer"><button class="in" aria-label="Zoom in">+</button><button class="out" aria-label="Zoom out">−</button></div>',
        ),
        viz(
            "Chart pan",
            """\
const DATA = Array.from({ length: 80 }, (_, i) => 50 + Math.sin(i / 5) * 24 + Math.sin(i / 1.7) * 9 + rand() * 6);
const SPAN = 20;
const y = linear(0, 100, H - M.bottom, M.top);
let from = 0, velocity = 0, dragging = false, lastX = 0;
const render = () => {
  svg.replaceChildren();
  yAxis(y, 100);
  const x = linear(from, from + SPAN, M.left, W - M.right);
  const clip = el("clipPath", { id: "plot" });
  el("rect", { x: M.left, y: 0, width: W - M.left - M.right, height: H }, undefined, clip);
  el("path", { d: path(DATA.map((value, i) => [x(i), y(value)])), class: "stroke s1", "clip-path": "url(#plot)" });
  for (let i = Math.ceil(from / 5) * 5; i <= from + SPAN; i += 5) el("text", { x: x(i), y: H - 10, class: "tick mid" }, `d${i}`);
};
const shift = (units) => { from = Math.min(DATA.length - 1 - SPAN, Math.max(0, from + units)); render(); };
const perPixel = () => SPAN / (svg.getBoundingClientRect().width * ((W - M.left - M.right) / W));
svg.addEventListener("pointerdown", (event) => { dragging = true; lastX = event.clientX; velocity = 0; svg.setPointerCapture(event.pointerId); });
svg.addEventListener("pointermove", (event) => {
  if (!dragging) return;
  velocity = (lastX - event.clientX) * perPixel();
  lastX = event.clientX;
  shift(velocity);
});
// On release the chart keeps moving and slows down, as if it had weight.
const coast = () => { if (dragging || Math.abs(velocity) < 0.01) return; shift(velocity); velocity *= 0.93; requestAnimationFrame(coast); };
const release = () => { dragging = false; if (!matchMedia("(prefers-reduced-motion: reduce)").matches) coast(); };
svg.addEventListener("pointerup", release);
svg.addEventListener("pointercancel", release);
svg.addEventListener("keydown", (event) => { if (event.key === "ArrowRight") shift(2); if (event.key === "ArrowLeft") shift(-2); });
render();
""",
            "Drag the chart sideways to move through the data; let go and it coasts to a stop. Arrow keys pan too.",
            "svg.plot { cursor: grab; touch-action: none; outline: none; }\nsvg.plot:active { cursor: grabbing; }\n",
            replay=False,
            sub="Drag sideways",
        ),
        viz(
            "Chart crosshair",
            SCENE
            + """\
axes();
el("path", { d: path(points), class: "stroke s0" });
const cross = el("g", { class: "cross", visibility: "hidden" });
const vertical = el("line", { y1: M.top, y2: H - M.bottom }, undefined, cross);
const horizontal = el("line", { x1: M.left, x2: W - M.right }, undefined, cross);
const yTag = el("text", { x: M.left - 8, class: "tag end" }, "", cross);
const xTag = el("text", { y: H - 10, class: "tag mid" }, "", cross);
svg.addEventListener("pointermove", (event) => {
  const box = svg.getBoundingClientRect();
  const px = Math.min(W - M.right, Math.max(M.left, ((event.clientX - box.left) / box.width) * W));
  const py = Math.min(H - M.bottom, Math.max(M.top, ((event.clientY - box.top) / box.height) * H));
  vertical.setAttribute("x1", px); vertical.setAttribute("x2", px);
  horizontal.setAttribute("y1", py); horizontal.setAttribute("y2", py);
  // Read the values back off the scales: pixel position to data value.
  yTag.setAttribute("y", py + 4); yTag.textContent = Math.round(max * (1 - (py - M.top) / (H - M.bottom - M.top)));
  xTag.setAttribute("x", px); xTag.textContent = MONTHS[Math.round(((px - M.left - 10) / (W - M.left - M.right - 20)) * (MONTHS.length - 1))] ?? "";
  cross.setAttribute("visibility", "visible");
});
svg.addEventListener("pointerleave", () => cross.setAttribute("visibility", "hidden"));
""",
            "Two hairlines follow the pointer and the axes report the exact value under each.",
            ".cross line { stroke: var(--muted); stroke-width: 1; stroke-dasharray: 3 3; }\n.tag { fill: var(--fg); font: 700 11px var(--font); paint-order: stroke; stroke: var(--surface); stroke-width: 5; }\nsvg.plot { cursor: crosshair; }\n",
            replay=False,
            sub="Move across the chart",
        ),
        viz(
            "Chart focus",
            """\
const LINES = [["Free", [20, 34, 30, 44, 52, 60, 58, 70]], ["Pro", [60, 72, 90, 84, 110, 126, 140, 150]], ["Team", [40, 38, 56, 70, 66, 92, 100, 118]]];
const x = linear(0, 7, M.left + 10, W - M.right - 40);
const y = linear(0, 160, H - M.bottom, M.top);
yAxis(y, 160);
xLabels(MONTHS, x);
LINES.forEach(([label, values], i) => {
  const group = el("g", { class: `series s${i}`, tabindex: 0, role: "img", "aria-label": `${label}: ${values.join(", ")}` });
  const line = values.map((value, index) => [x(index), y(value)]);
  el("path", { d: path(line), class: "wide" }, undefined, group);   // an invisible thick stroke, easier to hit
  el("path", { d: path(line), class: "stroke" }, undefined, group);
  el("text", { x: line.at(-1)[0] + 8, y: line.at(-1)[1] + 4, class: "lbl" }, label, group);
});
""",
            "Pointing at one series pushes the others back: they fade, so the one of interest can be followed across the chart.",
            ".series { outline: none; cursor: pointer; transition: opacity .25s; }\n.wide { fill: none; stroke: transparent; stroke-width: 18; }\nsvg.plot:has(.series:hover) .series:not(:hover), svg.plot:has(.series:focus-visible) .series:not(:focus-visible) { opacity: .18; }\n.series:hover .stroke, .series:focus-visible .stroke { stroke-width: 4; }\n",
            replay=False,
            sub="Hover a line",
        ),
        viz(
            "Chart selection highlight",
            BARS
            + """\
axes();
const bars = SERIES.map((value, i) => bar(i, value, { tabindex: 0, role: "button", "aria-pressed": "false", "aria-label": `${MONTHS[i]}: ${value}` }));
const label = el("text", { class: "lbl mid", visibility: "hidden" });
const pick = (index) => {
  const already = bars[index].getAttribute("aria-pressed") === "true";
  bars.forEach((rect, i) => rect.setAttribute("aria-pressed", !already && i === index));
  svg.classList.toggle("picked", !already);
  label.setAttribute("visibility", already ? "hidden" : "visible");
  label.setAttribute("x", centre(index)); label.setAttribute("y", y(SERIES[index]) - 8);
  label.textContent = SERIES[index];
};
bars.forEach((rect, index) => {
  rect.addEventListener("click", () => pick(index));
  rect.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); pick(index); } });
});
pick(5);
""",
            "Click a bar to select it: it takes the accent colour and shows its value, and every other bar recedes. Click again to clear.",
            'rect.fill { cursor: pointer; outline: none; transition: opacity .25s, fill .25s; }\n.picked rect.fill { opacity: .25; }\n.picked rect.fill[aria-pressed="true"] { opacity: 1; fill: var(--accent); }\nrect.fill:focus-visible { stroke: var(--fg); stroke-width: 2; }\n',
            replay=False,
            sub="Click a bar",
        ),
        viz(
            "Chart comparison transition",
            BARS
            + TWEEN
            + """\
const LAST_YEAR = [90, 140, 170, 160, 250, 220, 310, 290];
axes();
const ghosts = SERIES.map((value, i) => bar(i, value, { class: "ghost" }));
const bars = SERIES.map((value, i) => bar(i, value));
let current = SERIES;
const set = (rect, value) => { rect.setAttribute("y", y(value)); rect.setAttribute("height", y(0) - y(value)); };
// The outline keeps the series being left, so the difference stays visible after the bars have moved.
const compare = (next) => {
  const from = current;
  ghosts.forEach((rect, i) => set(rect, from[i]));
  tween(600, (t) => bars.forEach((rect, i) => set(rect, mix(from[i], next[i], t))), () => { current = next; });
};
const toggle = document.querySelector(".again");
toggle.addEventListener("click", () => { const next = current === SERIES ? LAST_YEAR : SERIES; toggle.textContent = next === SERIES ? "Show last year" : "Show this year"; compare(next); });
""",
            "Switching period, each bar travels to its new height and leaves a dashed outline where it was, so the change can be read off directly.",
            ".ghost { fill: none; stroke: var(--muted); stroke-width: 1; stroke-dasharray: 3 3; }\n",
            replay=False,
            extra='<button class="again">Show last year</button>',
        ),
        viz(
            "Chart filtering animation",
            TWEEN
            + """\
const ITEMS = [["Docs", 64, "a"], ["Blog", 38, "b"], ["Pricing", 82, "a"], ["Guides", 51, "b"], ["Home", 96, "a"], ["Changelog", 27, "b"]];
const y = linear(0, 100, H - M.bottom, M.top);
yAxis(y, 100);
const groups = ITEMS.map(([label, value]) => {
  const group = el("g");
  el("rect", { y: y(value), height: y(0) - y(value), rx: 4, class: "fill s0" }, undefined, group);
  el("text", { y: H - 10, class: "tick mid" }, label, group);
  return group;
});
// Each bar has a slot (x, width) and a presence (0..1); filtering changes both for everything that remains.
let state = ITEMS.map(() => ({ x: 0, width: 0, presence: 0 }));
const layout = (kind) => {
  const kept = ITEMS.map(([, , group]) => kind === "all" || group === kind);
  const band = (W - M.left - M.right) / kept.filter(Boolean).length;
  let slot = 0;
  return ITEMS.map((_, i) => (kept[i] ? { x: M.left + band * (slot++ + 0.5), width: band * 0.6, presence: 1 } : { x: state[i].x, width: 0, presence: 0 }));
};
const paint = (values) => values.forEach(({ x: cx, width, presence }, i) => {
  const [rect, text] = groups[i].children;
  rect.setAttribute("x", cx - width / 2); rect.setAttribute("width", Math.max(0, width));
  text.setAttribute("x", cx);
  groups[i].style.opacity = presence;
});
const filter = (kind) => {
  const from = state, to = layout(kind);
  tween(500, (t) => paint(from.map((a, i) => ({ x: mix(a.x || to[i].x, to[i].x, t), width: mix(a.width, to[i].width, t), presence: mix(a.presence, to[i].presence, t) }))), () => { state = to; });
};
document.querySelectorAll(".chips button").forEach((chip) => chip.addEventListener("click", () => {
  document.querySelectorAll(".chips button").forEach((other) => other.setAttribute("aria-pressed", other === chip));
  filter(chip.dataset.kind);
}));
filter("all");
""",
            "Filtered-out bars narrow to nothing and fade, while the bars that remain slide and widen to share the freed space.",
            '.chips { position: absolute; top: 12px; right: 14px; display: flex; gap: 6px; }\n.chips button { padding: 4px 10px; border: 1px solid var(--border); border-radius: 99px; background: none; font-size: 12px; }\n.chips button[aria-pressed="true"] { background: var(--primary); border-color: var(--primary); color: #fff; }\n',
            replay=False,
            extra='<div class="chips"><button data-kind="all" aria-pressed="true">All</button><button data-kind="a" aria-pressed="false">Product</button><button data-kind="b" aria-pressed="false">Content</button></div>',
        ),
        viz(
            "Chart morphing",
            BARS
            + TWEEN
            + """\
axes();
const DOT = 10;
const line = el("path", { d: path(SERIES.map((value, i) => [centre(i), y(value)])), class: "stroke s0 line", pathLength: 1 });
const bars = SERIES.map((value, i) => bar(i, value));
let asLine = false, amount = 0;
// amount 0 = bars, 1 = dots: each bar's width, height and corner radius shrink toward a dot at its top.
const paint = (t) => bars.forEach((rect, i) => {
  const width = mix(band * 0.6, DOT, t), height = mix(y(0) - y(SERIES[i]), DOT, t);
  rect.setAttribute("x", centre(i) - width / 2); rect.setAttribute("width", width);
  rect.setAttribute("y", y(SERIES[i]) - (DOT / 2) * t); rect.setAttribute("height", height);
  rect.setAttribute("rx", mix(4, DOT / 2, t));
});
const toggle = document.querySelector(".again");
toggle.addEventListener("click", () => {
  asLine = !asLine;
  toggle.textContent = asLine ? "Show bars" : "Show line";
  svg.classList.toggle("lined", asLine);
  const from = amount, to = asLine ? 1 : 0;
  tween(600, (t) => { amount = mix(from, to, t); paint(amount); });
});
""",
            "One chart type becomes another: each bar shrinks into a dot at its own top, and a line is then drawn through the dots. The data never leaves the screen.",
            ".line { stroke-dasharray: 1; stroke-dashoffset: 1; transition: stroke-dashoffset .3s ease-in; }\n.lined .line { stroke-dashoffset: 0; transition: stroke-dashoffset .7s .45s var(--ease); }\n",
            replay=False,
            extra='<button class="again">Show line</button>',
        ),
        viz(
            "Chart stacking animation",
            TWEEN
            + """\
const QUARTERS = ["Q1", "Q2", "Q3", "Q4"];
const STACK = [[40, 30, 20], [55, 35, 25], [50, 45, 30], [70, 50, 40]];  // three series per quarter
const y = linear(0, 160, H - M.bottom, M.top);
const band = (W - M.left - M.right) / QUARTERS.length;
yAxis(y, 160);
QUARTERS.forEach((label, q) => el("text", { x: M.left + band * (q + 0.5), y: H - 10, class: "tick mid" }, label));
const rects = STACK.map((values) => values.map((_, s) => el("rect", { rx: 3, class: `fill s${s}` })));
// Stacked: full width, each segment sitting on the ones before. Grouped: a third of the width, side by side on the axis.
const place = (q, s, t) => {
  const below = STACK[q].slice(0, s).reduce((sum, value) => sum + value, 0);
  const left = M.left + band * q + band * 0.15, full = band * 0.7, slim = full / 3 - 2;
  return { x: mix(left, left + s * (slim + 3), t), width: mix(full, slim, t), y: y(mix(below, 0, t) + STACK[q][s]), height: y(0) - y(STACK[q][s]) };
};
const paint = (t) => rects.forEach((row, q) => row.forEach((rect, s) => { for (const [key, value] of Object.entries(place(q, s, t))) rect.setAttribute(key, value); }));
let grouped = false, amount = 0;
const toggle = document.querySelector(".again");
toggle.addEventListener("click", () => {
  grouped = !grouped;
  toggle.textContent = grouped ? "Stack" : "Group";
  const from = amount, to = grouped ? 1 : 0;
  tween(600, (t) => { amount = mix(from, to, t); paint(amount); });
});
paint(0);
""",
            "Stacked segments come down off one another and stand side by side on the axis, and go back: totals in one view, comparisons in the other.",
            replay=False,
            extra='<button class="again">Group</button>',
        ),
        viz(
            "Chart sorting animation",
            BARS
            + """\
yAxis(y, max);
const groups = SERIES.map((value, i) => {
  const group = el("g", { class: "slot" });
  el("rect", { x: -band * 0.3, width: band * 0.6, y: y(value), height: y(0) - y(value), rx: 4, class: "fill s0" }, undefined, group);
  el("text", { x: 0, y: H - 10, class: "tick mid" }, MONTHS[i], group);
  return group;
});
// Each bar is a group positioned by a transform, so reordering is only a change of translate, which CSS animates.
const arrange = (order) => order.forEach((index, position) => { groups[index].style.translate = `${centre(position)}px 0`; groups[index].style.transitionDelay = `${position * 40}ms`; });
const byTime = SERIES.map((_, i) => i);
const byValue = [...byTime].sort((a, b) => SERIES[b] - SERIES[a]);
let sorted = false;
const toggle = document.querySelector(".again");
toggle.addEventListener("click", () => { sorted = !sorted; toggle.textContent = sorted ? "Sort by month" : "Sort by value"; arrange(sorted ? byValue : byTime); });
arrange(byTime);
""",
            "Bars slide past each other to their new places, so the eye can follow where each one went.",
            ".slot { transition: translate .6s var(--ease); }\n",
            replay=False,
            extra='<button class="again">Sort by value</button>',
        ),
        viz(
            "Chart reordering",
            CALM
            + """\
const TEAMS = [["Atlas", 62], ["Borealis", 58], ["Cobalt", 51], ["Delta", 44], ["Echo", 39]].map(([name, score], i) => ({ name, score, i }));
const ROW = 40, LEFT = 86;
const rows = TEAMS.map((team) => {
  const group = el("g", { class: "row" });
  team.label = el("text", { x: LEFT - 10, y: 24, class: "lbl end" }, team.name, group);
  team.bar = el("rect", { x: LEFT, y: 8, height: 24, rx: 5, class: `fill s${team.i}` }, undefined, group);
  team.figure = el("text", { y: 24, class: "tick" }, "", group);
  team.group = group;
  return group;
});
const x = linear(0, 100, 0, W - LEFT - 50);
const paint = () => {
  // Rank decides the row; the bar's length and the row's position both animate through CSS.
  [...TEAMS].sort((a, b) => b.score - a.score).forEach((team, rank) => { team.group.style.translate = `0 ${20 + rank * ROW}px`; });
  TEAMS.forEach((team) => { team.bar.style.width = `${x(team.score)}px`; team.figure.style.translate = `${LEFT + x(team.score) + 8}px 0`; team.figure.textContent = Math.round(team.score); });
};
paint();
if (!calm) setInterval(() => { TEAMS.forEach((team) => { team.score = Math.min(100, Math.max(10, team.score + (rand() - 0.42) * 16)); }); paint(); }, 1300);
""",
            "A bar-chart race: values change on a timer, bars lengthen or shorten, and rows overtake one another as their rank changes.",
            ".row { transition: translate .8s var(--ease); }\n.row rect { transition: width .8s var(--ease); }\n.row .tick { transition: translate .8s var(--ease); }\n",
            replay=False,
        ),
        viz(
            "Chart interpolation",
            TWEEN
            + """\
const y = linear(0, 100, H - M.bottom, M.top);
const x = linear(0, 11, M.left + 10, W - M.right - 10);
yAxis(y, 100);
const line = el("path", { class: "stroke s1" });
const sample = () => Array.from({ length: 12 }, (_, i) => 30 + Math.sin(i / 2 + rand() * 4) * 22 + rand() * 30);
let shown = sample();
const draw = (values) => line.setAttribute("d", path(values.map((value, i) => [x(i), y(value)])));
// Every point is interpolated between its old and new value, so the old shape bends into the new one.
const play = () => { const from = shown, to = sample(); tween(700, (t) => { shown = from.map((value, i) => mix(value, to[i], t)); draw(shown); }); };
draw(shown);
""",
            "New data does not replace the line; the line bends into its new shape, each point travelling from its old value to its new one.",
        ),
    ),
)
