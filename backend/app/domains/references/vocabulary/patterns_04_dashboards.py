"""Patterns 121-150: bento grids, dashboards and their widgets."""

from app.domains.references.vocabulary.base import Item, Section

# One tile vocabulary shared by every dashboard in this section.
TILE = """\
.dash { display: grid; gap: 12px; width: min(680px, 100%); }
.t { display: flex; flex-direction: column; gap: 6px; min-width: 0; padding: 14px 16px; border: 1px solid var(--border);
  border-radius: 16px; background: var(--surface); }
.t h4 { margin: 0; font-size: 12px; font-weight: 500; color: var(--muted); }
.t .v { font-size: 24px; font-weight: 700; letter-spacing: -.02em; font-variant-numeric: tabular-nums; }
.t .d { font-size: 12px; font-weight: 600; color: var(--success); }
.t .d.down { color: var(--danger); }
.t svg { width: 100%; flex: 1; min-height: 40px; }
.t polyline, .t path.line { fill: none; stroke: var(--primary); stroke-width: 2; vector-effect: non-scaling-stroke; stroke-linejoin: round; }
.t path.area { fill: color-mix(in srgb, var(--primary) 22%, transparent); stroke: none; }
.t rect { fill: var(--primary); }
.t ul { margin: 0; padding: 0; list-style: none; display: grid; gap: 8px; font-size: 13px; }
.t li { display: flex; justify-content: space-between; gap: 8px; color: var(--muted); }
.t li b { color: var(--fg); font-weight: 500; }
"""
LINE = '<svg viewBox="0 0 120 40" preserveAspectRatio="none" aria-hidden="true"><path class="area" d="M0 30 15 26 30 28 45 18 60 22 75 12 90 16 105 8 120 11V40H0z"/><polyline points="0,30 15,26 30,28 45,18 60,22 75,12 90,16 105,8 120,11"/></svg>'
BARS = (
    '<svg viewBox="0 0 120 40" preserveAspectRatio="none" aria-hidden="true">'
    + "".join(
        f'<rect x="{i * 10 + 1}" y="{40 - h}" width="7" height="{h}" rx="2"/>'
        for i, h in enumerate([12, 18, 15, 24, 20, 30, 26, 34, 22, 28, 36, 31])
    )
    + "</svg>"
)


def kpi(label: str, value: str, delta: str = "", down: bool = False, cls: str = "") -> str:
    change = f'<span class="d{" down" if down else ""}">{delta}</span>' if delta else ""
    return (
        f'<article class="t {cls}"><h4>{label}</h4><span class="v">{value}</span>{change}</article>'
    )


def chart(label: str, svg: str, cls: str = "") -> str:
    return f'<article class="t {cls}"><h4>{label}</h4>{svg}</article>'


def listing(label: str, rows: list[tuple[str, str]], cls: str = "") -> str:
    body = "".join(f"<li><b>{a}</b><span>{b}</span></li>" for a, b in rows)
    return f'<article class="t {cls}"><h4>{label}</h4><ul>{body}</ul></article>'


K4 = (
    kpi("Revenue", "$182k", "▲ 8.2%")
    + kpi("Orders", "2,714", "▲ 3.1%")
    + kpi("Refunds", "41", "▼ 12%", True)
    + kpi("NPS", "62", "▲ 4")
)
TOP = listing("Top regions", [("EMEA", "$74k"), ("Americas", "$68k"), ("APAC", "$40k")])
FEED_ROWS = [
    ("Mika deployed api", "2m"),
    ("Dana merged #482", "9m"),
    ("Build passed", "14m"),
    ("Ravi opened #483", "31m"),
]


def dash(name: str, grid_css: str, html: str, note: str, js: str = "", extra_css: str = "") -> Item:
    return Item(
        name,
        f'<section class="dash g">{html}</section>',
        TILE + ".g { " + grid_css + " }\n" + extra_css,
        js,
        note,
    )


FEED_CSS = """\
.feed { width: min(440px, 100%); max-height: 340px; overflow: auto; margin: 0; padding: 6px; list-style: none; border: 1px solid var(--border);
  border-radius: 16px; background: var(--surface); }
.feed li { display: grid; grid-template-columns: auto 1fr auto; gap: 10px; align-items: center; padding: 10px; border-radius: 10px; }
.feed li + li { border-top: 1px solid var(--border); border-radius: 0; }
.feed i { width: 8px; height: 8px; border-radius: 50%; background: var(--primary); }
.feed time { font-size: 12px; color: var(--muted); }
"""
LIVE_JS = """\
const feed = document.querySelector(".feed");
const events = ["Checkout completed", "New sign-up", "Deploy finished", "Invoice paid", "Alert resolved", "Comment added"];
const stamp = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
const push = () => {
  const item = document.createElement("li");
  item.className = "in";
  item.append(document.createElement("i"), Object.assign(document.createElement("span"), { textContent: events[Math.floor(Math.random() * events.length)] }),
    Object.assign(document.createElement("time"), { textContent: stamp() }));
  feed.prepend(item);
  while (feed.children.length > MAX_ROWS) feed.lastElementChild.remove();  // a live list must not grow without bound
};
const MAX_ROWS = 30;
let timer = setInterval(push, 1600);
// Stop while the tab is hidden; nobody is watching and it saves the battery.
document.addEventListener("visibilitychange", () => {
  clearInterval(timer);
  if (!document.hidden) timer = setInterval(push, 1600);
});
push();
"""

SECTION = Section(
    "patterns",
    "Bento & Dashboard Patterns",
    121,
    (
        dash(
            "Bento grid",
            "grid-template-columns: repeat(4, 1fr); grid-auto-rows: 110px;",
            kpi("Revenue", "$182k", "▲ 8.2%", cls="s2")
            + kpi("Users", "48k")
            + kpi("NPS", "62")
            + chart("Traffic", LINE, "s2 r2")
            + TOP.replace('class="t "', 'class="t s2 r2"'),
            "Equal cells with a few that span two columns or rows.",
            extra_css=".s2 { grid-column: span 2; }\n.r2 { grid-row: span 2; }\n",
        ),
        dash(
            "Asymmetric bento grid",
            "grid-template-columns: 1.6fr 1fr 1fr; grid-template-rows: 130px 100px 100px;",
            chart("Sessions", LINE, "hero")
            + kpi("Conversion", "4.8%", "▲ 0.6")
            + kpi("Bounce", "31%", "▼ 2", True)
            + kpi("Avg. order", "$67")
            + kpi("LTV", "$412")
            + chart("Orders", BARS, "wide"),
            "Unequal tracks: one dominant cell sets the hierarchy for the rest.",
            extra_css=".hero { grid-row: span 2; }\n.wide { grid-column: span 3; }\n",
        ),
        Item(
            "Masonry dashboard",
            '<section class="mason">'
            + kpi("Revenue", "$182k", "▲ 8.2%")
            + chart("Traffic", LINE, "h1")
            + TOP
            + kpi("Orders", "2,714")
            + chart("Sales", BARS, "h2")
            + listing("Activity", FEED_ROWS)
            + "</section>",
            TILE
            + ".mason { columns: 3 190px; column-gap: 12px; width: min(680px, 100%); }\n.mason .t { break-inside: avoid; margin-bottom: 12px; }\n.h1 { height: 150px; }\n.h2 { height: 190px; }\n",
            note="Columns of tiles with natural heights; order runs down each column.",
        ),
        dash(
            "Modular dashboard",
            "grid-template-columns: repeat(12, 1fr);",
            K4.replace('class="t "', 'class="t c3"')
            + chart("Revenue", LINE, "c8")
            + TOP.replace('class="t "', 'class="t c4"')
            + chart("Orders", BARS, "c6")
            + listing("Activity", FEED_ROWS, "c6"),
            "A 12-column grid; every module declares its span, so the layout is data.",
            extra_css=".c3 { grid-column: span 3; }\n.c4 { grid-column: span 4; }\n.c6 { grid-column: span 6; }\n.c8 { grid-column: span 8; }\n.c8, .c4 { min-height: 150px; }\n@media (max-width: 620px) { .g > * { grid-column: span 12; } }\n",
        ),
        dash(
            "KPI dashboard",
            "grid-template-columns: repeat(4, 1fr);",
            K4
            + kpi("Churn", "1.9%", "▼ 0.3", True)
            + kpi("MRR", "$58k", "▲ 5%")
            + kpi("ARPU", "$41")
            + kpi("Trials", "318", "▲ 12%"),
            "Nothing but figures and their change: a scoreboard.",
        ),
        dash(
            "Executive dashboard",
            "grid-template-columns: 2fr 1fr; grid-template-rows: auto 170px;",
            '<article class="t lead"><h4>Quarter to date</h4><span class="v big">$4.82M</span><span class="d">▲ 12.4% vs plan</span><p>Ahead of plan in EMEA and Americas; APAC is 6% behind on enterprise renewals.</p></article>'
            + listing(
                "Risks",
                [("APAC renewals", "High"), ("Hiring plan", "Medium"), ("Cloud spend", "Low")],
            )
            + chart("Bookings", LINE)
            + listing("Decisions needed", [("Pricing change", "Fri"), ("Headcount", "Next week")]),
            "One headline figure, a sentence of interpretation, risks and decisions.",
            extra_css=".big { font-size: 40px !important; }\n.lead p { margin: 6px 0 0; color: var(--muted); font-size: 14px; }\n",
        ),
        dash(
            "Analytics dashboard",
            "grid-template-columns: repeat(3, 1fr); grid-template-rows: auto 160px 150px;",
            '<header class="filters"><strong>Analytics</strong><span><button aria-pressed="true">7d</button><button aria-pressed="false">30d</button><button aria-pressed="false">90d</button></span></header>'
            + chart("Visitors", LINE, "w3")
            + chart("Sources", BARS)
            + TOP
            + listing("Top pages", [("/pricing", "18k"), ("/docs", "12k"), ("/blog", "9k")]),
            "A range filter over a main trend and three breakdowns.",
            js='document.querySelectorAll(".filters button").forEach((button, _, all) => button.addEventListener("click", () => all.forEach((item) => item.setAttribute("aria-pressed", String(item === button)))));\n',
            extra_css='.filters { grid-column: 1 / -1; display: flex; justify-content: space-between; align-items: center; }\n.filters button { padding: 4px 10px; border: 1px solid var(--border); background: var(--surface); color: var(--muted); }\n.filters button:first-child { border-radius: 8px 0 0 8px; }\n.filters button:last-child { border-radius: 0 8px 8px 0; }\n.filters button[aria-pressed="true"] { background: var(--primary); color: #fff; border-color: var(--primary); }\n.w3 { grid-column: span 3; }\n',
        ),
        dash(
            "AI dashboard",
            "grid-template-columns: repeat(3, 1fr); grid-template-rows: auto 110px 150px;",
            '<article class="t ask"><h4>Ask about your data</h4><label><input placeholder="Why did churn rise in March?" aria-label="Ask about your data"><button>Ask</button></label></article>'
            + kpi("Requests", "1.2M", "▲ 18%")
            + kpi("Tokens", "842M")
            + kpi("Cost", "$3,410", "▲ 6%")
            + chart("Latency p95", LINE, "s2")
            + listing("Models", [("sonnet", "61%"), ("haiku", "33%"), ("opus", "6%")]),
            "A question box above usage, cost, latency and model mix.",
            extra_css=".ask { grid-column: 1 / -1; background: linear-gradient(120deg, color-mix(in srgb, var(--primary) 22%, var(--surface)), var(--surface)); }\n.ask label { display: flex; gap: 8px; }\n.ask input { flex: 1; min-width: 0; height: 38px; padding: 0 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); }\n.ask button { padding: 0 16px; border: 0; border-radius: 10px; background: var(--primary); color: #fff; font-weight: 600; }\n.s2 { grid-column: span 2; }\n",
        ),
        dash(
            "Command center",
            "grid-template-columns: 1fr 2fr 1fr; grid-template-rows: 150px 150px;",
            listing("Queues", [("Ingest", "12"), ("Review", "4"), ("Publish", "0")], "r2")
            + '<article class="t map r2"><h4>Live map</h4><div class="grid"><i style="left:22%;top:38%"></i><i style="left:58%;top:30%"></i><i style="left:71%;top:62%"></i><i style="left:40%;top:70%"></i></div></article>'
            + kpi("Incidents", "2", "1 critical", True)
            + listing("On call", [("Primary", "Ravi"), ("Secondary", "Dana")]),
            "A central live view flanked by queues, incidents and who is responsible.",
            extra_css=".r2 { grid-row: span 2; }\n.map .grid { position: relative; flex: 1; border-radius: 10px; background: linear-gradient(var(--border) 1px, transparent 1px) 0 0 / 100% 28px, linear-gradient(90deg, var(--border) 1px, transparent 1px) 0 0 / 28px 100%, var(--bg); }\n.map i { position: absolute; width: 10px; height: 10px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 0 var(--accent); animation: ping 1.8s ease-out infinite; }\n.map i:nth-child(2) { animation-delay: .5s; }\n.map i:nth-child(3) { animation-delay: 1s; background: var(--danger); }\n@keyframes ping { to { box-shadow: 0 0 0 14px transparent; } }\n",
        ),
        dash(
            "Operations dashboard",
            "grid-template-columns: repeat(3, 1fr);",
            kpi("Open tickets", "128", "▲ 9", True)
            + kpi("First response", "14m", "▼ 3m")
            + kpi("SLA met", "96.2%")
            + listing(
                "Backlog by team",
                [("Billing", "44"), ("Onboarding", "38"), ("Technical", "46")],
                "s2",
            )
            + listing("Breaching soon", [("#8841", "12m"), ("#8836", "25m"), ("#8829", "41m")]),
            "Work in progress: volume, speed, commitments at risk.",
            extra_css=".s2 { grid-column: span 2; }\n",
        ),
        dash(
            "Monitoring dashboard",
            "grid-template-columns: repeat(4, 1fr); grid-auto-rows: 104px;",
            "".join(
                f'<article class="t svc"><h4>{name}</h4><span class="v">{val}</span><span class="state {st}">{st}</span></article>'
                for name, val, st in [
                    ("api", "212ms", "ok"),
                    ("web", "88ms", "ok"),
                    ("queue", "4.1k", "warn"),
                    ("db", "71%", "ok"),
                    ("cache", "99%", "ok"),
                    ("search", "640ms", "bad"),
                    ("auth", "31ms", "ok"),
                    ("cdn", "18ms", "ok"),
                ]
            ),
            "One tile per service with a threshold colour; the eye goes to what is not green.",
            extra_css=".svc .state { align-self: flex-start; padding: 1px 8px; border-radius: 99px; font-size: 11px; font-weight: 700; text-transform: uppercase; }\n.ok { background: color-mix(in srgb, var(--success) 20%, transparent); color: var(--success); }\n.warn { background: color-mix(in srgb, var(--warning) 20%, transparent); color: var(--warning); }\n.bad { background: color-mix(in srgb, var(--danger) 20%, transparent); color: var(--danger); }\n.svc:has(.bad) { border-color: var(--danger); }\n",
        ),
        dash(
            "Activity dashboard",
            "grid-template-columns: 1.4fr 1fr;",
            listing(
                "Recent activity",
                [*FEED_ROWS, ("Sam invited 3 people", "1h"), ("Plan upgraded", "2h")],
                "r2",
            )
            + kpi("Active today", "214", "▲ 11%")
            + chart("Events per hour", BARS),
            "The feed is the main column; the numbers summarise it.",
            extra_css=".r2 { grid-row: span 2; }\n",
        ),
        Item(
            "Real-time dashboard",
            '<section class="dash rt"><article class="t"><h4>Requests / s <span class="live">live</span></h4><span class="v" id="rps">0</span><svg viewBox="0 0 240 60" preserveAspectRatio="none" aria-hidden="true"><polyline id="trace" points=""/></svg></article></section>',
            TILE
            + ".rt .t { height: 200px; }\n.live { margin-left: 6px; padding: 0 7px; border-radius: 99px; background: color-mix(in srgb, var(--danger) 22%, transparent); color: var(--danger); font-size: 10px; text-transform: uppercase; }\n",
            """\
const POINTS = 40;
const samples = Array.from({ length: POINTS }, () => 300);
const trace = document.getElementById("trace");
const figure = document.getElementById("rps");
const draw = () => {
  const max = Math.max(...samples), min = Math.min(...samples);
  trace.setAttribute("points", samples.map((value, i) => `${(i / (POINTS - 1)) * 240},${56 - ((value - min) / (max - min || 1)) * 52}`).join(" "));
  figure.textContent = Math.round(samples.at(-1)).toLocaleString();
};
// Replace with a WebSocket or EventSource handler; keep the fixed-size window.
const tick = () => {
  samples.push(Math.max(40, samples.at(-1) + (Math.random() - 0.5) * 90));
  samples.shift();
  draw();
};
let timer = setInterval(tick, 500);
document.addEventListener("visibilitychange", () => { clearInterval(timer); if (!document.hidden) timer = setInterval(tick, 500); });
draw();
""",
            "A sliding window of samples redrawn on each tick; pauses while the tab is hidden.",
        ),
        Item(
            "Split dashboard",
            '<section class="splitd"><aside>'
            + listing(
                "Accounts",
                [("Northwind", "$74k"), ("Acme", "$41k"), ("Globex", "$38k"), ("Initech", "$22k")],
            )
            + "</aside><main>"
            + kpi("Northwind", "$74k", "▲ 14%")
            + chart("Monthly spend", LINE)
            + "</main></section>",
            TILE
            + ".splitd { display: grid; grid-template-columns: 220px 1fr; gap: 12px; width: min(680px, 100%); height: 300px; }\n.splitd aside, .splitd main { display: grid; gap: 12px; min-height: 0; }\n.splitd main { grid-template-rows: auto 1fr; }\n.splitd aside li:first-child { color: var(--fg); }\n",
            note="A list on the left chooses what the right side shows (master-detail).",
        ),
        Item(
            "Full-bleed dashboard",
            '<section class="bleed"><header><strong>Fleet</strong><span>312 vehicles online</span></header><div class="plot">'
            + LINE
            + "</div><footer>"
            + K4
            + "</footer></section>",
            TILE
            + ".bleed { width: min(720px, 100%); border-radius: 18px; overflow: hidden; border: 1px solid var(--border); background: var(--surface); }\n.bleed header { display: flex; justify-content: space-between; padding: 14px 18px; color: var(--muted); }\n.bleed header strong { color: var(--fg); }\n.plot { height: 170px; }\n.plot svg { width: 100%; height: 100%; display: block; }\n.plot path.area { fill: color-mix(in srgb, var(--primary) 30%, transparent); }\n.plot polyline { fill: none; stroke: var(--primary); stroke-width: 2; vector-effect: non-scaling-stroke; }\n.bleed footer { display: grid; grid-template-columns: repeat(4, 1fr); border-top: 1px solid var(--border); }\n.bleed footer .t { border: 0; border-radius: 0; border-right: 1px solid var(--border); }\n.bleed footer .t:last-child { border-right: 0; }\n",
            note="The chart runs edge to edge with no card around it; figures sit in a strip below.",
        ),
        dash(
            "Widget dashboard",
            "grid-template-columns: repeat(3, 1fr); grid-auto-rows: 130px;",
            "".join(
                f'<article class="t w"><header><h4>{name}</h4><button aria-label="{name} options">⋯</button></header>{body}</article>'
                for name, body in [
                    ("Weather", '<span class="v">18°</span>'),
                    (
                        "Tasks",
                        "<ul><li><b>Review PR</b><span>Today</span></li><li><b>Plan sprint</b><span>Fri</span></li></ul>",
                    ),
                    ("Clock", '<span class="v">14:02</span>'),
                    ("Notes", "<ul><li><b>Ask about SSO</b></li></ul>"),
                    ("Sales", BARS),
                    ("Traffic", LINE),
                ]
            ),
            "Independent widgets, each with its own title bar and menu.",
            extra_css=".w header { display: flex; justify-content: space-between; align-items: center; }\n.w header button { border: 0; background: none; color: var(--muted); }\n",
        ),
        Item(
            "Drag-and-drop dashboard",
            '<section class="dash dnd" aria-label="Reorderable widgets">'
            + "".join(
                f'<article class="t" draggable="true" tabindex="0"><h4>⠿ {n}</h4><span class="v">{v}</span></article>'
                for n, v in [
                    ("Revenue", "$182k"),
                    ("Orders", "2,714"),
                    ("Users", "48k"),
                    ("NPS", "62"),
                    ("Churn", "1.9%"),
                    ("Trials", "318"),
                ]
            )
            + '</section><p class="sr" role="status"></p>',
            TILE
            + ".dnd { grid-template-columns: repeat(3, 1fr); }\n.dnd .t { cursor: grab; transition: transform .15s var(--ease), opacity .15s, border-color .15s; }\n.dnd .t.dragging { opacity: .4; }\n.dnd .t.over { border-color: var(--primary); transform: scale(1.03); }\n.dnd .t:focus-visible { outline: 2px solid var(--accent); }\n.sr { position: fixed; bottom: 16px; color: var(--muted); font-size: 13px; }\n",
            """\
const board = document.querySelector(".dnd");
const status = document.querySelector(".sr");
let dragged = null;
board.addEventListener("dragstart", (event) => { dragged = event.target.closest(".t"); dragged.classList.add("dragging"); event.dataTransfer.effectAllowed = "move"; });
board.addEventListener("dragend", () => { dragged?.classList.remove("dragging"); board.querySelectorAll(".over").forEach((tile) => tile.classList.remove("over")); dragged = null; });
board.addEventListener("dragover", (event) => {
  event.preventDefault();
  const target = event.target.closest(".t");
  board.querySelectorAll(".over").forEach((tile) => tile.classList.toggle("over", tile === target));
  if (target && target !== dragged) target.classList.add("over");
});
board.addEventListener("drop", (event) => {
  event.preventDefault();
  const target = event.target.closest(".t");
  if (!target || !dragged || target === dragged) return;
  const tiles = [...board.children];
  board.insertBefore(dragged, tiles.indexOf(dragged) < tiles.indexOf(target) ? target.nextSibling : target);
});
// Keyboard equivalent: Alt+arrow moves the focused widget.
board.addEventListener("keydown", (event) => {
  const tile = event.target.closest(".t");
  if (!tile || !event.altKey) return;
  if (event.key === "ArrowLeft" && tile.previousElementSibling) board.insertBefore(tile, tile.previousElementSibling);
  else if (event.key === "ArrowRight" && tile.nextElementSibling) board.insertBefore(tile.nextElementSibling, tile);
  else return;
  tile.focus();
  status.textContent = `Moved to position ${[...board.children].indexOf(tile) + 1}.`;
});
""",
            "Native drag and drop to reorder, with Alt+arrow as the keyboard path and a status announcement.",
        ),
        Item(
            "Customizable dashboard",
            '<section class="cust"><fieldset><legend>Show widgets</legend>'
            + "".join(
                f'<label><input type="checkbox" value="{k}" checked> {k.title()}</label>'
                for k in ["revenue", "orders", "traffic", "regions"]
            )
            + '</fieldset><div class="dash">'
            + kpi("Revenue", "$182k", cls="w-revenue")
            + kpi("Orders", "2,714", cls="w-orders")
            + chart("Traffic", LINE, "w-traffic")
            + TOP.replace('class="t "', 'class="t w-regions"')
            + "</div></section>",
            TILE
            + ".cust { display: grid; gap: 12px; width: min(620px, 100%); }\n.cust fieldset { display: flex; gap: 16px; border: 1px solid var(--border); border-radius: 12px; padding: 10px 14px; }\n.cust legend { padding: 0 6px; color: var(--muted); font-size: 12px; }\n.cust .dash { grid-template-columns: repeat(2, 1fr); width: 100%; }\n",
            """\
const KEY = "dashboard.hidden";
const read = () => { try { return JSON.parse(localStorage.getItem(KEY)) ?? []; } catch { return []; } };
const boxes = [...document.querySelectorAll(".cust input")];
const apply = () => {
  const hidden = boxes.filter((box) => !box.checked).map((box) => box.value);
  for (const box of boxes) document.querySelector(`.w-${box.value}`).hidden = !box.checked;
  try { localStorage.setItem(KEY, JSON.stringify(hidden)); } catch { /* private mode: the choice lasts for this visit only */ }
};
const hidden = read();
boxes.forEach((box) => { box.checked = !hidden.includes(box.value); box.addEventListener("change", apply); });
apply();
""",
            "The user chooses which widgets appear; the choice is remembered when storage is available.",
        ),
        Item(
            "Dashboard widget",
            '<article class="t widget"><header><h4>Revenue</h4><span class="range">Last 30 days</span></header><span class="v">$182,410</span><span class="d">▲ 8.2% vs previous period</span>'
            + LINE
            + '<footer><a href="#">View report →</a></footer></article>',
            TILE
            + ".widget { width: 320px; height: 250px; }\n.widget header { display: flex; justify-content: space-between; }\n.range { font-size: 12px; color: var(--muted); }\n.widget footer { padding-top: 8px; border-top: 1px solid var(--border); }\n.widget footer a { color: var(--fg); font-size: 13px; font-weight: 600; text-decoration: none; }\n",
            note="The anatomy of one widget: title, period, value, change, trend, link to detail.",
        ),
        Item(
            "Expandable widget",
            '<div class="stagex"><article class="t xw"><header><h4>Traffic</h4><button aria-expanded="false" aria-label="Expand widget">⤢</button></header>'
            + LINE
            + "</article></div>",
            TILE
            + ".stagex { position: relative; width: min(560px, 100%); height: 320px; }\n.xw { position: absolute; top: 0; left: 0; width: 240px; height: 150px; transition: width .35s var(--ease), height .35s var(--ease); }\n.xw.big { width: 100%; height: 100%; z-index: 2; box-shadow: var(--shadow); }\n.xw header { display: flex; justify-content: space-between; }\n.xw button { border: 0; background: none; color: var(--muted); }\n",
            """\
const widget = document.querySelector(".xw");
const button = widget.querySelector("button");
const set = (open) => {
  widget.classList.toggle("big", open);
  button.setAttribute("aria-expanded", String(open));
  button.setAttribute("aria-label", open ? "Collapse widget" : "Expand widget");
};
button.addEventListener("click", () => set(!widget.classList.contains("big")));
document.addEventListener("keydown", (event) => { if (event.key === "Escape") set(false); });
""",
            "Grows in place to fill its area and returns; Escape collapses.",
        ),
        Item(
            "Resizable widget",
            '<article class="t rz"><h4>Notes</h4><p>Drag the corner to resize. The widget keeps a sensible minimum and maximum.</p></article>',
            TILE
            + ".rz { width: 280px; height: 160px; min-width: 200px; min-height: 120px; max-width: min(600px, 90vw); max-height: 360px; resize: both; overflow: auto; }\n.rz p { margin: 0; color: var(--muted); font-size: 14px; }\n.rz::-webkit-resizer { background: linear-gradient(135deg, transparent 50%, var(--muted) 50%); border-radius: 0 0 12px 0; }\n",
            note="CSS resize with bounds; no script needed for a free-form resize.",
        ),
        Item(
            "Widget carousel",
            '<div class="car"><div class="track" tabindex="0" aria-label="Widgets">'
            + K4
            + kpi("Churn", "1.9%")
            + kpi("MRR", "$58k")
            + '</div><div class="nav"><button aria-label="Previous">‹</button><button aria-label="Next">›</button></div></div>',
            TILE
            + ".car { width: min(520px, 100%); }\n.track { display: flex; gap: 12px; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; padding-bottom: 4px; }\n.track::-webkit-scrollbar { display: none; }\n.track .t { flex: 0 0 160px; scroll-snap-align: start; }\n.nav { display: flex; justify-content: flex-end; gap: 6px; margin-top: 10px; }\n.nav button { width: 32px; height: 32px; border: 1px solid var(--border); border-radius: 50%; background: var(--surface); }\n",
            """\
const track = document.querySelector(".track");
const [previous, next] = document.querySelectorAll(".nav button");
const step = () => track.firstElementChild.getBoundingClientRect().width + 12;
previous.addEventListener("click", () => track.scrollBy({ left: -step(), behavior: "smooth" }));
next.addEventListener("click", () => track.scrollBy({ left: step(), behavior: "smooth" }));
""",
            "Scroll-snapped strip of widgets; the buttons scroll by one card, touch and keyboard scroll natively.",
        ),
        Item(
            "Metric strip",
            '<dl class="strip">'
            + "".join(
                f"<div><dt>{a}</dt><dd>{b}</dd></div>"
                for a, b in [
                    ("Requests", "1.2M"),
                    ("Errors", "0.04%"),
                    ("p95", "212ms"),
                    ("Apdex", "0.97"),
                    ("Uptime", "99.98%"),
                ]
            )
            + "</dl>",
            ".strip { display: flex; width: min(640px, 100%); margin: 0; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); overflow: hidden; }\n.strip div { flex: 1; padding: 12px 16px; border-right: 1px solid var(--border); }\n.strip div:last-child { border-right: 0; }\n.strip dt { font-size: 12px; color: var(--muted); }\n.strip dd { margin: 2px 0 0; font-size: 18px; font-weight: 700; font-variant-numeric: tabular-nums; }\n",
            note="A single row of figures separated by hairlines; denser than cards.",
        ),
        Item(
            "KPI ribbon",
            '<div class="ribbon">'
            + "".join(
                f'<span><b>{a}</b>{b}<i class="{c}">{d}</i></span>'
                for a, b, c, d in [
                    ("MRR", "$58.2k", "up", "▲ 5.1%"),
                    ("ARR", "$698k", "up", "▲ 5.1%"),
                    ("Churn", "1.9%", "down", "▼ 0.3"),
                    ("CAC", "$312", "down", "▲ 4%"),
                    ("LTV", "$4.1k", "up", "▲ 2%"),
                ]
            )
            + "</div>",
            ".ribbon { display: flex; gap: 28px; width: min(680px, 100%); padding: 10px 18px; border-block: 1px solid var(--border); overflow-x: auto; white-space: nowrap; }\n.ribbon span { display: flex; align-items: baseline; gap: 8px; font-weight: 700; font-variant-numeric: tabular-nums; }\n.ribbon b { font-size: 11px; font-weight: 600; letter-spacing: .08em; color: var(--muted); }\n.ribbon i { font-style: normal; font-size: 12px; }\n.up { color: var(--success); }\n.down { color: var(--danger); }\n",
            note="A thin band of labelled figures with their change, across the top of a page.",
        ),
        Item(
            "Insight ribbon",
            '<div class="insight" role="status"><span class="spark">✦</span><p><strong>Sign-ups are up 24%</strong> this week, mostly from the pricing page experiment.</p><a href="#">Explore</a><button aria-label="Dismiss">×</button></div>',
            ".insight { display: flex; align-items: center; gap: 12px; width: min(640px, 100%); padding: 10px 12px 10px 14px; border-radius: 14px;\n  border: 1px solid color-mix(in srgb, var(--primary) 45%, transparent); background: linear-gradient(90deg, color-mix(in srgb, var(--primary) 18%, transparent), transparent); }\n.spark { color: var(--accent); }\n.insight p { flex: 1; margin: 0; color: var(--muted); font-size: 14px; }\n.insight strong { color: var(--fg); }\n.insight a { color: var(--fg); font-weight: 600; font-size: 14px; }\n.insight button { border: 0; background: none; color: var(--muted); font-size: 16px; }\n",
            'document.querySelector(".insight button").addEventListener("click", (event) => event.target.closest(".insight").remove());\n',
            "One generated observation in a sentence, with a way in and a way to dismiss it.",
        ),
        Item(
            "Activity feed",
            '<ul class="feed">'
            + "".join(
                f"<li><i></i><span>{a}</span><time>{b}</time></li>"
                for a, b in [*FEED_ROWS, ("Sam invited 3 people", "1h")]
            )
            + "</ul>",
            FEED_CSS,
            note="Newest first; each row is actor, action, object and a relative time.",
        ),
        Item(
            "Live activity feed",
            '<ul class="feed" aria-live="polite" aria-label="Live activity"></ul>',
            FEED_CSS
            + ".feed li.in { animation: slide .35s var(--ease); }\n@keyframes slide { from { opacity: 0; translate: 0 -10px; } }\n",
            LIVE_JS,
            "New rows slide in at the top; the list is capped and the timer stops while hidden.",
        ),
        Item(
            "Event stream",
            '<pre class="stream" aria-live="off" tabindex="0"></pre><label class="follow"><input type="checkbox" checked> Follow</label>',
            ".stream { width: min(560px, 100%); height: 260px; margin: 0; padding: 12px 14px; overflow: auto; border: 1px solid var(--border); border-radius: 14px;\n  background: #06080c; font: 12px/1.7 var(--mono); color: #b8c0d4; white-space: pre-wrap; }\n.stream .warn { color: var(--warning); }\n.stream .err { color: var(--danger); }\n.follow { position: fixed; bottom: 18px; display: flex; gap: 8px; color: var(--muted); font-size: 13px; }\n",
            """\
const stream = document.querySelector(".stream");
const follow = document.querySelector(".follow input");
const levels = [["info", ""], ["info", ""], ["info", ""], ["warn", "warn"], ["error", "err"]];
const messages = ["GET /api/orders 200 41ms", "cache hit orders:list", "POST /api/checkout 201 180ms", "slow query 812ms", "upstream timeout payments"];
const MAX_LINES = 400;
const append = () => {
  const [level, cls] = levels[Math.floor(Math.random() * levels.length)];
  const line = document.createElement("span");
  if (cls) line.className = cls;
  line.textContent = `${new Date().toISOString().slice(11, 23)} ${level.padEnd(5)} ${messages[Math.floor(Math.random() * messages.length)]}\\n`;
  stream.append(line);
  while (stream.childElementCount > MAX_LINES) stream.firstElementChild.remove();
  if (follow.checked) stream.scrollTop = stream.scrollHeight;
};
// Scrolling up to read stops following; returning to the bottom resumes it.
stream.addEventListener("scroll", () => { follow.checked = stream.scrollHeight - stream.scrollTop - stream.clientHeight < 24; });
let timer = setInterval(append, 450);
document.addEventListener("visibilitychange", () => { clearInterval(timer); if (!document.hidden) timer = setInterval(append, 450); });
""",
            "A log tail: monospace lines, levels by colour, follows the bottom until the reader scrolls up.",
        ),
        Item(
            "System health panel",
            '<section class="health"><header><span class="orb"></span><div><strong>All systems operational</strong><small>Checked 12 seconds ago</small></div></header><ul>'
            + "".join(
                f'<li><span>{n}</span><meter min="0" max="100" value="{v}" low="60" high="85" optimum="100">{v}%</meter><b>{v}%</b></li>'
                for n, v in [("API", 99), ("Database", 97), ("Queue", 74), ("Search", 58)]
            )
            + "</ul></section>",
            ".health { width: min(420px, 100%); border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.health header { display: flex; gap: 12px; align-items: center; padding: 16px; border-bottom: 1px solid var(--border); }\n.orb { width: 12px; height: 12px; border-radius: 50%; background: var(--success); box-shadow: 0 0 0 5px color-mix(in srgb, var(--success) 22%, transparent); }\n.health small { display: block; color: var(--muted); }\n.health ul { margin: 0; padding: 8px 16px 14px; list-style: none; }\n.health li { display: grid; grid-template-columns: 90px 1fr 44px; gap: 12px; align-items: center; padding: 7px 0; font-size: 14px; }\n.health meter { width: 100%; height: 8px; }\n.health b { text-align: right; font-variant-numeric: tabular-nums; }\n",
            note="An overall verdict, then each subsystem as a native <meter> with thresholds.",
        ),
        Item(
            "Overview panel",
            '<section class="over"><header><div><h2>Northwind</h2><p>Pro plan · renews 14 May</p></div><button>Manage</button></header><dl>'
            + "".join(
                f"<div><dt>{a}</dt><dd>{b}</dd></div>"
                for a, b in [
                    ("Members", "12 of 20"),
                    ("Projects", "34"),
                    ("Storage", "18.4 GB"),
                    ("API calls", "1.2M"),
                ]
            )
            + '</dl><footer><span class="bar"><i style="width:60%"></i></span><small>60% of plan used</small></footer></section>',
            ".over { width: min(480px, 100%); padding: 18px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.over header { display: flex; justify-content: space-between; align-items: flex-start; }\n.over h2 { margin: 0; font-size: 20px; }\n.over p { margin: 2px 0 0; color: var(--muted); font-size: 14px; }\n.over button { padding: 6px 14px; border: 1px solid var(--border); border-radius: 9px; background: var(--surface-2); }\n.over dl { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 18px 0; }\n.over dt { font-size: 12px; color: var(--muted); }\n.over dd { margin: 2px 0 0; font-weight: 700; }\n.bar { display: block; height: 6px; border-radius: 99px; background: var(--surface-2); overflow: hidden; }\n.bar i { display: block; height: 100%; background: var(--primary); }\n.over small { display: block; margin-top: 6px; color: var(--muted); }\n",
            note="The summary at the top of an account or project: identity, key facts, usage.",
        ),
    ),
)
