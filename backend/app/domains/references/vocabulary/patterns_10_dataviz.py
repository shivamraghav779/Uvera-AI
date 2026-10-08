"""Patterns 331-370: data visualisation, drawn into SVG from data."""

from app.domains.references.vocabulary.base import Item, Section

CH = """\
.ch { width: min(520px, 100%); margin: 0; padding: 14px 16px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); position: relative; }
.ch figcaption { margin-bottom: 8px; font-weight: 600; }
.ch figcaption small { display: block; font-weight: 400; color: var(--muted); }
svg.plot { display: block; width: 100%; height: auto; overflow: visible; }
.grid { stroke: var(--border); stroke-width: 1; }
.tick { fill: var(--muted); font: 11px var(--font); }
.end { text-anchor: end; }
.mid { text-anchor: middle; }
.lbl { fill: var(--fg); font: 600 11px var(--font); }
.s0 { --c: var(--primary); } .s1 { --c: var(--accent); } .s2 { --c: #f472b6; } .s3 { --c: var(--warning); } .s4 { --c: var(--success); }
.fill { fill: var(--c); }
.soft { fill: color-mix(in srgb, var(--c) 24%, transparent); }
.stroke { fill: none; stroke: var(--c); stroke-width: 2.5; stroke-linejoin: round; stroke-linecap: round; }
.tip { position: absolute; padding: 5px 9px; border-radius: 8px; background: var(--fg); color: var(--bg); font-size: 12px; font-weight: 600;
  pointer-events: none; translate: -50% -130%; white-space: nowrap; }
.tip[hidden] { display: none; }
"""
# A few lines of scales and axes: enough for every chart here, small enough to read.
KIT = r"""const NS = "http://www.w3.org/2000/svg";
const svg = document.querySelector("svg.plot");
const W = 480, H = 260, M = { top: 16, right: 16, bottom: 30, left: 44 };
const el = (name, attrs = {}, text, parent = svg) => {
  const node = document.createElementNS(NS, name);
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  parent.append(node);
  return node;
};
const linear = (d0, d1, r0, r1) => (value) => r0 + ((value - d0) / (d1 - d0 || 1)) * (r1 - r0);
const niceMax = (max) => { const step = 10 ** Math.floor(Math.log10(max || 1)); return Math.ceil(max / step) * step; };
const fmt = (value) => Math.abs(value) >= 1000 ? `${+(value / 1000).toFixed(1)}k` : String(+value.toFixed(1));
const path = (points) => points.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join("");
const yAxis = (y, max, ticks = 4, min = 0) => {
  for (let i = 0; i <= ticks; i += 1) {
    const value = min + ((max - min) / ticks) * i;
    el("line", { x1: M.left, x2: W - M.right, y1: y(value), y2: y(value), class: "grid" });
    el("text", { x: M.left - 8, y: y(value) + 4, class: "tick end" }, fmt(value));
  }
};
const xLabels = (labels, x) => labels.forEach((label, i) => el("text", { x: x(i), y: H - 10, class: "tick mid" }, label));
const polar = (cx, cy, r, angle) => [cx + r * Math.cos(angle - Math.PI / 2), cy + r * Math.sin(angle - Math.PI / 2)];
const arc = (cx, cy, r, a0, a1) => {
  const [x0, y0] = polar(cx, cy, r, a0), [x1, y1] = polar(cx, cy, r, a1);
  return `M${x0.toFixed(1)} ${y0.toFixed(1)}A${r} ${r} 0 ${a1 - a0 > Math.PI ? 1 : 0} 1 ${x1.toFixed(1)} ${y1.toFixed(1)}`;
};
// Repeatable pseudo-random numbers, so a chart looks the same on every load.
let seed = 7;
const rand = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"];
const SERIES = [120, 180, 150, 240, 210, 300, 280, 360];
"""
CART = r"""const max = niceMax(Math.max(...SERIES));
const x = linear(0, SERIES.length - 1, M.left + 10, W - M.right - 10);
const y = linear(0, max, H - M.bottom, M.top);
yAxis(y, max);
xLabels(MONTHS, x);
const points = SERIES.map((value, i) => [x(i), y(value)]);
"""
BAND = r"""const band = (W - M.left - M.right) / MONTHS.length;
const centre = (i) => M.left + band * (i + 0.5);
"""


def chart(
    name: str,
    caption: str,
    js: str,
    note: str,
    css: str = "",
    sub: str = "",
    extra: str = "",
    view: str = "0 0 480 260",
) -> Item:
    small = f"<small>{sub}</small>" if sub else ""
    html = f'<figure class="ch"><figcaption>{caption}{small}</figcaption><svg class="plot" viewBox="{view}" role="img" aria-label="{caption}"></svg>{extra}</figure>'
    return Item(name, html, CH + css, KIT + js, note)


def plain(name: str, html: str, css: str, note: str, js: str = "") -> Item:
    return Item(name, html, css, js, note)


SECTION = Section(
    "patterns",
    "Data Visualization",
    331,
    (
        chart(
            "Line chart",
            "Sign-ups per month",
            CART
            + r"""el("path", { d: path(points), class: "stroke s0" });
points.forEach(([px, py]) => el("circle", { cx: px, cy: py, r: 3.5, class: "fill s0" }));
""",
            "A value over time: gridlines, a nice maximum, a point at each observation.",
        ),
        chart(
            "Area chart",
            "Active users",
            CART
            + r"""el("path", { d: `${path(points)}L${x(SERIES.length - 1)} ${y(0)}L${x(0)} ${y(0)}Z`, class: "soft s0" });
el("path", { d: path(points), class: "stroke s0" });
""",
            "A line with the area to the baseline filled: volume as well as trend.",
        ),
        chart(
            "Bar chart",
            "Orders per month",
            BAND
            + r"""const max = niceMax(Math.max(...SERIES));
const y = linear(0, max, H - M.bottom, M.top);
yAxis(y, max);
xLabels(MONTHS, centre);
SERIES.forEach((value, i) => el("rect", { x: centre(i) - band * 0.3, y: y(value), width: band * 0.6, height: y(0) - y(value), rx: 4, class: "fill s0" }));
""",
            "Bars always start at zero; width is 60% of the band.",
        ),
        chart(
            "Horizontal bar chart",
            "Revenue by region",
            r"""const DATA = [["EMEA", 74], ["Americas", 68], ["APAC", 40], ["LATAM", 22], ["Africa", 11]];
const max = niceMax(Math.max(...DATA.map(([, value]) => value)));
const x = linear(0, max, 90, W - 40);
const row = (H - 20) / DATA.length;
DATA.forEach(([label, value], i) => {
  const top = 10 + i * row;
  el("text", { x: 82, y: top + row / 2 + 4, class: "tick end" }, label);
  el("rect", { x: 90, y: top + row * 0.2, width: x(value) - 90, height: row * 0.6, rx: 4, class: "fill s0" });
  el("text", { x: x(value) + 6, y: top + row / 2 + 4, class: "lbl" }, `$${value}k`);
});
""",
            "Sorted longest first, labels to the left, values at the bar ends: best for named categories.",
        ),
        chart(
            "Stacked bar chart",
            "Revenue by plan",
            BAND
            + r"""const PLANS = [[40, 52, 48, 70, 66, 90, 84, 110], [50, 70, 60, 90, 80, 120, 110, 140], [30, 58, 42, 80, 64, 90, 86, 110]];
const totals = MONTHS.map((_, i) => PLANS.reduce((sum, plan) => sum + plan[i], 0));
const max = niceMax(Math.max(...totals));
const y = linear(0, max, H - M.bottom, M.top);
yAxis(y, max);
xLabels(MONTHS, centre);
MONTHS.forEach((_, i) => {
  let base = 0;
  PLANS.forEach((plan, s) => {
    el("rect", { x: centre(i) - band * 0.3, y: y(base + plan[i]), width: band * 0.6, height: y(base) - y(base + plan[i]), class: `fill s${s}` });
    base += plan[i];
  });
});
""",
            "Parts stacked into a total: read the whole first, the bottom series second.",
        ),
        chart(
            "Grouped bar chart",
            "This year vs last",
            BAND
            + r"""const GROUPS = [SERIES, [90, 140, 160, 200, 190, 240, 260, 300]];
const max = niceMax(Math.max(...GROUPS.flat()));
const y = linear(0, max, H - M.bottom, M.top);
yAxis(y, max);
xLabels(MONTHS, centre);
const width = (band * 0.7) / GROUPS.length;
GROUPS.forEach((group, s) => group.forEach((value, i) =>
  el("rect", { x: centre(i) - band * 0.35 + s * width, y: y(value), width: width - 2, height: y(0) - y(value), rx: 3, class: `fill s${s}` })));
""",
            "Series side by side within each category, for comparing like with like.",
        ),
        chart(
            "Histogram",
            "Response time distribution",
            r"""// 400 samples around 220 ms, binned into 14 equal intervals.
const samples = Array.from({ length: 400 }, () => 220 + (rand() + rand() + rand() - 1.5) * 180);
const BINS = 14, low = Math.min(...samples), high = Math.max(...samples);
const counts = new Array(BINS).fill(0);
for (const sample of samples) counts[Math.min(BINS - 1, Math.floor(((sample - low) / (high - low)) * BINS))] += 1;
const max = niceMax(Math.max(...counts));
const x = linear(0, BINS, M.left, W - M.right), y = linear(0, max, H - M.bottom, M.top);
yAxis(y, max);
counts.forEach((count, i) => el("rect", { x: x(i) + 0.5, y: y(count), width: x(1) - x(0) - 1, height: y(0) - y(count), class: "fill s1" }));
for (let i = 0; i <= BINS; i += 2) el("text", { x: x(i), y: H - 10, class: "tick mid" }, `${Math.round(low + ((high - low) / BINS) * i)}`);
""",
            "Bars touch because the axis is continuous; each bar is a range, not a category.",
            sub="milliseconds",
        ),
        chart(
            "Scatter plot",
            "Seats vs monthly spend",
            r"""const dots = Array.from({ length: 60 }, () => { const seats = 2 + rand() * 48; return [seats, seats * 22 + (rand() - 0.5) * 500]; });
const x = linear(0, 50, M.left, W - M.right), y = linear(0, 1500, H - M.bottom, M.top);
yAxis(y, 1500, 3);
for (let seats = 0; seats <= 50; seats += 10) el("text", { x: x(seats), y: H - 10, class: "tick mid" }, String(seats));
dots.forEach(([seats, spend]) => el("circle", { cx: x(seats), cy: y(Math.max(0, spend)), r: 4, class: "fill s0", "fill-opacity": 0.65 }));
""",
            "One dot per observation on two numeric axes; translucency shows where they pile up.",
        ),
        chart(
            "Bubble chart",
            "Accounts by size, growth and revenue",
            r"""const dots = Array.from({ length: 16 }, () => [5 + rand() * 90, rand() * 40 - 5, 4 + rand() * 22]);
const x = linear(0, 100, M.left, W - M.right), y = linear(-10, 40, H - M.bottom, M.top);
yAxis(y, 40, 5, -10);
for (let value = 0; value <= 100; value += 25) el("text", { x: x(value), y: H - 10, class: "tick mid" }, String(value));
// Largest first, so small bubbles are never hidden behind big ones.
dots.sort((a, b) => b[2] - a[2]).forEach(([seats, growth, size], i) =>
  el("circle", { cx: x(seats), cy: y(growth), r: size, class: `fill s${i % 3}`, "fill-opacity": 0.55, stroke: "var(--surface)" }));
""",
            "A scatter plot with a third measure as area; draw large bubbles first.",
        ),
        chart(
            "Pie chart",
            "Traffic by source",
            r"""const DATA = [["Search", 46], ["Direct", 27], ["Social", 17], ["Email", 10]];
const total = DATA.reduce((sum, [, value]) => sum + value, 0);
let angle = 0;
DATA.forEach(([label, value], i) => {
  const next = angle + (value / total) * Math.PI * 2;
  el("path", { d: `${arc(150, 130, 100, angle, next)}L150 130Z`, class: `fill s${i}`, stroke: "var(--surface)", "stroke-width": 2 });
  const [tx, ty] = polar(150, 130, 62, (angle + next) / 2);
  el("text", { x: tx, y: ty + 4, class: "lbl mid", fill: "#fff" }, `${Math.round((value / total) * 100)}%`);
  el("rect", { x: 300, y: 70 + i * 28, width: 12, height: 12, rx: 3, class: `fill s${i}` });
  el("text", { x: 320, y: 81 + i * 28, class: "tick" }, label);
  angle = next;
});
""",
            "Parts of one whole, at most five slices, starting at twelve o'clock, labelled with shares.",
        ),
        chart(
            "Donut chart",
            "Storage used",
            r"""const DATA = [["Documents", 18], ["Media", 12], ["Backups", 7], ["Free", 13]];
const total = DATA.reduce((sum, [, value]) => sum + value, 0);
let angle = 0;
DATA.forEach(([label, value], i) => {
  const next = angle + (value / total) * Math.PI * 2;
  // A thick stroke along an arc makes the ring; a small gap separates the parts.
  el("path", { d: arc(150, 130, 84, angle + 0.02, next - 0.02), class: `stroke s${i}`, style: "stroke-width: 28px; stroke-linecap: butt", opacity: label === "Free" ? 0.25 : 1 });
  el("rect", { x: 300, y: 70 + i * 28, width: 12, height: 12, rx: 3, class: `fill s${i}` });
  el("text", { x: 320, y: 81 + i * 28, class: "tick" }, `${label} · ${value} GB`);
  angle = next;
});
el("text", { x: 150, y: 128, class: "mid", fill: "var(--fg)", "font-size": 26, "font-weight": 700 }, `${total - 13} GB`);
el("text", { x: 150, y: 148, class: "tick mid" }, `of ${total} GB`);
""",
            "A pie with the middle used for the total; the remainder is drawn faint.",
        ),
        chart(
            "Radar chart",
            "Skills profile",
            r"""const AXES = ["Design", "Code", "Research", "Writing", "Data", "Strategy"];
const SETS = [[8, 6, 7, 9, 5, 7], [5, 9, 4, 6, 8, 6]];
const cx = 240, cy = 132, R = 100;
const spot = (i, value) => polar(cx, cy, (value / 10) * R, (i / AXES.length) * Math.PI * 2);
for (let ring = 2; ring <= 10; ring += 2) el("polygon", { points: AXES.map((_, i) => spot(i, ring).join(",")).join(" "), fill: "none", class: "grid" });
AXES.forEach((label, i) => {
  const [ex, ey] = spot(i, 10), [tx, ty] = spot(i, 11.6);
  el("line", { x1: cx, y1: cy, x2: ex, y2: ey, class: "grid" });
  el("text", { x: tx, y: ty + 4, class: "tick mid" }, label);
});
SETS.forEach((values, s) => {
  const shape = values.map((value, i) => spot(i, value).join(",")).join(" ");
  el("polygon", { points: shape, class: `soft s${s}` });
  el("polygon", { points: shape, class: `stroke s${s}` });
});
""",
            "Several measures on spokes from one centre; good for profiles, poor for exact reading.",
        ),
        chart(
            "Funnel chart",
            "Checkout funnel",
            r"""const STEPS = [["Visited", 12400], ["Added to cart", 4300], ["Started checkout", 2100], ["Paid", 1480]];
const rowH = (H - 20) / STEPS.length, mid = 240, maxW = 380;
STEPS.forEach(([label, value], i) => {
  const top = (value / STEPS[0][1]) * maxW, bottom = ((STEPS[i + 1]?.[1] ?? value) / STEPS[0][1]) * maxW;
  const y0 = 10 + i * rowH, y1 = y0 + rowH - 6;
  el("polygon", { points: `${mid - top / 2},${y0} ${mid + top / 2},${y0} ${mid + bottom / 2},${y1} ${mid - bottom / 2},${y1}`, class: "fill s0", "fill-opacity": 1 - i * 0.18 });
  el("text", { x: mid, y: y0 + rowH / 2, class: "lbl mid", fill: "#fff" }, `${label} · ${value.toLocaleString()}`);
  if (i > 0) el("text", { x: W - 8, y: y0 + rowH / 2, class: "tick end" }, `${Math.round((value / STEPS[i - 1][1]) * 100)}% of previous`);
});
""",
            "Stages narrowing in proportion to who remains, with the step-to-step conversion beside each.",
        ),
        chart(
            "Waterfall chart",
            "From last quarter to this",
            r"""const STEPS = [["Q2", 420, "total"], ["New", 90], ["Expansion", 60], ["Churn", -70], ["Downgrade", -30], ["Q3", 0, "total"]];
let running = 0;
const bars = STEPS.map(([label, change, kind]) => {
  if (kind === "total" && change === 0) return { label, from: 0, to: running, kind };
  const from = kind === "total" ? 0 : running;
  running = kind === "total" ? change : running + change;
  return { label, from, to: running, kind: kind ?? (change >= 0 ? "up" : "down") };
});
const max = niceMax(Math.max(...bars.map((bar) => Math.max(bar.from, bar.to))));
const band = (W - M.left - M.right) / bars.length, y = linear(0, max, H - M.bottom, M.top);
yAxis(y, max);
bars.forEach((bar, i) => {
  const x0 = M.left + i * band + band * 0.2;
  el("rect", { x: x0, y: y(Math.max(bar.from, bar.to)), width: band * 0.6, height: Math.abs(y(bar.from) - y(bar.to)), rx: 3, class: `fill ${bar.kind === "total" ? "s0" : bar.kind === "up" ? "s4" : "s2"}` });
  el("text", { x: x0 + band * 0.3, y: H - 10, class: "tick mid" }, bar.label);
  // A hairline carries each running total to the next bar.
  if (i < bars.length - 1) el("line", { x1: x0 + band * 0.6, x2: x0 + band, y1: y(bar.to), y2: y(bar.to), class: "grid", "stroke-dasharray": "3 3" });
});
""",
            "How a starting total becomes an ending one: gains up, losses down, joined by their running total.",
        ),
        chart(
            "Sankey diagram",
            "Where visitors go",
            r"""const LINKS = [["Search", "Pricing", 40], ["Search", "Docs", 25], ["Direct", "Pricing", 15], ["Direct", "Sign up", 20], ["Social", "Docs", 12], ["Social", "Sign up", 8]];
const sum = (side, name) => LINKS.filter((link) => link[side] === name).reduce((total, link) => total + link[2], 0);
const column = (side, x) => {
  const names = [...new Set(LINKS.map((link) => link[side]))];
  const scale = (H - 30 - (names.length - 1) * 12) / LINKS.reduce((total, link) => total + link[2], 0);
  let top = 15;
  return Object.fromEntries(names.map((name) => { const height = sum(side, name) * scale; const node = { x, top, height, used: 0, scale }; top += height + 12; return [name, node]; }));
};
const left = column(0, 70), right = column(1, W - 82);
LINKS.forEach(([from, to, value], i) => {
  const a = left[from], b = right[to], thickness = value * a.scale;
  const y0 = a.top + a.used + thickness / 2, y1 = b.top + b.used + thickness / 2;
  a.used += thickness; b.used += thickness;
  el("path", { d: `M${a.x + 12} ${y0}C${W / 2} ${y0} ${W / 2} ${y1} ${b.x} ${y1}`, fill: "none", stroke: "var(--primary)", "stroke-opacity": 0.3, "stroke-width": thickness });
});
for (const [nodes, anchor, dx] of [[left, "end", -6], [right, "start", 18]]) for (const [name, node] of Object.entries(nodes)) {
  el("rect", { x: node.x, y: node.top, width: 12, height: node.height, rx: 3, class: "fill s0" });
  el("text", { x: node.x + dx, y: node.top + node.height / 2 + 4, class: "tick", "text-anchor": anchor }, name);
}
""",
            "Flows between two sets of nodes; the thickness of each band is its quantity.",
        ),
        chart(
            "Treemap",
            "Bundle size by package",
            r"""const DATA = [["react-dom", 130], ["charts", 96], ["editor", 74], ["app code", 60], ["icons", 38], ["date lib", 26], ["utils", 14]];
// Slice-and-dice: split the remaining rectangle along its longer side, largest item first.
const layout = (items, x, y, w, h, out = []) => {
  if (items.length === 0) return out;
  const total = items.reduce((sum, [, value]) => sum + value, 0);
  const [name, value] = items[0], share = value / total;
  if (w >= h) { out.push([name, value, x, y, w * share, h]); layout(items.slice(1), x + w * share, y, w * (1 - share), h, out); }
  else { out.push([name, value, x, y, w, h * share]); layout(items.slice(1), x, y + h * share, w, h * (1 - share), out); }
  return out;
};
layout(DATA, 4, 4, W - 8, H - 8).forEach(([name, value, x, y, w, h], i) => {
  el("rect", { x: x + 1.5, y: y + 1.5, width: Math.max(0, w - 3), height: Math.max(0, h - 3), rx: 5, class: "fill s0", "fill-opacity": 1 - i * 0.11 });
  if (w > 56 && h > 30) { el("text", { x: x + 9, y: y + 20, class: "lbl", fill: "#fff" }, name); el("text", { x: x + 9, y: y + 35, fill: "#fff", "font-size": 11, opacity: 0.8 }, `${value} kB`); }
});
""",
            "Nested rectangles sized by value; labels appear only where they fit.",
        ),
        chart(
            "Heatmap",
            "Activity by hour and day",
            r"""const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const cellW = (W - 50) / 24, cellH = (H - 40) / 7;
DAYS.forEach((day, d) => {
  el("text", { x: 38, y: 14 + d * cellH + cellH / 2, class: "tick end" }, day);
  for (let hour = 0; hour < 24; hour += 1) {
    // Busy in working hours on weekdays, quiet otherwise.
    const value = Math.max(0, Math.sin(((hour - 6) / 14) * Math.PI)) * (d < 5 ? 1 : 0.35) * (0.6 + rand() * 0.4);
    el("rect", { x: 46 + hour * cellW, y: 6 + d * cellH, width: cellW - 2, height: cellH - 2, rx: 3, fill: "var(--primary)", "fill-opacity": 0.08 + value * 0.92 });
  }
});
for (let hour = 0; hour < 24; hour += 4) el("text", { x: 46 + hour * cellW + cellW / 2, y: H - 8, class: "tick mid" }, `${String(hour).padStart(2, "0")}:00`);
""",
            "A grid where colour intensity is the value: patterns across two dimensions at a glance.",
        ),
        chart(
            "Calendar heatmap",
            "Contributions, last 20 weeks",
            r"""const WEEKS = 20, size = 16, gap = 4;
const today = new Date();
const start = new Date(today); start.setDate(today.getDate() - (WEEKS * 7 - 1) - ((today.getDay() + 6) % 7));
["Mon", "Wed", "Fri"].forEach((day, i) => el("text", { x: 30, y: 36 + i * 2 * (size + gap), class: "tick end" }, day));
for (let i = 0; i < WEEKS * 7 + ((today.getDay() + 6) % 7) + 1; i += 1) {
  const date = new Date(start); date.setDate(start.getDate() + i);
  if (date > today) break;
  const level = [0, 0, 1, 1, 2, 3, 4][Math.floor(rand() * 7)];
  const week = Math.floor(i / 7), day = i % 7;
  const cell = el("rect", { x: 38 + week * (size + gap), y: 22 + day * (size + gap), width: size, height: size, rx: 4, fill: level ? "var(--success)" : "var(--surface-2)", "fill-opacity": level ? 0.25 + level * 0.19 : 1 });
  el("title", {}, `${date.toDateString()}: ${level * 3} contributions`, cell);
  if (date.getDate() <= 7 && day === 0) el("text", { x: 38 + week * (size + gap), y: 14, class: "tick" }, date.toLocaleDateString(undefined, { month: "short" }));
}
""",
            "One square per day in week columns, five intensity levels, each with a title for hover and screen readers.",
            view="0 0 480 190",
        ),
        chart(
            "Choropleth map",
            "Customers by country",
            r"""// A tile-grid map: one equal square per country, placed roughly where it lies.
// Swap the tiles for real outlines (GeoJSON paths) when shape matters more than comparison.
const TILES = [["IS", 0, 0, 2], ["NO", 3, 0, 14], ["SE", 4, 0, 22], ["FI", 5, 0, 9], ["IE", 0, 2, 11], ["GB", 1, 2, 64], ["NL", 2, 2, 31], ["DK", 3, 1, 12], ["DE", 3, 2, 78], ["PL", 4, 2, 26],
  ["PT", 0, 4, 8], ["ES", 1, 4, 37], ["FR", 2, 3, 59], ["CH", 3, 3, 18], ["AT", 4, 3, 13], ["IT", 3, 4, 42], ["GR", 5, 4, 6]];
const max = Math.max(...TILES.map((tile) => tile[3])), size = 46;
TILES.forEach(([code, col, row, value]) => {
  const x = 90 + col * (size + 4), y = 6 + row * (size + 4);
  const tile = el("rect", { x, y, width: size, height: size, rx: 8, fill: "var(--primary)", "fill-opacity": 0.12 + (value / max) * 0.88 });
  el("title", {}, `${code}: ${value} customers`, tile);
  el("text", { x: x + size / 2, y: y + size / 2 - 1, class: "lbl mid", fill: "#fff" }, code);
  el("text", { x: x + size / 2, y: y + size / 2 + 13, class: "mid", fill: "#fff", "font-size": 10, opacity: 0.8 }, String(value));
});
""",
            "Regions shaded by value. Built as an equal-area tile grid, so small countries are as readable as large ones.",
        ),
        chart(
            "Geographic map",
            "Offices",
            r"""// Equirectangular projection: longitude and latitude map straight onto x and y.
const lon = linear(-130, 150, 10, W - 10), lat = linear(70, -45, 10, H - 10);
for (let meridian = -120; meridian <= 150; meridian += 30) el("line", { x1: lon(meridian), x2: lon(meridian), y1: lat(70), y2: lat(-45), class: "grid" });
for (let parallel = -30; parallel <= 60; parallel += 30) {
  el("line", { x1: lon(-130), x2: lon(150), y1: lat(parallel), y2: lat(parallel), class: "grid", "stroke-dasharray": parallel === 0 ? "" : "2 4" });
  el("text", { x: 14, y: lat(parallel) - 4, class: "tick" }, `${Math.abs(parallel)}°${parallel > 0 ? "N" : parallel < 0 ? "S" : ""}`);
}
const CITIES = [["San Francisco", -122.4, 37.8, 40], ["New York", -74, 40.7, 85], ["London", -0.1, 51.5, 120], ["Berlin", 13.4, 52.5, 60, "below"], ["Bengaluru", 77.6, 13, 95], ["Singapore", 103.8, 1.4, 35], ["Sydney", 151.2, -33.9, 25]];
CITIES.forEach(([name, cityLon, cityLat, people, side]) => {
  const x = lon(Math.min(149, cityLon)), y = lat(cityLat);
  el("circle", { cx: x, cy: y, r: 4 + Math.sqrt(people), class: "soft s1" });
  el("circle", { cx: x, cy: y, r: 3.5, class: "fill s1" });
  // Neighbouring cities take opposite sides so their names do not collide.
  el("text", { x, y: side === "below" ? y + 18 + Math.sqrt(people) : y - 8 - Math.sqrt(people), class: "tick mid" }, name);
});
""",
            "Points placed by longitude and latitude on a graticule; marker area is head-count. Add coastline paths for context.",
        ),
        chart(
            "Network graph",
            "Service calls",
            r"""const NODES = ["web", "api", "auth", "db", "cache", "queue", "worker", "search", "mail"];
const LINKS = [[0, 1], [1, 2], [1, 3], [1, 4], [1, 5], [5, 6], [6, 3], [1, 7], [6, 8], [2, 3]];
const pos = NODES.map(() => ({ x: 140 + rand() * 200, y: 60 + rand() * 140, vx: 0, vy: 0 }));
// A small force layout: every pair repels, every link pulls, everything drifts to the centre.
for (let step = 0; step < 300; step += 1) {
  for (const a of pos) for (const b of pos) {
    if (a === b) continue;
    const dx = a.x - b.x, dy = a.y - b.y, d2 = Math.max(60, dx * dx + dy * dy);
    a.vx += (dx / d2) * 110; a.vy += (dy / d2) * 110;
  }
  for (const [from, to] of LINKS) {
    const a = pos[from], b = pos[to], dx = b.x - a.x, dy = b.y - a.y;
    a.vx += dx * 0.012; a.vy += dy * 0.012; b.vx -= dx * 0.012; b.vy -= dy * 0.012;
  }
  for (const node of pos) {
    node.vx += (240 - node.x) * 0.004; node.vy += (130 - node.y) * 0.006;
    node.x = Math.min(W - 30, Math.max(30, node.x + node.vx)); node.y = Math.min(H - 20, Math.max(20, node.y + node.vy));
    node.vx *= 0.6; node.vy *= 0.6;
  }
}
LINKS.forEach(([from, to]) => el("line", { x1: pos[from].x, y1: pos[from].y, x2: pos[to].x, y2: pos[to].y, class: "grid", "stroke-width": 1.5 }));
NODES.forEach((name, i) => {
  const degree = LINKS.filter((link) => link.includes(i)).length;
  el("circle", { cx: pos[i].x, cy: pos[i].y, r: 6 + degree * 2, class: "fill s0", stroke: "var(--surface)", "stroke-width": 2 });
  el("text", { x: pos[i].x, y: pos[i].y - 12 - degree * 2, class: "tick mid" }, name);
});
""",
            "Nodes placed by a small force simulation; a node's size is how many connections it has.",
        ),
        chart(
            "Relationship graph",
            "Who works with Dana",
            r"""const PEOPLE = [["Mika", "reports to"], ["Ravi", "peer"], ["Sam", "mentors"], ["Zoe", "peer"], ["Ana", "client"], ["Lee", "reports to"]];
const cx = 240, cy = 130;
PEOPLE.forEach(([name, relation], i) => {
  const [x, y] = polar(cx, cy, 104, (i / PEOPLE.length) * Math.PI * 2);
  const [lx, ly] = polar(cx, cy, 56, (i / PEOPLE.length) * Math.PI * 2);
  el("line", { x1: cx, y1: cy, x2: x, y2: y, class: "grid", "stroke-width": 1.5 });
  // The relation is written on the edge: in this kind of graph the edges are the content.
  el("rect", { x: lx - 30, y: ly - 9, width: 60, height: 18, rx: 9, fill: "var(--surface-2)" });
  el("text", { x: lx, y: ly + 4, class: "tick mid", "font-size": 10 }, relation);
  el("circle", { cx: x, cy: y, r: 18, class: "soft s1", stroke: "var(--accent)" });
  el("text", { x, y: y + 4, class: "lbl mid" }, name);
});
el("circle", { cx, cy, r: 26, class: "fill s0" });
el("text", { x: cx, y: cy + 4, class: "lbl mid", fill: "#fff" }, "Dana");
""",
            "One entity at the centre, its relations around it, each edge labelled with what the relation is.",
        ),
        chart(
            "Dependency graph",
            "Build order",
            r"""const DEPS = { app: ["ui", "api-client"], ui: ["tokens", "icons"], "api-client": ["types"], tokens: [], icons: [], types: [] };
// A node's layer is one more than the deepest thing it depends on.
const layerOf = {};
const depth = (name) => layerOf[name] ?? (layerOf[name] = DEPS[name].length ? 1 + Math.max(...DEPS[name].map(depth)) : 0);
Object.keys(DEPS).forEach(depth);
const layers = [];
for (const [name, layer] of Object.entries(layerOf)) (layers[layer] ??= []).push(name);
const place = {};
layers.forEach((names, layer) => names.forEach((name, i) => { place[name] = { x: 70 + layer * 170, y: ((i + 1) * H) / (names.length + 1) }; }));
const defs = el("defs");
const marker = el("marker", { id: "tip", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 7, markerHeight: 7, orient: "auto" }, undefined, defs);
el("path", { d: "M0 0 10 5 0 10z", fill: "var(--muted)" }, undefined, marker);
for (const [name, needs] of Object.entries(DEPS)) for (const need of needs) {
  const a = place[need], b = place[name];
  el("path", { d: `M${a.x + 48} ${a.y}C${a.x + 110} ${a.y} ${b.x - 110} ${b.y} ${b.x - 50} ${b.y}`, fill: "none", stroke: "var(--muted)", "stroke-width": 1.5, "marker-end": "url(#tip)" });
}
for (const [name, { x, y }] of Object.entries(place)) {
  el("rect", { x: x - 48, y: y - 15, width: 96, height: 30, rx: 8, fill: "var(--surface-2)", stroke: "var(--border)" });
  el("text", { x, y: y + 4, class: "lbl mid" }, name);
}
""",
            "A directed graph laid out in layers: everything a node needs sits to its left.",
        ),
        chart(
            "Gantt chart",
            "Launch plan",
            r"""const TASKS = [["Research", 0, 3, 0], ["Design", 2, 4, 1], ["Build", 4, 6, 0], ["QA", 9, 2, 3], ["Launch", 11, 1, 4]];
const WEEKS = 12, x = linear(0, WEEKS, 90, W - 10), rowH = (H - 40) / TASKS.length;
for (let week = 0; week <= WEEKS; week += 1) {
  el("line", { x1: x(week), x2: x(week), y1: 20, y2: H - 20, class: "grid" });
  if (week < WEEKS) el("text", { x: x(week + 0.5), y: 14, class: "tick mid" }, `W${week + 1}`);
}
TASKS.forEach(([name, start, length, tone], i) => {
  const y = 26 + i * rowH;
  el("text", { x: 82, y: y + rowH / 2 + 1, class: "tick end" }, name);
  el("rect", { x: x(start) + 2, y: y + 4, width: x(start + length) - x(start) - 4, height: rowH - 14, rx: 6, class: `fill s${tone}` });
});
el("line", { x1: x(5.4), x2: x(5.4), y1: 18, y2: H - 18, stroke: "var(--danger)", "stroke-width": 2 });
el("text", { x: x(5.4), y: H - 6, class: "tick mid", fill: "var(--danger)" }, "Today");
""",
            "Tasks as bars on a shared time axis, with a line for today.",
        ),
        chart(
            "Gauge",
            "CPU usage",
            r"""const value = 68, cx = 240, cy = 190, R = 140;
const sweep = (share) => -Math.PI / 2 + share * Math.PI;  // a half circle, left to right
el("path", { d: arc(cx, cy, R, sweep(0), sweep(1)), fill: "none", stroke: "var(--surface-2)", "stroke-width": 22, "stroke-linecap": "round" });
el("path", { d: arc(cx, cy, R, sweep(0), sweep(value / 100)), fill: "none", stroke: value > 85 ? "var(--danger)" : value > 70 ? "var(--warning)" : "var(--success)", "stroke-width": 22, "stroke-linecap": "round" });
el("text", { x: cx, y: cy - 20, class: "mid", fill: "var(--fg)", "font-size": 44, "font-weight": 700 }, `${value}%`);
el("text", { x: cx - R, y: cy + 26, class: "tick mid" }, "0");
el("text", { x: cx + R, y: cy + 26, class: "tick mid" }, "100");
""",
            "One value against a range on a half ring; the colour changes at thresholds.",
            view="0 0 480 230",
        ),
        chart(
            "Speedometer",
            "Requests per second",
            r"""const value = 740, max = 1000, cx = 240, cy = 175, R = 130;
const angle = (v) => (-0.7 + (v / max) * 1.4) * Math.PI;
[[0, 600, "var(--success)"], [600, 850, "var(--warning)"], [850, 1000, "var(--danger)"]].forEach(([from, to, colour]) =>
  el("path", { d: arc(cx, cy, R, angle(from), angle(to)), fill: "none", stroke: colour, "stroke-width": 10 }));
for (let tick = 0; tick <= max; tick += 100) {
  const [x0, y0] = polar(cx, cy, R - 12, angle(tick)), [x1, y1] = polar(cx, cy, R - (tick % 500 === 0 ? 26 : 19), angle(tick));
  el("line", { x1: x0, y1: y0, x2: x1, y2: y1, stroke: "var(--muted)", "stroke-width": tick % 500 === 0 ? 2 : 1 });
  if (tick % 500 === 0) { const [tx, ty] = polar(cx, cy, R - 40, angle(tick)); el("text", { x: tx, y: ty + 4, class: "tick mid" }, String(tick)); }
}
const [nx, ny] = polar(cx, cy, R - 30, angle(value));
el("line", { x1: cx, y1: cy, x2: nx, y2: ny, stroke: "var(--fg)", "stroke-width": 3, "stroke-linecap": "round" });
el("circle", { cx, cy, r: 8, fill: "var(--fg)" });
el("text", { x: cx, y: cy + 40, class: "mid", fill: "var(--fg)", "font-size": 26, "font-weight": 700 }, String(value));
""",
            "A dial with zones, ticks and a needle: the value and how close it is to trouble.",
        ),
        plain(
            "Sparkline",
            '<p class="sp">Revenue <svg viewBox="0 0 80 20" role="img" aria-label="Rising over eight months"><polyline points="0,16 11,12 22,14 34,8 45,10 57,4 68,6 80,1"/><circle cx="80" cy="1" r="2"/></svg> <b>$36k</b> · Churn <svg viewBox="0 0 80 20" class="down" role="img" aria-label="Falling over eight months"><polyline points="0,3 11,5 22,4 34,9 45,8 57,13 68,12 80,17"/><circle cx="80" cy="17" r="2"/></svg> <b>1.9%</b></p>',
            ".sp { font-size: 16px; }\n.sp svg { width: 80px; height: 20px; vertical-align: -4px; overflow: visible; }\n.sp polyline { fill: none; stroke: var(--success); stroke-width: 1.8; stroke-linejoin: round; vector-effect: non-scaling-stroke; }\n.sp circle { fill: var(--success); }\n.sp .down polyline { stroke: var(--accent); }\n.sp .down circle { fill: var(--accent); }\n",
            "A word-sized chart with no axes, set in a line of text beside the figure it explains.",
        ),
        plain(
            "Progress ring",
            '<div class="ring" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="72" aria-label="Profile completeness"><svg viewBox="0 0 120 120"><circle cx="60" cy="60" r="52" class="tr"/><circle cx="60" cy="60" r="52" class="fl" pathLength="100"/></svg><strong>72%</strong></div>',
            ".ring { position: relative; width: 140px; height: 140px; display: grid; place-items: center; }\n.ring svg { position: absolute; inset: 0; rotate: -90deg; }\n.ring circle { fill: none; stroke-width: 10; }\n.tr { stroke: var(--surface-2); }\n.fl { stroke: var(--primary); stroke-linecap: round; stroke-dasharray: 100; stroke-dashoffset: 100; transition: stroke-dashoffset 1s var(--ease); }\n.ring strong { font-size: 28px; font-variant-numeric: tabular-nums; }\n",
            "pathLength makes the circle 100 units long, so the dash offset is simply the percentage left.",
            'const ring = document.querySelector(".ring");\nrequestAnimationFrame(() => { ring.querySelector(".fl").style.strokeDashoffset = String(100 - Number(ring.getAttribute("aria-valuenow"))); });\n',
        ),
        plain(
            "Circular progress",
            '<div class="cp"><svg viewBox="0 0 48 48" class="spin" role="progressbar" aria-label="Loading"><circle cx="24" cy="24" r="20"/></svg><div class="det" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="Uploading"><svg viewBox="0 0 48 48"><circle cx="24" cy="24" r="20" class="tr"/><circle cx="24" cy="24" r="20" class="fl" pathLength="100"/></svg><span>0%</span></div></div>',
            ".cp { display: flex; gap: 32px; align-items: center; }\n.cp svg { width: 56px; height: 56px; }\n.cp circle { fill: none; stroke: var(--primary); stroke-width: 4; stroke-linecap: round; }\n.spin { animation: turn 1.4s linear infinite; }\n.spin circle { stroke-dasharray: 90 150; animation: dash 1.4s ease-in-out infinite; }\n.det { position: relative; display: grid; place-items: center; }\n.det svg { rotate: -90deg; }\n.det .tr { stroke: var(--surface-2); }\n.det .fl { stroke-dasharray: 100; stroke-dashoffset: 100; transition: stroke-dashoffset .2s linear; }\n.det span { position: absolute; font-size: 12px; font-weight: 700; font-variant-numeric: tabular-nums; }\n@keyframes turn { to { rotate: 360deg; } }\n@keyframes dash { 0% { stroke-dasharray: 1 150; stroke-dashoffset: 0; } 50% { stroke-dasharray: 90 150; stroke-dashoffset: -35; } 100% { stroke-dasharray: 90 150; stroke-dashoffset: -124; } }\n",
            "Indeterminate when the length is unknown, determinate with a number as soon as it is.",
            'const det = document.querySelector(".det");\nlet value = 0;\nconst timer = setInterval(() => {\n  value = Math.min(100, value + 4);\n  det.setAttribute("aria-valuenow", String(value));\n  det.querySelector(".fl").style.strokeDashoffset = String(100 - value);\n  det.querySelector("span").textContent = value === 100 ? "✓" : `${value}%`;\n  if (value === 100) clearInterval(timer);\n}, 160);\n',
        ),
        plain(
            "Linear progress",
            '<div class="lp"><label for="p1">Uploading report.pdf <span>64%</span></label><progress id="p1" max="100" value="64"></progress><label for="p2">Preparing…</label><progress id="p2"></progress></div>',
            ".lp { display: grid; gap: 8px; width: min(380px, 100%); }\n.lp label { display: flex; justify-content: space-between; font-size: 13px; color: var(--muted); }\n.lp label span { color: var(--fg); font-weight: 700; }\n.lp progress { appearance: none; width: 100%; height: 8px; border: 0; border-radius: 99px; overflow: hidden; background: var(--surface-2); margin-bottom: 10px; }\n.lp progress::-webkit-progress-bar { background: var(--surface-2); }\n.lp progress::-webkit-progress-value { background: linear-gradient(90deg, var(--primary), var(--accent)); border-radius: 99px; }\n.lp progress::-moz-progress-bar { background: var(--primary); border-radius: 99px; }\n.lp progress:indeterminate { background: linear-gradient(90deg, var(--surface-2) 30%, var(--primary) 50%, var(--surface-2) 70%) 0 0 / 200% 100%; animation: slide 1.4s linear infinite; }\n.lp progress:indeterminate::-webkit-progress-bar { background: transparent; }\n@keyframes slide { from { background-position: 100% 0; } to { background-position: -100% 0; } }\n",
            "The native <progress> element, styled: with a value it is determinate, without one it is not.",
        ),
        plain(
            "Metric comparison",
            '<div class="mc"><div class="row"><span>This month</span><div class="bar"><i style="--w:86%"></i></div><b>$182k</b></div><div class="row prev"><span>Last month</span><div class="bar"><i style="--w:79%"></i></div><b>$168k</b></div><p><strong class="up">+8.2%</strong> · $14k more than last month</p></div>',
            ".mc { display: grid; gap: 10px; width: min(420px, 100%); padding: 16px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.row { display: grid; grid-template-columns: 90px 1fr 60px; gap: 12px; align-items: center; font-size: 14px; }\n.row span { color: var(--muted); }\n.row b { text-align: right; font-variant-numeric: tabular-nums; }\n.bar { height: 12px; border-radius: 99px; background: var(--surface-2); overflow: hidden; }\n.bar i { display: block; height: 100%; width: var(--w); border-radius: inherit; background: var(--primary); }\n.prev .bar i { background: var(--muted); }\n.mc p { margin: 4px 0 0; font-size: 14px; color: var(--muted); }\n.up { color: var(--success); }\n",
            "Two bars on one scale with the difference stated as a percentage and as an amount.",
        ),
        plain(
            "Trend indicator",
            '<div class="trs"></div>',
            ".trs { display: grid; gap: 10px; }\n.tr { display: flex; align-items: center; gap: 10px; padding: 8px 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.tr span { width: 90px; color: var(--muted); font-size: 14px; }\n.tr svg { width: 70px; height: 22px; overflow: visible; }\n.tr polyline { fill: none; stroke: var(--c); stroke-width: 2; vector-effect: non-scaling-stroke; }\n.tr b { color: var(--c); font-variant-numeric: tabular-nums; min-width: 70px; text-align: right; }\n.up { --c: var(--success); }\n.down { --c: var(--danger); }\n.flat { --c: var(--muted); }\n",
            "Direction is computed, not asserted: the slope of a fitted line decides up, down or flat.",
            r"""const SETS = [["Sign-ups", [12, 14, 13, 18, 17, 22, 25]], ["Latency", [220, 214, 219, 201, 190, 186, 172]], ["Tickets", [31, 30, 32, 31, 30, 31, 31]]];
// Least-squares slope, as a share of the mean, so series of any size compare.
const slope = (values) => {
  const n = values.length, meanX = (n - 1) / 2, meanY = values.reduce((a, b) => a + b, 0) / n;
  const top = values.reduce((sum, value, i) => sum + (i - meanX) * (value - meanY), 0);
  const bottom = values.reduce((sum, _, i) => sum + (i - meanX) ** 2, 0);
  return (top / bottom / meanY) * (n - 1);
};
const root = document.querySelector(".trs");
for (const [label, values] of SETS) {
  const change = slope(values);
  const kind = Math.abs(change) < 0.03 ? "flat" : change > 0 ? "up" : "down";
  const min = Math.min(...values), max = Math.max(...values);
  const points = values.map((value, i) => `${(i / (values.length - 1)) * 70},${20 - ((value - min) / (max - min || 1)) * 18}`).join(" ");
  const row = Object.assign(document.createElement("div"), { className: `tr ${kind}` });
  row.innerHTML = `<span></span><svg viewBox="0 0 70 22" aria-hidden="true"><polyline points="${points}"/></svg><b></b>`;
  row.querySelector("span").textContent = label;
  row.querySelector("b").textContent = `${{ up: "▲", down: "▼", flat: "■" }[kind]} ${(Math.abs(change) * 100).toFixed(0)}%`;
  root.append(row);
}
""",
        ),
        plain(
            "Delta indicator",
            '<dl class="dl"></dl>',
            ".dl { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 0; width: min(480px, 100%); }\n.dl div { padding: 12px 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.dl dt { font-size: 12px; color: var(--muted); }\n.dl dd { margin: 4px 0 0; font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums; }\n.dl span { display: inline-block; margin-top: 6px; padding: 1px 8px; border-radius: 99px; font-size: 12px; font-weight: 700; background: color-mix(in srgb, var(--c) 20%, transparent); color: var(--c); }\n.good { --c: var(--success); }\n.bad { --c: var(--danger); }\n.none { --c: var(--muted); }\n",
            "The sign shows direction, the colour shows whether that is good: for churn, down is green.",
            r"""// `better` says which direction is an improvement for this metric.
const METRICS = [["Revenue", 182400, 168600, "up", (v) => `$${(v / 1000).toFixed(1)}k`], ["Churn", 1.9, 2.2, "down", (v) => `${v}%`], ["Tickets", 128, 128, "down", (v) => String(v)]];
const root = document.querySelector(".dl");
for (const [label, now, before, better, format] of METRICS) {
  const change = before === 0 ? 0 : ((now - before) / before) * 100;
  const direction = change > 0.05 ? "up" : change < -0.05 ? "down" : "same";
  const kind = direction === "same" ? "none" : direction === better ? "good" : "bad";
  const item = document.createElement("div");
  item.innerHTML = "<dt></dt><dd></dd><span></span>";
  item.querySelector("dt").textContent = label;
  item.querySelector("dd").textContent = format(now);
  const chip = item.querySelector("span");
  chip.className = kind;
  chip.textContent = direction === "same" ? "No change" : `${change > 0 ? "+" : "−"}${Math.abs(change).toFixed(1)}%`;
  root.append(item);
}
""",
        ),
        plain(
            "Benchmark indicator",
            '<div class="bm"><div class="hd"><span>Net revenue retention</span><b>108%</b></div><div class="track"><i class="r1"></i><i class="r2"></i><i class="r3"></i><span class="val" style="--v:72%"></span><span class="tg" style="--t:80%"><em>Target 112%</em></span></div><div class="sc"><span>80%</span><span>100%</span><span>120%</span></div></div>',
            ".bm { width: min(420px, 100%); display: grid; gap: 8px; }\n.hd { display: flex; justify-content: space-between; }\n.hd span { color: var(--muted); }\n.track { position: relative; display: flex; height: 26px; border-radius: 6px; overflow: visible; }\n.track i { height: 100%; }\n.r1 { width: 50%; background: color-mix(in srgb, var(--fg) 26%, transparent); border-radius: 6px 0 0 6px; }\n.r2 { width: 25%; background: color-mix(in srgb, var(--fg) 16%, transparent); }\n.r3 { width: 25%; background: color-mix(in srgb, var(--fg) 8%, transparent); border-radius: 0 6px 6px 0; }\n.val { position: absolute; left: 0; top: 8px; height: 10px; width: var(--v); border-radius: 3px; background: var(--primary); }\n.tg { position: absolute; left: var(--t); top: -4px; bottom: -4px; width: 3px; background: var(--fg); }\n.tg em { position: absolute; bottom: calc(100% + 2px); left: 50%; translate: -50% 0; font: normal 11px var(--font); color: var(--muted); white-space: nowrap; }\n.sc { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); }\n",
            "A bullet graph: the value as a bar, the target as a tick, poor-fair-good bands behind them.",
        ),
        chart(
            "Forecast visualization",
            "Revenue, actual and forecast",
            r"""const ACTUAL = [120, 180, 150, 240, 210, 300], FORECAST = [300, 330, 365, 395];
const LABELS = [...MONTHS.slice(0, 6), "Jul", "Aug", "Sep"];
const max = niceMax(Math.max(...ACTUAL, ...FORECAST));
const x = linear(0, LABELS.length - 1, M.left + 10, W - M.right - 10), y = linear(0, max, H - M.bottom, M.top);
yAxis(y, max);
xLabels(LABELS, x);
el("rect", { x: x(5), y: M.top, width: x(8) - x(5), height: H - M.bottom - M.top, fill: "var(--primary)", "fill-opacity": 0.06 });
el("path", { d: path(ACTUAL.map((value, i) => [x(i), y(value)])), class: "stroke s0" });
// The forecast continues from the last actual point and is dashed: it is not data.
el("path", { d: path(FORECAST.map((value, i) => [x(5 + i), y(value)])), class: "stroke s0", "stroke-dasharray": "6 5" });
el("text", { x: x(6.5), y: M.top + 14, class: "tick mid" }, "Forecast");
""",
            "Measured values solid, projected values dashed over a tinted region: never the same line style.",
        ),
        chart(
            "Confidence band",
            "Latency with 95% interval",
            CART.replace("yAxis(y, max);", "yAxis(y, max);")
            + r"""const spread = SERIES.map((value, i) => 18 + i * 9);  // uncertainty grows over time
const upper = SERIES.map((value, i) => [x(i), y(Math.min(max, value + spread[i]))]);
const lower = SERIES.map((value, i) => [x(i), y(Math.max(0, value - spread[i]))]).reverse();
el("path", { d: `${path([...upper, ...lower])}Z`, class: "soft s0" });
el("path", { d: path(points), class: "stroke s0" });
""",
            "The estimate as a line inside a band showing how far the truth may reasonably be from it.",
        ),
        chart(
            "Anomaly indicator",
            "Error rate",
            r"""const VALUES = [12, 14, 11, 13, 15, 12, 41, 14, 13, 12, 11, 2, 13, 14];
// Median and median absolute deviation: unlike mean and standard deviation,
// they are not dragged around by the very outliers being looked for.
const median = (list) => { const sorted = [...list].sort((a, b) => a - b), mid = sorted.length >> 1; return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2; };
const centre = median(VALUES);
const spread = median(VALUES.map((value) => Math.abs(value - centre))) || 1;
const LIMIT = 5 * spread;
const max = niceMax(Math.max(...VALUES));
const x = linear(0, VALUES.length - 1, M.left + 10, W - M.right - 10), y = linear(0, max, H - M.bottom, M.top);
yAxis(y, max);
el("rect", { x: M.left, y: y(centre + LIMIT), width: W - M.left - M.right, height: y(Math.max(0, centre - LIMIT)) - y(centre + LIMIT), fill: "var(--success)", "fill-opacity": 0.1 });
el("path", { d: path(VALUES.map((value, i) => [x(i), y(value)])), class: "stroke s0" });
VALUES.forEach((value, i) => {
  if (Math.abs(value - centre) <= LIMIT) return;
  el("circle", { cx: x(i), cy: y(value), r: 9, fill: "var(--danger)", "fill-opacity": 0.2 });
  el("circle", { cx: x(i), cy: y(value), r: 4, fill: "var(--danger)" });
  el("text", { x: x(i), y: y(value) + (value > centre ? -14 : -12), class: "tick mid", fill: "var(--danger)" }, value > centre ? "Spike" : "Drop");
});
""",
            "Points outside the normal band are found from the data and marked, not hand-placed.",
        ),
        chart(
            "Data tooltip",
            "Sign-ups per month",
            CART
            + r"""el("path", { d: path(points), class: "stroke s0" });
const dot = el("circle", { r: 5, class: "fill s0", stroke: "var(--surface)", "stroke-width": 2, visibility: "hidden" });
const tip = document.querySelector(".tip");
const show = (i) => {
  const [px, py] = points[i];
  dot.setAttribute("cx", px); dot.setAttribute("cy", py); dot.setAttribute("visibility", "visible");
  const box = svg.getBoundingClientRect(), frame = svg.parentElement.getBoundingClientRect();
  tip.hidden = false;
  tip.textContent = `${MONTHS[i]}: ${SERIES[i]}`;
  tip.style.left = `${box.left - frame.left + (px / W) * box.width}px`;
  tip.style.top = `${box.top - frame.top + (py / H) * box.height}px`;
};
let current = 0;
svg.addEventListener("pointermove", (event) => {
  const box = svg.getBoundingClientRect(), sx = ((event.clientX - box.left) / box.width) * W;
  // The nearest observation along x: the pointer does not have to hit the line.
  current = points.reduce((best, [px], i) => Math.abs(px - sx) < Math.abs(points[best][0] - sx) ? i : best, 0);
  show(current);
});
svg.addEventListener("pointerleave", () => { tip.hidden = true; dot.setAttribute("visibility", "hidden"); });
svg.tabIndex = 0;
svg.addEventListener("keydown", (event) => {
  if (event.key === "ArrowRight") current = Math.min(points.length - 1, current + 1); else if (event.key === "ArrowLeft") current = Math.max(0, current - 1); else return;
  show(current);
});
""",
            "Snaps to the nearest point along the x axis; arrow keys step through the points for keyboard users.",
            extra='<div class="tip" role="status" hidden></div>',
        ),
        chart(
            "Chart crosshair",
            "Price",
            CART
            + r"""el("path", { d: path(points), class: "stroke s0" });
const vertical = el("line", { y1: M.top, y2: H - M.bottom, stroke: "var(--muted)", "stroke-dasharray": "3 3", visibility: "hidden" });
const horizontal = el("line", { x1: M.left, x2: W - M.right, stroke: "var(--muted)", "stroke-dasharray": "3 3", visibility: "hidden" });
const xTag = el("text", { y: H - M.bottom + 14, class: "lbl mid", visibility: "hidden" });
const yTag = el("text", { x: M.left - 8, class: "lbl end", visibility: "hidden" });
const parts = [vertical, horizontal, xTag, yTag];
svg.addEventListener("pointermove", (event) => {
  const box = svg.getBoundingClientRect();
  const px = Math.min(W - M.right, Math.max(M.left, ((event.clientX - box.left) / box.width) * W));
  const py = Math.min(H - M.bottom, Math.max(M.top, ((event.clientY - box.top) / box.height) * H));
  vertical.setAttribute("x1", px); vertical.setAttribute("x2", px);
  horizontal.setAttribute("y1", py); horizontal.setAttribute("y2", py);
  // Read both axes back from the pointer position by inverting the scales.
  const index = Math.round(((px - x(0)) / (x(SERIES.length - 1) - x(0))) * (SERIES.length - 1));
  xTag.setAttribute("x", px); xTag.textContent = MONTHS[Math.min(MONTHS.length - 1, Math.max(0, index))];
  yTag.setAttribute("y", py + 4); yTag.textContent = fmt(((y(0) - py) / (y(0) - y(max))) * max);
  parts.forEach((part) => part.setAttribute("visibility", "visible"));
});
svg.addEventListener("pointerleave", () => parts.forEach((part) => part.setAttribute("visibility", "hidden")));
""",
            "Two guide lines follow the pointer and read the value off each axis by inverting the scales.",
            css="svg.plot { cursor: crosshair; }\n",
        ),
        chart(
            "Interactive legend",
            "Requests by plan",
            r"""const SETS = [["Free", [60, 80, 70, 110, 100, 130, 120, 150]], ["Team", [120, 180, 150, 240, 210, 300, 280, 360]], ["Enterprise", [40, 50, 90, 80, 140, 150, 210, 260]]];
const hidden = new Set();
const legend = document.querySelector(".lg");
const plot = el("g");
const draw = () => {
  plot.replaceChildren();
  const shown = SETS.filter(([name]) => !hidden.has(name));
  // The axis rescales to what is visible, so a small series can be read once the large one is off.
  const max = niceMax(Math.max(1, ...shown.flatMap(([, values]) => values)));
  const x = linear(0, 7, M.left + 10, W - M.right - 10), y = linear(0, max, H - M.bottom, M.top);
  for (let i = 0; i <= 4; i += 1) {
    const value = (max / 4) * i;
    el("line", { x1: M.left, x2: W - M.right, y1: y(value), y2: y(value), class: "grid" }, undefined, plot);
    el("text", { x: M.left - 8, y: y(value) + 4, class: "tick end" }, fmt(value), plot);
  }
  MONTHS.forEach((label, i) => el("text", { x: x(i), y: H - 10, class: "tick mid" }, label, plot));
  SETS.forEach(([name, values], s) => { if (!hidden.has(name)) el("path", { d: path(values.map((value, i) => [x(i), y(value)])), class: `stroke s${s}` }, undefined, plot); });
};
SETS.forEach(([name], s) => {
  const button = Object.assign(document.createElement("button"), { className: `s${s}`, textContent: name });
  button.setAttribute("aria-pressed", "true");
  button.addEventListener("click", () => {
    if (hidden.has(name)) hidden.delete(name); else if (hidden.size < SETS.length - 1) hidden.add(name);  // one series always stays
    button.setAttribute("aria-pressed", String(!hidden.has(name)));
    draw();
  });
  legend.append(button);
});
draw();
""",
            "Legend entries are toggle buttons; hiding a series rescales the axis, and the last one cannot be hidden.",
            css='.lg { display: flex; gap: 8px; margin-top: 8px; }\n.lg button { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border: 1px solid var(--border); border-radius: 99px; background: none; font-size: 13px; }\n.lg button::before { content: ""; width: 10px; height: 10px; border-radius: 3px; background: var(--c); }\n.lg button[aria-pressed="false"] { opacity: .45; text-decoration: line-through; }\n',
            extra='<div class="lg" role="group" aria-label="Series"></div>',
        ),
    ),
)
