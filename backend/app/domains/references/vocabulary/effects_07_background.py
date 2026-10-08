"""Effects 181-210: backgrounds."""

from urllib.parse import quote

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import STAGE

BG = ".bg { position: relative; width: 100%; height: 100%; overflow: hidden; border: 1px solid var(--border); border-radius: 18px; background: #0b0b14; }\n"
CALM = 'const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\n'


def svg_url(svg: str) -> str:
    """An inline SVG as a CSS ``url()``: no request, and it tiles like any image."""
    return f'url("data:image/svg+xml,{quote(svg, safe=" =:/;,.()-")}")'


def noise(frequency: str, octaves: int = 3, size: int = 200, matrix: str = "") -> str:
    """Fractal noise as a tile. ``matrix`` recolours it (feColorMatrix values)."""
    recolour = f"<feColorMatrix values='{matrix}'/>" if matrix else ""
    return svg_url(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}'><filter id='n'>"
        f"<feTurbulence type='fractalNoise' baseFrequency='{frequency}' numOctaves='{octaves}' stitchTiles='stitch'/>{recolour}</filter>"
        "<rect width='100%' height='100%' filter='url(#n)'/></svg>"
    )


# Grey speckle, and soft white cloud whose opacity follows the noise.
GRAIN = noise(".8", matrix="0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  .9 0 0 0 0")
CLOUD = noise(".006 .011", 3, 600, "0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  1.5 0 0 0 -.62")


def bg(name: str, css: str, note: str, inner: str = "", js: str = "") -> Item:
    return Item(
        name, f'<div class="stage"><div class="bg">{inner}</div></div>', STAGE + BG + css, js, note
    )


SECTION = Section(
    "effects",
    "Background Effects",
    181,
    (
        bg(
            "Gradient background",
            ".bg { background: linear-gradient(135deg, #7c5cff, #22d3ee); }\n",
            "Two colours along a diagonal: the simplest atmosphere there is.",
        ),
        bg(
            "Animated gradient",
            """\
.bg { background: linear-gradient(120deg, #7c5cff, #22d3ee, #f472b6, #7c5cff) 0 50% / 300% 300%; animation: drift 10s ease-in-out infinite alternate; }
@keyframes drift { to { background-position: 100% 50%; } }
""",
            "An oversized gradient slid back and forth, so the colours appear to change.",
        ),
        bg(
            "Moving gradient",
            """\
@property --angle { syntax: "<angle>"; inherits: false; initial-value: 0deg; }
.bg { background: linear-gradient(var(--angle), #7c5cff, #0b0b14 45%, #22d3ee); animation: turn 8s linear infinite; }
@keyframes turn { to { --angle: 360deg; } }
""",
            "The gradient's angle itself is animated (a registered custom property), so the light circles the surface.",
        ),
        bg(
            "Radial gradient",
            ".bg { background: radial-gradient(circle at 30% 25%, #7c5cff, transparent 60%), #0b0b14; }\n",
            "Colour radiating from one off-centre point and falling away to the base.",
        ),
        bg(
            "Conic gradient",
            ".bg { background: conic-gradient(from 210deg at 50% 60%, #7c5cff, #22d3ee, #f472b6, #fbbf24, #7c5cff); }\n",
            "Colours swept around a centre point like a colour wheel.",
        ),
        bg(
            "Mesh gradient",
            """\
.bg { background:
  radial-gradient(at 12% 18%, #7c5cff 0, transparent 50%), radial-gradient(at 85% 12%, #22d3ee 0, transparent 45%),
  radial-gradient(at 70% 85%, #f472b6 0, transparent 50%), radial-gradient(at 15% 90%, #fbbf24 0, transparent 40%), #1e1b4b; }
""",
            "Several radial gradients anchored at different points blend into a soft multi-colour mesh.",
        ),
        bg(
            "Aurora gradient",
            """\
.bg i { position: absolute; left: -20%; width: 140%; height: 60%; border-radius: 50%; filter: blur(36px); mix-blend-mode: screen; animation: sway 9s ease-in-out infinite alternate; }
.bg i:nth-child(1) { top: -25%; background: #34d399; }
.bg i:nth-child(2) { top: 5%; background: #22d3ee; animation-duration: 12s; animation-direction: alternate-reverse; opacity: .7; }
.bg i:nth-child(3) { top: 30%; background: #7c5cff; animation-duration: 15s; opacity: .6; }
@keyframes sway { from { transform: translateX(-8%) rotate(-6deg) scaleY(.8); } to { transform: translateX(8%) rotate(5deg) scaleY(1.2); } }
""",
            "Wide blurred bands of green, cyan and violet swaying slowly across a dark sky.",
            "<i></i><i></i><i></i>",
        ),
        bg(
            "Liquid gradient",
            """\
.bg { background: #1e1b4b; }
.pool { position: absolute; inset: 0; filter: blur(22px) contrast(1.6); }
.pool i { position: absolute; width: 46%; aspect-ratio: 1; border-radius: 50%; animation: roam 11s ease-in-out infinite alternate; }
.pool i:nth-child(1) { left: 0; top: 0; background: #7c5cff; }
.pool i:nth-child(2) { right: 0; top: 10%; background: #22d3ee; animation-duration: 14s; animation-direction: alternate-reverse; }
.pool i:nth-child(3) { left: 28%; bottom: -20%; background: #f472b6; animation-duration: 17s; }
@keyframes roam { 0% { transform: translate(0, 0) scale(1); } 50% { transform: translate(40%, 30%) scale(1.3); } 100% { transform: translate(-10%, 55%) scale(.9); } }
""",
            "Blurred blobs wander and merge; raising the contrast after the blur gives their edges a liquid look.",
            '<div class="pool"><i></i><i></i><i></i></div>',
        ),
        bg(
            "Noise texture",
            f".bg {{ background: {noise('.65')}, #1c1c2b; background-blend-mode: soft-light; }}\n",
            "Fractal noise generated by an inline SVG filter and tiled: takes the flatness out of a plain colour.",
        ),
        bg(
            "Grain texture",
            f"""\
.bg {{ background: linear-gradient(135deg, #7c5cff, #f472b6); }}
.bg::after {{ content: ""; position: absolute; inset: 0; background: {GRAIN}; mix-blend-mode: overlay; opacity: .55; }}
""",
            "Fine speckle laid over a gradient with an overlay blend, which also hides colour banding.",
        ),
        bg(
            "Film grain",
            f"""\
.bg {{ background: radial-gradient(circle at 50% 40%, #3b3566, #0b0b14); }}
.bg::after {{ content: ""; position: absolute; inset: -50%; background: {GRAIN}; opacity: .28; animation: jitter .6s steps(1) infinite; }}
@keyframes jitter {{ 0% {{ translate: 0 0; }} 20% {{ translate: -6% 4%; }} 40% {{ translate: 5% -7%; }} 60% {{ translate: -3% -5%; }} 80% {{ translate: 7% 6%; }} }}
""",
            "The grain layer is larger than the frame and jumps to a new offset several times a second, like film stock.",
        ),
        bg(
            "Dot pattern",
            ".bg { background: radial-gradient(circle, rgb(255 255 255 / .22) 1.2px, transparent 1.6px) 0 0 / 18px 18px, #0b0b14; }\n",
            "One small radial gradient repeated on a fixed pitch.",
        ),
        bg(
            "Grid pattern",
            """\
.bg { background: linear-gradient(rgb(255 255 255 / .16) 1px, transparent 1px) 0 0 / 28px 28px, linear-gradient(90deg, rgb(255 255 255 / .16) 1px, transparent 1px) 0 0 / 28px 28px, #0b0b14; }
/* The grid fades toward the edges instead of stopping abruptly. */
.bg::after { content: ""; position: absolute; inset: 0; background: radial-gradient(ellipse at center, transparent 40%, #0b0b14 100%); }
""",
            "Hairlines in both directions, faded out toward the edges with a radial overlay.",
        ),
        bg(
            "Animated grid",
            """\
.bg { --cell: 30px; background: linear-gradient(rgb(255 255 255 / .07) 1px, transparent 1px) 0 0 / var(--cell) var(--cell), linear-gradient(90deg, rgb(255 255 255 / .07) 1px, transparent 1px) 0 0 / var(--cell) var(--cell), #0b0b14; }
.bg i { position: absolute; width: var(--cell); height: var(--cell); background: var(--primary); animation: lit 1.6s ease-out forwards; }
@keyframes lit { from { opacity: .7; } to { opacity: 0; } }
""",
            "Cells of the grid light up at random and fade, so the surface looks alive without drawing attention.",
            "",
            CALM
            + """\
const surface = document.querySelector(".bg");
const CELL = 30;
const light = () => {
  const cell = document.createElement("i");
  cell.style.left = `${Math.floor(Math.random() * (surface.clientWidth / CELL)) * CELL}px`;
  cell.style.top = `${Math.floor(Math.random() * (surface.clientHeight / CELL)) * CELL}px`;
  cell.addEventListener("animationend", () => cell.remove());
  surface.append(cell);
};
if (!calm) setInterval(light, 220);
""",
        ),
        bg(
            "Moving grid",
            """\
.bg { perspective: 220px; background: linear-gradient(#0b0b14 35%, #2a1458); }
.floor { position: absolute; left: -50%; right: -50%; bottom: -30%; height: 90%; transform: rotateX(62deg); transform-origin: 50% 0;
  background: linear-gradient(rgb(34 211 238 / .55) 1px, transparent 1px) 0 0 / 34px 34px, linear-gradient(90deg, rgb(34 211 238 / .55) 1px, transparent 1px) 0 0 / 34px 34px;
  mask: linear-gradient(transparent, #000 45%); animation: advance 1.2s linear infinite; }
@keyframes advance { to { background-position: 0 34px, 0 34px; } }
""",
            "A grid laid flat in perspective and scrolled by exactly one cell per loop: an endless floor rushing toward the viewer.",
            '<div class="floor"></div>',
        ),
        bg(
            "Glow field",
            """\
.bg i { position: absolute; width: 150px; aspect-ratio: 1; border-radius: 50%; filter: blur(34px); opacity: .75; animation: wander 12s ease-in-out infinite alternate; }
.bg i:nth-child(1) { left: 4%; top: 8%; background: #7c5cff; }
.bg i:nth-child(2) { right: 6%; top: 20%; background: #22d3ee; animation-delay: -4s; }
.bg i:nth-child(3) { left: 30%; bottom: -10%; background: #f472b6; animation-delay: -8s; }
.bg i:nth-child(4) { right: 28%; top: -20%; background: #34d399; animation-delay: -2s; width: 110px; }
@keyframes wander { to { translate: 40px -30px; scale: 1.25; } }
""",
            "Several coloured lights scattered over a dark surface, each drifting on its own schedule.",
            "<i></i><i></i><i></i><i></i>",
        ),
        bg(
            "Ambient glow",
            """\
.bg { display: grid; place-items: center; }
.bg::before { content: ""; position: absolute; width: 62%; height: 62%; border-radius: 50%; background: linear-gradient(90deg, #7c5cff, #22d3ee); filter: blur(46px); animation: breathe 5s ease-in-out infinite alternate; }
@keyframes breathe { from { opacity: .35; scale: .9; } to { opacity: .75; scale: 1.1; } }
.panel { position: relative; padding: 18px 26px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); font-weight: 600; }
""",
            "A large blurred light sits behind the content and slowly breathes, lifting it off the page.",
            '<div class="panel">Content in the light</div>',
        ),
        bg(
            "Radial glow",
            ".bg { background: radial-gradient(ellipse 70% 60% at 50% 0%, rgb(124 92 255 / .55), transparent 70%), #0b0b14; }\n",
            "An ellipse of light spilling down from the top edge: the classic hero-section spotlight.",
        ),
        bg(
            "Edge glow",
            ".bg { box-shadow: inset 0 0 40px rgb(124 92 255 / .55), inset 0 0 4px rgb(34 211 238 / .8); }\n",
            "Inset shadows light the surface from all four edges inward.",
        ),
        bg(
            "Corner glow",
            ".bg { background: radial-gradient(circle at 0 0, rgb(124 92 255 / .65), transparent 45%), radial-gradient(circle at 100% 100%, rgb(34 211 238 / .5), transparent 45%), #0b0b14; }\n",
            "Light enters from two opposite corners and leaves the middle dark for content.",
        ),
        bg(
            "Atmospheric blur",
            """\
.bg i { position: absolute; border-radius: 28%; animation: float 9s ease-in-out infinite alternate; }
.bg i:nth-child(1) { left: 8%; top: 14%; width: 120px; height: 120px; background: #f472b6; rotate: 18deg; }
.bg i:nth-child(2) { right: 10%; top: 30%; width: 150px; height: 90px; background: #22d3ee; animation-delay: -3s; }
.bg i:nth-child(3) { left: 36%; bottom: 6%; width: 100px; height: 100px; background: #fbbf24; border-radius: 50%; animation-delay: -6s; }
@keyframes float { to { translate: 26px -18px; } }
/* Everything behind this layer is seen through the blur. */
.bg::after { content: ""; position: absolute; inset: 0; backdrop-filter: blur(30px) saturate(1.3); background: rgb(11 11 20 / .25); }
""",
            "Hard-edged shapes move behind a full-surface backdrop blur, leaving only soft drifting colour.",
            "<i></i><i></i><i></i>",
        ),
        bg(
            "Fog effect",
            f"""\
.bg {{ background: linear-gradient(#1b2a3a, #0b1118); }}
.bg::before, .bg::after {{ content: ""; position: absolute; inset: 0; background: {CLOUD} 0 0 / 600px 100%; filter: blur(6px); opacity: .7; animation: roll 40s linear infinite; }}
.bg::after {{ opacity: .4; animation-duration: 65s; animation-direction: reverse; scale: 1 -1; }}
@keyframes roll {{ to {{ background-position: 600px 0; }} }}
""",
            "Two layers of low-frequency noise slide past each other at different speeds; because the tile repeats, the loop has no seam.",
        ),
        bg(
            "Haze effect",
            """\
.bg { background: linear-gradient(#f8b98a, #f3d9c2 55%, #e9e2dc); }
.bg i { position: absolute; left: -5%; right: -5%; bottom: 0; background: #33405a; clip-path: polygon(0 100%, 0 55%, 12% 30%, 24% 52%, 38% 12%, 52% 48%, 66% 22%, 80% 50%, 92% 28%, 100% 46%, 100% 100%); }
/* Each ridge further away is paler and lower in contrast: that is all haze is. */
.bg i:nth-child(1) { height: 78%; opacity: .22; }
.bg i:nth-child(2) { height: 58%; opacity: .45; scale: -1 1; }
.bg i:nth-child(3) { height: 38%; opacity: .9; }
""",
            "Distance shown by losing contrast: each farther ridge is lighter and closer to the sky colour.",
            "<i></i><i></i><i></i>",
        ),
        bg(
            "Vignette",
            """\
.bg { background: radial-gradient(circle at 30% 30%, #f472b6, transparent 45%), radial-gradient(circle at 75% 65%, #22d3ee, transparent 50%), linear-gradient(135deg, #312e81, #7c5cff); }
.bg::after { content: ""; position: absolute; inset: 0; background: radial-gradient(ellipse at center, transparent 45%, rgb(0 0 0 / .78) 100%); }
""",
            "Darkened corners pull the eye to the centre, as a camera lens does.",
        ),
        bg(
            "Light leak",
            """\
.bg { background: linear-gradient(160deg, #1f2937, #0b0b14); }
.bg::before { content: ""; position: absolute; top: -30%; right: -25%; width: 75%; height: 160%; background: linear-gradient(100deg, transparent, #f97316 40%, #fde047 60%, #ef4444 80%, transparent); filter: blur(34px); mix-blend-mode: screen; rotate: 14deg; animation: leak 7s ease-in-out infinite alternate; }
@keyframes leak { from { opacity: .45; translate: 6% 0; } to { opacity: .85; translate: -8% 0; } }
""",
            "A warm streak of orange and red bleeding in from one side, as if light had got into the camera.",
        ),
        bg(
            "Lens flare",
            """\
.bg { background: linear-gradient(160deg, #0f172a, #020617); cursor: crosshair; }
.sun, .ghost { position: absolute; left: 0; top: 0; border-radius: 50%; translate: calc(var(--x) - 50%) calc(var(--y) - 50%); mix-blend-mode: screen; pointer-events: none; }
.sun { width: 190px; height: 190px; background: radial-gradient(circle, #fff 0 6%, rgb(255 236 179 / .85) 12%, rgb(251 146 60 / .35) 34%, transparent 68%); }
.sun::after { content: ""; position: absolute; left: -90%; right: -90%; top: 49%; height: 2%; background: linear-gradient(90deg, transparent, rgb(186 230 253 / .9), transparent); }
.ghost { width: var(--size); height: var(--size); background: radial-gradient(circle, transparent 40%, var(--tint) 70%, transparent 72%); }
""",
            "A light source with an anamorphic streak, and ghosts strung along the line through the centre of the frame. Move the pointer to move the light.",
            '<div class="sun"></div>'
            '<div class="ghost" data-k="0.45" style="--size: 36px; --tint: rgb(34 211 238 / .5)"></div>'
            '<div class="ghost" data-k="1.25" style="--size: 70px; --tint: rgb(124 92 255 / .4)"></div>'
            '<div class="ghost" data-k="1.7" style="--size: 26px; --tint: rgb(244 114 182 / .6)"></div>'
            '<div class="ghost" data-k="2.1" style="--size: 110px; --tint: rgb(52 211 153 / .25)"></div>',
            """\
const surface = document.querySelector(".bg");
const sun = surface.querySelector(".sun");
const ghosts = [...surface.querySelectorAll(".ghost")];
const place = (element, x, y) => { element.style.setProperty("--x", `${x}px`); element.style.setProperty("--y", `${y}px`); };
const aim = (x, y) => {
  const cx = surface.clientWidth / 2, cy = surface.clientHeight / 2;
  place(sun, x, y);
  // Each ghost sits on the line from the light through the centre, k times as far along.
  ghosts.forEach((ghost) => place(ghost, x + (cx - x) * Number(ghost.dataset.k), y + (cy - y) * Number(ghost.dataset.k)));
};
surface.addEventListener("pointermove", (event) => {
  const box = surface.getBoundingClientRect();
  aim(event.clientX - box.left, event.clientY - box.top);
});
aim(surface.clientWidth * 0.24, surface.clientHeight * 0.3);
""",
        ),
        bg(
            "Soft bloom",
            """\
.bg { display: grid; place-items: center; }
.lit { position: relative; font-size: 44px; font-weight: 800; color: #fff; }
/* The bloom is a blurred, brightened copy of the same thing drawn underneath. */
.lit::before { content: attr(data-text); position: absolute; inset: 0; color: #fff; filter: blur(14px) brightness(1.6); opacity: .9; }
""",
            "Bright things spill light: a blurred copy underneath makes the edges glow softly.",
            '<span class="lit" data-text="Bloom">Bloom</span>',
        ),
        bg(
            "Color bloom",
            """\
.bg { display: grid; place-items: center; }
.swatches { position: relative; display: flex; gap: 22px; isolation: isolate; }
.swatches i { position: relative; width: 72px; height: 72px; border-radius: 18px; background: var(--c); }
.swatches i::before { content: ""; position: absolute; inset: -6px; border-radius: inherit; background: var(--c); filter: blur(26px) saturate(1.8); opacity: .85; z-index: -1; animation: swell 3.5s ease-in-out infinite alternate; animation-delay: var(--d); }
@keyframes swell { from { scale: .8; opacity: .5; } to { scale: 1.35; opacity: .95; } }
""",
            "Each shape throws a saturated halo of its own colour, and neighbouring halos mix where they meet.",
            '<div class="swatches"><i style="--c: #7c5cff; --d: 0s"></i><i style="--c: #22d3ee; --d: -1.2s"></i><i style="--c: #f472b6; --d: -2.4s"></i></div>',
        ),
        bg(
            "Animated particles",
            ".bg canvas { display: block; width: 100%; height: 100%; }\n",
            "Points drift on a canvas and bounce off the edges; any two that come close are joined by a line that fades with distance.",
            '<canvas aria-hidden="true"></canvas>',
            CALM
            + """\
const canvas = document.querySelector("canvas");
const context = canvas.getContext("2d");
const ratio = Math.min(window.devicePixelRatio || 1, 2);
const width = canvas.clientWidth, height = canvas.clientHeight;
canvas.width = width * ratio; canvas.height = height * ratio;
context.scale(ratio, ratio);
const LINK = 78;
const points = Array.from({ length: 42 }, () => ({ x: Math.random() * width, y: Math.random() * height, vx: (Math.random() - 0.5) * 0.6, vy: (Math.random() - 0.5) * 0.6 }));
const draw = () => {
  context.clearRect(0, 0, width, height);
  points.forEach((point, i) => {
    point.x += point.vx; point.y += point.vy;
    if (point.x < 0 || point.x > width) point.vx *= -1;
    if (point.y < 0 || point.y > height) point.vy *= -1;
    for (const other of points.slice(i + 1)) {
      const distance = Math.hypot(point.x - other.x, point.y - other.y);
      if (distance > LINK) continue;
      context.strokeStyle = `rgb(124 92 255 / ${1 - distance / LINK})`;
      context.beginPath(); context.moveTo(point.x, point.y); context.lineTo(other.x, other.y); context.stroke();
    }
    context.fillStyle = "#22d3ee";
    context.beginPath(); context.arc(point.x, point.y, 1.8, 0, Math.PI * 2); context.fill();
  });
  if (!calm) requestAnimationFrame(draw);
};
draw();
""",
        ),
        bg(
            "Floating particles",
            """\
.bg { background: linear-gradient(#0b0b14, #1e1b4b); }
.bg i { position: absolute; bottom: -12px; left: var(--left); width: var(--size); height: var(--size); border-radius: 50%; background: var(--tint); box-shadow: 0 0 8px var(--tint); opacity: 0; animation: rise var(--time) linear var(--delay) infinite; }
@keyframes rise { 10% { opacity: .9; } 90% { opacity: .5; } 100% { translate: var(--sway) -300px; opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .bg i { animation: none; opacity: .7; bottom: var(--rest); } }
""",
            "Motes rise at different sizes and speeds and drift sideways as they go. Each one's values are set once; CSS does the rest.",
            "",
            """\
const surface = document.querySelector(".bg");
const TINTS = ["#22d3ee", "#7c5cff", "#f472b6", "#ffffff"];
for (let i = 0; i < 28; i += 1) {
  const mote = document.createElement("i");
  const set = (name, value) => mote.style.setProperty(name, value);
  set("--left", `${Math.random() * 100}%`);
  set("--size", `${2 + Math.random() * 5}px`);
  set("--time", `${6 + Math.random() * 8}s`);
  set("--delay", `${-Math.random() * 14}s`);  // negative: the field is already full at load
  set("--sway", `${(Math.random() - 0.5) * 80}px`);
  set("--rest", `${Math.random() * 90}%`);
  set("--tint", TINTS[i % TINTS.length]);
  surface.append(mote);
}
""",
        ),
    ),
)
