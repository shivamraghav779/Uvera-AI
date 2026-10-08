"""Effects 401-420: navigation."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.effects_15_overlay import SPRING
from app.domains.references.vocabulary.fx import STAGE

NAMES = ("Overview", "Activity", "Members", "Settings")
TABS_HTML = (
    '<div class="tabs" role="tablist" aria-label="Sections">'
    + "".join(
        f'<button role="tab" aria-selected="{"true" if index == 0 else "false"}" tabindex="{0 if index == 0 else -1}">{label}</button>'
        for index, label in enumerate(NAMES)
    )
    + "{extra}</div>"
)
TABS_CSS = """\
.tabs { position: relative; display: flex; gap: 4px; }
.tabs button { position: relative; z-index: 1; padding: 9px 14px; border: 0; border-radius: 10px; background: none; color: var(--muted); font-weight: 600; transition: color .25s; }
.tabs button[aria-selected="true"] { color: var(--fg); }
"""
# Selection, roving tabindex and arrow keys; `onSelect(index, previous)` is the effect's hook.
TABS_JS = """\
const list = document.querySelector(".tabs");
const tabs = [...list.querySelectorAll('[role="tab"]')];
let selected = 0;
const select = (index, focus = false) => {
  const previous = selected;
  selected = (index + tabs.length) % tabs.length;
  tabs.forEach((tab, i) => { tab.setAttribute("aria-selected", i === selected); tab.tabIndex = i === selected ? 0 : -1; });
  if (focus) tabs[selected].focus();
  onSelect(selected, previous);
};
tabs.forEach((tab, index) => tab.addEventListener("click", () => select(index)));
list.addEventListener("keydown", (event) => {
  if (event.key === "ArrowRight") select(selected + 1, true);
  if (event.key === "ArrowLeft") select(selected - 1, true);
});
"""
# The shared indicator is one element; it is told where the selected tab is.
MEASURE_JS = """\
const onSelect = (index) => {
  const tab = tabs[index];
  list.style.setProperty("--left", `${tab.offsetLeft}px`);
  list.style.setProperty("--width", `${tab.offsetWidth}px`);
};
"""
START = "select(0);\n"
PANELS_HTML = (
    '<div class="panels">'
    + "".join(
        f'<div class="panel" role="tabpanel"{"" if index == 0 else " hidden"}><b>{label}</b><p>Content for the {label.lower()} tab.</p></div>'
        for index, label in enumerate(NAMES)
    )
    + "</div>"
)
PANELS_CSS = '.stage { align-content: center; gap: 14px; }\n.panels { position: relative; width: 340px; height: 96px; overflow: hidden; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.panel { position: absolute; inset: 0; padding: 16px; }\n.panel p { margin: 6px 0 0; color: var(--muted); font-size: 13px; }\n.tabs button[aria-selected="true"] { background: var(--surface-2); }\n'


def tabs(
    name: str, css: str, note: str, extra: str = "", js: str = MEASURE_JS, after: str = ""
) -> Item:
    html = f'<div class="stage">{TABS_HTML.replace("{extra}", extra)}{after}</div>'
    return Item(name, html, STAGE + TABS_CSS + css, js + TABS_JS + START, note)


ICONS = ("⌂", "◔", "☰", "✉", "⚙")
LABELS = ("Home", "Reports", "Projects", "Inbox", "Settings")
SIDE_HTML = (
    '<div class="stage shell"><nav class="side" aria-label="Main"><button class="toggle" aria-expanded="{open}" aria-label="Toggle sidebar">☰</button>'
    + "".join(
        f'<a href="#" class="{"here" if index == 0 else ""}"><i aria-hidden="true">{icon}</i><span>{label}</span></a>'
        for index, (icon, label) in enumerate(zip(ICONS[:4], LABELS[:4], strict=True))
    )
    + '</nav><div class="main"><b>Dashboard</b><p>The content area takes whatever room the sidebar leaves.</p></div></div>'
)
SIDE_CSS = """\
.shell { display: flex; place-items: stretch; overflow: hidden; border: 1px solid var(--border); border-radius: 18px; background: var(--bg); }
.side { display: grid; align-content: start; gap: 4px; flex: none; width: 56px; padding: 10px 8px; overflow: hidden; background: var(--surface); border-right: 1px solid var(--border); }
.side:has(.toggle[aria-expanded="true"]) { width: 170px; }
.side a, .toggle { display: flex; align-items: center; gap: 12px; height: 38px; padding: 0 11px; border: 0; border-radius: 10px; background: none; color: var(--muted); text-decoration: none; white-space: nowrap; font-weight: 600; font-size: 13px; }
.side i { flex: none; width: 18px; text-align: center; font-style: normal; font-size: 16px; }
.side a.here { background: var(--surface-2); color: var(--fg); }
.side span { opacity: 0; transition: opacity .2s; }
.side:has(.toggle[aria-expanded="true"]) span { opacity: 1; }
.main { flex: 1; min-width: 0; padding: 18px; }
.main p { margin: 6px 0 0; color: var(--muted); font-size: 13px; }
"""
SIDE_JS = 'const toggle = document.querySelector(".toggle");\ntoggle.addEventListener("click", () => toggle.setAttribute("aria-expanded", toggle.getAttribute("aria-expanded") !== "true"));\n'


def sidebar(name: str, css: str, note: str, expanded: bool = False, js: str = SIDE_JS) -> Item:
    return Item(
        name,
        SIDE_HTML.replace("{open}", "true" if expanded else "false"),
        STAGE + SIDE_CSS + css,
        js,
        note,
    )


ROUTE_HTML = (
    '<div class="stage"><div class="device"><nav class="links" aria-label="Pages">'
    + "".join(
        f"<button{' aria-current="page"' if index == 0 else ''}>{label}</button>"
        for index, label in enumerate(("Home", "Pricing", "Docs"))
    )
    + '</nav><div class="view">'
    + "".join(
        f'<section class="route"{"" if index == 0 else " hidden"}><h3>{title}</h3><p>{text}</p></section>'
        for index, (title, text) in enumerate(
            (
                ("Home", "Where every visit starts."),
                ("Pricing", "Three plans, billed monthly."),
                ("Docs", "Guides and the API reference."),
            )
        )
    )
    + "</div></div></div>"
)
ROUTE_CSS = """\
.device { width: 340px; overflow: hidden; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }
.links { display: flex; gap: 4px; padding: 8px; border-bottom: 1px solid var(--border); }
.links button { padding: 6px 12px; border: 0; border-radius: 8px; background: none; color: var(--muted); font-weight: 600; }
.links button[aria-current="page"] { background: var(--surface-2); color: var(--fg); }
.view { position: relative; height: 130px; overflow: hidden; }
.route { position: absolute; inset: 0; padding: 18px; }
.route h3 { margin: 0 0 6px; }
.route p { margin: 0; color: var(--muted); }
"""
# The outgoing route stays in the page until its exit animation has ended, then is hidden.
ROUTE_JS = """\
const links = [...document.querySelectorAll(".links button")];
const routes = [...document.querySelectorAll(".route")];
const view = document.querySelector(".view");
const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
let current = 0;
const go = (index) => {
  if (index === current) return;
  const leaving = routes[current], entering = routes[index];
  view.dataset.direction = index > current ? "forward" : "back";
  links.forEach((link, i) => { if (i === index) link.setAttribute("aria-current", "page"); else link.removeAttribute("aria-current"); });
  routes.forEach((route) => route.classList.remove("in", "out"));
  entering.hidden = false;
  current = index;
  if (calm) { leaving.hidden = true; return; }
  entering.classList.add("in"); leaving.classList.add("out");
  leaving.addEventListener("animationend", () => { if (leaving !== routes[current]) leaving.hidden = true; leaving.classList.remove("out"); }, { once: true });
};
links.forEach((link, index) => link.addEventListener("click", () => go(index)));
"""


def routed(name: str, css: str, note: str) -> Item:
    return Item(name, ROUTE_HTML, STAGE + ROUTE_CSS + css, ROUTE_JS, note)


PANEL_SWITCH = """\
const panels = [...document.querySelectorAll(".panel")];
const onSelect = (index, previous) => {
  if (index === previous) return;
  const stage = document.querySelector(".panels");
  stage.dataset.direction = index > previous ? "forward" : "back";
  panels.forEach((panel, i) => { panel.classList.remove("in", "out"); panel.hidden = i !== index && i !== previous; });
  panels[index].classList.add("in"); panels[previous].classList.add("out");
  panels[previous].addEventListener("animationend", () => { if (previous !== selected) panels[previous].hidden = true; panels[previous].classList.remove("out"); }, { once: true });
};
"""

SECTION = Section(
    "effects",
    "Navigation Effects",
    401,
    (
        tabs(
            "Active indicator slide",
            ".tabs { border-bottom: 1px solid var(--border); }\n.ind { position: absolute; left: 0; bottom: -1px; width: var(--width); height: 2px; background: var(--primary); translate: var(--left) 0; transition: translate .35s var(--ease), width .35s var(--ease); }\n",
            "One underline shared by all tabs: it travels to the selected tab and takes that tab's width.",
            '<i class="ind"></i>',
        ),
        tabs(
            "Active indicator morph",
            ".ind { position: absolute; top: 0; bottom: 0; left: var(--left); right: var(--right); border-radius: 10px; background: var(--surface-2); }\n"
            "/* The edge facing the direction of travel leaves first; the other follows, so the pill stretches and then contracts. */\n"
            '.tabs[data-direction="forward"] .ind { transition: right .25s var(--ease), left .25s var(--ease) .12s; }\n.tabs[data-direction="back"] .ind { transition: left .25s var(--ease), right .25s var(--ease) .12s; }\n',
            "The pill stretches toward the new tab before its trailing edge lets go, like a drop of liquid being pulled across.",
            '<i class="ind"></i>',
            js='const onSelect = (index, previous) => {\n  const tab = tabs[index];\n  list.dataset.direction = index >= previous ? "forward" : "back";\n  list.style.setProperty("--left", `${tab.offsetLeft}px`);\n  list.style.setProperty("--right", `${list.offsetWidth - tab.offsetLeft - tab.offsetWidth}px`);\n};\n',
        ),
        tabs(
            "Active indicator glow",
            ".tabs { border-bottom: 1px solid var(--border); }\n.ind { position: absolute; left: 0; bottom: -1px; width: var(--width); height: 2px; background: var(--accent); box-shadow: 0 0 10px var(--accent), 0 -6px 20px 4px rgb(34 211 238 / .35); translate: var(--left) 0; transition: translate .4s var(--ease), width .4s var(--ease); }\n",
            "The sliding underline is a light source: it throws a soft glow up into the tab it sits beneath.",
            '<i class="ind"></i>',
        ),
        tabs(
            "Active tab underline",
            '.tabs button::after { content: ""; position: absolute; left: 14px; right: 14px; bottom: 2px; height: 2px; border-radius: 2px; background: var(--primary); scale: 0 1; transition: scale .3s var(--ease); }\n.tabs button[aria-selected="true"]::after { scale: 1 1; }\n',
            "Each tab owns its underline, which grows from its centre when selected. Nothing needs measuring, so no script is involved in the effect.",
            js="const onSelect = () => {};\n",
        ),
        tabs(
            "Active tab pill",
            '.tabs { padding: 4px; border-radius: 14px; background: var(--surface); border: 1px solid var(--border); }\n.ind { position: absolute; top: 4px; bottom: 4px; left: 0; width: var(--width); border-radius: 10px; background: var(--primary); translate: var(--left) 0; transition: translate .35s var(--ease), width .35s var(--ease); }\n.tabs button[aria-selected="true"] { color: #fff; }\n',
            "A segmented control: a filled pill slides under the labels to the selected one.",
            '<i class="ind"></i>',
        ),
        tabs(
            "Tab background transition",
            '.tabs button { transition: color .25s, background-color .35s; }\n.tabs button[aria-selected="true"] { background-color: var(--surface-2); }\n.tabs button:hover { background-color: color-mix(in srgb, var(--surface-2) 50%, transparent); }\n',
            "No moving part: the old tab's background fades out as the new one's fades in.",
            js="const onSelect = () => {};\n",
        ),
        tabs(
            "Tab content slide",
            PANELS_CSS
            + '.panel.in { animation: enter .35s var(--ease) both; }\n.panel.out { animation: leave .35s var(--ease) both; }\n/* Forward: the new panel comes from the right. Back: from the left. */\n.panels[data-direction="forward"] { --from: 100%; --to: -100%; }\n.panels[data-direction="back"] { --from: -100%; --to: 100%; }\n@keyframes enter { from { translate: var(--from) 0; } }\n@keyframes leave { to { translate: var(--to) 0; } }\n',
            "Panels behave as if laid side by side: choosing a later tab slides the content left, an earlier one slides it right.",
            js=PANEL_SWITCH,
            after=PANELS_HTML,
        ),
        tabs(
            "Tab content fade",
            PANELS_CSS
            + ".panel.in { animation: enter .3s ease-out .1s both; }\n.panel.out { animation: leave .2s ease-in both; }\n@keyframes enter { from { opacity: 0; translate: 0 6px; } }\n@keyframes leave { to { opacity: 0; } }\n",
            "The old panel fades out and the new one fades in just after it, rising a few pixels.",
            js=PANEL_SWITCH,
            after=PANELS_HTML,
        ),
        sidebar(
            "Sidebar expansion",
            ".side { transition: width .3s var(--ease); }\n.side span { transition-delay: .1s; }\n",
            "A rail of icons widens to show labels. The labels fade in slightly after the width starts to change.",
        ),
        sidebar(
            "Sidebar collapse",
            ".side { transition: width .3s var(--ease) .08s; }\n",
            "The reverse order: labels fade first, then the width closes over them, so no text is seen being cut off.",
            expanded=True,
        ),
        sidebar(
            "Sidebar spring",
            f".side {{ transition: width .6s {SPRING}; }}\n",
            "The sidebar overshoots its width a little and settles, in both directions.",
        ),
        sidebar(
            "Sidebar morph",
            ".shell { position: relative; }\n.side { position: absolute; z-index: 1; left: 0; top: 0; bottom: 0; transition: all .5s var(--ease); }\n.main { padding-left: 76px; transition: padding .5s var(--ease); }\n"
            "/* Toggled: the full-height rail becomes a floating dock along the bottom. */\n"
            '.side:has(.toggle[aria-expanded="true"]) { top: auto; left: 50%; bottom: 12px; translate: -50% 0; display: flex; width: 240px; padding: 6px; border: 1px solid var(--border); border-radius: 99px; box-shadow: 0 14px 34px rgb(0 0 0 / .5); }\n'
            '.side:has(.toggle[aria-expanded="true"]) span { display: none; }\n.shell:has(.toggle[aria-expanded="true"]) .main { padding-left: 18px; }\n',
            "One element, two shapes: the side rail turns into a floating pill-shaped dock, with size, position and corner radius all animating.",
        ),
        sidebar(
            "Sidebar item highlight",
            ".side { position: relative; width: 170px; }\n.side span { opacity: 1; }\n.toggle { display: none; }\n.side a.here { background: none; }\n.side a { position: relative; z-index: 1; }\n"
            ".glide { position: absolute; left: 8px; right: 8px; top: 0; height: 38px; border-radius: 10px; background: var(--surface-2); translate: 0 var(--top, 10px); opacity: var(--shown, 0); transition: translate .22s var(--ease), opacity .2s; }\n",
            "One highlight follows the pointer from item to item instead of each item lighting up separately; keyboard focus moves it too.",
            js='const nav = document.querySelector(".side");\nconst glide = nav.appendChild(Object.assign(document.createElement("i"), { className: "glide" }));\nconst rest = () => nav.querySelector(".here");\nconst moveTo = (item) => { nav.style.setProperty("--top", `${item.offsetTop}px`); nav.style.setProperty("--shown", 1); };\nnav.querySelectorAll("a").forEach((item) => {\n  item.addEventListener("pointerenter", () => moveTo(item));\n  item.addEventListener("focus", () => moveTo(item));\n});\n// Leaving returns the highlight to the current page.\nnav.addEventListener("pointerleave", () => moveTo(rest()));\nmoveTo(rest());\n',
        ),
        sidebar(
            "Sidebar active glow",
            '.side { width: 170px; }\n.side span { opacity: 1; }\n.toggle { display: none; }\n.side a { position: relative; transition: color .3s, background .3s; }\n.side a.here { background: linear-gradient(90deg, rgb(124 92 255 / .28), transparent 80%); color: #fff; }\n.side a::before { content: ""; position: absolute; left: -8px; top: 8px; bottom: 8px; width: 3px; border-radius: 0 3px 3px 0; background: var(--primary); box-shadow: 0 0 12px 2px var(--primary); scale: 1 0; transition: scale .3s var(--ease); }\n.side a.here::before { scale: 1 1; }\n',
            "The current item is marked by a glowing bar at the edge and a wash of the same colour fading across it. Click another item to move it.",
            js='const items = [...document.querySelectorAll(".side a")];\nitems.forEach((item) => item.addEventListener("click", (event) => {\n  event.preventDefault();\n  items.forEach((other) => { other.classList.toggle("here", other === item); if (other === item) other.setAttribute("aria-current", "page"); else other.removeAttribute("aria-current"); });\n}));\n',
        ),
        Item(
            "Breadcrumb transition",
            '<div class="stage"><nav aria-label="Breadcrumb"><ol class="crumbs"></ol></nav><button class="deeper">Go deeper</button></div>',
            STAGE
            + ".stage { align-content: center; gap: 18px; }\n.crumbs { display: flex; flex-wrap: wrap; align-items: center; margin: 0; padding: 0; list-style: none; min-height: 30px; }\n"
            ".crumbs li { display: flex; align-items: center; animation: arrive .3s var(--ease) both; }\n.crumbs li.gone { animation: depart .2s ease-in both; }\n"
            '.crumbs li + li::before { content: "/"; margin: 0 8px; color: var(--muted); }\n.crumbs button { padding: 4px 6px; border: 0; border-radius: 6px; background: none; color: var(--muted); font-weight: 600; }\n.crumbs li:last-child button { color: var(--fg); }\n'
            ".deeper { padding: 8px 14px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }\n"
            "@keyframes arrive { from { opacity: 0; translate: -10px 0; } }\n@keyframes depart { to { opacity: 0; translate: 10px 0; } }\n",
            """\
const list = document.querySelector(".crumbs");
const TRAIL = ["Home", "Projects", "Aurora", "Design", "Tokens"];
const add = (label) => {
  const item = document.createElement("li");
  const link = Object.assign(document.createElement("button"), { textContent: label });
  link.addEventListener("click", () => cutAfter(item));
  item.append(link);
  list.append(item);
  mark();
};
// Going up: everything after the chosen crumb leaves, last first.
const cutAfter = (item) => {
  const later = [...list.children].slice([...list.children].indexOf(item) + 1).filter((crumb) => !crumb.classList.contains("gone"));
  later.reverse().forEach((crumb, index) => {
    crumb.style.animationDelay = `${index * 50}ms`;
    crumb.classList.add("gone");
    crumb.addEventListener("animationend", () => { crumb.remove(); mark(); }, { once: true });
  });
};
const mark = () => [...list.children].forEach((crumb, index, all) => {
  if (index === all.length - 1) crumb.firstChild.setAttribute("aria-current", "page"); else crumb.firstChild.removeAttribute("aria-current");
});
document.querySelector(".deeper").addEventListener("click", () => {
  const depth = list.querySelectorAll("li:not(.gone)").length;
  if (depth < TRAIL.length) add(TRAIL[depth]);
});
TRAIL.slice(0, 3).forEach(add);
""",
            "Going deeper, the new crumb slides in at the end. Clicking an earlier crumb removes the later ones one at a time, from the end.",
        ),
        routed(
            "Page transition",
            ".route.in { animation: enter .45s var(--ease) both; }\n.route.out { animation: leave .45s var(--ease) both; }\n@keyframes enter { from { translate: 0 100%; } }\n@keyframes leave { to { scale: .92; opacity: 0; } }\n.route { background: var(--surface); }\n.route.in { z-index: 1; box-shadow: 0 -10px 30px rgb(0 0 0 / .4); }\n",
            "A new page rises over the old one like a card, while the old page shrinks back and fades.",
        ),
        routed(
            "Route fade",
            ".route.in { animation: enter .3s ease-out .12s both; }\n.route.out { animation: leave .15s ease-in both; }\n@keyframes enter { from { opacity: 0; } }\n@keyframes leave { to { opacity: 0; } }\n",
            "The old view fades out quickly and the new one fades in after it: the neutral default for unrelated pages.",
        ),
        routed(
            "Route slide",
            '.route.in { animation: enter .4s var(--ease) both; }\n.route.out { animation: leave .4s var(--ease) both; }\n.view[data-direction="forward"] { --from: 100%; --to: -30%; }\n.view[data-direction="back"] { --from: -100%; --to: 30%; }\n@keyframes enter { from { translate: var(--from) 0; } }\n@keyframes leave { to { translate: var(--to) 0; opacity: 0; } }\n',
            "Forward navigation brings the new view in from the right; going back brings it from the left. The old view moves a shorter distance, as if it were further away.",
        ),
        Item(
            "Route morph",
            '<div class="stage"><div class="device"><div class="list"><button class="row"><i class="thumb"></i><span><b>Aurora plan</b><small>Open details</small></span></button></div>'
            '<div class="detail" hidden><i class="thumb"></i><h3>Aurora plan</h3><p>The thumbnail grew into this header.</p><button class="back">Back</button></div></div></div>',
            STAGE
            + ".device { width: 340px; height: 190px; overflow: hidden; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n"
            ".list { padding: 14px; }\n.row { display: flex; align-items: center; gap: 12px; width: 100%; padding: 10px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); color: inherit; text-align: left; }\n.row span { display: grid; }\n.row small { color: var(--muted); }\n"
            ".thumb { display: block; flex: none; width: 48px; height: 48px; border-radius: 12px; background: linear-gradient(135deg, #7c5cff, #22d3ee); }\n"
            ".detail .thumb { width: 100%; height: 76px; border-radius: 0; }\n.detail h3 { margin: 10px 16px 2px; }\n.detail p { margin: 0 16px 8px; color: var(--muted); font-size: 13px; }\n.back { margin-left: 16px; padding: 5px 12px; border: 1px solid var(--border); border-radius: 8px; background: none; color: inherit; }\n"
            "/* Whichever thumbnail is on screen carries the name, so the browser pairs the old and new one and animates between them. */\n"
            ".list:not([hidden]) .thumb, .detail:not([hidden]) .thumb { view-transition-name: hero; }\n::view-transition-group(hero) { animation-duration: .45s; animation-timing-function: cubic-bezier(.2, .8, .2, 1); }\n",
            """\
const list = document.querySelector(".list");
const detail = document.querySelector(".detail");
const swap = (showDetail) => { list.hidden = showDetail; detail.hidden = !showDetail; (showDetail ? detail.querySelector(".back") : list.querySelector(".row")).focus(); };
// With the View Transitions API the shared element morphs; without it the views simply swap.
const navigate = (showDetail) => {
  if (document.startViewTransition && !matchMedia("(prefers-reduced-motion: reduce)").matches) document.startViewTransition(() => swap(showDetail));
  else swap(showDetail);
};
list.querySelector(".row").addEventListener("click", () => navigate(true));
detail.querySelector(".back").addEventListener("click", () => navigate(false));
""",
            "A shared element: the list thumbnail grows into the detail page's header instead of one view replacing the other. Uses the View Transitions API, and falls back to an instant swap where it is missing.",
        ),
        Item(
            "Navigation indicator animation",
            '<div class="stage"><nav class="dock" aria-label="Main">'
            + "".join(
                f'<button aria-label="{label}"{' aria-current="page"' if index == 0 else ""}><i aria-hidden="true">{icon}</i></button>'
                for index, (icon, label) in enumerate(zip(ICONS, LABELS, strict=True))
            )
            + '<i class="blob"></i></nav></div>',
            STAGE
            + ".dock { position: relative; display: flex; padding: 8px; border: 1px solid var(--border); border-radius: 22px; background: var(--surface); }\n"
            ".dock button { position: relative; z-index: 1; width: 56px; height: 48px; border: 0; background: none; color: var(--muted); font-size: 20px; transition: color .3s; }\n.dock button i { display: block; font-style: normal; transition: translate .4s "
            + SPRING
            + ", scale .4s "
            + SPRING
            + "; }\n"
            '.dock button[aria-current="page"] { color: #fff; }\n.dock button[aria-current="page"] i { translate: 0 -3px; scale: 1.2; }\n'
            "/* The blob stretches while it travels and springs back to a circle when it lands. */\n"
            ".blob { position: absolute; left: 8px; top: 8px; width: 56px; height: 48px; border-radius: 16px; background: linear-gradient(135deg, var(--primary), var(--accent)); translate: calc(var(--at, 0) * 56px) 0; transition: translate .5s "
            + SPRING
            + "; }\n.blob.moving { animation: stretch .45s ease-out; }\n@keyframes stretch { 40% { scale: 1.35 .7; } }\n",
            """\
const dock = document.querySelector(".dock");
const buttons = [...dock.querySelectorAll("button")];
const blob = dock.querySelector(".blob");
buttons.forEach((button, index) => button.addEventListener("click", () => {
  buttons.forEach((other) => other.removeAttribute("aria-current"));
  button.setAttribute("aria-current", "page");
  dock.style.setProperty("--at", index);
  blob.classList.remove("moving"); void blob.offsetWidth; blob.classList.add("moving");
}));
""",
            "A dock whose marker springs to the chosen item, stretching as it travels; the icon it lands under lifts and grows.",
        ),
    ),
)
