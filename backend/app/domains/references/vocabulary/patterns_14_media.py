"""Patterns 451-470: files, media and content."""

from app.domains.references.vocabulary.base import Item, Section

# Pictures are painted with gradients so every entry works offline.
PIC = ".pic { background: linear-gradient(135deg, hsl(var(--h) 72% 58%), hsl(calc(var(--h) + 55) 70% 32%)); }\n"
FILES = [
    ("Design", "folder", "—", "Today"),
    ("Reports", "folder", "—", "Yesterday"),
    ("brief.pdf", "pdf", "284 KB", "12 May"),
    ("forecast.xlsx", "xls", "91 KB", "10 May"),
    ("hero.png", "img", "1.2 MB", "9 May"),
    ("notes.md", "txt", "4 KB", "2 May"),
]
KIND = ".k { display: grid; place-items: center; flex: none; width: 30px; height: 30px; border-radius: 8px; font: 700 9px var(--mono); text-transform: uppercase; --c: var(--muted); background: color-mix(in srgb, var(--c) 22%, transparent); color: var(--c); }\n.k.folder { --c: var(--warning); }\n.k.pdf { --c: var(--danger); }\n.k.xls { --c: var(--success); }\n.k.img { --c: var(--accent); }\n"
HUES = [250, 190, 20, 320, 140, 45, 280, 200]
TILES = "".join(
    f'<button class="pic" style="--h:{h}" aria-label="Photo {i + 1}"></button>'
    for i, h in enumerate(HUES)
)
SLIDES = "".join(
    f'<li class="pic" style="--h:{h}" aria-label="Slide {i + 1} of 5"><span>{i + 1}</span></li>'
    for i, h in enumerate(HUES[:5])
)
CAR = (
    PIC
    + """\
.car { position: relative; width: min(520px, 100%); }
.track { display: flex; gap: 12px; margin: 0; padding: 0; list-style: none; overflow-x: auto; scroll-snap-type: x mandatory; scrollbar-width: none; border-radius: 16px; outline: none; }
.track::-webkit-scrollbar { display: none; }
.track li { flex: 0 0 100%; aspect-ratio: 16 / 9; scroll-snap-align: center; border-radius: 16px; display: grid; place-items: center; font-size: 40px; font-weight: 800; color: rgb(255 255 255 / .6); }
.car .nav { position: absolute; top: 50%; translate: 0 -50%; width: 38px; height: 38px; border: 0; border-radius: 50%; background: rgb(0 0 0 / .5); color: #fff; backdrop-filter: blur(6px); }
.car .nav:disabled { opacity: .3; }
.car .prev { left: 10px; }
.car .next { right: 10px; }
.pips { display: flex; justify-content: center; gap: 6px; margin-top: 10px; }
.pips button { width: 8px; height: 8px; padding: 0; border: 0; border-radius: 50%; background: var(--border); transition: width .2s, background .2s; }
.pips button[aria-current="true"] { width: 22px; border-radius: 99px; background: var(--primary); }
"""
)
# A scroll-snap carousel: the browser does the sliding, the script only keeps the controls in step.
CAR_JS = """\
const track = document.querySelector(".track");
const slides = [...track.children];
const [previous, next] = document.querySelectorAll(".car .nav");
const pips = document.querySelector(".pips");
let index = 0;
const go = (to) => slides[Math.min(slides.length - 1, Math.max(0, to))].scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
slides.forEach((_, i) => {
  const pip = document.createElement("button");
  pip.setAttribute("aria-label", `Go to slide ${i + 1}`);
  pip.addEventListener("click", () => go(i));
  pips.append(pip);
});
const sync = () => {
  [...pips.children].forEach((pip, i) => pip.setAttribute("aria-current", String(i === index)));
  previous.disabled = index === 0;
  next.disabled = index === slides.length - 1;
};
// Whichever slide is mostly in view is the current one, however it got there.
const observer = new IntersectionObserver((entries) => {
  for (const entry of entries) if (entry.isIntersecting) { index = slides.indexOf(entry.target); sync(); }
}, { root: track, threshold: 0.6 });
slides.forEach((slide) => observer.observe(slide));
previous.addEventListener("click", () => go(index - 1));
next.addEventListener("click", () => go(index + 1));
track.addEventListener("keydown", (event) => { if (event.key === "ArrowRight") go(index + 1); if (event.key === "ArrowLeft") go(index - 1); });
sync();
"""
CAR_HTML = f'<div class="car" role="region" aria-roledescription="carousel" aria-label="Gallery"><ul class="track" tabindex="0">{SLIDES}</ul><button class="nav prev" aria-label="Previous slide">‹</button><button class="nav next" aria-label="Next slide">›</button><div class="pips"></div></div>'
PAGE = """\
.pg { width: 240px; aspect-ratio: 1 / 1.414; padding: 22px; background: #f6f7fb; color: #1b2130; box-shadow: 0 8px 24px rgb(0 0 0 / .5); border-radius: 3px; }
.pg h4 { margin: 0 0 12px; font-size: 14px; }
.pg i { display: block; height: 6px; margin-bottom: 8px; border-radius: 3px; background: #d5d9e6; }
.pg i.s { width: 55%; }
"""
PAGE_HTML = (
    '<h4>Quarterly report</h4><i></i><i></i><i class="s"></i><i></i><i></i><i class="s"></i><i></i>'
)

SECTION = Section(
    "patterns",
    "Files, Media & Content",
    451,
    (
        Item(
            "File explorer",
            '<div class="fe"><nav aria-label="Path"><button>Home</button><span>/</span><button>Projects</button><span>/</span><b>Apollo</b></nav><table><thead><tr><th scope="col">Name</th><th scope="col">Size</th><th scope="col">Modified</th></tr></thead><tbody>'
            + "".join(
                f'<tr tabindex="0"><td><span class="k {k}">{k[:3]}</span>{n}</td><td>{s}</td><td>{d}</td></tr>'
                for n, k, s, d in FILES
            )
            + "</tbody></table></div>",
            KIND
            + '.fe { width: min(560px, 100%); border: 1px solid var(--border); border-radius: 14px; background: var(--surface); overflow: hidden; }\n.fe nav { display: flex; gap: 6px; align-items: center; padding: 10px 14px; border-bottom: 1px solid var(--border); font-size: 13px; color: var(--muted); }\n.fe nav button { border: 0; background: none; color: var(--muted); padding: 0; }\n.fe nav b { color: var(--fg); }\n.fe table { width: 100%; border-collapse: collapse; font-size: 14px; }\n.fe th { padding: 8px 14px; text-align: left; font-size: 12px; color: var(--muted); font-weight: 600; }\n.fe td { padding: 7px 14px; border-top: 1px solid var(--border); color: var(--muted); }\n.fe td:first-child { display: flex; align-items: center; gap: 10px; color: var(--fg); }\n.fe tr:hover td, .fe tr:focus td { background: var(--surface-2); }\n.fe tr { outline: none; }\n.fe tr[aria-selected="true"] td { background: color-mix(in srgb, var(--primary) 18%, transparent); }\n',
            'const rows = [...document.querySelectorAll(".fe tbody tr")];\nconst select = (row) => rows.forEach((other) => other.setAttribute("aria-selected", String(other === row)));\nrows.forEach((row, index) => {\n  row.addEventListener("click", () => select(row));\n  row.addEventListener("keydown", (event) => {\n    const next = rows[index + (event.key === "ArrowDown" ? 1 : event.key === "ArrowUp" ? -1 : 0)];\n    if (next && next !== row) { event.preventDefault(); next.focus(); select(next); }\n  });\n});\n',
            "A path bar over a details table: type badge, name, size, date, with row selection and arrow keys.",
        ),
        Item(
            "Folder tree",
            '<ul class="ft" role="tree" aria-label="Folders"></ul>',
            '.ft, .ft ul { margin: 0; padding: 0; list-style: none; }\n.ft { width: 260px; padding: 8px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.ft ul { margin-left: 18px; border-left: 1px solid var(--border); padding-left: 4px; }\n.ft .row { display: flex; align-items: center; gap: 6px; padding: 5px 8px; border-radius: 8px; cursor: pointer; outline: none; }\n.ft .row:hover { background: var(--surface-2); }\n.ft .row:focus-visible { box-shadow: 0 0 0 2px var(--accent); }\n.ft [aria-selected="true"] > .row { background: color-mix(in srgb, var(--primary) 20%, transparent); }\n.ft .tw { width: 14px; color: var(--muted); transition: rotate .15s; }\n.ft [aria-expanded="true"] > .row .tw { rotate: 90deg; }\n.ft [aria-expanded="false"] > ul { display: none; }\n',
            'const TREE = [{ name: "src", open: true, children: [{ name: "components", open: true, children: [{ name: "Button.tsx" }, { name: "Card.tsx" }] }, { name: "hooks", children: [{ name: "useTheme.ts" }] }, { name: "index.ts" }] }, { name: "public", children: [{ name: "favicon.svg" }] }, { name: "README.md" }];\nconst root = document.querySelector(".ft");\nconst build = (nodes, parent) => nodes.forEach((node) => {\n  const item = document.createElement("li");\n  item.setAttribute("role", "treeitem");\n  item.setAttribute("aria-selected", "false");\n  const row = Object.assign(document.createElement("div"), { className: "row" });\n  row.tabIndex = -1;\n  row.append(Object.assign(document.createElement("span"), { className: "tw", textContent: node.children ? "›" : "" }), node.name);\n  item.append(row);\n  if (node.children) {\n    item.setAttribute("aria-expanded", String(Boolean(node.open)));\n    const group = document.createElement("ul");\n    group.setAttribute("role", "group");\n    build(node.children, group);\n    item.append(group);\n  }\n  parent.append(item);\n});\nbuild(TREE, root);\nconst visible = () => [...root.querySelectorAll(".row")].filter((row) => row.offsetParent !== null);\nconst focus = (row) => { root.querySelectorAll(".row").forEach((other) => { other.tabIndex = other === row ? 0 : -1; }); row.focus(); };\nconst select = (row) => root.querySelectorAll("[role=treeitem]").forEach((item) => item.setAttribute("aria-selected", String(item === row.parentElement)));\nroot.addEventListener("click", (event) => {\n  const row = event.target.closest(".row");\n  if (!row) return;\n  const item = row.parentElement;\n  if (item.hasAttribute("aria-expanded")) item.setAttribute("aria-expanded", String(item.getAttribute("aria-expanded") !== "true"));\n  select(row);\n  focus(row);\n});\n// The tree keyboard pattern: up and down move, right opens or enters, left closes or leaves.\nroot.addEventListener("keydown", (event) => {\n  const row = event.target.closest(".row");\n  if (!row) return;\n  const item = row.parentElement, rows = visible(), index = rows.indexOf(row);\n  const expanded = item.getAttribute("aria-expanded");\n  if (event.key === "ArrowDown" && rows[index + 1]) focus(rows[index + 1]);\n  else if (event.key === "ArrowUp" && rows[index - 1]) focus(rows[index - 1]);\n  else if (event.key === "ArrowRight" && expanded === "false") item.setAttribute("aria-expanded", "true");\n  else if (event.key === "ArrowRight" && expanded === "true") focus(item.querySelector("ul .row"));\n  else if (event.key === "ArrowLeft" && expanded === "true") item.setAttribute("aria-expanded", "false");\n  else if (event.key === "ArrowLeft") { const parent = item.parentElement.closest("[role=treeitem]"); if (parent) focus(parent.querySelector(".row")); }\n  else if (event.key === "Enter" || event.key === " ") select(row);\n  else return;\n  event.preventDefault();\n});\nvisible()[0].tabIndex = 0;\n',
            "The ARIA tree pattern: one tab stop, arrows to move, open, close and climb, Enter to select.",
        ),
        Item(
            "File browser",
            '<div class="fb"><header><b>Apollo</b><div role="radiogroup" aria-label="View"><button role="radio" aria-checked="true" data-v="grid">Grid</button><button role="radio" aria-checked="false" data-v="list">List</button></div></header><ul data-view="grid">'
            + "".join(
                f'<li><span class="k {k}">{k[:3]}</span><b>{n}</b><small>{s}</small></li>'
                for n, k, s, _ in FILES
            )
            + "</ul></div>",
            KIND
            + '.fb { width: min(520px, 100%); border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.fb header { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-bottom: 1px solid var(--border); }\n.fb [role=radio] { padding: 4px 10px; border: 1px solid var(--border); background: var(--surface-2); color: var(--muted); font-size: 12px; }\n.fb [role=radio]:first-child { border-radius: 8px 0 0 8px; }\n.fb [role=radio]:last-child { border-radius: 0 8px 8px 0; }\n.fb [role=radio][aria-checked="true"] { background: var(--primary); border-color: var(--primary); color: #fff; }\n.fb ul { margin: 0; padding: 12px; list-style: none; display: grid; gap: 10px; }\n.fb ul[data-view=grid] { grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); }\n.fb ul[data-view=grid] li { display: grid; justify-items: center; gap: 6px; padding: 14px 8px; border: 1px solid var(--border); border-radius: 12px; text-align: center; }\n.fb ul[data-view=grid] .k { width: 44px; height: 44px; font-size: 11px; }\n.fb ul[data-view=list] { gap: 0; padding: 4px 12px; }\n.fb ul[data-view=list] li { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }\n.fb ul[data-view=list] small { margin-left: auto; }\n.fb li b { font-weight: 500; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; }\n.fb small { color: var(--muted); }\n',
            'const list = document.querySelector(".fb ul");\nconst options = [...document.querySelectorAll(".fb [role=radio]")];\noptions.forEach((option) => option.addEventListener("click", () => {\n  options.forEach((other) => other.setAttribute("aria-checked", String(other === option)));\n  list.dataset.view = option.dataset.v;  // same items, two layouts\n}));\n',
            "The same files as tiles or as rows; one attribute switches the layout.",
        ),
        Item(
            "Grid gallery",
            f'<div class="gg">{TILES}</div>',
            PIC
            + ".gg { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 8px; width: min(540px, 100%); }\n.gg button { aspect-ratio: 1; border: 0; border-radius: 12px; transition: scale .2s var(--ease), filter .2s; }\n.gg button:hover, .gg button:focus-visible { scale: 1.04; filter: brightness(1.15); z-index: 1; }\n",
            note="Equal square tiles that fill each row; auto-fill decides the column count.",
        ),
        Item(
            "Image gallery",
            f'<div class="ig"><div class="main pic" style="--h:{HUES[0]}" role="img" aria-label="Photo 1 of 8"></div><div class="thumbs" role="listbox" aria-label="Photos">'
            + "".join(
                f'<button class="pic" role="option" aria-selected="{"true" if i == 0 else "false"}" style="--h:{h}" data-h="{h}" aria-label="Photo {i + 1}"></button>'
                for i, h in enumerate(HUES)
            )
            + "</div></div>",
            PIC
            + '.ig { display: grid; gap: 10px; width: min(480px, 100%); }\n.main { aspect-ratio: 16 / 10; border-radius: 16px; transition: opacity .2s; }\n.thumbs { display: grid; grid-template-columns: repeat(8, 1fr); gap: 6px; }\n.thumbs button { aspect-ratio: 1; border: 2px solid transparent; border-radius: 9px; opacity: .55; }\n.thumbs button[aria-selected="true"] { border-color: var(--fg); opacity: 1; }\n',
            'const main = document.querySelector(".main");\nconst thumbs = [...document.querySelectorAll(".thumbs button")];\nconst show = (thumb) => {\n  thumbs.forEach((other) => other.setAttribute("aria-selected", String(other === thumb)));\n  main.style.setProperty("--h", thumb.dataset.h);\n  main.setAttribute("aria-label", `${thumb.getAttribute("aria-label")} of ${thumbs.length}`);\n};\nthumbs.forEach((thumb, index) => {\n  thumb.addEventListener("click", () => show(thumb));\n  thumb.addEventListener("keydown", (event) => {\n    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;\n    if (!step) return;\n    const next = thumbs[(index + step + thumbs.length) % thumbs.length];\n    show(next);\n    next.focus();\n  });\n});\n',
            "One large picture above a row of thumbnails that choose it.",
        ),
        Item(
            "Masonry gallery",
            '<div class="mg">'
            + "".join(
                f'<div class="pic" style="--h:{h};aspect-ratio:{r}"></div>'
                for h, r in zip(
                    HUES + HUES[:4],
                    [
                        "3/4",
                        "4/3",
                        "1/1",
                        "3/5",
                        "16/9",
                        "4/5",
                        "1/1",
                        "3/4",
                        "4/3",
                        "2/3",
                        "1/1",
                        "16/10",
                    ],
                    strict=True,
                )
            )
            + "</div>",
            PIC
            + ".mg { columns: 3 150px; column-gap: 10px; width: min(540px, 100%); }\n.mg div { break-inside: avoid; margin-bottom: 10px; border-radius: 12px; }\n",
            note="Pictures keep their own proportions and pack into columns.",
        ),
        Item(
            "Media carousel",
            CAR_HTML.replace("<span>1</span>", "<span>▶</span>", 1),
            CAR,
            CAR_JS,
            "Scroll-snap does the sliding, so touch, trackpad and keyboard all work; buttons and dots follow what is in view.",
        ),
        Item(
            "Image carousel",
            CAR_HTML.replace('class="car"', 'class="car peek"'),
            CAR
            + ".peek .track { padding-inline: 12%; scroll-padding-inline: 12%; }\n.peek .track li { flex-basis: 76%; transition: scale .3s var(--ease), opacity .3s; }\n",
            CAR_JS,
            "The neighbours peek in at the edges, hinting that there is more.",
        ),
        Item(
            "Thumbnail strip",
            f'<div class="ts"><button class="edge" aria-label="Scroll left">‹</button><div class="strip" tabindex="0" aria-label="Thumbnails">{TILES * 2}</div><button class="edge" aria-label="Scroll right">›</button></div>',
            PIC
            + '.ts { display: flex; align-items: center; gap: 6px; width: min(520px, 100%); min-width: 0; }\n.strip { flex: 1; min-width: 0; display: flex; gap: 6px; overflow-x: auto; scroll-snap-type: x proximity; scrollbar-width: none; padding: 4px; }\n.strip::-webkit-scrollbar { display: none; }\n.strip button { flex: 0 0 72px; height: 54px; border: 2px solid transparent; border-radius: 9px; scroll-snap-align: start; opacity: .6; }\n.strip button[aria-current="true"] { border-color: var(--fg); opacity: 1; }\n.edge { flex: none; width: 30px; height: 54px; border: 1px solid var(--border); border-radius: 9px; background: var(--surface); }\n.edge:disabled { opacity: .3; }\n',
            'const strip = document.querySelector(".strip");\nconst [left, right] = document.querySelectorAll(".edge");\nconst tiles = [...strip.children];\nconst edges = () => { left.disabled = strip.scrollLeft <= 0; right.disabled = strip.scrollLeft + strip.clientWidth >= strip.scrollWidth - 1; };\nleft.addEventListener("click", () => strip.scrollBy({ left: -strip.clientWidth * 0.8, behavior: "smooth" }));\nright.addEventListener("click", () => strip.scrollBy({ left: strip.clientWidth * 0.8, behavior: "smooth" }));\nstrip.addEventListener("scroll", edges, { passive: true });\ntiles.forEach((tile) => tile.addEventListener("click", () => {\n  tiles.forEach((other) => other.setAttribute("aria-current", String(other === tile)));\n  tile.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });  // the chosen one is brought to the middle\n}));\ntiles[0].setAttribute("aria-current", "true");\nedges();\n',
            "A scrolling film strip: the chosen frame centres itself and the arrows disable at the ends.",
        ),
        Item(
            "Image cropper",
            '<div class="cr"><div class="stage pic" style="--h:200"><div class="crop" tabindex="0" role="group" aria-label="Crop area. Arrow keys move it."><i data-h="nw"></i><i data-h="ne"></i><i data-h="sw"></i><i data-h="se"></i></div></div><p><output></output><label><input type="checkbox" checked> Keep square</label></p></div>',
            PIC
            + ".cr { display: grid; gap: 10px; }\n.stage { position: relative; width: 360px; height: 240px; border-radius: 12px; overflow: hidden; touch-action: none; }\n.crop { position: absolute; border: 2px solid #fff; box-shadow: 0 0 0 9999px rgb(0 0 0 / .55); cursor: move; outline: none; background: linear-gradient(#fff6, #fff6) 33.3% 0 / 1px 100% no-repeat, linear-gradient(#fff6, #fff6) 66.6% 0 / 1px 100% no-repeat, linear-gradient(#fff6, #fff6) 0 33.3% / 100% 1px no-repeat, linear-gradient(#fff6, #fff6) 0 66.6% / 100% 1px no-repeat; }\n.crop i { position: absolute; width: 14px; height: 14px; background: #fff; border-radius: 3px; }\n.crop i[data-h=nw] { left: -7px; top: -7px; cursor: nw-resize; }\n.crop i[data-h=ne] { right: -7px; top: -7px; cursor: ne-resize; }\n.crop i[data-h=sw] { left: -7px; bottom: -7px; cursor: sw-resize; }\n.crop i[data-h=se] { right: -7px; bottom: -7px; cursor: se-resize; }\n.cr p { display: flex; justify-content: space-between; margin: 0; font-size: 13px; color: var(--muted); }\n.cr output { font-family: var(--mono); }\n",
            'const stage = document.querySelector(".stage");\nconst crop = stage.querySelector(".crop");\nconst square = document.querySelector(".cr input");\nconst readout = document.querySelector(".cr output");\nconst MIN = 50;\nlet box = { x: 100, y: 50, w: 140, h: 140 };\nconst apply = () => {\n  // The crop can never leave the picture.\n  box.w = Math.min(box.w, stage.clientWidth); box.h = Math.min(box.h, stage.clientHeight);\n  box.x = Math.min(stage.clientWidth - box.w, Math.max(0, box.x)); box.y = Math.min(stage.clientHeight - box.h, Math.max(0, box.y));\n  Object.assign(crop.style, { left: `${box.x}px`, top: `${box.y}px`, width: `${box.w}px`, height: `${box.h}px` });\n  readout.textContent = `${Math.round(box.w)} × ${Math.round(box.h)} at ${Math.round(box.x)}, ${Math.round(box.y)}`;\n};\nconst track = (target, onMove) => target.addEventListener("pointerdown", (event) => {\n  if (event.target !== target) return;\n  event.preventDefault();\n  target.setPointerCapture(event.pointerId);\n  const start = { ...box }, x0 = event.clientX, y0 = event.clientY;\n  const move = (e) => { onMove(start, e.clientX - x0, e.clientY - y0); apply(); };\n  target.addEventListener("pointermove", move);\n  target.addEventListener("pointerup", () => target.removeEventListener("pointermove", move), { once: true });\n});\ntrack(crop, (start, dx, dy) => { box.x = start.x + dx; box.y = start.y + dy; });\ncrop.querySelectorAll("i").forEach((handle) => track(handle, (start, dx, dy) => {\n  const west = handle.dataset.h.includes("w"), north = handle.dataset.h.includes("n");\n  let w = Math.max(MIN, start.w + (west ? -dx : dx)), h = Math.max(MIN, start.h + (north ? -dy : dy));\n  if (square.checked) w = h = Math.max(w, h);  // one size for both sides\n  box = { w, h, x: west ? start.x + start.w - w : start.x, y: north ? start.y + start.h - h : start.y };\n}));\ncrop.addEventListener("keydown", (event) => {\n  const step = { ArrowLeft: [-5, 0], ArrowRight: [5, 0], ArrowUp: [0, -5], ArrowDown: [0, 5] }[event.key];\n  if (step) { event.preventDefault(); box.x += step[0]; box.y += step[1]; apply(); }\n});\nsquare.addEventListener("change", () => { if (square.checked) { box.h = box.w = Math.min(box.w, box.h); apply(); } });\napply();\n',
            "A movable, resizable crop frame with a rule-of-thirds grid, an optional fixed ratio, and the result in pixels.",
        ),
        Item(
            "Image annotation",
            '<div class="an"><div class="stage pic" style="--h:260" tabindex="0" aria-label="Click the image to add a note"></div><ol aria-label="Notes"></ol></div>',
            PIC
            + ".an { display: grid; grid-template-columns: 340px 200px; gap: 12px; }\n.an .stage { position: relative; height: 230px; border-radius: 12px; cursor: crosshair; }\n.pin { position: absolute; display: grid; place-items: center; width: 24px; height: 24px; margin: -12px; border-radius: 50% 50% 50% 0; rotate: -45deg; background: #f43f5e; color: #fff; font: 700 11px var(--font); box-shadow: 0 4px 10px rgb(0 0 0 / .5); border: 0; }\n.pin span { rotate: 45deg; }\n.pin.on { background: var(--accent); color: #04121a; }\n.an ol { margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; align-content: start; counter-reset: n; }\n.an li { counter-increment: n; display: flex; gap: 8px; align-items: center; padding: 6px 8px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }\n.an li::before { content: counter(n); font-weight: 700; color: var(--muted); width: 14px; }\n.an li.on { border-color: var(--accent); }\n.an li input { flex: 1; min-width: 0; border: 0; outline: 0; background: none; }\n.an li button { border: 0; background: none; color: var(--muted); }\n@media (max-width: 600px) { .an { grid-template-columns: 1fr; } }\n",
            'const stage = document.querySelector(".an .stage");\nconst list = document.querySelector(".an ol");\nconst notes = [];\nconst render = (active) => {\n  stage.replaceChildren();\n  list.replaceChildren();\n  notes.forEach((note, index) => {\n    const pin = Object.assign(document.createElement("button"), { className: `pin ${note === active ? "on" : ""}` });\n    // Positions are stored as fractions of the image, so they survive any resize.\n    pin.style.left = `${note.x * 100}%`; pin.style.top = `${note.y * 100}%`;\n    pin.setAttribute("aria-label", `Note ${index + 1}: ${note.text || "empty"}`);\n    pin.append(Object.assign(document.createElement("span"), { textContent: String(index + 1) }));\n    pin.addEventListener("click", (event) => { event.stopPropagation(); render(note); list.children[index].querySelector("input").focus(); });\n    stage.append(pin);\n    const item = Object.assign(document.createElement("li"), { className: note === active ? "on" : "" });\n    const input = Object.assign(document.createElement("input"), { value: note.text, placeholder: "Describe this spot" });\n    input.setAttribute("aria-label", `Note ${index + 1}`);\n    input.addEventListener("input", () => { note.text = input.value; });\n    input.addEventListener("focus", () => { stage.querySelectorAll(".pin").forEach((other, i) => other.classList.toggle("on", i === index)); });\n    const remove = Object.assign(document.createElement("button"), { textContent: "×" });\n    remove.setAttribute("aria-label", `Delete note ${index + 1}`);\n    remove.addEventListener("click", () => { notes.splice(index, 1); render(); });\n    item.append(input, remove);\n    list.append(item);\n  });\n};\nconst add = (x, y) => { const note = { x, y, text: "" }; notes.push(note); render(note); list.lastElementChild.querySelector("input").focus(); };\nstage.addEventListener("click", (event) => { const box = stage.getBoundingClientRect(); add((event.clientX - box.left) / box.width, (event.clientY - box.top) / box.height); });\nstage.addEventListener("keydown", (event) => { if (event.key === "Enter" && event.target === stage) add(0.5, 0.5); });\nnotes.push({ x: 0.3, y: 0.4, text: "Logo is off-centre" });\nrender();\n',
            "Clicking the picture drops a numbered pin tied to a note in the list; positions are stored as fractions.",
        ),
        Item(
            "Image comparison slider",
            '<div class="cs" style="--p:50%"><div class="a pic" style="--h:210"><span>After</span></div><div class="b pic" style="--h:30"><span>Before</span></div><input type="range" min="0" max="100" value="50" aria-label="Reveal the before image"><i></i></div>',
            PIC
            + '.cs { position: relative; width: min(480px, 100%); aspect-ratio: 16 / 10; border-radius: 16px; overflow: hidden; }\n.cs .pic { position: absolute; inset: 0; }\n.cs .b { clip-path: inset(0 calc(100% - var(--p)) 0 0); }\n.cs span { position: absolute; bottom: 10px; padding: 2px 10px; border-radius: 99px; background: rgb(0 0 0 / .55); color: #fff; font-size: 12px; }\n.cs .a span { right: 10px; }\n.cs .b span { left: 10px; }\n.cs i { position: absolute; top: 0; bottom: 0; left: var(--p); width: 2px; margin-left: -1px; background: #fff; pointer-events: none; }\n.cs i::after { content: "⇔"; position: absolute; top: 50%; left: 50%; translate: -50% -50%; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 50%; background: #fff; color: #111; }\n.cs input { position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; opacity: 0; cursor: ew-resize; }\n.cs:has(input:focus-visible) i::after { box-shadow: 0 0 0 3px var(--accent); }\n',
            'const slider = document.querySelector(".cs");\nconst range = slider.querySelector("input");\n// An invisible range input is the control, so dragging, tapping and arrow keys all work.\nrange.addEventListener("input", () => slider.style.setProperty("--p", `${range.value}%`));\n',
            "Two pictures stacked; a hidden range input moves the dividing line, which makes it keyboard-operable for free.",
        ),
        Item(
            "Before/after viewer",
            '<div class="ba"><div class="frame"><div class="pic one" style="--h:30"></div><div class="pic two" style="--h:210"></div></div><div class="sw" role="radiogroup" aria-label="Version"><button role="radio" aria-checked="true" data-s="before">Before</button><button role="radio" aria-checked="false" data-s="after">After</button><button role="radio" aria-checked="false" data-s="both">Side by side</button></div></div>',
            PIC
            + '.ba { display: grid; gap: 10px; width: min(480px, 100%); }\n.frame { position: relative; display: grid; grid-template-columns: 1fr; aspect-ratio: 16 / 10; border-radius: 16px; overflow: hidden; gap: 4px; }\n.frame .pic { grid-area: 1 / 1; transition: opacity .35s var(--ease); }\n.ba[data-s=before] .two, .ba[data-s=after] .one { opacity: 0; }\n.ba[data-s=both] .frame { grid-template-columns: 1fr 1fr; }\n.ba[data-s=both] .pic { grid-area: auto; }\n.sw { display: inline-flex; justify-self: center; padding: 3px; border-radius: 10px; background: var(--surface-2); }\n.sw button { padding: 5px 14px; border: 0; border-radius: 7px; background: none; color: var(--muted); font-size: 13px; }\n.sw button[aria-checked="true"] { background: var(--surface); color: var(--fg); }\n',
            'const viewer = document.querySelector(".ba");\nconst options = [...viewer.querySelectorAll("[role=radio]")];\nconst set = (state) => { viewer.dataset.s = state; options.forEach((option) => option.setAttribute("aria-checked", String(option.dataset.s === state))); };\noptions.forEach((option) => option.addEventListener("click", () => set(option.dataset.s)));\n// Holding the space bar flips to the other version for as long as it is held.\nlet held = null;\nviewer.addEventListener("keydown", (event) => { if (event.key === " " && !held && viewer.dataset.s !== "both") { event.preventDefault(); held = viewer.dataset.s; set(held === "before" ? "after" : "before"); } });\nviewer.addEventListener("keyup", (event) => { if (event.key === " " && held) { set(held); held = null; } });\nset("before");\n',
            "Cross-fades between two versions, shows them side by side, or flips while a key is held.",
        ),
        Item(
            "PDF preview",
            f'<a class="pp" href="#" aria-label="Open Quarterly report, PDF, 12 pages"><div class="stack"><div class="pg b2"></div><div class="pg b1"></div><div class="pg">{PAGE_HTML}</div></div><div class="meta"><span class="ext">PDF</span><div><b>Quarterly report</b><small>12 pages · 284 KB</small></div></div></a>',
            PAGE
            + ".pp { display: grid; gap: 14px; justify-items: center; color: var(--fg); text-decoration: none; }\n.stack { position: relative; width: 170px; }\n.stack .pg { width: 170px; padding: 16px; transition: translate .25s var(--ease), rotate .25s var(--ease); }\n.stack .b1, .stack .b2 { position: absolute; inset: 0; }\n.stack .b1 { translate: 5px 5px; }\n.stack .b2 { translate: 10px 10px; }\n.pp:hover .b1, .pp:focus-visible .b1 { translate: 10px 4px; rotate: 3deg; }\n.pp:hover .b2, .pp:focus-visible .b2 { translate: 20px 8px; rotate: 6deg; }\n.meta { display: flex; gap: 10px; align-items: center; }\n.ext { padding: 3px 7px; border-radius: 6px; background: var(--danger); color: #1a0606; font: 700 10px var(--mono); }\n.meta small { display: block; color: var(--muted); }\n",
            note="The first page as a thumbnail on a small stack that fans out on hover, with type, pages and size.",
        ),
        Item(
            "Document viewer",
            '<div class="dv"><aside aria-label="Pages">'
            + "".join(
                f'<button aria-current="{"true" if i == 1 else "false"}" data-p="{i}"><span class="pg mini"></span>{i}</button>'
                for i in range(1, 5)
            )
            + '</aside><main tabindex="0">'
            + "".join(f'<div class="pg" id="dvp{i}">{PAGE_HTML}</div>' for i in range(1, 5))
            + "</main></div>",
            PAGE
            + '.dv { display: grid; grid-template-columns: 96px 1fr; width: min(520px, 100%); height: 340px; border: 1px solid var(--border); border-radius: 14px; overflow: hidden; background: #06080c; }\n.dv aside { display: grid; gap: 10px; align-content: start; padding: 12px; overflow: auto; border-right: 1px solid var(--border); background: var(--surface); }\n.dv aside button { display: grid; justify-items: center; gap: 4px; border: 0; background: none; color: var(--muted); font-size: 11px; }\n.dv .mini { width: 56px; padding: 0; box-shadow: none; outline: 2px solid transparent; outline-offset: 2px; }\n.dv aside button[aria-current="true"] .mini { outline-color: var(--primary); }\n.dv main { overflow: auto; padding: 18px; display: grid; gap: 18px; justify-items: center; scroll-behavior: smooth; }\n',
            'const main = document.querySelector(".dv main");\nconst thumbs = [...document.querySelectorAll(".dv aside button")];\nthumbs.forEach((thumb) => thumb.addEventListener("click", () => document.getElementById(`dvp${thumb.dataset.p}`).scrollIntoView({ block: "start" })));\n// Scrolling the pages moves the highlight in the thumbnail rail.\nconst observer = new IntersectionObserver((entries) => {\n  for (const entry of entries) {\n    if (!entry.isIntersecting) continue;\n    thumbs.forEach((thumb) => thumb.setAttribute("aria-current", String(`dvp${thumb.dataset.p}` === entry.target.id)));\n  }\n}, { root: main, threshold: 0.55 });\nmain.querySelectorAll(".pg").forEach((page) => observer.observe(page));\n',
            "A rail of page thumbnails beside the pages; each follows the other.",
        ),
        Item(
            "Code preview",
            '<figure class="cp"><figcaption><span>total.js</span><button>Copy</button></figcaption><pre><code>function total(items) {\n  // Sum the price of every item\n  return items.reduce((sum, item) =&gt; sum + item.price, 0);\n}\n\nconst label = `Total: ${total(cart)}`;</code></pre></figure>',
            ".cp { width: min(520px, 100%); margin: 0; border: 1px solid var(--border); border-radius: 14px; overflow: hidden; background: #06080c; }\n.cp figcaption { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; border-bottom: 1px solid var(--border); background: var(--surface); font: 12px var(--mono); color: var(--muted); }\n.cp button { padding: 3px 10px; border: 1px solid var(--border); border-radius: 7px; background: var(--surface-2); font-size: 12px; }\n.cp pre { margin: 0; padding: 14px 0; overflow: auto; font: 13px/1.65 var(--mono); counter-reset: line; }\n.cp .ln { display: block; padding: 0 16px 0 0; }\n.cp .ln::before { counter-increment: line; content: counter(line); display: inline-block; width: 40px; padding-right: 14px; text-align: right; color: #4b5266; user-select: none; }\n.t-k { color: #c792ea; } .t-s { color: #c3e88d; } .t-c { color: #5c6680; font-style: italic; } .t-n { color: #f78c6c; } .t-f { color: #82aaff; }\n",
            'const code = document.querySelector(".cp code");\nconst source = code.textContent;\n// A small tokenizer: one pass with a single pattern, each alternative a token type.\nconst TOKEN = /(\\/\\/[^\\n]*)|(`(?:\\\\.|[^`])*`|"(?:\\\\.|[^"])*"|\'(?:\\\\.|[^\'])*\')|\\b(function|return|const|let|if|else|for|of|new|class|import|export|from)\\b|\\b(\\d+(?:\\.\\d+)?)\\b|([A-Za-z_$][\\w$]*)(?=\\()/g;\nconst CLASS = ["t-c", "t-s", "t-k", "t-n", "t-f"];\nconst paint = (line) => {\n  const row = Object.assign(document.createElement("span"), { className: "ln" });\n  let last = 0;\n  for (const match of line.matchAll(TOKEN)) {\n    row.append(line.slice(last, match.index));\n    const kind = match.slice(1).findIndex((group) => group !== undefined);\n    row.append(Object.assign(document.createElement("span"), { className: CLASS[kind], textContent: match[0] }));  // text nodes only: nothing in the code can become markup\n    last = match.index + match[0].length;\n  }\n  row.append(line.slice(last) || " ");\n  return row;\n};\ncode.replaceChildren(...source.split("\\n").map(paint));\nconst button = document.querySelector(".cp button");\nbutton.addEventListener("click", async () => {\n  try { await navigator.clipboard.writeText(source); button.textContent = "Copied"; } catch { button.textContent = "Select and copy"; }\n  setTimeout(() => { button.textContent = "Copy"; }, 1500);\n});\n',
            "Line numbers that are not selected with the code, a copy button, and highlighting from a one-pattern tokenizer.",
        ),
        Item(
            "Markdown preview",
            '<div class="mp"><textarea aria-label="Markdown"># Release notes\n\nWe shipped **bulk export** and a _faster_ search.\n\n- Fix `login` redirect\n- New [pricing page](https://example.com)\n\n&gt; Thanks to everyone who tested.</textarea><article aria-live="polite" aria-label="Preview"></article></div>',
            ".mp { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; width: min(640px, 100%); height: 300px; }\n.mp textarea, .mp article { padding: 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); overflow: auto; }\n.mp textarea { resize: none; font: 13px/1.6 var(--mono); }\n.mp article h1 { margin: 0 0 10px; font-size: 22px; }\n.mp article h2 { margin: 0 0 8px; font-size: 17px; }\n.mp article p { margin: 0 0 10px; }\n.mp article ul { margin: 0 0 10px; padding-left: 20px; }\n.mp article code { padding: 1px 5px; border-radius: 5px; background: var(--surface-2); font: 13px var(--mono); }\n.mp article blockquote { margin: 0 0 10px; padding-left: 12px; border-left: 3px solid var(--primary); color: var(--muted); }\n.mp article a { color: var(--accent); }\n@media (max-width: 560px) { .mp { grid-template-columns: 1fr; height: auto; } .mp textarea { height: 160px; } }\n",
            'const source = document.querySelector(".mp textarea");\nconst preview = document.querySelector(".mp article");\n// Inline marks become elements built with createElement; the text is never parsed as HTML.\nconst inline = (text) => {\n  const nodes = [];\n  const pattern = /\\*\\*(.+?)\\*\\*|_(.+?)_|`(.+?)`|\\[(.+?)\\]\\((https?:\\/\\/[^\\s)]+)\\)/g;\n  let last = 0;\n  for (const match of text.matchAll(pattern)) {\n    nodes.push(text.slice(last, match.index));\n    if (match[1] !== undefined) nodes.push(Object.assign(document.createElement("strong"), { textContent: match[1] }));\n    else if (match[2] !== undefined) nodes.push(Object.assign(document.createElement("em"), { textContent: match[2] }));\n    else if (match[3] !== undefined) nodes.push(Object.assign(document.createElement("code"), { textContent: match[3] }));\n    else nodes.push(Object.assign(document.createElement("a"), { textContent: match[4], href: match[5], rel: "noopener noreferrer", target: "_blank" }));  // only http(s) links match\n    last = match.index + match[0].length;\n  }\n  nodes.push(text.slice(last));\n  return nodes;\n};\nconst render = () => {\n  const blocks = [];\n  let list = null;\n  for (const line of source.value.split("\\n")) {\n    const item = line.match(/^[-*]\\s+(.*)/);\n    if (item) { if (!list) { list = document.createElement("ul"); blocks.push(list); } const li = document.createElement("li"); li.append(...inline(item[1])); list.append(li); continue; }\n    list = null;\n    if (!line.trim()) continue;\n    const heading = line.match(/^(#{1,2})\\s+(.*)/), quote = line.match(/^>\\s?(.*)/);\n    const block = document.createElement(heading ? `h${heading[1].length}` : quote ? "blockquote" : "p");\n    block.append(...inline(heading ? heading[2] : quote ? quote[1] : line));\n    blocks.push(block);\n  }\n  preview.replaceChildren(...blocks);\n};\nsource.addEventListener("input", render);\nrender();\n',
            "Markdown on the left, rendered on the right as it is typed, built from elements rather than innerHTML so nothing can inject markup.",
        ),
        Item(
            "Audio waveform",
            '<div class="aw"><canvas height="96" aria-hidden="true"></canvas><div class="row"><button aria-label="Play">▶</button><span class="t">0:00 / 0:08</span></div><input type="range" min="0" max="1000" value="0" aria-label="Seek"></div>',
            ".aw { position: relative; width: min(480px, 100%); padding: 14px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.aw canvas { display: block; width: 100%; height: 96px; cursor: pointer; }\n.aw .row { display: flex; align-items: center; gap: 12px; margin-top: 10px; }\n.aw button { width: 38px; height: 38px; border: 0; border-radius: 50%; background: var(--primary); color: #fff; }\n.aw .t { font: 12px var(--mono); color: var(--muted); }\n.aw input { position: absolute; left: 14px; right: 14px; top: 14px; width: calc(100% - 28px); height: 96px; margin: 0; opacity: 0; cursor: pointer; }\n",
            'const canvas = document.querySelector(".aw canvas");\nconst context = canvas.getContext("2d");\nconst seek = document.querySelector(".aw input");\nconst button = document.querySelector(".aw button");\nconst label = document.querySelector(".aw .t");\nconst DURATION = 8, BARS = 90;\n// Peaks: one loudness value per bar. With real audio, decode it (AudioContext.decodeAudioData)\n// and take the largest sample in each slice.\nconst peaks = Array.from({ length: BARS }, (_, i) => 0.15 + Math.abs(Math.sin(i * 0.31) * Math.sin(i * 0.07 + 1)) * 0.85);\nlet position = 0, timer = null;\nconst draw = () => {\n  const ratio = devicePixelRatio || 1, width = canvas.clientWidth, height = canvas.clientHeight;\n  canvas.width = width * ratio; canvas.height = height * ratio;\n  context.scale(ratio, ratio);\n  const styles = getComputedStyle(canvas);\n  const played = styles.getPropertyValue("--primary"), rest = styles.getPropertyValue("--border");\n  const step = width / BARS;\n  peaks.forEach((peak, i) => {\n    context.fillStyle = i / BARS < position ? played : rest;\n    const bar = peak * height;\n    context.beginPath();\n    context.roundRect(i * step + 1, (height - bar) / 2, Math.max(1, step - 2), bar, 2);  // mirrored about the centre line\n    context.fill();\n  });\n  const seconds = Math.round(position * DURATION);\n  label.textContent = `0:${String(seconds).padStart(2, "0")} / 0:${String(DURATION).padStart(2, "0")}`;\n};\nconst stop = () => { clearInterval(timer); timer = null; button.textContent = "▶"; button.setAttribute("aria-label", "Play"); };\nbutton.addEventListener("click", () => {\n  if (timer) { stop(); return; }\n  if (position >= 1) position = 0;\n  button.textContent = "❚❚"; button.setAttribute("aria-label", "Pause");\n  timer = setInterval(() => { position = Math.min(1, position + 0.05 / DURATION); seek.value = String(position * 1000); draw(); if (position >= 1) stop(); }, 50);\n});\nseek.addEventListener("input", () => { position = seek.value / 1000; draw(); });\nnew ResizeObserver(draw).observe(canvas);\n',
            "Peaks drawn on a canvas, coloured up to the playhead; a transparent range input over it handles seeking.",
        ),
        Item(
            "Video timeline",
            '<div class="vt"><div class="ruler"></div><div class="lanes"><div class="lane"><span>Video</span><div class="clip pic" style="--h:250;left:0;width:46%">Intro</div><div class="clip pic" style="--h:190;left:48%;width:38%">Demo</div></div><div class="lane"><span>Audio</span><div class="clip au" style="left:6%;width:70%">Music</div></div><i class="head" role="slider" tabindex="0" aria-label="Playhead" aria-valuemin="0" aria-valuemax="30" aria-valuenow="0"></i></div><p><output>00:00.0</output></p></div>',
            PIC
            + '.vt { width: min(600px, 100%); padding: 12px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.ruler { position: relative; height: 22px; margin-left: 60px; border-bottom: 1px solid var(--border); font: 10px var(--mono); color: var(--muted); }\n.ruler span { position: absolute; top: 2px; translate: -50% 0; }\n.ruler span::after { content: ""; position: absolute; left: 50%; top: 14px; height: 6px; border-left: 1px solid var(--border); }\n.lanes { position: relative; margin-left: 60px; padding: 8px 0; touch-action: none; cursor: text; }\n.lane { position: relative; height: 40px; margin-bottom: 6px; border-radius: 8px; background: var(--bg); }\n.lane > span { position: absolute; right: calc(100% + 10px); top: 12px; font-size: 12px; color: var(--muted); }\n.clip { position: absolute; top: 4px; bottom: 4px; display: flex; align-items: center; padding: 0 10px; border-radius: 6px; font-size: 12px; font-weight: 600; color: #fff; overflow: hidden; }\n.clip.au { background: color-mix(in srgb, var(--success) 45%, var(--surface-2)); }\n.head { position: absolute; top: 0; bottom: 0; left: 0; width: 2px; margin-left: -1px; background: #f43f5e; cursor: ew-resize; outline: none; }\n.head::before { content: ""; position: absolute; top: -6px; left: -6px; border: 7px solid transparent; border-top-color: #f43f5e; }\n.head:focus-visible { box-shadow: 0 0 0 3px color-mix(in srgb, #f43f5e 40%, transparent); }\n.vt p { margin: 6px 0 0 60px; }\n.vt output { font: 13px var(--mono); }\n',
            'const DURATION = 30;\nconst lanes = document.querySelector(".lanes");\nconst head = document.querySelector(".head");\nconst ruler = document.querySelector(".ruler");\nconst readout = document.querySelector(".vt output");\nfor (let second = 0; second <= DURATION; second += 5) { const tick = Object.assign(document.createElement("span"), { textContent: `${second}s` }); tick.style.left = `${(second / DURATION) * 100}%`; ruler.append(tick); }\nlet time = 0;\nconst set = (seconds) => {\n  time = Math.min(DURATION, Math.max(0, seconds));\n  head.style.left = `${(time / DURATION) * 100}%`;\n  head.setAttribute("aria-valuenow", time.toFixed(1));\n  readout.textContent = `00:${String(Math.floor(time)).padStart(2, "0")}.${Math.round((time % 1) * 10)}`;\n};\nconst fromPointer = (event) => { const box = lanes.getBoundingClientRect(); return ((event.clientX - box.left) / box.width) * DURATION; };\n// Clicking anywhere on the tracks or dragging the playhead scrubs to that time.\nlanes.addEventListener("pointerdown", (event) => {\n  lanes.setPointerCapture(event.pointerId);\n  set(fromPointer(event));\n  const move = (e) => set(fromPointer(e));\n  lanes.addEventListener("pointermove", move);\n  lanes.addEventListener("pointerup", () => lanes.removeEventListener("pointermove", move), { once: true });\n});\nhead.addEventListener("keydown", (event) => {\n  const step = event.shiftKey ? 1 : 0.1;  // Shift moves a second, otherwise a frame-ish tenth\n  if (event.key === "ArrowRight") set(time + step); else if (event.key === "ArrowLeft") set(time - step); else if (event.key === "Home") set(0); else if (event.key === "End") set(DURATION);\n});\nset(0);\n',
            "A ruler, lanes of clips and a playhead that scrubs by click, drag or arrow keys.",
        ),
        Item(
            "Media player",
            '<div class="mpl" tabindex="0"><div class="screen pic" style="--h:250"><button class="big" aria-label="Play">▶</button></div><div class="bar"><button class="pp" aria-label="Play">▶</button><input class="seek" type="range" min="0" max="1000" value="0" aria-label="Seek"><span class="t">0:00 / 1:24</span><button class="mute" aria-pressed="false" aria-label="Mute">🔊</button><input class="vol" type="range" min="0" max="100" value="80" aria-label="Volume"><button class="rate" aria-label="Playback speed">1×</button></div></div>',
            PIC
            + ".mpl { width: min(520px, 100%); border-radius: 16px; overflow: hidden; border: 1px solid var(--border); background: #000; outline: none; }\n.mpl:focus-visible { box-shadow: 0 0 0 3px var(--accent); }\n.screen { position: relative; aspect-ratio: 16 / 9; display: grid; place-items: center; }\n.big { width: 64px; height: 64px; border: 0; border-radius: 50%; background: rgb(0 0 0 / .5); color: #fff; font-size: 22px; backdrop-filter: blur(6px); transition: opacity .2s, scale .2s; }\n.mpl.playing .big { opacity: 0; scale: 1.3; pointer-events: none; }\n.bar { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: var(--surface); }\n.bar button { min-width: 32px; height: 32px; border: 0; border-radius: 8px; background: none; }\n.bar button:hover { background: var(--surface-2); }\n.seek { flex: 1; min-width: 0; accent-color: var(--primary); }\n.vol { width: 70px; accent-color: var(--fg); }\n.t { font: 12px var(--mono); color: var(--muted); white-space: nowrap; }\n@media (max-width: 480px) { .vol { display: none; } }\n",
            '// The control logic of a player, driving a clock. With a real <video> the same handlers call\n// play(), pause(), currentTime, volume, muted and playbackRate, and listen to timeupdate.\nconst player = document.querySelector(".mpl");\nconst seek = player.querySelector(".seek");\nconst label = player.querySelector(".t");\nconst mute = player.querySelector(".mute");\nconst volume = player.querySelector(".vol");\nconst rate = player.querySelector(".rate");\nconst DURATION = 84, RATES = [1, 1.25, 1.5, 2];\nlet time = 0, speed = 1, timer = null;\nconst clock = (seconds) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;\nconst render = () => { seek.value = String((time / DURATION) * 1000); label.textContent = `${clock(time)} / ${clock(DURATION)}`; };\nconst playing = () => timer !== null;\nconst setPlaying = (on) => {\n  clearInterval(timer);\n  timer = on ? setInterval(() => { time = Math.min(DURATION, time + 0.1 * speed); render(); if (time >= DURATION) setPlaying(false); }, 100) : null;\n  player.classList.toggle("playing", on);\n  player.querySelectorAll(".pp, .big").forEach((button) => button.setAttribute("aria-label", on ? "Pause" : "Play"));\n  player.querySelector(".pp").textContent = on ? "❚❚" : "▶";\n};\nconst toggle = () => { if (!playing() && time >= DURATION) time = 0; setPlaying(!playing()); };\nplayer.querySelector(".pp").addEventListener("click", toggle);\nplayer.querySelector(".big").addEventListener("click", toggle);\nplayer.querySelector(".screen").addEventListener("click", (event) => { if (event.target.classList.contains("screen")) toggle(); });\nseek.addEventListener("input", () => { time = (seek.value / 1000) * DURATION; render(); });\nconst setMuted = (on) => { mute.setAttribute("aria-pressed", String(on)); mute.textContent = on ? "🔇" : "🔊"; };\nmute.addEventListener("click", () => setMuted(mute.getAttribute("aria-pressed") !== "true"));\nvolume.addEventListener("input", () => setMuted(volume.value === "0"));\nrate.addEventListener("click", () => { speed = RATES[(RATES.indexOf(speed) + 1) % RATES.length]; rate.textContent = `${speed}×`; });\n// The usual keys: space or K to play, arrows to seek five seconds, M to mute.\nplayer.addEventListener("keydown", (event) => {\n  if (event.target.matches("input")) return;\n  if (event.key === " " || event.key.toLowerCase() === "k") { event.preventDefault(); toggle(); }\n  else if (event.key === "ArrowRight") { time = Math.min(DURATION, time + 5); render(); }\n  else if (event.key === "ArrowLeft") { time = Math.max(0, time - 5); render(); }\n  else if (event.key.toLowerCase() === "m") setMuted(mute.getAttribute("aria-pressed") !== "true");\n});\nrender();\n',
            "Play, seek, time, mute, volume and speed with the standard keyboard shortcuts; the handlers map one-to-one onto a <video> element.",
        ),
    ),
)
