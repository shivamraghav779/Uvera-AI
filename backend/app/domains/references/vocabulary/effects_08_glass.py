"""Effects 211-230: glass and materials."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.effects_07_background import GRAIN
from app.domains.references.vocabulary.fx import STAGE

# Glass is only visible against something: every entry sits on this busy scene.
WORLD_HTML = '<div class="world" aria-hidden="true"><i></i><i></i><i></i><b>BEHIND</b></div>'
SCENE = """\
.scene { border-radius: 18px; overflow: hidden; background: #0b1020; }
.world { position: absolute; inset: 0; display: grid; place-items: center; }
.world i { position: absolute; border-radius: 50%; }
.world i:nth-child(1) { left: 4%; top: -18%; width: 190px; height: 190px; background: #f472b6; }
.world i:nth-child(2) { right: 2%; bottom: -22%; width: 220px; height: 220px; background: #22d3ee; }
.world i:nth-child(3) { right: 30%; top: 8%; width: 90px; height: 90px; background: #fbbf24; }
.world b { position: relative; font-size: 88px; font-weight: 900; letter-spacing: -.04em; color: #fff; }
.glass { position: relative; display: grid; place-items: center; width: 250px; height: 140px; border-radius: 22px; color: #fff; font-weight: 600; text-align: center; }
"""


def glass(
    name: str,
    rule: str,
    note: str,
    extra: str = "",
    label: str = "",
    js: str = "",
    inner: str = "",
    after: str = "",
) -> Item:
    panel = inner or f'<div class="glass">{label or name}</div>'
    css = STAGE + SCENE + (f".glass {{ {rule} }}\n" if rule else "") + extra
    return Item(name, f'<div class="stage scene">{WORLD_HTML}{panel}{after}</div>', css, js, note)


POINTER = """\
const stage = document.querySelector(".stage");
const panel = document.querySelector(".glass");
"""

SECTION = Section(
    "effects",
    "Glass & Material Effects",
    211,
    (
        glass(
            "Glassmorphism",
            "background: rgb(255 255 255 / .1); backdrop-filter: blur(14px) saturate(140%); border: 1px solid rgb(255 255 255 / .22); box-shadow: 0 10px 40px rgb(0 0 0 / .3);",
            "The four ingredients together: a faint white fill, a backdrop blur, a light hairline border and a soft shadow.",
        ),
        glass(
            "Frosted glass",
            "background: rgb(255 255 255 / .22); backdrop-filter: blur(30px); border: 1px solid rgb(255 255 255 / .3);",
            "A heavy blur and a milkier fill, with fine grain on top: what is behind is reduced to colour.",
            f'.glass::after {{ content: ""; position: absolute; inset: 0; border-radius: inherit; background: {GRAIN}; opacity: .25; mix-blend-mode: overlay; pointer-events: none; }}\n',
        ),
        glass(
            "Backdrop blur",
            "backdrop-filter: blur(var(--blur, 12px)); border: 1px solid rgb(255 255 255 / .25); gap: 8px; align-content: center;",
            "Blur alone, with no tint. Drag the slider to see how the radius changes what can still be read through it.",
            ".glass input { width: 150px; accent-color: #fff; }\n",
            inner='<div class="glass"><label for="blur">Blur <output id="amount">12px</output></label><input id="blur" type="range" min="0" max="40" value="12"></div>',
            js=POINTER
            + 'const slider = document.querySelector("#blur");\nslider.addEventListener("input", () => {\n  panel.style.setProperty("--blur", `${slider.value}px`);\n  document.querySelector("#amount").textContent = `${slider.value}px`;\n});\n',
        ),
        glass(
            "Backdrop saturation",
            "backdrop-filter: blur(10px) saturate(260%); background: rgb(255 255 255 / .06); border: 1px solid rgb(255 255 255 / .2);",
            "Colours behind the pane are intensified, so the glass looks vivid instead of washed out.",
        ),
        glass(
            "Backdrop brightness",
            "backdrop-filter: blur(10px) brightness(.45); border: 1px solid rgb(255 255 255 / .16);",
            "The backdrop is dimmed instead of tinted: white text stays readable over any background.",
        ),
        glass(
            "Translucent overlay",
            "background: rgb(15 23 42 / .62); border: 1px solid rgb(255 255 255 / .12);",
            "A semi-opaque fill and no blur: the cheap version, and the fallback where backdrop-filter is unavailable.",
        ),
        glass(
            "Acrylic effect",
            "background: linear-gradient(rgb(40 44 70 / .55), rgb(40 44 70 / .7)); backdrop-filter: blur(30px) saturate(160%); border: 1px solid rgb(255 255 255 / .14); box-shadow: 0 16px 40px rgb(0 0 0 / .35);",
            "Blur, a saturation boost, a tinted fill and a noise layer: the recipe for a material that feels physical instead of merely see-through.",
            f'.glass::after {{ content: ""; position: absolute; inset: 0; border-radius: inherit; background: {GRAIN}; opacity: .12; pointer-events: none; }}\n',
        ),
        glass(
            "Liquid glass",
            "backdrop-filter: blur(5px) saturate(180%); background: rgb(255 255 255 / .06); box-shadow: inset 0 0 0 1px rgb(255 255 255 / .28), inset 2px 3px 6px rgb(255 255 255 / .55), inset -3px -4px 10px rgb(255 255 255 / .2), inset 0 0 26px rgb(255 255 255 / .12), 0 14px 34px rgb(0 0 0 / .35); animation: settle 7s ease-in-out infinite alternate;",
            "Barely blurred and nearly clear, with bright inner rims that read as a thick, rounded edge; the outline slowly shifts like a droplet.",
            "@keyframes settle { from { border-radius: 44% 56% 52% 48% / 58% 46% 54% 42%; } to { border-radius: 56% 44% 46% 54% / 44% 56% 44% 56%; } }\n",
        ),
        glass(
            "Crystal effect",
            "width: 170px; height: 170px; border-radius: 0; clip-path: polygon(50% 0, 100% 34%, 82% 100%, 18% 100%, 0 34%); backdrop-filter: blur(6px) brightness(1.25); background: conic-gradient(from 0deg at 50% 42%, rgb(255 255 255 / .5), rgb(255 255 255 / .05) 20%, rgb(255 255 255 / .35) 40%, rgb(255 255 255 / .02) 60%, rgb(255 255 255 / .3) 80%, rgb(255 255 255 / .5));",
            "A faceted gem: hard conic bands of light and dark meet at a point, each band reading as a cut face.",
        ),
        glass(
            "Holographic glass",
            "background: rgb(255 255 255 / .08); backdrop-filter: blur(12px); border: 1px solid rgb(255 255 255 / .25); overflow: hidden;",
            "A rainbow foil layer blended over the pane; its position follows the pointer, so the colours slide as the 'card' is turned.",
            '.glass::before { content: ""; position: absolute; inset: 0; background: linear-gradient(115deg, transparent 20%, #ff5ea8 32%, #ffe45e 44%, #5effa0 56%, #5ec8ff 68%, #b05eff 80%, transparent 92%) var(--px, 50%) 0 / 300% 100%; mix-blend-mode: color-dodge; opacity: .55; transition: background-position .15s linear; }\n',
            js=POINTER
            + 'stage.addEventListener("pointermove", (event) => {\n  const box = stage.getBoundingClientRect();\n  panel.style.setProperty("--px", `${((event.clientX - box.left) / box.width) * 100}%`);\n});\n',
        ),
        glass(
            "Iridescent glass",
            "background: linear-gradient(135deg, rgb(124 92 255 / .35), rgb(34 211 238 / .3), rgb(244 114 182 / .35)); backdrop-filter: blur(12px); border: 1px solid rgb(255 255 255 / .3); animation: sheen 6s linear infinite;",
            "A thin-film sheen: the tint cycles through the spectrum the way a soap bubble or oil slick does.",
            "@keyframes sheen { to { filter: hue-rotate(360deg); } }\n",
        ),
        glass(
            "Glass reflection",
            "background: rgb(255 255 255 / .08); backdrop-filter: blur(12px); border: 1px solid rgb(255 255 255 / .2); overflow: hidden;",
            "A broad diagonal band of light across the upper corner, as if a window were reflected in the surface.",
            '.glass::before { content: ""; position: absolute; top: -60%; left: -30%; width: 80%; height: 220%; background: linear-gradient(90deg, transparent, rgb(255 255 255 / .22) 45%, rgb(255 255 255 / .05) 55%, transparent); rotate: 28deg; }\n',
        ),
        glass(
            "Glass highlight",
            "background: radial-gradient(circle 140px at var(--px, 30%) var(--py, 0%), rgb(255 255 255 / .35), transparent), rgb(255 255 255 / .07); backdrop-filter: blur(12px); box-shadow: inset 0 1px 0 rgb(255 255 255 / .6), inset 0 -1px 0 rgb(0 0 0 / .2);",
            "A specular hot-spot that tracks the pointer, plus a bright top edge and a dark bottom edge that give the pane thickness.",
            js=POINTER
            + 'panel.addEventListener("pointermove", (event) => {\n  const box = panel.getBoundingClientRect();\n  panel.style.setProperty("--px", `${event.clientX - box.left}px`);\n  panel.style.setProperty("--py", `${event.clientY - box.top}px`);\n});\n',
        ),
        glass(
            "Glass edge glow",
            "background: rgb(255 255 255 / .07); backdrop-filter: blur(12px); border: 1px solid rgb(165 243 252 / .8); box-shadow: 0 0 22px rgb(34 211 238 / .6), inset 0 0 18px rgb(34 211 238 / .3);",
            "The rim is lit: a bright border with glow spilling both outward and into the pane.",
        ),
        glass(
            "Glass distortion",
            "backdrop-filter: blur(8px); backdrop-filter: url(#ripple) blur(1px); border: 1px solid rgb(255 255 255 / .25);",
            "Patterned glass: the backdrop is pushed around by a noise displacement map. Chromium applies SVG filters to backdrops; other engines keep the plain blur declared first.",
            after='<svg width="0" height="0" aria-hidden="true"><filter id="ripple" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.012 0.03" numOctaves="1" seed="4"/><feDisplacementMap in="SourceGraphic" scale="18" xChannelSelector="R" yChannelSelector="G"/></filter></svg>',
        ),
        glass(
            "Glass refraction",
            "",
            "A lens: inside the circle the scene is drawn again, magnified about the pointer. Move over the scene to carry the lens around.",
            ".stage { cursor: none; }\n.lens { position: absolute; left: 0; top: 0; width: 120px; height: 120px; border-radius: 50%; overflow: hidden; translate: var(--x) var(--y); box-shadow: inset 0 0 0 1px rgb(255 255 255 / .5), inset 0 0 18px rgb(255 255 255 / .35), 0 10px 30px rgb(0 0 0 / .45); pointer-events: none; }\n.lens .world { inset: auto; left: 0; top: 0; scale: 1.5; }\n",
            inner='<div class="lens"></div>',
            js="""\
const stage = document.querySelector(".stage");
const lens = stage.querySelector(".lens");
const copy = stage.querySelector(".world").cloneNode(true);
lens.append(copy);
const RADIUS = 60;
const move = (x, y) => {
  lens.style.setProperty("--x", `${x - RADIUS}px`);
  lens.style.setProperty("--y", `${y - RADIUS}px`);
  // The copy is laid exactly over the original, then scaled about the pointer.
  Object.assign(copy.style, { width: `${stage.clientWidth}px`, height: `${stage.clientHeight}px`, translate: `${RADIUS - x}px ${RADIUS - y}px`, transformOrigin: `${x}px ${y}px` });
};
stage.addEventListener("pointermove", (event) => {
  const box = stage.getBoundingClientRect();
  move(event.clientX - box.left, event.clientY - box.top);
});
move(stage.clientWidth / 2, stage.clientHeight / 2);
""",
        ),
        glass(
            "Glass depth",
            "",
            "Three panes at different distances: nearer ones blur more, cast larger shadows and move further when the pointer moves.",
            ".pane { position: absolute; width: 150px; height: 100px; border-radius: 18px; border: 1px solid rgb(255 255 255 / .22); background: rgb(255 255 255 / .08); translate: calc(var(--mx, 0) * var(--z) * 1px) calc(var(--my, 0) * var(--z) * 1px); transition: translate .2s ease-out; }\n"
            ".pane:nth-of-type(2) { --z: 8; left: 12%; top: 16%; backdrop-filter: blur(4px); box-shadow: 0 4px 12px rgb(0 0 0 / .2); }\n"
            ".pane:nth-of-type(3) { --z: 18; left: 34%; top: 30%; backdrop-filter: blur(10px); box-shadow: 0 12px 28px rgb(0 0 0 / .3); }\n"
            ".pane:nth-of-type(4) { --z: 32; left: 54%; top: 44%; backdrop-filter: blur(18px); box-shadow: 0 24px 50px rgb(0 0 0 / .4); }\n",
            inner='<div class="pane"></div><div class="pane"></div><div class="pane"></div>',
            js='const stage = document.querySelector(".stage");\nstage.addEventListener("pointermove", (event) => {\n  const box = stage.getBoundingClientRect();\n  stage.style.setProperty("--mx", ((event.clientX - box.left) / box.width - 0.5).toFixed(3));\n  stage.style.setProperty("--my", ((event.clientY - box.top) / box.height - 0.5).toFixed(3));\n});\nstage.addEventListener("pointerleave", () => { stage.style.setProperty("--mx", 0); stage.style.setProperty("--my", 0); });\n',
        ),
        glass(
            "Layered transparency",
            "",
            "Overlapping sheets of the same tint: wherever two or three overlap, the tint accumulates and the overlap reads as a new shade.",
            ".sheet { position: absolute; width: 170px; height: 120px; border-radius: 18px; background: rgb(255 255 255 / .16); border: 1px solid rgb(255 255 255 / .2); }\n.sheet:nth-of-type(2) { left: 14%; top: 14%; }\n.sheet:nth-of-type(3) { left: 31%; top: 27%; }\n.sheet:nth-of-type(4) { left: 48%; top: 40%; }\n",
            inner='<div class="sheet"></div><div class="sheet"></div><div class="sheet"></div>',
        ),
        glass(
            "Gradient transparency",
            "width: 100%; height: 100%; border-radius: 0; align-items: end; padding-bottom: 26px; background: linear-gradient(transparent 20%, rgb(11 16 32 / .9)); backdrop-filter: blur(16px); mask: linear-gradient(transparent 15%, #000 60%);",
            "The pane itself fades out: a mask takes both the tint and the blur from full strength to nothing, so there is no visible top edge.",
            label="Blur and tint fade upward",
        ),
        glass(
            "Dynamic transparency",
            "",
            "A header that starts clear and turns to glass as content scrolls beneath it: opacity and blur both follow the scroll offset.",
            ".scroller { position: absolute; inset: 0; overflow-y: auto; }\n"
            ".bar { position: sticky; top: 0; z-index: 1; padding: 14px 18px; color: #fff; font-weight: 600; background: rgb(11 16 32 / calc(var(--a, 0) * .65)); backdrop-filter: blur(calc(var(--a, 0) * 16px)); border-bottom: 1px solid rgb(255 255 255 / calc(var(--a, 0) * .18)); }\n"
            ".scroller p { margin: 14px 18px; padding: 22px; border-radius: 14px; color: #0b1020; font-weight: 600; }\n"
            ".scroller p:nth-child(even) { background: #f472b6; }\n.scroller p:nth-child(odd) { background: #22d3ee; }\n.scroller p:nth-child(3n) { background: #fbbf24; }\n",
            inner='<div class="scroller" tabindex="0"><div class="bar">Scroll the content</div><p>One</p><p>Two</p><p>Three</p><p>Four</p><p>Five</p><p>Six</p></div>',
            js='const scroller = document.querySelector(".scroller");\nconst bar = scroller.querySelector(".bar");\nconst update = () => bar.style.setProperty("--a", Math.min(1, scroller.scrollTop / 90).toFixed(3));\nscroller.addEventListener("scroll", update, { passive: true });\nupdate();\n',
        ),
    ),
)
