"""Patterns 1-40: navigation and the application shell."""

from app.domains.references.vocabulary.base import BTN, Item, Section

IC = ".ic { width: 16px; height: 16px; border-radius: 5px; background: currentColor; opacity: .75; flex: none; }\n"
LINKS = '<a href="#" aria-current="page">Overview</a><a href="#">Projects</a><a href="#">Reports</a><a href="#">Team</a>'
BRAND = '<a class="brand" href="#"><span class="mark"></span>Northwind</a>'
BAR = (
    """\
.bar { display: flex; align-items: center; gap: 24px; width: min(820px, 100%); height: 60px; padding: 0 20px;
  border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }
.brand { display: flex; align-items: center; gap: 10px; font-weight: 700; color: var(--fg); text-decoration: none; }
.mark { width: 26px; height: 26px; border-radius: 8px; background: linear-gradient(135deg, var(--primary), var(--accent)); }
.bar nav { display: flex; gap: 4px; flex: 1; }
.bar nav a { padding: 8px 12px; border-radius: 8px; color: var(--muted); text-decoration: none; font-weight: 500;
  transition: background .15s, color .15s; }
.bar nav a:hover { color: var(--fg); background: var(--surface-2); }
.bar nav a[aria-current="page"] { color: var(--fg); background: var(--surface-2); }
"""
    + BTN
)
SIDE = (
    """\
.side { display: flex; flex-direction: column; gap: 4px; width: 240px; height: 440px; padding: 14px;
  border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }
.side a { display: flex; align-items: center; gap: 10px; padding: 9px 10px; border-radius: 9px; color: var(--muted);
  text-decoration: none; font-weight: 500; white-space: nowrap; transition: background .15s, color .15s; }
.side a:hover { background: var(--surface-2); color: var(--fg); }
.side a[aria-current="page"] { background: color-mix(in srgb, var(--primary) 18%, transparent); color: var(--fg); }
.side h4 { margin: 14px 10px 4px; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
"""
    + IC
)
SIDE_LINKS = (
    '<a href="#" aria-current="page"><i class="ic"></i><span>Dashboard</span></a>'
    '<a href="#"><i class="ic"></i><span>Inbox</span></a>'
    '<a href="#"><i class="ic"></i><span>Projects</span></a>'
    '<a href="#"><i class="ic"></i><span>Analytics</span></a>'
    '<a href="#"><i class="ic"></i><span>Settings</span></a>'
)
SWITCHER_CSS = """\
.switcher { position: relative; width: 280px; }
.switcher > button { display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px 12px; text-align: left;
  border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }
.switcher > button::after { content: ""; margin-left: auto; width: 8px; height: 8px; border: solid var(--muted);
  border-width: 0 2px 2px 0; transform: rotate(45deg) translateY(-2px); }
.avatar { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 8px; font-weight: 700; font-size: 12px;
  background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; flex: none; }
.switcher small { display: block; color: var(--muted); font-size: 12px; }
.switcher ul { position: absolute; inset: calc(100% + 6px) 0 auto; margin: 0; padding: 6px; list-style: none; z-index: 2;
  border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); box-shadow: var(--shadow); }
.switcher ul[hidden] { display: none; }
.switcher li { display: flex; align-items: center; gap: 10px; padding: 8px; border-radius: 8px; cursor: pointer; }
.switcher li:hover, .switcher li[aria-selected="true"] { background: color-mix(in srgb, var(--primary) 16%, transparent); }
"""
SWITCHER_JS = """\
const root = document.querySelector(".switcher");
const button = root.querySelector("button");
const list = root.querySelector("ul");
button.addEventListener("click", () => {
  list.hidden = !list.hidden;
  button.setAttribute("aria-expanded", String(!list.hidden));
});
list.addEventListener("click", (event) => {
  const option = event.target.closest("li");
  if (!option) return;
  list.querySelectorAll("li").forEach((item) => item.setAttribute("aria-selected", String(item === option)));
  button.querySelector("strong").textContent = option.dataset.name;
  button.querySelector(".avatar").textContent = option.dataset.name[0];
  list.hidden = true;
});
document.addEventListener("click", (event) => { if (!root.contains(event.target)) list.hidden = true; });
"""


def switcher(label: str, options: list[tuple[str, str]], note: str) -> Item:
    first = options[0]
    rows = "".join(
        f'<li role="option" data-name="{name}" aria-selected="{str(i == 0).lower()}">'
        f'<span class="avatar">{name[0]}</span><span>{name}<small>{meta}</small></span></li>'
        for i, (name, meta) in enumerate(options)
    )
    html = (
        f'<div class="switcher"><button type="button" aria-haspopup="listbox" aria-expanded="false">'
        f'<span class="avatar">{first[0][0]}</span><span><small>{label}</small><strong>{first[0]}</strong></span></button>'
        f'<ul role="listbox" aria-label="{label}" hidden>{rows}</ul></div>'
    )
    return Item(f"{label} switcher", html, SWITCHER_CSS, SWITCHER_JS, note)


SECTION = Section(
    "patterns",
    "Navigation & App Shell",
    1,
    (
        Item(
            "Top navigation bar",
            f'<header class="bar">{BRAND}<nav aria-label="Main">{LINKS}</nav><button class="btn">New project</button></header>',
            BAR,
            note="Brand left, primary destinations in the middle, one primary action right.",
        ),
        Item(
            "Floating navigation bar",
            f'<header class="bar float">{BRAND}<nav aria-label="Main">{LINKS}</nav><button class="btn">Sign in</button></header>',
            BAR
            + """\
.float { position: fixed; top: 16px; left: 50%; translate: -50% 0; width: min(760px, calc(100% - 32px)); border-radius: 999px;
  padding: 0 10px 0 20px; background: color-mix(in srgb, var(--surface) 82%, transparent); backdrop-filter: blur(14px);
  box-shadow: 0 10px 40px -12px rgb(0 0 0 / .6); }
.float .btn { border-radius: 999px; }
""",
            note="Detached from the edges; pill shape and blur keep content readable beneath it.",
        ),
        Item(
            "Transparent navigation",
            f'<section class="hero"><header class="bar clear">{BRAND}<nav aria-label="Main">{LINKS}</nav></header><h1>Over imagery</h1></section>',
            BAR
            + """\
.hero { width: min(820px, 100%); height: 300px; border-radius: var(--radius); overflow: hidden; display: grid; align-content: start;
  background: radial-gradient(120% 120% at 20% 0%, #4338ca, #0b0d12 70%); }
.hero h1 { margin: 60px 24px 0; font-size: 44px; letter-spacing: -.02em; }
.clear { width: 100%; border: 0; border-radius: 0; background: transparent; }
.clear nav a, .clear .brand { color: #fff; }
.clear nav a[aria-current="page"], .clear nav a:hover { background: rgb(255 255 255 / .14); }
""",
            note="No background of its own; sits on a hero and inherits its colour.",
        ),
        Item(
            "Glass navigation",
            f'<section class="scene"><header class="bar glass">{BRAND}<nav aria-label="Main">{LINKS}</nav></header></section>',
            BAR
            + """\
.scene { width: min(820px, 100%); height: 220px; padding: 20px; border-radius: var(--radius);
  background: conic-gradient(from 210deg at 60% 40%, #7c5cff, #22d3ee, #f472b6, #7c5cff); }
.glass { width: 100%; border-color: rgb(255 255 255 / .28); background: rgb(255 255 255 / .12);
  backdrop-filter: blur(18px) saturate(1.5); box-shadow: inset 0 1px 0 rgb(255 255 255 / .35), 0 12px 30px -14px rgb(0 0 0 / .5); }
.glass nav a, .glass .brand { color: #fff; }
.glass nav a[aria-current="page"], .glass nav a:hover { background: rgb(255 255 255 / .18); }
""",
            note="Backdrop blur plus a light inner edge; needs colourful content behind to read as glass.",
        ),
        Item(
            "Sidebar navigation",
            f'<nav class="side" aria-label="Main"><h4>Workspace</h4>{SIDE_LINKS}</nav>',
            SIDE,
            note="The default shell for tools with five or more destinations.",
        ),
        Item(
            "Collapsible sidebar",
            f'<nav class="side" aria-label="Main"><button class="toggle" aria-expanded="true" aria-label="Collapse sidebar"></button>{SIDE_LINKS}</nav>',
            SIDE
            + """\
.side { transition: width .28s var(--ease); overflow: hidden; }
.side.collapsed { width: 66px; }
.side.collapsed span { opacity: 0; }
.side span { transition: opacity .18s; }
.toggle { align-self: flex-end; width: 30px; height: 30px; margin-bottom: 6px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--surface-2); flex: none; }
.toggle::before { content: "‹"; display: block; transition: rotate .28s var(--ease); }
.side.collapsed .toggle::before { rotate: 180deg; }
""",
            """\
const side = document.querySelector(".side");
const toggle = side.querySelector(".toggle");
toggle.addEventListener("click", () => {
  const collapsed = side.classList.toggle("collapsed");
  toggle.setAttribute("aria-expanded", String(!collapsed));
  toggle.setAttribute("aria-label", collapsed ? "Expand sidebar" : "Collapse sidebar");
});
""",
            "Width animates between full and icon-only; labels fade rather than wrap.",
        ),
        Item(
            "Mini sidebar",
            f'<nav class="side mini" aria-label="Main">{SIDE_LINKS}</nav>',
            SIDE
            + """\
.mini { width: 92px; align-items: stretch; }
.mini a { flex-direction: column; gap: 5px; padding: 10px 4px; font-size: 11px; text-align: center; }
.mini .ic { width: 20px; height: 20px; }
""",
            note="Icon above a short label; half the width of a full sidebar without losing the words.",
        ),
        Item(
            "Icon-only sidebar",
            '<nav class="side icons" aria-label="Main">'
            '<a href="#" aria-current="page" data-tip="Dashboard"><i class="ic"></i></a><a href="#" data-tip="Inbox"><i class="ic"></i></a>'
            '<a href="#" data-tip="Projects"><i class="ic"></i></a><a href="#" data-tip="Settings"><i class="ic"></i></a></nav>',
            SIDE
            + """\
.icons { width: 62px; align-items: center; overflow: visible; }
.icons a { position: relative; justify-content: center; width: 40px; height: 40px; padding: 0; }
.icons a::after { content: attr(data-tip); position: absolute; left: calc(100% + 10px); padding: 4px 8px; border-radius: 6px;
  background: var(--fg); color: var(--bg); font-size: 12px; opacity: 0; translate: -4px 0; pointer-events: none;
  transition: opacity .15s, translate .15s; }
.icons a:hover::after, .icons a:focus-visible::after { opacity: 1; translate: 0 0; }
""",
            note="Every icon needs a tooltip and an accessible name; use only when icons are unmistakable.",
        ),
        Item(
            "Nested sidebar",
            '<nav class="side" aria-label="Main"><a href="#"><i class="ic"></i><span>Dashboard</span></a>'
            '<details open><summary><i class="ic"></i>Projects</summary><a href="#" aria-current="page">Roadmap</a><a href="#">Backlog</a><a href="#">Archive</a></details>'
            '<details><summary><i class="ic"></i>Reports</summary><a href="#">Weekly</a><a href="#">Quarterly</a></details></nav>',
            SIDE
            + """\
.side summary { display: flex; align-items: center; gap: 10px; padding: 9px 10px; border-radius: 9px; cursor: pointer;
  color: var(--muted); font-weight: 500; list-style: none; }
.side summary::after { content: "›"; margin-left: auto; transition: rotate .2s var(--ease); }
.side details[open] > summary::after { rotate: 90deg; }
.side summary:hover { background: var(--surface-2); color: var(--fg); }
.side details a { margin-left: 18px; padding-left: 16px; border-left: 1px solid var(--border); border-radius: 0 9px 9px 0; }
""",
            note="Native <details> gives keyboard support and state for free.",
        ),
        Item(
            "Command sidebar",
            f'<nav class="side" aria-label="Main"><label class="cmd"><input placeholder="Jump to…" aria-label="Filter navigation"><kbd>/</kbd></label>{SIDE_LINKS}<p class="none" hidden>No match</p></nav>',
            SIDE
            + """\
.cmd { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; padding: 0 10px; height: 38px;
  border: 1px solid var(--border); border-radius: 9px; background: var(--bg); }
.cmd input { flex: 1; min-width: 0; border: 0; outline: 0; background: none; }
.cmd:focus-within { border-color: var(--primary); }
kbd { padding: 1px 6px; border: 1px solid var(--border); border-radius: 5px; font: 11px var(--mono); color: var(--muted); }
.none { margin: 8px 10px; color: var(--muted); }
""",
            """\
const input = document.querySelector(".cmd input");
const links = [...document.querySelectorAll(".side a")];
const none = document.querySelector(".none");
input.addEventListener("input", () => {
  const query = input.value.trim().toLowerCase();
  let shown = 0;
  for (const link of links) {
    link.hidden = !link.textContent.toLowerCase().includes(query);
    if (!link.hidden) shown += 1;
  }
  none.hidden = shown > 0;
});
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter") links.find((link) => !link.hidden)?.click();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "/" && document.activeElement !== input) { event.preventDefault(); input.focus(); }
});
""",
            "A filter field on top of the sidebar; '/' focuses it, Enter opens the first match.",
        ),
        Item(
            "Bottom navigation",
            '<div class="phone"><main>Content</main><nav class="bottom" aria-label="Main">'
            '<a href="#" aria-current="page"><i class="ic"></i>Home</a><a href="#"><i class="ic"></i>Search</a>'
            '<a href="#"><i class="ic"></i>Saved</a><a href="#"><i class="ic"></i>Profile</a></nav></div>',
            IC
            + """\
.phone { display: grid; grid-template-rows: 1fr auto; width: 320px; height: 460px; border: 1px solid var(--border);
  border-radius: 28px; overflow: hidden; background: var(--surface); }
.phone main { display: grid; place-items: center; color: var(--muted); }
.bottom { display: flex; border-top: 1px solid var(--border); padding: 6px 6px calc(6px + env(safe-area-inset-bottom)); }
.bottom a { flex: 1; display: grid; justify-items: center; gap: 3px; padding: 8px 0; border-radius: 12px; font-size: 11px;
  color: var(--muted); text-decoration: none; }
.bottom a[aria-current="page"] { color: var(--primary); }
""",
            note="Three to five destinations on phones; respects the safe-area inset.",
        ),
        Item(
            "Tab bar",
            '<div class="tabs" role="tablist" aria-label="Views"><button role="tab" aria-selected="true">Overview</button>'
            '<button role="tab" aria-selected="false">Activity</button><button role="tab" aria-selected="false">Files</button>'
            '<button role="tab" aria-selected="false">Settings</button></div>',
            """\
.tabs { display: flex; gap: 4px; width: min(520px, 100%); border-bottom: 1px solid var(--border); }
.tabs button { position: relative; padding: 12px 14px; border: 0; background: none; color: var(--muted); font-weight: 500; }
.tabs button:hover { color: var(--fg); }
.tabs button[aria-selected="true"] { color: var(--fg); }
.tabs button[aria-selected="true"]::after { content: ""; position: absolute; inset: auto 8px -1px; height: 2px;
  border-radius: 2px; background: var(--primary); }
""",
            """\
const tabs = [...document.querySelectorAll('[role="tab"]')];
const select = (tab) => tabs.forEach((item) => {
  item.setAttribute("aria-selected", String(item === tab));
  item.tabIndex = item === tab ? 0 : -1;
});
tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => select(tab));
  tab.addEventListener("keydown", (event) => {
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    const next = tabs[(index + step + tabs.length) % tabs.length];
    select(next);
    next.focus();
  });
});
select(tabs[0]);
""",
            "Underlined tabs with roving tabindex and arrow-key movement.",
        ),
        Item(
            "Floating tab bar",
            '<nav class="dockbar" aria-label="Main"><a href="#" aria-current="page"><i class="ic"></i></a><a href="#"><i class="ic"></i></a>'
            '<a href="#" class="plus" aria-label="Create">+</a><a href="#"><i class="ic"></i></a><a href="#"><i class="ic"></i></a></nav>',
            IC
            + """\
.dockbar { display: flex; align-items: center; gap: 6px; padding: 8px; border: 1px solid var(--border); border-radius: 999px;
  background: color-mix(in srgb, var(--surface) 85%, transparent); backdrop-filter: blur(16px);
  box-shadow: 0 18px 40px -16px rgb(0 0 0 / .7); }
.dockbar a { display: grid; place-items: center; width: 46px; height: 46px; border-radius: 999px; color: var(--muted);
  text-decoration: none; transition: background .15s, color .15s; }
.dockbar a[aria-current="page"] { background: var(--surface-2); color: var(--fg); }
.dockbar .plus { background: var(--primary); color: var(--primary-fg); font-size: 22px; }
""",
            note="A pill hovering above the content with the create action in the middle.",
        ),
        Item(
            "Segmented navigation",
            '<div class="seg" role="tablist" aria-label="Range"><span class="thumb"></span><button role="tab" aria-selected="true">Day</button>'
            '<button role="tab" aria-selected="false">Week</button><button role="tab" aria-selected="false">Month</button><button role="tab" aria-selected="false">Year</button></div>',
            """\
.seg { position: relative; display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; width: 340px; padding: 4px;
  border-radius: 12px; background: var(--surface-2); }
.seg button { position: relative; z-index: 1; height: 34px; border: 0; background: none; color: var(--muted); font-weight: 600; }
.seg button[aria-selected="true"] { color: var(--fg); }
.thumb { position: absolute; top: 4px; bottom: 4px; left: 4px; width: calc((100% - 8px) / 4); border-radius: 9px;
  background: var(--surface); box-shadow: 0 1px 3px rgb(0 0 0 / .4); transition: translate .28s var(--ease); }
""",
            """\
const buttons = [...document.querySelectorAll(".seg button")];
const thumb = document.querySelector(".thumb");
buttons.forEach((button, index) => button.addEventListener("click", () => {
  buttons.forEach((item) => item.setAttribute("aria-selected", String(item === button)));
  thumb.style.translate = `${index * 100}% 0`;
}));
""",
            "One sliding thumb moves between equal segments instead of each segment restyling.",
        ),
        Item(
            "Breadcrumb navigation",
            '<nav aria-label="Breadcrumb"><ol class="crumbs"><li><a href="#">Home</a></li><li><a href="#">Projects</a></li>'
            '<li><a href="#">Apollo</a></li><li aria-current="page">Settings</li></ol></nav>',
            """\
.crumbs { display: flex; flex-wrap: wrap; gap: 8px; margin: 0; padding: 0; list-style: none; }
.crumbs li { display: flex; align-items: center; gap: 8px; color: var(--muted); }
.crumbs li + li::before { content: "/"; color: var(--border); }
.crumbs a { color: var(--muted); text-decoration: none; }
.crumbs a:hover { color: var(--fg); text-decoration: underline; }
.crumbs [aria-current="page"] { color: var(--fg); font-weight: 600; }
""",
            note="An ordered list inside a labelled nav; the current page is text, not a link.",
        ),
        Item(
            "Contextual breadcrumbs",
            '<nav aria-label="Breadcrumb"><ol class="crumbs"><li><a href="#">Projects</a></li>'
            '<li><details class="crumb-menu"><summary>Apollo</summary><div><a href="#">Apollo</a><a href="#">Gemini</a><a href="#">Mercury</a></div></details></li>'
            '<li aria-current="page">Roadmap <span class="tag">Draft</span></li></ol></nav>',
            """\
.crumbs { display: flex; align-items: center; gap: 8px; margin: 0; padding: 0; list-style: none; }
.crumbs li { display: flex; align-items: center; gap: 8px; color: var(--muted); }
.crumbs li + li::before { content: "›"; }
.crumbs a { color: var(--muted); text-decoration: none; }
.crumbs [aria-current="page"] { color: var(--fg); font-weight: 600; }
.crumb-menu { position: relative; }
.crumb-menu summary { list-style: none; cursor: pointer; padding: 4px 8px; border-radius: 7px; color: var(--fg); }
.crumb-menu summary::after { content: " ▾"; color: var(--muted); }
.crumb-menu summary:hover { background: var(--surface-2); }
.crumb-menu div { position: absolute; top: calc(100% + 6px); left: 0; display: grid; min-width: 160px; padding: 6px;
  border: 1px solid var(--border); border-radius: 10px; background: var(--surface-2); box-shadow: var(--shadow); }
.crumb-menu div a { padding: 7px 9px; border-radius: 7px; }
.crumb-menu div a:hover { background: var(--surface); color: var(--fg); }
.tag { padding: 1px 8px; border-radius: 999px; background: color-mix(in srgb, var(--warning) 20%, transparent); color: var(--warning);
  font-size: 12px; font-weight: 500; }
""",
            note="A crumb that is also a switcher for its siblings, with the page's state beside the last one.",
        ),
        Item(
            "Mega menu",
            '<div class="mega"><button class="trigger" aria-expanded="false" aria-controls="mega-panel">Products ▾</button>'
            '<div class="sheet" id="mega-panel" hidden><section><h4>Build</h4><a href="#"><strong>Studio</strong><span>Design screens visually</span></a>'
            '<a href="#"><strong>Flows</strong><span>Automate handoffs</span></a></section><section><h4>Measure</h4>'
            '<a href="#"><strong>Insights</strong><span>Product analytics</span></a><a href="#"><strong>Replay</strong><span>Watch real sessions</span></a></section>'
            "<aside><h4>New</h4><p>Agents can now run your weekly report.</p></aside></div></div>",
            """\
.mega { position: relative; width: min(680px, 100%); height: 300px; }
.trigger { padding: 9px 14px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }
.sheet { position: absolute; top: 48px; left: 0; display: grid; grid-template-columns: 1fr 1fr 200px; gap: 8px; width: 100%;
  padding: 14px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow);
  animation: drop .22s var(--ease); }
.sheet[hidden] { display: none; }
.sheet h4 { margin: 4px 10px 8px; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.sheet a { display: grid; padding: 9px 10px; border-radius: 10px; color: var(--fg); text-decoration: none; }
.sheet a:hover { background: var(--surface-2); }
.sheet a span { color: var(--muted); font-size: 13px; }
.sheet aside { padding: 8px; border-radius: 10px; background: var(--surface-2); }
.sheet aside p { margin: 0 10px; color: var(--muted); font-size: 13px; }
@keyframes drop { from { opacity: 0; translate: 0 -6px; } }
""",
            """\
const trigger = document.querySelector(".trigger");
const sheet = document.querySelector(".sheet");
const set = (open) => { sheet.hidden = !open; trigger.setAttribute("aria-expanded", String(open)); };
trigger.addEventListener("click", () => set(sheet.hidden));
document.addEventListener("keydown", (event) => { if (event.key === "Escape") { set(false); trigger.focus(); } });
document.addEventListener("click", (event) => { if (!event.target.closest(".mega")) set(false); });
""",
            "A wide panel of grouped links with descriptions and one promotional slot.",
        ),
        Item(
            "Radial navigation",
            '<div class="radial"><button class="hub" aria-expanded="false" aria-label="Open menu">+</button>'
            '<a href="#" style="--i:0">A</a><a href="#" style="--i:1">B</a><a href="#" style="--i:2">C</a><a href="#" style="--i:3">D</a><a href="#" style="--i:4">E</a></div>',
            """\
.radial { position: relative; width: 260px; height: 260px; display: grid; place-items: center; }
.hub { position: relative; z-index: 1; width: 60px; height: 60px; border: 0; border-radius: 50%; background: var(--primary);
  color: var(--primary-fg); font-size: 26px; transition: rotate .3s var(--ease); }
.radial.open .hub { rotate: 45deg; }
.radial a { position: absolute; display: grid; place-items: center; width: 46px; height: 46px; border-radius: 50%;
  border: 1px solid var(--border); background: var(--surface); color: var(--fg); text-decoration: none; opacity: 0; scale: .4;
  --angle: calc(var(--i) * 72deg - 90deg);
  transition: translate .35s var(--ease) calc(var(--i) * 30ms), opacity .2s calc(var(--i) * 30ms), scale .35s var(--ease) calc(var(--i) * 30ms); }
.radial.open a { opacity: 1; scale: 1; translate: calc(cos(var(--angle)) * 96px) calc(sin(var(--angle)) * 96px); }
""",
            """\
const radial = document.querySelector(".radial");
const hub = radial.querySelector(".hub");
hub.addEventListener("click", () => {
  const open = radial.classList.toggle("open");
  hub.setAttribute("aria-expanded", String(open));
  hub.setAttribute("aria-label", open ? "Close menu" : "Open menu");
});
""",
            "Items fan out on a circle using CSS trigonometry; each is staggered by its index.",
        ),
        Item(
            "Dock navigation",
            '<nav class="dock" aria-label="Apps"><a href="#"></a><a href="#"></a><a href="#"></a><a href="#"></a><a href="#"></a><a href="#"></a></nav>',
            """\
.dock { display: flex; align-items: flex-end; gap: 10px; height: 84px; padding: 10px 14px; border: 1px solid var(--border);
  border-radius: 22px; background: color-mix(in srgb, var(--surface) 80%, transparent); backdrop-filter: blur(16px); }
.dock a { width: 48px; height: 48px; border-radius: 14px; background: linear-gradient(145deg, var(--primary), var(--accent));
  transform-origin: bottom; transition: width .18s var(--ease), height .18s var(--ease); }
.dock a:nth-child(even) { background: linear-gradient(145deg, #f472b6, var(--warning)); }
""",
            """\
const dock = document.querySelector(".dock");
const icons = [...dock.querySelectorAll("a")];
dock.addEventListener("pointermove", (event) => {
  for (const icon of icons) {
    const box = icon.getBoundingClientRect();
    const distance = Math.abs(event.clientX - (box.left + box.width / 2));
    const size = 48 + Math.max(0, 1 - distance / 140) * 24;
    icon.style.width = icon.style.height = `${size}px`;
  }
});
dock.addEventListener("pointerleave", () => icons.forEach((icon) => { icon.style.width = icon.style.height = ""; }));
""",
            "Icons grow with proximity to the pointer, the way a desktop dock does.",
        ),
        Item(
            "App launcher",
            '<div class="launcher"><button class="grid-btn" aria-expanded="false" aria-label="Apps"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></button>'
            '<div class="apps" hidden><a href="#"><b></b>Mail</a><a href="#"><b></b>Docs</a><a href="#"><b></b>Calendar</a><a href="#"><b></b>Drive</a><a href="#"><b></b>Chat</a><a href="#"><b></b>Admin</a></div></div>',
            """\
.launcher { position: relative; height: 300px; }
.grid-btn { display: grid; grid-template-columns: repeat(3, 5px); gap: 4px; place-content: center; width: 42px; height: 42px;
  border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }
.grid-btn i { width: 5px; height: 5px; border-radius: 50%; background: var(--fg); }
.apps { position: absolute; top: 50px; left: 0; display: grid; grid-template-columns: repeat(3, 84px); gap: 4px; padding: 10px;
  border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow); }
.apps[hidden] { display: none; }
.apps a { display: grid; justify-items: center; gap: 6px; padding: 12px 4px; border-radius: 12px; color: var(--fg);
  font-size: 12px; text-decoration: none; }
.apps a:hover { background: var(--surface-2); }
.apps b { width: 36px; height: 36px; border-radius: 11px; background: linear-gradient(135deg, var(--primary), var(--accent)); }
""",
            """\
const button = document.querySelector(".grid-btn");
const apps = document.querySelector(".apps");
button.addEventListener("click", () => {
  apps.hidden = !apps.hidden;
  button.setAttribute("aria-expanded", String(!apps.hidden));
});
document.addEventListener("click", (event) => { if (!event.target.closest(".launcher")) apps.hidden = true; });
""",
            "A nine-dot button opening a grid of sibling products.",
        ),
        switcher(
            "Workspace",
            [
                ("Northwind", "Pro · 12 members"),
                ("Acme Labs", "Free · 3 members"),
                ("Personal", "Just you"),
            ],
            "Chooses which workspace the whole shell shows.",
        ),
        switcher(
            "Project",
            [
                ("Apollo", "Updated 2h ago"),
                ("Gemini", "Updated yesterday"),
                ("Mercury", "Archived"),
            ],
            "Scopes the current workspace to one project.",
        ),
        switcher(
            "Account",
            [("Dana Whitfield", "dana@northwind.io"), ("Dana (admin)", "admin@northwind.io")],
            "Moves between signed-in identities without signing out.",
        ),
        switcher(
            "Organization",
            [
                ("Northwind Group", "Enterprise"),
                ("Northwind EU", "Enterprise"),
                ("Sandbox Org", "Trial"),
            ],
            "The outermost scope when one person belongs to several organisations.",
        ),
        Item(
            "Environment switcher",
            '<div class="env" role="radiogroup" aria-label="Environment"><label><input type="radio" name="env" value="dev" checked><span>Development</span></label>'
            '<label><input type="radio" name="env" value="staging"><span>Staging</span></label><label><input type="radio" name="env" value="prod"><span>Production</span></label></div>',
            """\
.env { display: flex; padding: 4px; gap: 4px; border: 1px solid var(--border); border-radius: 999px; background: var(--surface); }
.env input { position: absolute; opacity: 0; }
.env span { display: flex; align-items: center; gap: 8px; padding: 7px 14px; border-radius: 999px; color: var(--muted); cursor: pointer; }
.env span::before { content: ""; width: 8px; height: 8px; border-radius: 50%; background: var(--success); }
.env label:nth-child(2) span::before { background: var(--warning); }
.env label:nth-child(3) span::before { background: var(--danger); }
.env input:checked + span { background: var(--surface-2); color: var(--fg); }
.env input:focus-visible + span { outline: 2px solid var(--accent); }
""",
            note="Colour-codes where changes land; production is always the alarming one.",
        ),
        Item(
            "Navigation rail",
            '<nav class="rail" aria-label="Main"><button class="fab" aria-label="Compose">+</button>'
            '<a href="#" aria-current="page"><i class="ic"></i>Home</a><a href="#"><i class="ic"></i>Search</a><a href="#"><i class="ic"></i>Library</a></nav>',
            IC
            + """\
.rail { display: flex; flex-direction: column; align-items: center; gap: 12px; width: 80px; height: 420px; padding: 16px 0;
  border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }
.fab { width: 52px; height: 52px; margin-bottom: 12px; border: 0; border-radius: 16px; background: var(--primary); color: var(--primary-fg); font-size: 24px; }
.rail a { display: grid; justify-items: center; gap: 4px; width: 100%; font-size: 11px; color: var(--muted); text-decoration: none; }
.rail a .ic { width: 56px; height: 30px; border-radius: 999px; background: transparent; position: relative; }
.rail a .ic::after { content: ""; position: absolute; inset: 7px 20px; border-radius: 5px; background: currentColor; }
.rail a[aria-current="page"] { color: var(--fg); }
.rail a[aria-current="page"] .ic { background: color-mix(in srgb, var(--primary) 30%, transparent); }
""",
            note="Tablet-width shell: a pill highlights the active icon, the create action sits on top.",
        ),
        Item(
            "Navigation drawer",
            f'<div class="stage"><button class="btn open">Open menu</button><div class="scrim" hidden></div>'
            f'<nav class="side drawer" aria-label="Main" inert>{SIDE_LINKS}</nav></div>',
            SIDE
            + BTN
            + """\
.stage { position: relative; width: min(620px, 100%); height: 440px; overflow: hidden; border: 1px solid var(--border);
  border-radius: var(--radius); display: grid; place-items: center; }
.scrim { position: absolute; inset: 0; background: rgb(0 0 0 / .5); }
.scrim[hidden] { display: none; }
.drawer { position: absolute; inset: 0 auto 0 0; height: 100%; border-radius: 0; border-width: 0 1px 0 0; translate: -100% 0;
  transition: translate .3s var(--ease); }
.drawer.open { translate: 0 0; }
""",
            """\
const drawer = document.querySelector(".drawer");
const scrim = document.querySelector(".scrim");
const opener = document.querySelector(".open");
const set = (open) => {
  drawer.classList.toggle("open", open);
  drawer.inert = !open;
  scrim.hidden = !open;
  if (open) drawer.querySelector("a").focus(); else opener.focus();
};
opener.addEventListener("click", () => set(true));
scrim.addEventListener("click", () => set(false));
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && !scrim.hidden) set(false); });
""",
            "Off-canvas menu from the leading edge; inert while closed so it cannot be tabbed into.",
        ),
        Item(
            "Slide-over navigation",
            '<div class="stage"><button class="btn open">Details</button><aside class="over" aria-label="Details" inert><header><strong>Navigation</strong>'
            '<button class="close" aria-label="Close">×</button></header><a href="#">Profile</a><a href="#">Billing</a><a href="#">Notifications</a><a href="#">API keys</a></aside></div>',
            BTN
            + """\
.stage { position: relative; width: min(620px, 100%); height: 400px; overflow: hidden; border: 1px solid var(--border);
  border-radius: var(--radius); display: grid; place-items: center; }
.over { position: absolute; inset: 10px 10px 10px auto; width: 260px; padding: 14px; display: grid; align-content: start; gap: 4px;
  border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface-2); box-shadow: var(--shadow);
  translate: calc(100% + 20px) 0; transition: translate .32s var(--ease); }
.over.open { translate: 0 0; }
.over header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.over a { padding: 9px 10px; border-radius: 9px; color: var(--fg); text-decoration: none; }
.over a:hover { background: var(--surface); }
.close { width: 28px; height: 28px; border: 0; border-radius: 8px; background: var(--surface); }
""",
            """\
const over = document.querySelector(".over");
const set = (open) => { over.classList.toggle("open", open); over.inert = !open; };
document.querySelector(".open").addEventListener("click", () => set(true));
over.querySelector(".close").addEventListener("click", () => set(false));
document.addEventListener("keydown", (event) => { if (event.key === "Escape") set(false); });
""",
            "A floating panel from the trailing edge that leaves the page visible and usable beside it.",
        ),
        Item(
            "Sticky header",
            f'<div class="scroller"><header class="bar sticky">{BRAND}<nav aria-label="Main">{LINKS}</nav></header><div class="filler"></div></div>',
            BAR
            + """\
.scroller { width: min(820px, 100%); height: 320px; overflow: auto; border: 1px solid var(--border); border-radius: var(--radius); }
.sticky { position: sticky; top: 0; z-index: 2; width: 100%; border-width: 0 0 1px; border-radius: 0;
  background: color-mix(in srgb, var(--surface) 88%, transparent); backdrop-filter: blur(12px); }
.filler { height: 900px; background: repeating-linear-gradient(var(--bg) 0 60px, var(--surface) 60px 61px); }
""",
            note="Stays at the top of its scroll container; translucent so scrolled content hints through.",
        ),
        Item(
            "Auto-hiding header",
            f'<div class="scroller"><header class="bar sticky">{BRAND}<nav aria-label="Main">{LINKS}</nav></header><div class="filler"></div></div>',
            BAR
            + """\
.scroller { width: min(820px, 100%); height: 320px; overflow: auto; border: 1px solid var(--border); border-radius: var(--radius); }
.sticky { position: sticky; top: 0; z-index: 2; width: 100%; border-width: 0 0 1px; border-radius: 0; transition: translate .25s var(--ease); }
.sticky.away { translate: 0 -100%; }
.filler { height: 1200px; background: repeating-linear-gradient(var(--bg) 0 60px, var(--surface) 60px 61px); }
""",
            """\
const scroller = document.querySelector(".scroller");
const header = scroller.querySelector(".sticky");
let last = 0;
scroller.addEventListener("scroll", () => {
  const now = scroller.scrollTop;
  // Hide when moving down past the header, show as soon as the user turns back.
  header.classList.toggle("away", now > last && now > 80);
  last = now;
}, { passive: true });
""",
            "Slides away while reading downwards and returns on the first upward scroll.",
        ),
        Item(
            "Contextual header",
            '<header class="ctx" data-mode="default"><div class="default"><strong>Documents</strong><span class="muted">24 items</span><button class="btn pick">Select</button></div>'
            '<div class="selection"><button class="x" aria-label="Clear selection">×</button><strong>3 selected</strong><span></span><button>Move</button><button>Share</button><button class="danger">Delete</button></div></header>',
            BTN
            + """\
.ctx { position: relative; width: min(680px, 100%); height: 60px; border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--surface); overflow: hidden; }
.ctx > div { position: absolute; inset: 0; display: flex; align-items: center; gap: 12px; padding: 0 16px;
  transition: translate .28s var(--ease), opacity .2s; }
.ctx .muted { color: var(--muted); flex: 1; }
.selection { background: color-mix(in srgb, var(--primary) 22%, var(--surface)); translate: 0 100%; opacity: 0; }
.selection span { flex: 1; }
.selection button { padding: 6px 12px; border: 0; border-radius: 8px; background: rgb(255 255 255 / .1); }
.selection .danger { color: var(--danger); }
.ctx[data-mode="selection"] .default { translate: 0 -100%; opacity: 0; }
.ctx[data-mode="selection"] .selection { translate: 0 0; opacity: 1; }
""",
            """\
const header = document.querySelector(".ctx");
header.querySelector(".pick").addEventListener("click", () => { header.dataset.mode = "selection"; });
header.querySelector(".x").addEventListener("click", () => { header.dataset.mode = "default"; });
""",
            "The header's content is replaced by actions for the current selection, then restored.",
        ),
        Item(
            "Page header",
            '<header class="page"><nav class="muted">Projects / Apollo</nav><div class="title"><h1>Roadmap</h1><span class="tag">On track</span></div>'
            '<p class="muted">What ships this quarter and who owns it.</p><div class="actions"><button class="btn btn-ghost">Share</button><button class="btn">Add milestone</button></div></header>',
            BTN
            + """\
.page { display: grid; grid-template-columns: 1fr auto; gap: 4px 16px; width: min(720px, 100%); padding-bottom: 18px;
  border-bottom: 1px solid var(--border); }
.page nav, .page p { grid-column: 1; margin: 0; }
.muted { color: var(--muted); font-size: 14px; }
.title { display: flex; align-items: center; gap: 12px; }
.title h1 { margin: 0; font-size: 28px; letter-spacing: -.02em; }
.tag { padding: 2px 10px; border-radius: 999px; background: color-mix(in srgb, var(--success) 18%, transparent); color: var(--success); font-size: 12px; }
.actions { grid-column: 2; grid-row: 2 / 4; display: flex; gap: 8px; align-self: end; }
.btn-ghost { background: transparent; color: var(--fg); border-color: var(--border); }
""",
            note="Where am I, what is this, what is its state, what can I do: in that order.",
        ),
        Item(
            "Split header",
            '<header class="split"><div><p class="eyebrow">Q3 planning</p><h1>Design systems that scale with the team</h1></div>'
            '<div><p>Tokens, patterns and review rituals for products that outgrow one designer.</p><a href="#">Read the guide →</a></div></header>',
            """\
.split { display: grid; grid-template-columns: 1.2fr 1fr; gap: 40px; align-items: end; width: min(820px, 100%); padding: 28px 0;
  border-block: 1px solid var(--border); }
.eyebrow { margin: 0 0 10px; font-size: 12px; letter-spacing: .12em; text-transform: uppercase; color: var(--primary); }
.split h1 { margin: 0; font-size: 34px; line-height: 1.1; letter-spacing: -.025em; text-wrap: balance; }
.split p { margin: 0 0 10px; color: var(--muted); }
.split a { color: var(--fg); font-weight: 600; }
@media (max-width: 640px) { .split { grid-template-columns: 1fr; gap: 16px; } }
""",
            note="Headline and supporting copy share a baseline in two columns; an editorial opener.",
        ),
        Item(
            "Command header",
            f'<header class="bar">{BRAND}<label class="search"><input placeholder="Search or run a command" aria-label="Search or run a command"><kbd>⌘K</kbd></label><button class="btn">Invite</button></header>',
            BAR
            + """\
.search { flex: 1; display: flex; align-items: center; gap: 8px; height: 38px; padding: 0 12px; border: 1px solid var(--border);
  border-radius: 10px; background: var(--bg); }
.search:focus-within { border-color: var(--primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 25%, transparent); }
.search input { flex: 1; min-width: 0; border: 0; outline: 0; background: none; }
kbd { padding: 1px 6px; border: 1px solid var(--border); border-radius: 5px; font: 11px var(--mono); color: var(--muted); }
""",
            """\
const input = document.querySelector(".search input");
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); input.focus(); input.select(); }
});
""",
            "Search is the centrepiece of the bar and answers to ⌘K / Ctrl+K from anywhere.",
        ),
        Item(
            "Section navigation",
            '<nav class="sections" aria-label="Settings sections"><a href="#" aria-current="true">General</a><a href="#">Members <span>12</span></a>'
            '<a href="#">Billing</a><a href="#">Integrations <span>3</span></a><a href="#">Security</a></nav>',
            """\
.sections { display: grid; gap: 2px; width: 220px; }
.sections a { display: flex; justify-content: space-between; padding: 8px 12px; border-left: 2px solid var(--border);
  color: var(--muted); text-decoration: none; transition: color .15s, border-color .15s; }
.sections a:hover { color: var(--fg); }
.sections a[aria-current="true"] { color: var(--fg); border-color: var(--primary); font-weight: 600; }
.sections span { padding: 0 7px; border-radius: 999px; background: var(--surface-2); font-size: 12px; }
""",
            note="Secondary navigation inside one area; a rail on the left edge marks the current section.",
        ),
        Item(
            "Anchor navigation",
            '<div class="doc"><nav aria-label="On this page"><a href="#a-intro">Introduction</a><a href="#a-setup">Setup</a><a href="#a-usage">Usage</a><a href="#a-faq">FAQ</a></nav>'
            '<article><section id="a-intro"><h2>Introduction</h2></section><section id="a-setup"><h2>Setup</h2></section><section id="a-usage"><h2>Usage</h2></section><section id="a-faq"><h2>FAQ</h2></section></article></div>',
            """\
.doc { display: grid; grid-template-columns: 170px 1fr; gap: 24px; width: min(680px, 100%); height: 360px; }
.doc nav { display: grid; align-content: start; gap: 2px; }
.doc nav a { padding: 6px 10px; border-left: 2px solid var(--border); color: var(--muted); text-decoration: none; font-size: 14px; }
.doc nav a.active { border-color: var(--primary); color: var(--fg); }
.doc article { overflow: auto; scroll-behavior: smooth; border: 1px solid var(--border); border-radius: var(--radius); }
.doc section { height: 300px; padding: 18px; border-bottom: 1px solid var(--border); }
.doc h2 { margin: 0; }
""",
            """\
const article = document.querySelector(".doc article");
const links = [...document.querySelectorAll(".doc nav a")];
const observer = new IntersectionObserver((entries) => {
  for (const entry of entries) {
    if (!entry.isIntersecting) continue;
    links.forEach((link) => link.classList.toggle("active", link.hash === `#${entry.target.id}`));
  }
}, { root: article, rootMargin: "0px 0px -70% 0px" });
article.querySelectorAll("section").forEach((section) => observer.observe(section));
links.forEach((link) => link.addEventListener("click", (event) => {
  event.preventDefault();
  article.querySelector(link.hash).scrollIntoView();
}));
""",
            "A table of contents that highlights the section being read (scroll-spy).",
        ),
        Item(
            "Step navigation",
            '<ol class="steps"><li class="done"><span>1</span>Account</li><li class="done"><span>2</span>Workspace</li><li aria-current="step"><span>3</span>Invite team</li><li><span>4</span>Finish</li></ol>',
            """\
.steps { display: flex; gap: 0; margin: 0; padding: 0; list-style: none; width: min(640px, 100%); }
.steps li { flex: 1; display: grid; justify-items: center; gap: 8px; position: relative; color: var(--muted); font-size: 13px; }
.steps li::before { content: ""; position: absolute; top: 15px; right: 50%; width: 100%; height: 2px; background: var(--border); }
.steps li:first-child::before { display: none; }
.steps span { position: relative; z-index: 1; display: grid; place-items: center; width: 32px; height: 32px; border-radius: 50%;
  border: 2px solid var(--border); background: var(--bg); font-weight: 700; }
.steps .done span { border-color: var(--primary); background: var(--primary); color: var(--primary-fg); }
.steps .done::before, .steps [aria-current="step"]::before { background: var(--primary); }
.steps [aria-current="step"] { color: var(--fg); }
.steps [aria-current="step"] span { border-color: var(--primary); box-shadow: 0 0 0 4px color-mix(in srgb, var(--primary) 25%, transparent); }
""",
            note="Numbered stages of a flow; completed ones fill, the current one is ringed.",
        ),
        Item(
            "Progress navigation",
            '<div class="prog"><div class="meter" role="progressbar" aria-valuemin="0" aria-valuemax="4" aria-valuenow="2" aria-label="Setup progress"><i></i></div>'
            '<div class="row"><button class="btn back">Back</button><span class="count">Step 2 of 4</span><button class="btn next">Continue</button></div></div>',
            BTN
            + """\
.prog { display: grid; gap: 16px; width: min(460px, 100%); }
.meter { height: 6px; border-radius: 999px; background: var(--surface-2); overflow: hidden; }
.meter i { display: block; height: 100%; width: 50%; border-radius: inherit; background: linear-gradient(90deg, var(--primary), var(--accent));
  transition: width .35s var(--ease); }
.row { display: flex; align-items: center; justify-content: space-between; }
.count { color: var(--muted); font-size: 14px; }
.back { background: transparent; border-color: var(--border); color: var(--fg); }
""",
            """\
const total = 4;
let step = 2;
const meter = document.querySelector(".meter");
const render = () => {
  meter.firstElementChild.style.width = `${(step / total) * 100}%`;
  meter.setAttribute("aria-valuenow", String(step));
  document.querySelector(".count").textContent = `Step ${step} of ${total}`;
  document.querySelector(".back").disabled = step === 1;
  document.querySelector(".next").textContent = step === total ? "Finish" : "Continue";
};
document.querySelector(".back").addEventListener("click", () => { step = Math.max(1, step - 1); render(); });
document.querySelector(".next").addEventListener("click", () => { step = Math.min(total, step + 1); render(); });
render();
""",
            "A continuous bar with back and continue, for flows where step names matter less than momentum.",
        ),
        Item(
            "Pagination",
            '<nav class="pages" aria-label="Pagination"><button aria-label="Previous page">‹</button><span class="list"></span><button aria-label="Next page">›</button></nav>',
            """\
.pages { display: flex; align-items: center; gap: 4px; }
.pages .list { display: flex; gap: 4px; }
.pages button, .pages i { display: grid; place-items: center; min-width: 36px; height: 36px; padding: 0 8px; border: 1px solid transparent;
  border-radius: 9px; background: none; color: var(--muted); font-style: normal; }
.pages button:hover:not(:disabled) { background: var(--surface-2); color: var(--fg); }
.pages button[aria-current="page"] { border-color: var(--primary); color: var(--fg); background: color-mix(in srgb, var(--primary) 16%, transparent); }
.pages button:disabled { opacity: .35; cursor: default; }
""",
            """\
const total = 24;
let current = 6;
const list = document.querySelector(".pages .list");
const [previous, next] = document.querySelectorAll(".pages > button");
// First, last, and a window around the current page; gaps become an ellipsis.
const visible = () => [...new Set([1, total, current - 1, current, current + 1])].filter((n) => n >= 1 && n <= total).sort((a, b) => a - b);
const render = () => {
  list.replaceChildren();
  let before = 0;
  for (const page of visible()) {
    if (page - before > 1) list.append(Object.assign(document.createElement("i"), { textContent: "…" }));
    const button = Object.assign(document.createElement("button"), { textContent: String(page) });
    if (page === current) button.setAttribute("aria-current", "page");
    button.addEventListener("click", () => { current = page; render(); });
    list.append(button);
    before = page;
  }
  previous.disabled = current === 1;
  next.disabled = current === total;
};
previous.addEventListener("click", () => { current -= 1; render(); });
next.addEventListener("click", () => { current += 1; render(); });
render();
""",
            "Shows first, last and the neighbours of the current page, with ellipses for the gaps.",
        ),
        Item(
            "Infinite navigation",
            '<div class="feed" aria-live="polite"><ul></ul><div class="sentinel">Loading more…</div></div>',
            """\
.feed { width: min(420px, 100%); height: 360px; overflow: auto; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }
.feed ul { margin: 0; padding: 0; list-style: none; }
.feed li { padding: 14px 16px; border-bottom: 1px solid var(--border); animation: rise .3s var(--ease); }
.sentinel { padding: 16px; text-align: center; color: var(--muted); font-size: 13px; }
@keyframes rise { from { opacity: 0; translate: 0 8px; } }
""",
            """\
const feed = document.querySelector(".feed");
const list = feed.querySelector("ul");
const sentinel = feed.querySelector(".sentinel");
const LIMIT = 60;
let loaded = 0;
const loadMore = () => {
  for (let i = 0; i < 12 && loaded < LIMIT; i += 1) {
    loaded += 1;
    list.append(Object.assign(document.createElement("li"), { textContent: `Item ${loaded}` }));
  }
  if (loaded >= LIMIT) { sentinel.textContent = "You have reached the end."; observer.disconnect(); }
};
// The sentinel entering view is the request for the next page: no scroll maths.
const observer = new IntersectionObserver((entries) => { if (entries[0].isIntersecting) loadMore(); }, { root: feed, rootMargin: "120px" });
observer.observe(sentinel);
loadMore();
""",
            "An IntersectionObserver on a sentinel loads the next page; always say when the end is reached.",
        ),
    ),
)
