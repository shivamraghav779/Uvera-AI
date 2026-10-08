"""Effects 481-500: premium and experimental."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.effects_14_image import PHOTO
from app.domains.references.vocabulary.fx import STAGE, pointer_js

CALM = 'const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\n'
# A canvas sized for the display's pixel density, drawn in CSS pixels.
CANVAS_HTML = '<canvas aria-hidden="true"></canvas>'
CANVAS_CSS = "canvas { display: block; width: 100%; height: 100%; border-radius: 18px; background: #07070d; cursor: pointer; }\n"
CANVAS_JS = (
    CALM
    + """\
const canvas = document.querySelector("canvas");
const context = canvas.getContext("2d");
const ratio = Math.min(window.devicePixelRatio || 1, 2);
const W = canvas.clientWidth, H = canvas.clientHeight;
canvas.width = W * ratio; canvas.height = H * ratio;
context.scale(ratio, ratio);
const at = (event) => { const box = canvas.getBoundingClientRect(); return [event.clientX - box.left, event.clientY - box.top]; };
"""
)
BIG = ".word { margin: 0; font-size: 64px; font-weight: 900; letter-spacing: -.03em; }\n"


def lab(name: str, inner: str, css: str, note: str, js: str = "") -> Item:
    return Item(name, f'<div class="stage">{inner}</div>', STAGE + css, js, note)


def filters(body: str) -> str:
    return f'<svg width="0" height="0" aria-hidden="true">{body}</svg>'


SECTION = Section(
    "effects",
    "Premium / Experimental Effects",
    481,
    (
        lab(
            "Liquid morphing",
            '<svg class="liquid" viewBox="0 0 200 200" aria-hidden="true"><defs><linearGradient id="ink" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c5cff"/><stop offset="1" stop-color="#22d3ee"/></linearGradient></defs>'
            '<path fill="url(#ink)"><animate attributeName="d" dur="9s" repeatCount="indefinite" calcMode="spline" keyTimes="0;.33;.66;1" keySplines=".4 0 .6 1;.4 0 .6 1;.4 0 .6 1" values="'
            "M100 22 C146 22 178 54 178 100 C178 146 146 178 100 178 C54 178 22 146 22 100 C22 54 54 22 100 22 Z;"
            "M112 16 C164 30 186 70 166 112 C150 150 128 190 86 176 C40 162 10 126 30 84 C46 50 70 6 112 16 Z;"
            "M90 30 C130 8 190 50 176 96 C164 138 160 172 108 184 C62 194 28 150 20 106 C12 66 52 50 90 30 Z;"
            'M100 22 C146 22 178 54 178 100 C178 146 146 178 100 178 C54 178 22 146 22 100 C22 54 54 22 100 22 Z"/></path></svg>',
            ".liquid { width: 210px; filter: drop-shadow(0 0 30px rgb(124 92 255 / .5)); }\n",
            "A path morphs between hand-drawn outlines. Every keyframe has the same number and kind of segments, which is what lets the shapes interpolate smoothly.",
        ),
        lab(
            "Blob morphing",
            '<div class="blob"></div>',
            ".blob { width: 180px; height: 180px; background: linear-gradient(135deg, #f472b6, #7c5cff 60%, #22d3ee); animation: wobble 10s ease-in-out infinite, drift 24s linear infinite; }\n@keyframes wobble { 0%, 100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; } 33% { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; } 66% { border-radius: 50% 50% 34% 66% / 36% 64% 52% 48%; } }\n@keyframes drift { to { rotate: 360deg; } }\n",
            "No SVG: the eight values of border-radius are animated, and a slow rotation hides the fact that there are only three shapes.",
        ),
        lab(
            "Gooey effect",
            '<div class="goo"><i></i><i></i><i></i><i></i></div>'
            + filters(
                '<filter id="goo"><feGaussianBlur in="SourceGraphic" stdDeviation="10"/><feColorMatrix values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9"/></filter>'
            ),
            "/* Blur makes neighbouring shapes overlap softly; the matrix then sharpens alpha back to a hard edge, so they appear to fuse. */\n.goo { position: relative; width: 300px; height: 200px; filter: url(#goo); }\n.goo i { position: absolute; left: 50%; top: 50%; width: 56px; height: 56px; margin: -28px; border-radius: 50%; background: var(--accent); animation: roam var(--t) ease-in-out infinite alternate; }\n.goo i:nth-child(1) { width: 90px; height: 90px; margin: -45px; background: var(--primary); animation: none; }\n.goo i:nth-child(2) { --t: 2.6s; --x: 110px; --y: -40px; }\n.goo i:nth-child(3) { --t: 3.4s; --x: -100px; --y: 50px; }\n.goo i:nth-child(4) { --t: 4.2s; --x: 40px; --y: 70px; background: #f472b6; }\n@keyframes roam { from { translate: calc(var(--x) * -1) calc(var(--y) * -1); } to { translate: var(--x) var(--y); } }\n",
            "Separate circles pass through one another and stretch into bridges as they part, like drops of liquid.",
        ),
        lab(
            "SVG turbulence",
            '<svg class="smoke" viewBox="0 0 400 220" preserveAspectRatio="none" aria-hidden="true"><filter id="marble" x="0" y="0" width="100%" height="100%"><feTurbulence type="turbulence" baseFrequency="0.008 0.014" numOctaves="3" seed="8"><animate attributeName="baseFrequency" dur="18s" values="0.008 0.014;0.014 0.008;0.008 0.014" repeatCount="indefinite"/></feTurbulence>'
            '<feColorMatrix values="2.4 0 0 0 -.5  0 1.2 1.4 0 -.4  1.6 0 2 0 -.2  0 0 0 0 1"/></filter><rect width="400" height="220" filter="url(#marble)"/></svg>',
            ".smoke { width: 100%; height: 100%; border-radius: 18px; }\n",
            "Procedural texture with no image: Perlin turbulence is generated by a filter, recoloured by a matrix, and its frequency drifts so the pattern flows.",
        ),
        lab(
            "Displacement distortion",
            '<h2 class="word bent">WARPED</h2>'
            + filters(
                '<filter id="bend" x="-20%" y="-40%" width="140%" height="180%"><feTurbulence type="fractalNoise" baseFrequency="0.018 0.05" numOctaves="2" seed="3"/><feDisplacementMap in="SourceGraphic" scale="0" xChannelSelector="R" yChannelSelector="G"/></filter>'
            ),
            BIG + ".bent { filter: url(#bend); }\n.stage { cursor: ew-resize; }\n",
            "Each pixel is moved by an amount read from a noise map. The pointer's horizontal position sets how far: clean at the left edge, torn at the right.",
            'const stage = document.querySelector(".stage");\nconst map = document.querySelector("#bend feDisplacementMap");\nconst set = (share) => map.setAttribute("scale", (share * 70).toFixed(1));\nstage.addEventListener("pointermove", (event) => {\n  const box = stage.getBoundingClientRect();\n  set((event.clientX - box.left) / box.width);\n});\nset(0.35);\n',
        ),
        lab(
            "Chromatic aberration",
            '<h2 class="word fringe">LENS</h2>',
            BIG
            + ".fringe { --px: .5; --py: .5; --dx: calc((var(--px) - .5) * 16px); --dy: calc((var(--py) - .5) * 16px); color: #fff; text-shadow: var(--dx) var(--dy) 0 rgb(255 0 80 / .8), calc(var(--dx) * -1) calc(var(--dy) * -1) 0 rgb(0 200 255 / .8); mix-blend-mode: screen; transition: text-shadow .1s linear; }\n",
            "A cheap lens bends colours by different amounts: red and cyan copies separate in opposite directions, more the further the pointer is from the centre.",
            pointer_js(".stage", ".fringe", ".stage") + 'target.style.setProperty("--px", 0.8);\n',
        ),
        lab(
            "RGB split",
            '<div class="tv" tabindex="0"><i class="r"></i><i class="g"></i><i class="b"></i></div>'
            + filters(
                '<filter id="only-r"><feColorMatrix values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"/></filter><filter id="only-g"><feColorMatrix values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0"/></filter><filter id="only-b"><feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0"/></filter>'
            ),
            f".tv {{ position: relative; width: 300px; height: 200px; overflow: hidden; border-radius: 18px; background: #000; isolation: isolate; outline: none; cursor: pointer; }}\n.tv i {{ position: absolute; inset: 0; background: {PHOTO} center / cover; mix-blend-mode: screen; transition: translate .35s var(--ease); }}\n"
            "/* The picture is three pictures, one per channel; screen-blending them back together restores it exactly. */\n.r { filter: url(#only-r); }\n.g { filter: url(#only-g); }\n.b { filter: url(#only-b); }\n"
            ".tv:hover .r, .tv:focus-visible .r { translate: -10px 3px; }\n.tv:hover .b, .tv:focus-visible .b { translate: 10px -3px; }\n",
            "The image's red, green and blue channels are separate layers. At rest they coincide; on hover red and blue slide apart.",
        ),
        lab(
            "Digital glitch",
            '<h2 class="word gl" data-text="SYSTEM">SYSTEM</h2>',
            BIG
            + ".gl { position: relative; }\n.gl::before, .gl::after { content: attr(data-text); position: absolute; inset: 0; clip-path: inset(var(--top) 0 var(--bottom) 0); translate: var(--shift) 0; opacity: var(--on, 0); }\n.gl::before { color: #22d3ee; }\n.gl::after { color: #f43f5e; --shift: calc(var(--shift-b)); clip-path: inset(var(--top-b) 0 var(--bottom-b) 0); }\n.gl.jolt { translate: var(--jolt) 0; }\n",
            "Unlike a looping glitch, this one is irregular: at random moments a script picks new slices and offsets for a few frames, then lets the text rest.",
            CALM
            + """\
const word = document.querySelector(".gl");
const set = (name, value) => word.style.setProperty(name, value);
const slice = (suffix) => { const top = Math.random() * 80; set(`--top${suffix}`, `${top}%`); set(`--bottom${suffix}`, `${Math.max(0, 100 - top - 8 - Math.random() * 24)}%`); };
const burst = (frames) => {
  if (frames === 0) { set("--on", 0); word.classList.remove("jolt"); setTimeout(() => burst(3 + Math.floor(Math.random() * 6)), 500 + Math.random() * 2200); return; }
  slice(""); slice("-b");
  set("--shift", `${(Math.random() - 0.5) * 30}px`); set("--shift-b", `${(Math.random() - 0.5) * 30}px`);
  set("--jolt", `${(Math.random() - 0.5) * 6}px`); set("--on", 1);
  word.classList.add("jolt");
  setTimeout(() => burst(frames - 1), 60);
};
if (!calm) burst(6);
""",
        ),
        lab(
            "Scanline effect",
            '<div class="crt"><b>READY.</b></div>',
            ".crt { position: relative; display: grid; place-items: center; width: 320px; height: 200px; overflow: hidden; border-radius: 22px; background: radial-gradient(ellipse at center, #0c2a1c, #020805); box-shadow: inset 0 0 60px #000; animation: hum .12s steps(2) infinite; }\n.crt b { font: 700 34px var(--mono); color: #6ee7b7; text-shadow: 0 0 8px #34d399, 0 0 24px #34d399; }\n"
            '/* Fixed fine lines, plus one soft band that rolls down the screen. */\n.crt::before { content: ""; position: absolute; inset: 0; background: repeating-linear-gradient(rgb(0 0 0 / .35) 0 1px, transparent 1px 3px); pointer-events: none; }\n.crt::after { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 40%; background: linear-gradient(transparent, rgb(110 231 183 / .1), transparent); animation: roll 5s linear infinite; }\n@keyframes roll { from { translate: 0 -100%; } to { translate: 0 250%; } }\n@keyframes hum { 50% { opacity: .96; } }\n@media (prefers-reduced-motion: reduce) { .crt { animation: none; } }\n',
            "An old tube display: fine horizontal lines over everything, a brighter band rolling down, phosphor glow on the text and a faint flicker.",
        ),
        lab(
            "Holographic shimmer",
            '<div class="holo" tabindex="0"><b>MEMBER</b><span>0427 · AURORA</span></div>',
            ".holo { --px: .5; --py: .5; position: relative; display: grid; align-content: end; gap: 4px; width: 280px; height: 170px; padding: 18px; overflow: hidden; border-radius: 18px; background: #14142b; color: #fff; outline: none; transform: perspective(700px) rotateX(calc((.5 - var(--py)) * 16deg)) rotateY(calc((var(--px) - .5) * 16deg)); transition: transform .15s ease-out; }\n.holo b { position: relative; font-size: 22px; letter-spacing: .12em; }\n.holo span { position: relative; font: 12px var(--mono); opacity: .8; }\n"
            '/* Two foil layers: a rainbow that slides with the pointer, and a glare that follows it. */\n.holo::before { content: ""; position: absolute; inset: 0; background: repeating-linear-gradient(115deg, #ff5ea8, #ffe45e, #5effa0, #5ec8ff, #b05eff, #ff5ea8 33%) calc(var(--px) * 100%) calc(var(--py) * 100%) / 300% 300%; mix-blend-mode: color-dodge; opacity: .5; }\n.holo::after { content: ""; position: absolute; inset: 0; background: radial-gradient(circle at calc(var(--px) * 100%) calc(var(--py) * 100%), rgb(255 255 255 / .5), transparent 45%); mix-blend-mode: overlay; }\n',
            "A trading-card foil: the card tilts toward the pointer, a rainbow layer slides across it and a glare follows, so it seems to catch the light.",
            pointer_js(".stage", ".holo")
            + 'target.style.setProperty("--px", 0.7); target.style.setProperty("--py", 0.3);\n',
        ),
        lab(
            "Metallic reflection",
            '<h2 class="word chrome">CHROME</h2>',
            BIG
            + ".chrome { --px: .5; color: transparent; background: linear-gradient(180deg, #f8fafc 0%, #94a3b8 38%, #1e293b 50%, #cbd5e1 54%, #f8fafc 78%, #64748b 100%), linear-gradient(100deg, transparent 40%, #fff 50%, transparent 60%); background-size: 100% 100%, 250% 100%; background-position: 0 0, calc(150% - var(--px) * 250%) 0; background-blend-mode: screen; -webkit-background-clip: text; background-clip: text; filter: drop-shadow(0 2px 0 #0f172a) drop-shadow(0 8px 14px rgb(0 0 0 / .6)); }\n",
            "Chrome is a picture of its surroundings: a sky-to-ground gradient with a hard dark horizon line across the middle, plus a glint that follows the pointer.",
            pointer_js(".stage", ".chrome", ".stage"),
        ),
        lab(
            "Iridescent shift",
            '<div class="shell" tabindex="0"></div>',
            ".shell { --px: .5; --py: .5; width: 190px; height: 190px; border-radius: 50%; outline: none; background: conic-gradient(from calc(var(--px) * 360deg) at calc(30% + var(--px) * 40%) calc(30% + var(--py) * 40%), #a5f3fc, #c4b5fd, #f9a8d4, #fde68a, #a7f3d0, #a5f3fc); filter: saturate(1.3); box-shadow: inset 0 0 40px rgb(255 255 255 / .6), inset -14px -18px 40px rgb(76 29 149 / .45), 0 20px 50px rgb(124 92 255 / .35); transition: background .1s linear; }\n",
            "Mother-of-pearl: the colours depend on the viewing angle, so the whole wheel of pastel hues turns and its centre shifts as the pointer moves.",
            pointer_js(".stage", ".shell", ".stage"),
        ),
        lab(
            "Prismatic effect",
            '<svg class="prism" viewBox="0 0 400 220" aria-hidden="true"><line class="beam" x1="0" y1="130" x2="172" y2="104" pathLength="1"/>'
            + "".join(
                f'<polygon class="ray" style="--i: {i}" fill="{colour}" points="226,{98 + i * 3} 400,{28 + i * 26} 400,{54 + i * 26} 226,{101 + i * 3}"/>'
                for i, colour in enumerate(
                    ("#ef4444", "#f97316", "#eab308", "#22c55e", "#06b6d4", "#6366f1", "#a855f7")
                )
            )
            + '<polygon class="glass" points="200,36 268,170 132,170"/><line class="inner" x1="172" y1="104" x2="228" y2="108"/></svg>',
            ".prism { width: 100%; height: 100%; }\n.beam { stroke: #fff; stroke-width: 3; stroke-dasharray: 1; animation: shine 4s ease-in-out infinite; filter: drop-shadow(0 0 4px #fff); }\n.inner { stroke: rgb(255 255 255 / .5); stroke-width: 2; }\n.glass { fill: rgb(255 255 255 / .06); stroke: rgb(255 255 255 / .7); stroke-width: 1.5; stroke-linejoin: round; }\n.ray { opacity: 0; mix-blend-mode: screen; animation: fan 4s ease-in-out infinite; animation-delay: calc(var(--i) * 50ms); }\n@keyframes shine { 0% { stroke-dashoffset: 1; } 25%, 100% { stroke-dashoffset: 0; } }\n@keyframes fan { 0%, 25% { opacity: 0; } 40%, 90% { opacity: .85; } 100% { opacity: 0; } }\n",
            "White light enters a prism and leaves as a fan of colours, red bent least and violet most. The beam is drawn first; the spectrum follows.",
        ),
        lab(
            "Light refraction",
            '<div class="tank"><div class="rods"></div><div class="water"><div class="rods"></div></div></div>',
            ".tank { position: relative; width: 320px; height: 210px; overflow: hidden; border-radius: 18px; background: #0b1020; }\n.rods { position: absolute; inset: 0; background: repeating-linear-gradient(100deg, transparent 0 34px, #f472b6 34px 40px, transparent 40px 74px, #fbbf24 74px 80px); }\n"
            "/* Below the waterline the same scene is drawn again, shifted and squeezed: the straight rods appear broken at the surface. */\n.water { position: absolute; left: 0; right: 0; bottom: 0; height: 50%; overflow: hidden; background: rgb(34 211 238 / .22); border-top: 2px solid rgb(165 243 252 / .8); animation: swell 4s ease-in-out infinite alternate; }\n.water .rods { top: auto; height: 210px; transform: translateX(var(--bend, 22px)) scaleX(1.12); transform-origin: 0 100%; filter: blur(.6px); }\n@keyframes swell { to { height: 56%; } }\n",
            "The pencil-in-a-glass illusion: straight rods appear to snap sideways where they enter the water, because the submerged part is a displaced copy.",
            'const tank = document.querySelector(".tank");\ntank.addEventListener("pointermove", (event) => {\n  const box = tank.getBoundingClientRect();\n  // Looking from further to one side bends the rods further.\n  tank.style.setProperty("--bend", `${(((event.clientX - box.left) / box.width) * 2 - 1) * 34}px`);\n});\n',
        ),
        lab(
            "Fresnel glow",
            '<div class="orb"></div>',
            "/* Surfaces seen edge-on reflect more: the rim is bright and the face is nearly clear. */\n.orb { width: 180px; height: 180px; border-radius: 50%; background: radial-gradient(circle at 50% 50%, rgb(11 16 32 / .9) 45%, rgb(34 211 238 / .35) 62%, rgb(165 243 252 / .95) 70%, transparent 71%), radial-gradient(circle at 34% 28%, rgb(255 255 255 / .5), transparent 22%); box-shadow: 0 0 40px 6px rgb(34 211 238 / .45), inset 0 0 30px rgb(34 211 238 / .5); animation: charge 3s ease-in-out infinite alternate; }\n@keyframes charge { from { filter: brightness(.8); } to { filter: brightness(1.25) hue-rotate(40deg); } }\n",
            "A force-field sphere: dark and transparent face-on, glowing at the silhouette, where the surface turns away from the viewer.",
        ),
        lab(
            "3D depth rotation",
            '<div class="scene3d"><div class="cube">'
            + "".join(
                f'<i class="f{n}">{label}</i>'
                for n, label in enumerate(("Plan", "Build", "Test", "Ship", "", ""))
            )
            + "</div></div>",
            ".scene3d { perspective: 700px; }\n.cube { position: relative; width: 120px; height: 120px; transform-style: preserve-3d; animation: tumble 12s linear infinite; }\n.cube i { position: absolute; inset: 0; display: grid; place-items: center; border: 1px solid rgb(255 255 255 / .35); background: rgb(124 92 255 / .28); font-style: normal; font-weight: 700; backface-visibility: visible; }\n"
            "/* Each face is turned to its side of the cube, then pushed out by half the cube's size. */\n.f0 { transform: rotateY(0deg) translateZ(60px); }\n.f1 { transform: rotateY(90deg) translateZ(60px); }\n.f2 { transform: rotateY(180deg) translateZ(60px); }\n.f3 { transform: rotateY(270deg) translateZ(60px); }\n.f4 { transform: rotateX(90deg) translateZ(60px); background: rgb(34 211 238 / .28); }\n.f5 { transform: rotateX(-90deg) translateZ(60px); background: rgb(34 211 238 / .28); }\n@keyframes tumble { from { transform: rotateX(-22deg) rotateY(0deg); } to { transform: rotateX(-22deg) rotateY(360deg); } }\n",
            "A real 3D object built from six flat elements, turning in perspective. Translucent faces let the far side show through.",
        ),
        lab(
            "3D object parallax",
            '<div class="diorama" tabindex="0"><i class="sky"></i><i class="far"></i><i class="mid"></i><b class="near">DEPTH</b><i class="dust"></i></div>',
            ".stage { perspective: 800px; }\n.diorama { --px: .5; --py: .5; position: relative; width: 300px; height: 190px; border-radius: 18px; outline: none; transform-style: preserve-3d; transform: rotateX(calc((.5 - var(--py)) * 26deg)) rotateY(calc((var(--px) - .5) * 26deg)); transition: transform .15s ease-out; }\n.diorama > * { position: absolute; }\n"
            "/* Layers sit at real distances along z, so tilting the box moves near ones more than far ones without any per-layer maths. */\n.sky { inset: 0; border-radius: 18px; background: linear-gradient(#1e1b4b, #be185d); transform: translateZ(-60px) scale(1.1); }\n.far { left: 12%; top: 16%; width: 70px; height: 70px; border-radius: 50%; background: #fde68a; transform: translateZ(-20px); box-shadow: 0 0 40px #fde68a; }\n.mid { left: 0; right: 0; bottom: 0; height: 55%; background: #4c1d95; clip-path: polygon(0 100%, 0 60%, 22% 20%, 40% 58%, 62% 8%, 82% 52%, 100% 30%, 100% 100%); transform: translateZ(30px); }\n.near { left: 0; right: 0; bottom: 18px; text-align: center; font-size: 34px; font-weight: 900; color: #fff; transform: translateZ(80px); text-shadow: 0 10px 24px rgb(0 0 0 / .5); }\n.dust { inset: 0; background: radial-gradient(circle, #fff 1px, transparent 1.5px) 0 0 / 46px 46px; opacity: .5; transform: translateZ(120px); }\n",
            "A shadow box: layers are placed at different depths inside a container that tilts with the pointer, so true perspective produces the parallax.",
            pointer_js(".stage", ".diorama", ".stage")
            + 'target.style.setProperty("--px", 0.72); target.style.setProperty("--py", 0.35);\n',
        ),
        lab(
            "Particle explosion",
            CANVAS_HTML,
            CANVAS_CSS,
            "Click anywhere: a burst of particles flies out, slows with drag, falls under gravity and fades. One on load shows the effect.",
            CANVAS_JS
            + """\
const TINTS = ["#7c5cff", "#22d3ee", "#f472b6", "#fbbf24", "#ffffff"];
let particles = [], running = false;
const explode = (x, y) => {
  for (let i = 0; i < 90; i += 1) {
    const angle = Math.random() * Math.PI * 2, speed = 1 + Math.random() * 6;
    particles.push({ x, y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed, life: 1, size: 1.5 + Math.random() * 2.5, tint: TINTS[i % TINTS.length] });
  }
  if (!running) { running = true; requestAnimationFrame(step); }
};
const step = () => {
  context.clearRect(0, 0, W, H);
  for (const particle of particles) {
    particle.vx *= 0.97; particle.vy = particle.vy * 0.97 + 0.12;  // drag, then gravity
    particle.x += particle.vx; particle.y += particle.vy;
    particle.life -= 0.014;
    context.globalAlpha = Math.max(0, particle.life);
    context.fillStyle = particle.tint;
    context.beginPath(); context.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2); context.fill();
  }
  context.globalAlpha = 1;
  particles = particles.filter((particle) => particle.life > 0);
  if (particles.length) requestAnimationFrame(step); else running = false;
};
canvas.addEventListener("click", (event) => { const [x, y] = event.clientX || event.clientY ? at(event) : [W / 2, H / 2]; if (!calm) explode(x, y); });
if (calm) { context.fillStyle = "#7c5cff"; context.beginPath(); context.arc(W / 2, H / 2, 6, 0, Math.PI * 2); context.fill(); } else explode(W / 2, H / 2);
""",
        ),
        lab(
            "Particle convergence",
            CANVAS_HTML,
            CANVAS_CSS,
            "The reverse of an explosion: particles start scattered and are pulled toward a point, spiralling in. Click to move the point they gather at.",
            CANVAS_JS
            + """\
let goal = [W / 2, H / 2];
const scatter = (particle) => Object.assign(particle, { x: Math.random() * W, y: Math.random() * H, vx: 0, vy: 0 });
const particles = Array.from({ length: 220 }, () => scatter({}));
const step = () => {
  context.fillStyle = "rgb(7 7 13 / .25)";  // not a full clear: the residue becomes trails
  context.fillRect(0, 0, W, H);
  for (const particle of particles) {
    const dx = goal[0] - particle.x, dy = goal[1] - particle.y, distance = Math.hypot(dx, dy) || 1;
    // Pulled toward the goal, with a sideways push that makes the path a spiral.
    particle.vx = (particle.vx + (dx / distance) * 0.25 + (-dy / distance) * 0.12) * 0.96;
    particle.vy = (particle.vy + (dy / distance) * 0.25 + (dx / distance) * 0.12) * 0.96;
    particle.x += particle.vx; particle.y += particle.vy;
    if (distance < 6) scatter(particle);  // arrived: start again from somewhere else
    context.fillStyle = `hsl(${190 + Math.min(70, distance / 3)} 90% 65%)`;
    context.fillRect(particle.x, particle.y, 2, 2);
  }
  if (!calm) requestAnimationFrame(step);
};
canvas.addEventListener("click", (event) => { if (event.clientX || event.clientY) goal = at(event); });
step();
""",
        ),
        lab(
            "Particle-to-object morph",
            CANVAS_HTML,
            CANVAS_CSS,
            "A cloud of particles arranges itself into a word, then a ring, then a star. Each particle has a target in the current shape and eases toward it. Click to change shape.",
            CANVAS_JS
            + """\
const COUNT = 700;
// Shapes are lists of target points. The word is found by drawing it off-screen and reading back which pixels are filled.
const fromText = (text) => {
  const sketch = Object.assign(document.createElement("canvas"), { width: W, height: H });
  const pen = sketch.getContext("2d", { willReadFrequently: true });
  pen.font = "900 110px system-ui, sans-serif"; pen.textAlign = "center"; pen.textBaseline = "middle";
  pen.fillText(text, W / 2, H / 2);
  const pixels = pen.getImageData(0, 0, W, H).data, found = [];
  for (let y = 0; y < H; y += 3) for (let x = 0; x < W; x += 3) if (pixels[(y * W + x) * 4 + 3] > 128) found.push([x, y]);
  return found;
};
const ring = Array.from({ length: COUNT }, (_, i) => { const a = (i / COUNT) * Math.PI * 2; return [W / 2 + Math.cos(a) * 80, H / 2 + Math.sin(a) * 80]; });
const star = Array.from({ length: COUNT }, (_, i) => {
  const a = (i / COUNT) * Math.PI * 2 - Math.PI / 2, r = 52 + 38 * Math.cos(5 * a);  // radius varies five times per turn
  return [W / 2 + Math.cos(a) * r, H / 2 + Math.sin(a) * r];
});
// Every shape is resampled to exactly COUNT targets so each particle always has somewhere to go.
const resample = (points) => Array.from({ length: COUNT }, (_, i) => points[Math.floor((i / COUNT) * points.length)] ?? [W / 2, H / 2]);
const SHAPES = [fromText("AI"), ring, star].map(resample);
const particles = Array.from({ length: COUNT }, () => ({ x: Math.random() * W, y: Math.random() * H, ease: 0.04 + Math.random() * 0.07 }));
let shape = 0;
const step = () => {
  context.clearRect(0, 0, W, H);
  particles.forEach((particle, i) => {
    const [tx, ty] = SHAPES[shape][i];
    particle.x += (tx - particle.x) * (calm ? 1 : particle.ease);
    particle.y += (ty - particle.y) * (calm ? 1 : particle.ease);
    context.fillStyle = `hsl(${250 - (i / COUNT) * 70} 90% 68%)`;
    context.fillRect(particle.x, particle.y, 2, 2);
  });
  if (!calm) requestAnimationFrame(step);
};
const next = () => { shape = (shape + 1) % SHAPES.length; if (calm) step(); };
canvas.addEventListener("click", next);
if (!calm) setInterval(next, 2800);
step();
""",
        ),
    ),
)
