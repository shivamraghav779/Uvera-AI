"""Patterns 471-500: premium, high-polish patterns."""

from app.domains.references.vocabulary.base import BTN, Item, Section

NOISE = "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E\")"
SCENE = ".scene { display: grid; place-items: center; width: min(560px, 100%); height: 300px; border-radius: 22px; overflow: hidden; position: relative; }\n"
COPY = (
    '<div class="copy"><h3>Designed, not decorated</h3><p>Every effect earns its place.</p></div>'
)
COPY_CSS = ".copy { position: relative; text-align: center; }\n.copy h3 { margin: 0 0 6px; font-size: 26px; letter-spacing: -.02em; }\n.copy p { margin: 0; color: rgb(255 255 255 / .7); }\n"
# Reads the pointer position into two custom properties on the element.
POINTER = """\
const track = (element) => element.addEventListener("pointermove", (event) => {
  const box = element.getBoundingClientRect();
  element.style.setProperty("--x", `${event.clientX - box.left}px`);
  element.style.setProperty("--y", `${event.clientY - box.top}px`);
});
"""
# Runs a callback once for each element the first time it scrolls into view.
SEEN = """\
const whenSeen = (elements, callback, options = { threshold: 0.3 }) => {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) if (entry.isIntersecting) { callback(entry.target); observer.unobserve(entry.target); }
  }, options);
  elements.forEach((element) => observer.observe(element));
};
"""
STILL = 'const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\n'


def scene(name: str, inner: str, css: str, note: str, js: str = "") -> Item:
    return Item(name, f'<section class="scene">{inner}</section>', SCENE + css, js, note)


SECTION = Section(
    "patterns",
    "Premium / Wow UI Patterns",
    471,
    (
        scene(
            "Glassmorphism panel",
            '<i class="b1"></i><i class="b2"></i><div class="glass"><h3>Glass panel</h3><p>Blur, saturation, a hairline edge and an inner highlight.</p></div>',
            ".scene { background: #0a0b14; }\n.scene i { position: absolute; border-radius: 50%; filter: blur(30px); }\n.b1 { width: 240px; height: 240px; left: 6%; top: -10%; background: #7c5cff; }\n.b2 { width: 220px; height: 220px; right: 4%; bottom: -18%; background: #22d3ee; }\n.glass { position: relative; width: 320px; padding: 24px; border-radius: 20px; background: linear-gradient(135deg, rgb(255 255 255 / .16), rgb(255 255 255 / .05)); border: 1px solid rgb(255 255 255 / .22);\n  backdrop-filter: blur(22px) saturate(1.6); box-shadow: inset 0 1px 0 rgb(255 255 255 / .35), 0 24px 48px -20px rgb(0 0 0 / .7); }\n.glass h3 { margin: 0 0 6px; }\n.glass p { margin: 0; color: rgb(255 255 255 / .75); }\n@supports not (backdrop-filter: blur(1px)) { .glass { background: rgb(30 34 48 / .92); } }\n",
            "Glass needs colour behind it; where backdrop-filter is missing, the panel falls back to an opaque fill.",
        ),
        Item(
            "Neumorphic control",
            '<div class="neu"><button class="k" aria-pressed="false">Power</button><label class="s"><input type="range" min="0" max="100" value="60" aria-label="Level"></label></div>',
            '.neu { --base: #1a1e2a; --dark: #10131b; --light: #252b3b; display: grid; gap: 28px; justify-items: center; padding: 40px 56px; border-radius: 28px; background: var(--base); }\n.k { width: 96px; height: 96px; border: 0; border-radius: 50%; background: var(--base); color: var(--muted); font-weight: 700; box-shadow: 8px 8px 18px var(--dark), -8px -8px 18px var(--light); transition: box-shadow .2s, color .2s; }\n.k[aria-pressed="true"] { color: var(--accent); box-shadow: inset 6px 6px 12px var(--dark), inset -6px -6px 12px var(--light); }\n.k:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }\n.s input { appearance: none; width: 200px; height: 14px; border-radius: 99px; background: var(--base); box-shadow: inset 3px 3px 6px var(--dark), inset -3px -3px 6px var(--light); }\n.s input::-webkit-slider-thumb { appearance: none; width: 26px; height: 26px; border-radius: 50%; background: var(--base); box-shadow: 4px 4px 8px var(--dark), -4px -4px 8px var(--light); cursor: grab; }\n.s input::-moz-range-thumb { width: 26px; height: 26px; border: 0; border-radius: 50%; background: var(--base); }\n',
            'const key = document.querySelector(".neu .k");\nkey.addEventListener("click", () => key.setAttribute("aria-pressed", String(key.getAttribute("aria-pressed") !== "true")));\n',
            "Raised and pressed states from paired light and dark shadows on one base colour; text colour still carries the state.",
        ),
        scene(
            "Aurora gradient background",
            "<i></i><i></i><i></i>" + COPY,
            COPY_CSS
            + ".scene { background: #06070d; }\n.scene i { position: absolute; width: 60%; height: 120%; border-radius: 50%; filter: blur(60px); opacity: .7; mix-blend-mode: screen; animation: drift 14s ease-in-out infinite alternate; }\n.scene i:nth-child(1) { left: -10%; top: -40%; background: #7c5cff; }\n.scene i:nth-child(2) { left: 30%; top: 10%; background: #22d3ee; animation-duration: 18s; animation-delay: -6s; }\n.scene i:nth-child(3) { right: -15%; top: -30%; background: #34d399; animation-duration: 22s; animation-delay: -11s; }\n@keyframes drift { to { translate: 12% 14%; rotate: 25deg; scale: 1.15; } }\n",
            "Large blurred colour fields drifting slowly and blending like light.",
        ),
        scene(
            "Mesh gradient",
            COPY,
            COPY_CSS
            + ".scene { background:\n  radial-gradient(at 12% 18%, #7c5cff 0, transparent 46%),\n  radial-gradient(at 86% 12%, #f472b6 0, transparent 44%),\n  radial-gradient(at 78% 88%, #22d3ee 0, transparent 48%),\n  radial-gradient(at 18% 84%, #fbbf24 0, transparent 42%),\n  #0b0d12; }\n",
            "Several radial gradients anchored at different points over a dark base: no images, no blur filter.",
        ),
        scene(
            "Animated gradient",
            COPY,
            COPY_CSS
            + '@property --a { syntax: "<angle>"; inherits: false; initial-value: 0deg; }\n.scene { background: conic-gradient(from var(--a) at 50% 50%, #7c5cff, #22d3ee, #f472b6, #fbbf24, #7c5cff); animation: spin 12s linear infinite; }\n.scene::after { content: ""; position: absolute; inset: 0; backdrop-filter: blur(60px); background: rgb(11 13 18 / .35); }\n.copy { z-index: 1; }\n@keyframes spin { to { --a: 360deg; } }\n',
            "A registered custom property lets the gradient's angle itself be animated, softened by a blur layer.",
        ),
        scene(
            "Grain texture",
            COPY,
            COPY_CSS
            + f'.scene {{ background: linear-gradient(135deg, #312e81, #7c5cff 55%, #f472b6); }}\n.scene::before {{ content: ""; position: absolute; inset: 0; background-image: {NOISE}; mix-blend-mode: overlay; opacity: .55; }}\n',
            "An SVG turbulence tile blended over the gradient removes banding and adds a printed feel.",
        ),
        scene(
            "Noise overlay",
            '<div class="card"><h3>Subtle noise</h3><p>Barely visible; you notice when it is gone.</p></div>',
            f'.scene {{ background: #0f1118; }}\n.card {{ position: relative; width: 320px; padding: 24px; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); overflow: hidden; }}\n.card::after {{ content: ""; position: absolute; inset: -50%; background-image: {NOISE}; opacity: .09; pointer-events: none; animation: jitter .9s steps(4) infinite; }}\n.card h3 {{ margin: 0 0 6px; }}\n.card p {{ margin: 0; color: var(--muted); }}\n@keyframes jitter {{ 25% {{ translate: 2% -3%; }} 50% {{ translate: -3% 2%; }} 75% {{ translate: 3% 3%; }} }}\n',
            "A faint noise layer over a flat surface, shifted in steps so it reads as film grain.",
        ),
        scene(
            "Glow effect",
            '<button class="glow">Launch</button>',
            '.scene { background: #07080d; }\n.glow { position: relative; height: 54px; padding: 0 34px; border: 0; border-radius: 999px; background: var(--primary); color: #fff; font-weight: 700; font-size: 16px; box-shadow: 0 0 0 1px rgb(255 255 255 / .12) inset; }\n.glow::before { content: ""; position: absolute; inset: -10px; z-index: -1; border-radius: inherit; background: linear-gradient(90deg, var(--primary), var(--accent), #f472b6); filter: blur(22px); opacity: .7; transition: opacity .3s, inset .3s; }\n.glow:hover::before, .glow:focus-visible::before { opacity: 1; inset: -16px; }\n.glow { isolation: isolate; }\n',
            "The glow is a blurred, coloured copy behind the element, so it can change colour and size independently.",
        ),
        Item(
            "Soft shadow system",
            '<div class="sh">'
            + "".join(
                f'<div class="e{i}"><b>Level {i}</b><small>{t}</small></div>'
                for i, t in enumerate(["Flat", "Resting", "Raised", "Floating", "Modal"])
            )
            + "</div>",
            ".sh { display: grid; grid-template-columns: repeat(5, 1fr); gap: 18px; width: min(640px, 100%); padding: 30px; border-radius: 22px; background: #eef0f6; color: #1b2130; }\n.sh div { display: grid; place-items: center; align-content: center; aspect-ratio: 1; border-radius: 16px; background: #fff; font-size: 13px; }\n.sh small { color: #6b7388; }\n/* Each level layers a tight contact shadow with wider, fainter ambient ones. */\n.e1 { box-shadow: 0 1px 2px rgb(16 24 40 / .06), 0 1px 3px rgb(16 24 40 / .1); }\n.e2 { box-shadow: 0 2px 4px rgb(16 24 40 / .06), 0 6px 12px -2px rgb(16 24 40 / .1); }\n.e3 { box-shadow: 0 4px 6px rgb(16 24 40 / .05), 0 14px 28px -6px rgb(16 24 40 / .14); }\n.e4 { box-shadow: 0 8px 10px rgb(16 24 40 / .04), 0 28px 56px -12px rgb(16 24 40 / .22); }\n@media (max-width: 560px) { .sh { grid-template-columns: repeat(3, 1fr); } }\n",
            note="An elevation scale: every level combines a short contact shadow with longer ambient ones, growing together.",
        ),
        Item(
            "Layered depth cards",
            '<div class="deck" tabindex="0" aria-label="Stacked cards"><article>Plan</article><article>Design</article><article>Ship</article></div>',
            ".deck { position: relative; width: 260px; height: 200px; outline: none; }\n.deck article { position: absolute; inset: 0; display: grid; place-items: center; border: 1px solid var(--border); border-radius: 20px; background: var(--surface); font-size: 22px; font-weight: 700; box-shadow: 0 20px 40px -20px rgb(0 0 0 / .8); transition: translate .45s var(--ease), scale .45s var(--ease), rotate .45s var(--ease), opacity .45s; }\n.deck article:nth-child(1) { translate: 0 -24px; scale: .86; opacity: .5; }\n.deck article:nth-child(2) { translate: 0 -12px; scale: .93; opacity: .8; background: var(--surface-2); }\n.deck article:nth-child(3) { background: linear-gradient(140deg, color-mix(in srgb, var(--primary) 45%, var(--surface)), var(--surface)); }\n.deck:hover article:nth-child(1), .deck:focus-visible article:nth-child(1) { translate: -80px -30px; rotate: -8deg; scale: .92; opacity: 1; }\n.deck:hover article:nth-child(2), .deck:focus-visible article:nth-child(2) { translate: 0 -46px; scale: .96; opacity: 1; }\n.deck:hover article:nth-child(3), .deck:focus-visible article:nth-child(3) { translate: 80px -20px; rotate: 8deg; }\n",
            note="Cards stacked with scale and opacity for depth; on hover or focus they fan apart.",
        ),
        Item(
            "Magnetic cursor interaction",
            '<div class="mag-area"><button class="m">Explore</button><button class="m alt">Docs</button></div>',
            ".mag-area { display: flex; gap: 60px; padding: 70px; }\n.m { width: 110px; height: 110px; border: 1px solid var(--border); border-radius: 50%; background: var(--surface); font-weight: 700; transition: translate .35s var(--ease), background .2s; will-change: translate; }\n.m.alt { background: var(--primary); color: #fff; border: 0; }\n.m.near { transition-duration: .12s; }\n",
            STILL
            + 'const RADIUS = 110, STRENGTH = 0.4;\nconst magnets = [...document.querySelectorAll(".m")];\nif (!calm) document.addEventListener("pointermove", (event) => {\n  for (const magnet of magnets) {\n    const box = magnet.getBoundingClientRect();\n    const dx = event.clientX - (box.left + box.width / 2), dy = event.clientY - (box.top + box.height / 2);\n    const distance = Math.hypot(dx, dy);\n    // Inside the radius the element follows the pointer, more the closer it gets; outside it rests.\n    const pull = distance < RADIUS ? (1 - distance / RADIUS) * STRENGTH : 0;\n    magnet.classList.toggle("near", pull > 0);\n    magnet.style.translate = `${dx * pull}px ${dy * pull}px`;\n  }\n});\n',
            "Elements lean toward a nearby pointer with a pull that fades with distance, and stand still for reduced-motion users.",
        ),
        scene(
            "Cursor spotlight",
            COPY,
            COPY_CSS
            + '.scene { background: #07080d; --x: 50%; --y: 50%; }\n.scene::before { content: ""; position: absolute; inset: 0; background: radial-gradient(260px circle at var(--x) var(--y), rgb(124 92 255 / .45), transparent 70%); transition: opacity .3s; }\n.scene::after { content: ""; position: absolute; inset: 0; background: linear-gradient(rgb(255 255 255 / .05) 1px, transparent 1px) 0 0 / 100% 32px, linear-gradient(90deg, rgb(255 255 255 / .05) 1px, transparent 1px) 0 0 / 32px 100%;\n  mask: radial-gradient(260px circle at var(--x) var(--y), #000, transparent 75%); }\n',
            "A soft light under the pointer that also reveals a grid through a mask.",
            POINTER + 'track(document.querySelector(".scene"));\n',
        ),
        Item(
            "Hover spotlight",
            '<div class="hs">'
            + "".join(
                f"<article><h4>{t}</h4><p>{p}</p></article>"
                for t, p in [
                    ("Fast", "Edge-rendered in 40 ms."),
                    ("Safe", "SOC 2 Type II."),
                    ("Open", "Every action has an API."),
                ]
            )
            + "</div>",
            '.hs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; width: min(600px, 100%); }\n.hs article { position: relative; padding: 22px; border-radius: 18px; background: var(--surface); overflow: hidden; isolation: isolate; }\n/* A border that lights up near the pointer: a gradient showing through a 1px ring. */\n.hs article::before { content: ""; position: absolute; inset: 0; z-index: -1; border-radius: inherit; padding: 1px; background: radial-gradient(180px circle at var(--x, -200px) var(--y, -200px), var(--accent), var(--border) 70%);\n  mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0); }\n.hs article::after { content: ""; position: absolute; inset: 0; z-index: -1; background: radial-gradient(220px circle at var(--x, -200px) var(--y, -200px), rgb(34 211 238 / .14), transparent 70%); }\n.hs h4 { margin: 0 0 6px; }\n.hs p { margin: 0; color: var(--muted); font-size: 14px; }\n@media (max-width: 520px) { .hs { grid-template-columns: 1fr; } }\n',
            'const grid = document.querySelector(".hs");\n// One listener for the whole grid: each card gets the pointer in its own coordinates,\n// so the light crosses card borders smoothly.\ngrid.addEventListener("pointermove", (event) => {\n  for (const card of grid.children) {\n    const box = card.getBoundingClientRect();\n    card.style.setProperty("--x", `${event.clientX - box.left}px`);\n    card.style.setProperty("--y", `${event.clientY - box.top}px`);\n  }\n});\ngrid.addEventListener("pointerleave", () => { for (const card of grid.children) { card.style.removeProperty("--x"); card.style.removeProperty("--y"); } });\n',
            "Cards whose border and surface light up near the pointer, shared across the whole grid.",
        ),
        scene(
            "Parallax panel",
            '<i class="far"></i><i class="mid"></i><div class="near"><h3>Depth</h3><p>Layers move at different rates.</p></div>',
            ".scene { background: #080a12; perspective: 800px; }\n.scene > * { position: absolute; transition: translate .2s ease-out; }\n.far { inset: -10%; background: radial-gradient(2px 2px at 20% 30%, #fff, transparent), radial-gradient(2px 2px at 70% 20%, #fff, transparent), radial-gradient(1.500px 1.500px at 40% 70%, #fff, transparent), radial-gradient(2px 2px at 85% 65%, #fff, transparent), radial-gradient(1.500px 1.500px at 55% 45%, #fff, transparent); opacity: .7; translate: calc(var(--px, 0) * -10px) calc(var(--py, 0) * -10px); }\n.mid { width: 200px; height: 200px; border-radius: 50%; background: radial-gradient(circle at 35% 35%, #a78bfa, #4c1d95); translate: calc(var(--px, 0) * -28px) calc(var(--py, 0) * -28px); }\n.near { position: relative !important; padding: 20px 26px; border-radius: 18px; background: rgb(255 255 255 / .1); backdrop-filter: blur(14px); border: 1px solid rgb(255 255 255 / .2); translate: calc(var(--px, 0) * 22px) calc(var(--py, 0) * 22px); }\n.near h3 { margin: 0 0 4px; }\n.near p { margin: 0; color: rgb(255 255 255 / .75); }\n",
            "Layers shift by different amounts as the pointer moves, far ones least and against the direction.",
            STILL
            + 'const panel = document.querySelector(".scene");\nif (!calm) {\n  panel.addEventListener("pointermove", (event) => {\n    const box = panel.getBoundingClientRect();\n    // -1 to 1 from the centre; each layer multiplies it by its own depth in CSS.\n    panel.style.setProperty("--px", (((event.clientX - box.left) / box.width) * 2 - 1).toFixed(3));\n    panel.style.setProperty("--py", (((event.clientY - box.top) / box.height) * 2 - 1).toFixed(3));\n  });\n  panel.addEventListener("pointerleave", () => { panel.style.setProperty("--px", "0"); panel.style.setProperty("--py", "0"); });\n}\n',
        ),
        Item(
            "Scroll-triggered animation",
            '<div class="sc" tabindex="0">'
            + "".join(
                f'<section><div class="it" data-fx="{fx}">{t}</div></section>'
                for fx, t in [
                    ("up", "Rises in"),
                    ("left", "Slides from the left"),
                    ("zoom", "Scales up"),
                    ("blur", "Comes into focus"),
                ]
            )
            + "</div>",
            ".sc { width: min(460px, 100%); height: 320px; overflow: auto; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); }\n.sc section { display: grid; place-items: center; height: 260px; }\n.it { padding: 18px 26px; border-radius: 14px; background: var(--surface-2); font-weight: 700; opacity: 0; transition: opacity .7s var(--ease), translate .7s var(--ease), scale .7s var(--ease), filter .7s var(--ease); }\n.it[data-fx=up] { translate: 0 40px; }\n.it[data-fx=left] { translate: -60px 0; }\n.it[data-fx=zoom] { scale: .7; }\n.it[data-fx=blur] { filter: blur(12px); }\n.it.in { opacity: 1; translate: 0 0; scale: 1; filter: none; }\n@media (prefers-reduced-motion: reduce) { .it { opacity: 1; translate: 0 0; scale: 1; filter: none; } }\n",
            SEEN
            + 'const root = document.querySelector(".sc");\nwhenSeen([...root.querySelectorAll(".it")], (item) => item.classList.add("in"), { root, threshold: 0.6 });\n',
            "An IntersectionObserver adds one class when an element arrives; the animation itself is CSS and is skipped for reduced motion.",
        ),
        Item(
            "Reveal animation",
            '<div class="rv"><h2><span><i>Build</i></span> <span><i>things</i></span> <span><i>people</i></span> <span><i>love.</i></span></h2><p>Each word rises from behind its own mask.</p><button class="btn">Replay</button></div>',
            BTN
            + ".rv { display: grid; gap: 14px; justify-items: center; text-align: center; }\n.rv h2 { margin: 0; font-size: 44px; letter-spacing: -.03em; line-height: 1.1; }\n.rv h2 span { display: inline-block; overflow: hidden; vertical-align: bottom; padding-bottom: .08em; }\n.rv h2 i { display: inline-block; font-style: normal; translate: 0 110%; }\n.rv.go h2 i { animation: rise .8s var(--ease) forwards; }\n.rv.go h2 span:nth-child(2) i { animation-delay: .08s; }\n.rv.go h2 span:nth-child(3) i { animation-delay: .16s; }\n.rv.go h2 span:nth-child(4) i { animation-delay: .24s; }\n.rv p { margin: 0; color: var(--muted); opacity: 0; }\n.rv.go p { animation: fade .6s .5s forwards; }\n@keyframes rise { to { translate: 0 0; } }\n@keyframes fade { to { opacity: 1; } }\n@media (prefers-reduced-motion: reduce) { .rv h2 i { translate: 0 0; } .rv p { opacity: 1; } }\n",
            'const block = document.querySelector(".rv");\nconst play = () => { block.classList.remove("go"); void block.offsetWidth; block.classList.add("go"); };\nblock.querySelector("button").addEventListener("click", play);\nplay();\n',
            "Words slide up from behind a clipping wrapper, one after another: a masked reveal.",
        ),
        Item(
            "Morphing transition",
            '<button class="morph" aria-expanded="false"><span class="lab">New message</span><span class="form"><b>New message</b><i></i><i></i><i class="s"></i></span></button>',
            '.morph { position: relative; width: 170px; height: 48px; padding: 0; border: 0; border-radius: 24px; background: var(--primary); color: #fff; overflow: hidden; text-align: left;\n  transition: width .5s var(--ease), height .5s var(--ease), border-radius .5s var(--ease), background .5s var(--ease); }\n.morph .lab, .morph .form { position: absolute; inset: 0; transition: opacity .2s; }\n.morph .lab { display: grid; place-items: center; font-weight: 700; }\n.morph .form { display: grid; align-content: start; gap: 10px; padding: 18px; opacity: 0; }\n.morph .form i { height: 10px; border-radius: 5px; background: rgb(255 255 255 / .16); }\n.morph .form i.s { width: 55%; }\n.morph[aria-expanded="true"] { width: 320px; height: 200px; border-radius: 18px; background: var(--surface-2); }\n.morph[aria-expanded="true"] .lab { opacity: 0; }\n.morph[aria-expanded="true"] .form { opacity: 1; transition-delay: .25s; }\n',
            'const morph = document.querySelector(".morph");\nmorph.addEventListener("click", () => morph.setAttribute("aria-expanded", String(morph.getAttribute("aria-expanded") !== "true")));\n',
            "One element changes size, shape and colour to become another; the contents cross-fade partway through.",
        ),
        Item(
            "Shared-element transition",
            '<div class="se"><div class="list">'
            + "".join(
                f'<button style="--h:{h}" data-t="{t}"><i></i>{t}</button>'
                for h, t in [(250, "Aurora"), (20, "Ember"), (170, "Lagoon")]
            )
            + '</div><div class="detail" hidden><div class="hero"></div><h3></h3><button class="back">← Back</button></div></div>',
            ".se { position: relative; width: 320px; height: 300px; }\n.list { display: grid; gap: 10px; }\n.list button { display: flex; align-items: center; gap: 12px; padding: 8px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); font-weight: 600; }\n.list i, .hero { background: linear-gradient(135deg, hsl(var(--h) 72% 58%), hsl(calc(var(--h) + 55) 70% 32%)); }\n.list i { width: 56px; height: 56px; border-radius: 10px; }\n.detail { position: absolute; inset: 0; display: grid; grid-template-rows: 180px auto auto; gap: 10px; align-content: start; }\n.hero { border-radius: 18px; }\n.detail h3 { margin: 0; font-size: 22px; }\n.back { justify-self: start; border: 0; background: none; color: var(--primary); padding: 0; }\n.flying { transition: transform .45s var(--ease), border-radius .45s var(--ease); transform-origin: 0 0; }\n",
            STILL
            + '// FLIP: measure First, apply the Last state, Invert with a transform, then Play to nothing.\nconst list = document.querySelector(".list");\nconst detail = document.querySelector(".detail");\nconst hero = detail.querySelector(".hero");\nlet origin = null;\nconst fly = (from, element) => {\n  if (calm) return;\n  const to = element.getBoundingClientRect();\n  element.classList.remove("flying");\n  element.style.transform = `translate(${from.left - to.left}px, ${from.top - to.top}px) scale(${from.width / to.width}, ${from.height / to.height})`;\n  void element.offsetWidth;\n  element.classList.add("flying");\n  element.style.transform = "";\n};\nlist.addEventListener("click", (event) => {\n  const button = event.target.closest("button");\n  if (!button) return;\n  origin = button.querySelector("i");\n  const from = origin.getBoundingClientRect();\n  hero.style.setProperty("--h", button.style.getPropertyValue("--h"));\n  detail.querySelector("h3").textContent = button.dataset.t;\n  list.hidden = true;\n  detail.hidden = false;\n  fly(from, hero);  // the thumbnail appears to grow into the hero\n  detail.querySelector(".back").focus();\n});\ndetail.querySelector(".back").addEventListener("click", () => {\n  const from = hero.getBoundingClientRect();\n  detail.hidden = true;\n  list.hidden = false;\n  fly(from, origin);\n  origin.parentElement.focus();\n});\n',
            "The FLIP technique: the thumbnail seems to become the detail image because one is animated from the other's box.",
        ),
        Item(
            "Page transition",
            '<div class="pt"><nav><button aria-current="true" data-p="0">Home</button><button aria-current="false" data-p="1">Work</button><button aria-current="false" data-p="2">About</button></nav><div class="pages"><section>Home</section></div></div>',
            '.pt { width: min(420px, 100%); border: 1px solid var(--border); border-radius: 18px; background: var(--surface); overflow: hidden; }\n.pt nav { display: flex; gap: 4px; padding: 8px; border-bottom: 1px solid var(--border); }\n.pt nav button { padding: 6px 14px; border: 0; border-radius: 9px; background: none; color: var(--muted); }\n.pt nav button[aria-current="true"] { background: var(--surface-2); color: var(--fg); }\n.pages { position: relative; height: 200px; overflow: hidden; }\n.pages section { position: absolute; inset: 0; display: grid; place-items: center; font-size: 32px; font-weight: 800; }\n.pages .enter { animation: enter .4s var(--ease) both; }\n.pages .leave { animation: leave .4s var(--ease) both; }\n@keyframes enter { from { opacity: 0; translate: calc(var(--dir) * 40px) 0; } }\n@keyframes leave { to { opacity: 0; translate: calc(var(--dir) * -40px) 0; } }\n@media (prefers-reduced-motion: reduce) { .pages .enter, .pages .leave { animation-duration: .01s; } }\n',
            'const NAMES = ["Home", "Work", "About"];\nconst pages = document.querySelector(".pages");\nconst tabs = [...document.querySelectorAll(".pt nav button")];\nlet current = 0;\nconst go = (next) => {\n  if (next === current) return;\n  const direction = next > current ? 1 : -1;  // forward pages come from the right, earlier ones from the left\n  pages.style.setProperty("--dir", String(direction));\n  const leaving = pages.lastElementChild;\n  const entering = Object.assign(document.createElement("section"), { textContent: NAMES[next], className: "enter" });\n  leaving.className = "leave";\n  leaving.addEventListener("animationend", () => leaving.remove(), { once: true });\n  pages.append(entering);\n  tabs.forEach((tab, i) => tab.setAttribute("aria-current", String(i === next)));\n  current = next;\n};\ntabs.forEach((tab) => tab.addEventListener("click", () => go(Number(tab.dataset.p))));\n',
            "The old page leaves as the new one enters, in the direction of travel; the same structure maps onto the View Transitions API.",
        ),
        Item(
            "Microinteraction system",
            '<div class="mi"><button class="like" aria-pressed="false" aria-label="Like"><span>♥</span></button><label class="chk"><input type="checkbox"><i></i>Done</label><button class="send"><span>Send</span></button><input class="fld" placeholder="Focus me" aria-label="Sample field"></div>',
            '.mi { display: flex; flex-wrap: wrap; gap: 22px; align-items: center; justify-content: center; --fast: 120ms; --base: 220ms; --spring: cubic-bezier(.34, 1.56, .64, 1); }\n/* One vocabulary: press shrinks, success springs, focus rings grow. Durations and curves are tokens. */\n.mi button:active { scale: .94; transition: scale var(--fast); }\n.like { width: 46px; height: 46px; border: 1px solid var(--border); border-radius: 50%; background: var(--surface); font-size: 20px; color: var(--muted); transition: scale var(--base) var(--spring), color var(--fast); }\n.like[aria-pressed="true"] { color: #f43f5e; }\n.like[aria-pressed="true"] span { display: block; animation: pop var(--base) var(--spring); }\n.chk { display: flex; align-items: center; gap: 8px; cursor: pointer; }\n.chk input { position: absolute; opacity: 0; }\n.chk i { display: grid; place-items: center; width: 22px; height: 22px; border: 2px solid var(--border); border-radius: 7px; transition: background var(--fast), border-color var(--fast); }\n.chk i::after { content: ""; width: 10px; height: 5px; border: solid #fff; border-width: 0 0 2px 2px; rotate: -45deg; translate: 0 -1px; scale: 0; transition: scale var(--base) var(--spring); }\n.chk input:checked + i { background: var(--success); border-color: var(--success); }\n.chk input:checked + i::after { scale: 1; }\n.send { height: 40px; padding: 0 18px; border: 0; border-radius: 10px; background: var(--primary); color: #fff; font-weight: 600; overflow: hidden; transition: scale var(--base) var(--spring), background var(--base); }\n.send span { display: block; transition: translate var(--base) var(--ease); }\n.send.sent { background: var(--success); }\n.fld { height: 40px; padding: 0 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); outline: 0 solid color-mix(in srgb, var(--primary) 35%, transparent); transition: outline-width var(--fast), border-color var(--fast); }\n.fld:focus { outline-width: 4px; border-color: var(--primary); }\n@keyframes pop { 50% { scale: 1.45; } }\n',
            'const like = document.querySelector(".like");\nlike.addEventListener("click", () => like.setAttribute("aria-pressed", String(like.getAttribute("aria-pressed") !== "true")));\nconst send = document.querySelector(".send");\nsend.addEventListener("click", () => {\n  if (send.classList.contains("sent")) return;\n  send.classList.add("sent");\n  send.firstElementChild.textContent = "Sent ✓";\n  setTimeout(() => { send.classList.remove("sent"); send.firstElementChild.textContent = "Send"; }, 1600);\n});\n',
            "Small responses that share timing and easing tokens, so every control in the product answers in the same voice.",
        ),
        Item(
            "Animated icon",
            '<div class="ai"><button class="menu" aria-expanded="false" aria-label="Open menu"><i></i><i></i><i></i></button><button class="play" aria-pressed="false" aria-label="Play"><svg viewBox="0 0 24 24" width="24" height="24"><path d="M7 5 L19 12 L7 19 Z"/></svg></button><button class="bell" aria-label="Notifications"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M6 9a6 6 0 1 1 12 0c0 6 2.500 7 2.500 7h-17S6 15 6 9zM10 20a2 2 0 0 0 4 0"/></svg></button></div>',
            '.ai { display: flex; gap: 20px; }\n.ai button { display: grid; place-items: center; width: 52px; height: 52px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.menu { gap: 5px; align-content: center; }\n.menu i { display: block; width: 22px; height: 2px; border-radius: 2px; background: var(--fg); transition: translate .3s var(--ease), rotate .3s var(--ease), opacity .2s; }\n.menu[aria-expanded="true"] i:nth-child(1) { translate: 0 7px; rotate: 45deg; }\n.menu[aria-expanded="true"] i:nth-child(2) { opacity: 0; }\n.menu[aria-expanded="true"] i:nth-child(3) { translate: 0 -7px; rotate: -45deg; }\n.play path { fill: var(--fg); transition: d .3s var(--ease); }\n.play[aria-pressed="true"] path { d: path("M7 5 L11 5 L11 19 L7 19 Z M13 5 L17 5 L17 19 L13 19 Z"); }\n.bell svg { transform-origin: 50% 10%; }\n.bell:hover svg, .bell:focus-visible svg { animation: ring .7s var(--ease); }\n@keyframes ring { 20% { rotate: 14deg; } 40% { rotate: -12deg; } 60% { rotate: 8deg; } 80% { rotate: -5deg; } }\n',
            'const menu = document.querySelector(".menu");\nmenu.addEventListener("click", () => { const open = menu.getAttribute("aria-expanded") !== "true"; menu.setAttribute("aria-expanded", String(open)); menu.setAttribute("aria-label", open ? "Close menu" : "Open menu"); });\nconst play = document.querySelector(".play");\nplay.addEventListener("click", () => { const on = play.getAttribute("aria-pressed") !== "true"; play.setAttribute("aria-pressed", String(on)); play.setAttribute("aria-label", on ? "Pause" : "Play"); });\n',
            "Icons that change state by moving: a menu becomes a close mark, play morphs to pause, a bell rings.",
        ),
        Item(
            "Animated counter",
            '<dl class="ac"><div><dd data-to="48291">0</dd><dt>Active users</dt></div><div><dd data-to="99.98" data-dp="2" data-suffix="%">0</dd><dt>Uptime</dt></div><div><dd data-to="182" data-prefix="$" data-suffix="k">0</dd><dt>Revenue</dt></div></dl>',
            ".ac { display: grid; grid-template-columns: repeat(3, 1fr); gap: 28px; margin: 0; text-align: center; }\n.ac dd { margin: 0; font-size: 40px; font-weight: 800; letter-spacing: -.03em; font-variant-numeric: tabular-nums; }\n.ac dt { color: var(--muted); font-size: 14px; }\n",
            STILL
            + SEEN
            + 'const DURATION = 1400;\nconst show = (node, value) => {\n  const digits = Number(node.dataset.dp ?? 0);\n  node.textContent = `${node.dataset.prefix ?? ""}${value.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits })}${node.dataset.suffix ?? ""}`;\n};\nwhenSeen([...document.querySelectorAll(".ac dd")], (node) => {\n  const target = Number(node.dataset.to);\n  if (calm) { show(node, target); return; }  // no motion: the real figure straight away\n  const started = performance.now();\n  const frame = (now) => {\n    const progress = Math.min(1, (now - started) / DURATION);\n    show(node, target * (1 - (1 - progress) ** 4));  // fast at first, settling at the end\n    if (progress < 1) requestAnimationFrame(frame);\n  };\n  requestAnimationFrame(frame);\n});\n',
            "Figures count up when they first scroll into view, in tabular digits so the width does not jitter.",
        ),
        Item(
            "Number morphing",
            '<div class="nm"><div class="reel" aria-live="polite" aria-atomic="true"></div><div class="row"><button class="btn" data-d="-137">−137</button><button class="btn" data-d="137">+137</button></div></div>',
            BTN
            + ".nm { display: grid; gap: 18px; justify-items: center; }\n.reel { display: flex; font-size: 56px; font-weight: 800; line-height: 1; font-variant-numeric: tabular-nums; }\n.reel .col { height: 1em; overflow: hidden; }\n.reel .strip { display: grid; transition: translate .6s var(--ease); }\n.reel .strip span { height: 1em; }\n.reel .sep { opacity: .5; }\n.row { display: flex; gap: 10px; }\n",
            'const reel = document.querySelector(".reel");\nlet value = 4821;\n// Each digit is a strip of 0-9 behind a one-line window; changing the value slides the strips.\nconst render = () => {\n  const text = value.toLocaleString("en-US");\n  reel.setAttribute("aria-label", text);\n  const existing = [...reel.children];\n  [...text].forEach((char, i) => {\n    let slot = existing[i];\n    const isDigit = /\\d/.test(char);\n    if (!slot || slot.classList.contains("col") !== isDigit) {\n      const fresh = document.createElement("span");\n      if (isDigit) { fresh.className = "col"; const strip = Object.assign(document.createElement("span"), { className: "strip" }); for (let d = 0; d < 10; d += 1) strip.append(Object.assign(document.createElement("span"), { textContent: String(d) })); fresh.append(strip); }\n      else { fresh.className = "sep"; fresh.textContent = char; }\n      fresh.setAttribute("aria-hidden", "true");\n      if (slot) slot.replaceWith(fresh); else reel.append(fresh);\n      slot = fresh;\n    }\n    if (isDigit) requestAnimationFrame(() => { slot.firstElementChild.style.translate = `0 -${Number(char)}em`; });\n  });\n  existing.slice(text.length).forEach((extra) => extra.remove());\n};\ndocument.querySelectorAll(".nm button").forEach((button) => button.addEventListener("click", () => { value = Math.max(0, value + Number(button.dataset.d)); render(); }));\nrender();\n',
            "Each digit rolls to its new value on its own reel, odometer style; the full number is exposed as the label.",
        ),
        Item(
            "Skeleton-to-content transition",
            '<div class="stc"><article class="card loading" aria-busy="true"><div class="ph"><i class="av"></i><i class="l w60"></i><i class="l"></i><i class="l w80"></i></div><div class="real"><span class="av">DW</span><h3>Dana Whitfield</h3><p>Design lead in Bristol. Reviews 142 pull requests a year and counting.</p></div></article><button class="btn">Reload</button></div>',
            BTN
            + ".stc { display: grid; gap: 14px; justify-items: center; }\n.card { position: relative; width: 320px; min-height: 150px; padding: 20px; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); }\n.ph, .real { transition: opacity .35s var(--ease), filter .35s var(--ease); }\n.ph { position: absolute; inset: 20px; display: grid; gap: 10px; align-content: start; }\n.ph i { display: block; border-radius: 6px; background: linear-gradient(100deg, var(--surface-2) 30%, color-mix(in srgb, var(--surface-2) 70%, white 10%) 50%, var(--surface-2) 70%) 0 0 / 300% 100%; animation: sweep 1.3s linear infinite; }\n.ph .av { width: 40px; height: 40px; border-radius: 50%; }\n.ph .l { height: 12px; }\n.w60 { width: 60%; } .w80 { width: 80%; }\n.real .av { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--accent)); font-size: 13px; font-weight: 700; margin-bottom: 10px; }\n.real h3 { margin: 0 0 4px; }\n.real p { margin: 0; color: var(--muted); }\n/* The skeleton has the same shape as the content, so swapping them moves nothing. */\n.card.loading .real { opacity: 0; filter: blur(6px); }\n.card:not(.loading) .ph { opacity: 0; pointer-events: none; }\n@keyframes sweep { from { background-position: 150% 0; } to { background-position: -150% 0; } }\n",
            'const card = document.querySelector(".stc .card");\nconst load = () => {\n  card.classList.add("loading");\n  card.setAttribute("aria-busy", "true");\n  setTimeout(() => { card.classList.remove("loading"); card.setAttribute("aria-busy", "false"); }, 1500);  // stands in for the request\n};\ndocument.querySelector(".stc .btn").addEventListener("click", load);\nload();\n',
            "Placeholder and content occupy the same box and cross-fade, so nothing shifts when the data arrives.",
        ),
        Item(
            "Liquid loading animation",
            '<div class="liq" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="Loading"><svg viewBox="0 0 120 120" aria-hidden="true"><defs><clipPath id="drop"><circle cx="60" cy="60" r="54"/></clipPath></defs><circle cx="60" cy="60" r="54" class="rim"/><g clip-path="url(#drop)"><g class="lvl"><path class="w1" d="M-120 0 Q-90 -10 -60 0 T0 0 T60 0 T120 0 T180 0 T240 0 V140 H-120 Z"/><path class="w2" d="M-120 0 Q-90 8 -60 0 T0 0 T60 0 T120 0 T180 0 T240 0 V140 H-120 Z"/></g></g></svg><b>0%</b></div>',
            ".liq { position: relative; width: 160px; height: 160px; display: grid; place-items: center; }\n.liq svg { position: absolute; inset: 0; }\n.rim { fill: var(--surface); stroke: var(--border); stroke-width: 2; }\n.lvl { transition: translate .4s var(--ease); translate: 0 120px; }\n.w1 { fill: var(--primary); animation: wave 2.2s linear infinite; }\n.w2 { fill: var(--accent); opacity: .5; animation: wave 3.1s linear infinite reverse; }\n.liq b { position: relative; font-size: 26px; font-variant-numeric: tabular-nums; mix-blend-mode: difference; }\n@keyframes wave { to { translate: 120px 0; } }\n",
            'const tank = document.querySelector(".liq");\nconst level = tank.querySelector(".lvl");\nlet value = 0;\nconst timer = setInterval(() => {\n  value = Math.min(100, value + 4);\n  // The liquid surface sits at this height inside the circle (0% at the bottom, 100% at the top).\n  level.style.translate = `0 ${114 - value * 1.08}px`;\n  tank.setAttribute("aria-valuenow", String(value));\n  tank.querySelector("b").textContent = `${value}%`;\n  if (value === 100) clearInterval(timer);\n}, 140);\n',
            "A circle fills with two offset waves; the level is the progress value.",
        ),
        scene(
            "Particle background",
            '<canvas aria-hidden="true"></canvas>' + COPY,
            COPY_CSS
            + ".scene { background: #06070d; }\n.scene canvas { position: absolute; inset: 0; width: 100%; height: 100%; }\n",
            "Points drifting on a canvas, joined by lines when close; it pauses off-screen and for reduced motion.",
            STILL
            + 'const canvas = document.querySelector(".scene canvas");\nconst context = canvas.getContext("2d");\nconst COUNT = 46, LINK = 90;\nlet width = 0, height = 0, particles = [], frame = 0;\nconst resize = () => {\n  const ratio = Math.min(2, devicePixelRatio || 1);\n  width = canvas.clientWidth; height = canvas.clientHeight;\n  canvas.width = width * ratio; canvas.height = height * ratio;\n  context.setTransform(ratio, 0, 0, ratio, 0, 0);\n  if (particles.length === 0) particles = Array.from({ length: COUNT }, () => ({ x: Math.random() * width, y: Math.random() * height, vx: (Math.random() - 0.5) * 0.5, vy: (Math.random() - 0.5) * 0.5 }));\n  draw();\n};\nconst draw = () => {\n  context.clearRect(0, 0, width, height);\n  for (const p of particles) {\n    p.x = (p.x + p.vx + width) % width; p.y = (p.y + p.vy + height) % height;  // leaving one edge, entering the opposite\n    context.fillStyle = "rgb(167 139 250 / .9)";\n    context.beginPath(); context.arc(p.x, p.y, 1.6, 0, Math.PI * 2); context.fill();\n  }\n  for (let i = 0; i < particles.length; i += 1) for (let j = i + 1; j < particles.length; j += 1) {\n    const a = particles[i], b = particles[j], distance = Math.hypot(a.x - b.x, a.y - b.y);\n    if (distance > LINK) continue;\n    context.strokeStyle = `rgb(124 92 255 / ${(1 - distance / LINK) * 0.5})`;\n    context.beginPath(); context.moveTo(a.x, a.y); context.lineTo(b.x, b.y); context.stroke();\n  }\n};\nconst loop = () => { draw(); frame = requestAnimationFrame(loop); };\nnew ResizeObserver(resize).observe(canvas);\n// Animate only while visible, and not at all if the person asked for less motion.\nif (!calm) new IntersectionObserver(([entry]) => { cancelAnimationFrame(frame); if (entry.isIntersecting) loop(); }).observe(canvas);\n',
        ),
        scene(
            "Interactive gradient",
            COPY,
            COPY_CSS
            + '.scene { --x: 50%; --y: 50%; background: radial-gradient(circle at var(--x) var(--y), #f472b6 0, transparent 38%), radial-gradient(circle at calc(100% - var(--x)) calc(100% - var(--y)), #22d3ee 0, transparent 42%), linear-gradient(135deg, #312e81, #0b0d12); transition: --x .4s ease-out, --y .4s ease-out; }\n@property --x { syntax: "<length-percentage>"; inherits: true; initial-value: 50%; }\n@property --y { syntax: "<length-percentage>"; inherits: true; initial-value: 50%; }\n',
            "Two colour fields follow the pointer, one directly and one mirrored; registered properties let them glide.",
            POINTER + 'track(document.querySelector(".scene"));\n',
        ),
        Item(
            "3D object viewer",
            '<div class="v3" tabindex="0" role="application" aria-label="3D object. Drag or use the arrow keys to rotate."><div class="cube"><i class="f">Front</i><i class="b">Back</i><i class="r">Right</i><i class="l">Left</i><i class="t">Top</i><i class="u">Bottom</i></div></div><p class="hint">Drag to rotate</p>',
            ".v3 { width: 300px; height: 280px; display: grid; place-items: center; perspective: 900px; cursor: grab; touch-action: none; outline: none; border-radius: 20px; }\n.v3:focus-visible { box-shadow: 0 0 0 2px var(--accent); }\n.v3:active { cursor: grabbing; }\n.cube { --s: 130px; position: relative; width: var(--s); height: var(--s); transform-style: preserve-3d; transform: rotateX(var(--rx, -20deg)) rotateY(var(--ry, 30deg)); }\n.cube.spin { transition: transform .8s var(--ease); }\n.cube i { position: absolute; inset: 0; display: grid; place-items: center; border: 1px solid rgb(255 255 255 / .25); border-radius: 12px; font: 600 13px var(--font); font-style: normal; color: #fff; background: linear-gradient(135deg, rgb(124 92 255 / .85), rgb(34 211 238 / .6)); backface-visibility: hidden; }\n.f { transform: translateZ(calc(var(--s) / 2)); }\n.b { transform: rotateY(180deg) translateZ(calc(var(--s) / 2)); }\n.r { transform: rotateY(90deg) translateZ(calc(var(--s) / 2)); }\n.l { transform: rotateY(-90deg) translateZ(calc(var(--s) / 2)); }\n.t { transform: rotateX(90deg) translateZ(calc(var(--s) / 2)); }\n.u { transform: rotateX(-90deg) translateZ(calc(var(--s) / 2)); }\n.hint { margin: 0; color: var(--muted); font-size: 13px; }\nbody { align-content: center; justify-items: center; }\n",
            'const viewer = document.querySelector(".v3");\nconst cube = viewer.querySelector(".cube");\nlet rx = -20, ry = 30;\nconst apply = () => { cube.style.setProperty("--rx", `${rx}deg`); cube.style.setProperty("--ry", `${ry}deg`); };\nviewer.addEventListener("pointerdown", (event) => {\n  viewer.setPointerCapture(event.pointerId);\n  cube.classList.remove("spin");\n  const start = { x: event.clientX, y: event.clientY, rx, ry };\n  const move = (e) => {\n    ry = start.ry + (e.clientX - start.x) * 0.5;\n    rx = Math.max(-85, Math.min(85, start.rx - (e.clientY - start.y) * 0.5));  // no flipping over the poles\n    apply();\n  };\n  viewer.addEventListener("pointermove", move);\n  viewer.addEventListener("pointerup", () => viewer.removeEventListener("pointermove", move), { once: true });\n});\nviewer.addEventListener("keydown", (event) => {\n  const step = { ArrowLeft: [0, -15], ArrowRight: [0, 15], ArrowUp: [15, 0], ArrowDown: [-15, 0] }[event.key];\n  if (!step) return;\n  event.preventDefault();\n  cube.classList.add("spin");\n  rx = Math.max(-85, Math.min(85, rx + step[0])); ry += step[1];\n  apply();\n});\napply();\n',
            "A CSS 3D object turned by dragging or with the arrow keys; the same controls suit a WebGL model viewer.",
        ),
        Item(
            "Spatial/3D card",
            '<div class="tilt"><article><div class="shine"></div><span class="chip">PRO</span><h3>Northwind Black</h3><p>•••• 4242</p></article></div>',
            ".tilt { perspective: 900px; }\n.tilt article { position: relative; width: 320px; height: 200px; padding: 24px; border-radius: 22px; overflow: hidden; color: #fff; background: linear-gradient(135deg, #1e1b4b, #4c1d95 55%, #0e7490);\n  transform-style: preserve-3d; transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg)); transition: transform .5s var(--ease), box-shadow .5s; box-shadow: 0 20px 40px -20px rgb(0 0 0 / .8); }\n.tilt article.live { transition-duration: .08s; box-shadow: calc(var(--ry, 0deg) / -1deg * 1.5px) calc(var(--rx, 0deg) / 1deg * 1.5px + 26px) 50px -18px rgb(0 0 0 / .85); }\n.shine { position: absolute; inset: 0; background: radial-gradient(circle at var(--gx, 50%) var(--gy, 50%), rgb(255 255 255 / .35), transparent 45%); opacity: 0; transition: opacity .3s; }\n.live .shine { opacity: 1; }\n/* Content floats above the card surface, so it shifts against it as the card tilts. */\n.tilt h3, .tilt p, .chip { position: relative; transform: translateZ(40px); }\n.chip { display: inline-block; padding: 2px 10px; border-radius: 99px; background: rgb(255 255 255 / .18); font: 700 11px var(--mono); }\n.tilt h3 { margin: 64px 0 2px; font-size: 20px; }\n.tilt p { margin: 0; font-family: var(--mono); opacity: .8; }\n",
            STILL
            + 'const card = document.querySelector(".tilt article");\nconst MAX = 14;  // degrees\nif (!calm) {\n  card.addEventListener("pointermove", (event) => {\n    const box = card.getBoundingClientRect();\n    const x = (event.clientX - box.left) / box.width, y = (event.clientY - box.top) / box.height;\n    card.classList.add("live");\n    card.style.setProperty("--ry", `${(x - 0.5) * 2 * MAX}deg`);\n    card.style.setProperty("--rx", `${(0.5 - y) * 2 * MAX}deg`);\n    card.style.setProperty("--gx", `${x * 100}%`);  // the highlight sits where the pointer is\n    card.style.setProperty("--gy", `${y * 100}%`);\n  });\n  card.addEventListener("pointerleave", () => { card.classList.remove("live"); card.style.setProperty("--rx", "0deg"); card.style.setProperty("--ry", "0deg"); });\n}\n',
            "The card tilts toward the pointer with a moving highlight, a shadow that follows, and content raised above its surface.",
        ),
        Item(
            "Cinematic hero section",
            '<header class="hero"><div class="sky"></div><div class="grain"></div><div class="in"><p class="eb">Introducing Northwind 4</p><h1><span>The workspace</span> <span>that thinks ahead.</span></h1><p class="sub">Plans, drafts and reports that write their first version themselves.</p><div class="cta"><a class="btn" href="#">Start free</a><a class="ghost" href="#">Watch the film <span>▶</span></a></div></div><div class="fade"></div></header>',
            BTN
            + f".hero {{ position: relative; display: grid; place-items: center; width: min(760px, 100%); min-height: 420px; padding: 40px 24px; border-radius: 26px; overflow: hidden; text-align: center; background: #05060b; isolation: isolate; }}\n.sky {{ position: absolute; inset: -20%; z-index: -3; background: radial-gradient(at 20% 20%, #7c5cff 0, transparent 45%), radial-gradient(at 80% 30%, #22d3ee 0, transparent 42%), radial-gradient(at 50% 90%, #f472b6 0, transparent 46%); filter: blur(30px); opacity: .75; animation: breathe 16s ease-in-out infinite alternate; }}\n.grain {{ position: absolute; inset: 0; z-index: -2; background-image: {NOISE}; mix-blend-mode: overlay; opacity: .45; }}\n.fade {{ position: absolute; inset: auto 0 0; height: 45%; z-index: -1; background: linear-gradient(transparent, #05060b); }}\n.eb {{ display: inline-block; margin: 0 0 18px; padding: 4px 14px; border: 1px solid rgb(255 255 255 / .22); border-radius: 99px; background: rgb(255 255 255 / .08); backdrop-filter: blur(10px); font-size: 13px; animation: up .8s var(--ease) both; }}\n.hero h1 {{ margin: 0; font-size: clamp(34px, 6vw, 60px); line-height: 1.02; letter-spacing: -.04em; text-wrap: balance; }}\n.hero h1 span {{ display: inline-block; animation: up .9s var(--ease) both; }}\n.hero h1 span:nth-child(1) {{ animation-delay: .1s; }}\n.hero h1 span:nth-child(2) {{ animation-delay: .22s; background: linear-gradient(90deg, #fff, #c4b5fd 60%, #67e8f9); -webkit-background-clip: text; background-clip: text; color: transparent; }}\n.sub {{ max-width: 44ch; margin: 18px auto 26px; color: rgb(255 255 255 / .72); font-size: 17px; animation: up .9s .34s var(--ease) both; }}\n.cta {{ display: flex; gap: 16px; justify-content: center; align-items: center; animation: up .9s .46s var(--ease) both; }}\n.cta .btn {{ height: 48px; padding: 0 24px; border-radius: 999px; background: #fff; color: #0b0d12; text-decoration: none; box-shadow: 0 0 40px rgb(124 92 255 / .6); }}\n.ghost {{ color: #fff; text-decoration: none; font-weight: 600; }}\n.ghost span {{ display: inline-grid; place-items: center; width: 26px; height: 26px; margin-left: 6px; border-radius: 50%; background: rgb(255 255 255 / .16); font-size: 10px; }}\n@keyframes up {{ from {{ opacity: 0; translate: 0 26px; filter: blur(8px); }} }}\n@keyframes breathe {{ to {{ scale: 1.15; rotate: 8deg; }} }}\n@media (prefers-reduced-motion: reduce) {{ .sky {{ animation: none; }} }}\n",
            note="Everything at once, in order: a breathing aurora, grain, a vignette, a glass eyebrow, staggered blur-in type, a gradient phrase and a glowing call to action.",
        ),
    ),
)
