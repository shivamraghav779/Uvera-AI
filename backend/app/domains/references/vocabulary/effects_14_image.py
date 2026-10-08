"""Effects 351-375: images and media."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.effects_07_background import svg_url
from app.domains.references.vocabulary.fx import REPLAY_BTN, REPLAY_CSS, STAGE, pointer_js

# A small drawn landscape stands in for a photograph: it has colour, tonal range and
# fine detail, which is what filters, masks and pixelation need to be visible.
_STARS = "".join(
    f"<circle cx='{(i * 73) % 300}' cy='{(i * 37) % 80}' r='{0.6 + (i % 3) * 0.4}' fill='#fff' opacity='{0.4 + (i % 4) * 0.15}'/>"
    for i in range(1, 26)
)
_TREES = "".join(
    f"<path d='M{x} 168 l5 -{14 + (x % 9)} l5 {14 + (x % 9)} z' fill='#0b1a2b'/>"
    for x in range(4, 300, 11)
)
_GLINTS = "".join(
    f"<rect x='{138 - i * 4}' y='{172 + i * 5}' width='{24 + i * 8}' height='1.5' fill='#fde68a' opacity='{0.7 - i * 0.1}'/>"
    for i in range(6)
)
PHOTO_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 300 200' preserveAspectRatio='xMidYMid slice'>"
    "<defs><linearGradient id='sky' x1='0' y1='0' x2='0' y2='1'><stop offset='0' stop-color='#1e1b4b'/><stop offset='.55' stop-color='#be185d'/><stop offset='.85' stop-color='#fb923c'/></linearGradient></defs>"
    f"<rect width='300' height='200' fill='url(#sky)'/>{_STARS}<circle cx='150' cy='128' r='30' fill='#fde68a'/>"
    "<path d='M0 150 L50 96 L88 132 L134 78 L176 130 L222 92 L300 150 Z' fill='#4c1d95'/>"
    "<path d='M0 168 L40 128 L84 158 L150 116 L206 160 L262 126 L300 156 L300 168 Z' fill='#1e1b4b'/>"
    f"{_TREES}<rect y='168' width='300' height='32' fill='#172554'/>{_GLINTS}</svg>"
)
PHOTO = svg_url(PHOTO_SVG)

FRAME = f"""\
.frame {{ position: relative; width: 300px; height: 200px; overflow: hidden; border-radius: 18px; outline: none; cursor: pointer; }}
.img {{ position: absolute; inset: 0; background: {PHOTO} center / cover; }}
"""
ON = ".frame:hover .img, .frame:focus-visible .img"
SLOW = "transition: all .6s var(--ease);"


def image(
    name: str,
    rest: str,
    active: str,
    note: str,
    extra: str = "",
    inner: str = "",
    js: str = "",
    replay: bool = False,
    after: str = "",
) -> Item:
    """An image effect: the picture's resting declarations and what hover or focus changes."""
    html = f'<div class="stage"><div class="frame" tabindex="0"><div class="img"></div>{inner}</div>{after}{REPLAY_BTN if replay else ""}</div>'
    css = (
        STAGE
        + FRAME
        + (REPLAY_CSS if replay else "")
        + (f".img {{ {rest} }}\n" if rest else "")
        + (f"{ON} {{ {active} }}\n" if active else "")
        + extra
    )
    return Item(name, html, css, js, note)


def svg_filter(body: str) -> str:
    return f'<svg width="0" height="0" aria-hidden="true">{body}</svg>'


REPLAY_FRAME = """\
const frame = document.querySelector(".frame");
const play = () => { frame.classList.remove("go"); void frame.offsetWidth; frame.classList.add("go"); };
document.querySelector(".replay").addEventListener("click", play);
play();
"""
CALM = 'const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\n'

SECTION = Section(
    "effects",
    "Image & Media Effects",
    351,
    (
        image(
            "Image fade",
            "",
            "",
            "A cross-fade: a second version of the picture sits on top and its opacity is all that changes.",
            ".alt { position: absolute; inset: 0; background: inherit; filter: hue-rotate(150deg) brightness(1.15); opacity: 0; transition: opacity .7s ease; }\n.frame:hover .alt, .frame:focus-visible .alt { opacity: 1; }\n.img, .alt { background: "
            + PHOTO
            + " center / cover; }\n",
            inner='<div class="alt"></div>',
        ),
        image(
            "Image zoom",
            SLOW,
            "scale: 1.18;",
            "The picture grows inside a frame that does not: the standard hover for thumbnails.",
        ),
        image(
            "Image pan",
            "scale: 1.3; translate: -9% 0; transition: translate 2.4s ease-in-out;",
            "translate: 9% 0;",
            "The picture is larger than its frame and drifts slowly across it, like a camera tracking.",
        ),
        image(
            "Image tilt",
            "",
            "",
            "The whole frame leans in 3D toward the pointer.",
            ".frame { --px: .5; --py: .5; transform: perspective(700px) rotateX(calc((.5 - var(--py)) * 22deg)) rotateY(calc((var(--px) - .5) * 22deg)); transition: transform .15s ease-out; }\n",
            js=pointer_js(".frame", ".frame"),
        ),
        image(
            "Image parallax",
            "inset: -12%; translate: calc((.5 - var(--px)) * 46px) calc((.5 - var(--py)) * 46px); transition: translate .2s ease-out;",
            "",
            "The picture slides against the pointer inside a fixed frame, as if seen through a window.",
            ".frame { --px: .5; --py: .5; }\n",
            js=pointer_js(".frame", ".frame"),
        ),
        image(
            "Image blur",
            "filter: blur(10px); scale: 1.08; " + SLOW,
            "filter: blur(0); scale: 1;",
            "Out of focus until hovered. The slight enlargement hides the soft transparent edge that a blur creates.",
        ),
        image(
            "Image sharpen",
            "filter: blur(.7px);",
            "filter: url(#sharpen);",
            "A convolution kernel that exaggerates the difference between each pixel and its neighbours, making edges crisper on hover.",
            after=svg_filter(
                '<filter id="sharpen"><feConvolveMatrix order="3" preserveAlpha="true" kernelMatrix="0 -1 0 -1 5 -1 0 -1 0"/></filter>'
            ),
        ),
        image(
            "Image grayscale transition",
            "filter: grayscale(1); " + SLOW,
            "filter: grayscale(0);",
            "Black and white at rest, full colour on hover: common for logo walls and team photos.",
        ),
        image(
            "Image saturation transition",
            "filter: saturate(.35); " + SLOW,
            "filter: saturate(1.7);",
            "Muted at rest and vivid on hover.",
        ),
        image(
            "Image brightness transition",
            "filter: brightness(.5); " + SLOW,
            "filter: brightness(1.1);",
            "Dimmed until it has attention, so a wall of images does not compete with the text over it.",
        ),
        image(
            "Image color shift",
            "transition: filter 1s ease;",
            "filter: hue-rotate(170deg);",
            "Every hue is turned round the colour wheel by the same angle: the sunset becomes a cold dawn.",
        ),
        image(
            "Image duotone transition",
            "",
            "",
            "Mapped to two inks, dark tones to one and light tones to the other; hovering fades the treatment away to show the original.",
            ".img { background: none; }\n.tone, .true { position: absolute; inset: 0; background: "
            + PHOTO
            + " center / cover; }\n.tone { filter: url(#duotone); transition: opacity .7s ease; }\n.frame:hover .tone, .frame:focus-visible .tone { opacity: 0; }\n",
            inner='<div class="true"></div><div class="tone"></div>',
            # Luminance first, then each channel is remapped between the two ink colours (#1e1b4b and #22d3ee).
            after=svg_filter(
                '<filter id="duotone" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values=".33 .33 .33 0 0  .33 .33 .33 0 0  .33 .33 .33 0 0  0 0 0 1 0"/><feComponentTransfer><feFuncR type="table" tableValues="0.118 0.133"/><feFuncG type="table" tableValues="0.106 0.827"/><feFuncB type="table" tableValues="0.294 0.933"/></feComponentTransfer></filter>'
            ),
        ),
        image(
            "Image reveal mask",
            "",
            "",
            "A soft-edged diagonal wipe: the mask's gradient stop is the animated value, so the edge stays feathered throughout.",
            '@property --edge { syntax: "<percentage>"; inherits: false; initial-value: 130%; }\n.img { mask: linear-gradient(115deg, #000 calc(var(--edge) - 30%), transparent var(--edge)); }\n.go .img { animation: unmask 1.3s var(--ease) both; }\n@keyframes unmask { from { --edge: 0%; } }\n',
            js=REPLAY_FRAME,
            replay=True,
        ),
        image(
            "Image clip reveal",
            "",
            "",
            "A hard-edged reveal from the bottom up while the picture settles from a slight enlargement.",
            ".go .img { animation: unclip 1s var(--ease) both; }\n@keyframes unclip { from { clip-path: inset(100% 0 0 0); scale: 1.25; } to { clip-path: inset(0); scale: 1; } }\n",
            js=REPLAY_FRAME,
            replay=True,
        ),
        image(
            "Image circular reveal",
            "clip-path: circle(var(--r, 150%) at var(--cx, 50%) var(--cy, 50%));",
            "",
            "The picture opens out from a point as a growing circle. Click anywhere on it to reveal from that spot.",
            '@property --r { syntax: "<percentage>"; inherits: true; initial-value: 150%; }\n.frame { background: var(--surface-2); }\n.go .img { animation: iris .9s var(--ease) both; }\n@keyframes iris { from { --r: 0%; } }\n',
            js='const frame = document.querySelector(".frame");\nconst reveal = (x, y) => {\n  frame.style.setProperty("--cx", `${x}px`); frame.style.setProperty("--cy", `${y}px`);\n  frame.classList.remove("go"); void frame.offsetWidth; frame.classList.add("go");\n};\nframe.addEventListener("click", (event) => {\n  const box = frame.getBoundingClientRect();\n  // A keyboard activation has no position: use the centre.\n  if (event.clientX || event.clientY) reveal(event.clientX - box.left, event.clientY - box.top); else reveal(box.width / 2, box.height / 2);\n});\nframe.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); frame.click(); } });\nreveal(frame.clientWidth / 2, frame.clientHeight / 2);\n',
        ),
        image(
            "Image wipe",
            "",
            "",
            "A second picture is uncovered from left to right over the first, with a bright line at the moving edge.",
            ".over { position: absolute; inset: 0; background: "
            + PHOTO
            + " center / cover; filter: hue-rotate(160deg) saturate(1.3); clip-path: inset(0 100% 0 0); transition: clip-path .8s var(--ease); }\n.frame:hover .over, .frame:focus-visible .over { clip-path: inset(0); }\n.line { position: absolute; top: 0; bottom: 0; left: 0; width: 2px; background: #fff; box-shadow: 0 0 12px #fff; opacity: 0; transition: left .8s var(--ease), opacity .2s; }\n.frame:hover .line, .frame:focus-visible .line { left: 100%; opacity: 1; }\n",
            inner='<div class="over"></div><i class="line"></i>',
        ),
        image(
            "Image pixelation",
            "",
            "",
            "Drawn at a very low resolution and scaled up without smoothing; on hover the resolution climbs in steps until the picture is clear.",
            ".frame canvas { position: absolute; inset: 0; width: 100%; height: 100%; }\n",
            inner="<canvas></canvas>",
            js=CALM
            + f"""\
const frame = document.querySelector(".frame");
const canvas = frame.querySelector("canvas");
const context = canvas.getContext("2d");
const small = document.createElement("canvas");
canvas.width = frame.clientWidth; canvas.height = frame.clientHeight;
const picture = new Image();
picture.src = `data:image/svg+xml,${{encodeURIComponent(`{PHOTO_SVG}`)}}`;
const STEPS = [8, 14, 24, 44, 90, 300];  // width of the low-resolution copy, in pixels
// Shrink to `width` pixels across, then enlarge with smoothing off: each small pixel becomes a block.
const draw = (width) => {{
  small.width = width; small.height = Math.round(width * canvas.height / canvas.width);
  small.getContext("2d").drawImage(picture, 0, 0, small.width, small.height);
  context.imageSmoothingEnabled = false;
  context.drawImage(small, 0, 0, canvas.width, canvas.height);
}};
let step = 1, timer;
const move = (direction) => {{
  clearInterval(timer);
  timer = setInterval(() => {{
    step = Math.max(1, Math.min(STEPS.length - 1, step + direction));
    draw(STEPS[step]);
    if (step === 1 || step === STEPS.length - 1) clearInterval(timer);
  }}, calm ? 0 : 90);
}};
picture.addEventListener("load", () => draw(STEPS[step]));
frame.addEventListener("pointerenter", () => move(1));
frame.addEventListener("pointerleave", () => move(-1));
frame.addEventListener("focus", () => move(1));
frame.addEventListener("blur", () => move(-1));
""",
        ),
        image(
            "Image glitch",
            "",
            "",
            "Two tinted copies show thin horizontal slices that jump sideways, and the whole picture twitches: a corrupted signal. Hover to trigger it.",
            ".slice { position: absolute; inset: 0; background: "
            + PHOTO
            + " center / cover; opacity: 0; mix-blend-mode: screen; }\n.s1 { filter: hue-rotate(90deg) saturate(3); }\n.s2 { filter: hue-rotate(-90deg) saturate(3); }\n"
            ".frame:hover .slice, .frame:focus-visible .slice { opacity: .9; }\n.frame:hover .s1, .frame:focus-visible .s1 { animation: cut-a .5s steps(1) infinite; }\n.frame:hover .s2, .frame:focus-visible .s2 { animation: cut-b .5s steps(1) infinite; }\n.frame:hover .img, .frame:focus-visible .img { animation: twitch .5s steps(1) infinite; }\n"
            "@keyframes cut-a { 0% { clip-path: inset(10% 0 78% 0); translate: -10px 0; } 25% { clip-path: inset(58% 0 30% 0); translate: 8px 0; } 50% { clip-path: inset(34% 0 52% 0); translate: -6px 0; } 75% { clip-path: inset(82% 0 6% 0); translate: 12px 0; } }\n"
            "@keyframes cut-b { 0% { clip-path: inset(66% 0 20% 0); translate: 10px 0; } 25% { clip-path: inset(20% 0 70% 0); translate: -12px 0; } 50% { clip-path: inset(74% 0 14% 0); translate: 6px 0; } 75% { clip-path: inset(42% 0 48% 0); translate: -8px 0; } }\n"
            "@keyframes twitch { 0%, 50% { translate: 0 0; } 25% { translate: 3px -1px; } 75% { translate: -3px 1px; } }\n"
            "@media (prefers-reduced-motion: reduce) { .frame .slice, .frame .img { animation: none !important; } }\n",
            inner='<div class="slice s1"></div><div class="slice s2"></div>',
        ),
        image(
            "Image distortion",
            "filter: url(#wobble); inset: -6%;",
            "",
            "On hover the picture is shaken by a noise displacement that swells and dies away within a second.",
            after=svg_filter(
                '<filter id="wobble"><feTurbulence type="fractalNoise" baseFrequency="0.015 0.03" numOctaves="2" seed="2"/><feDisplacementMap in="SourceGraphic" scale="0" xChannelSelector="R" yChannelSelector="G"/></filter>'
            ),
            js=CALM
            + """\
const frame = document.querySelector(".frame");
const map = document.querySelector("#wobble feDisplacementMap");
const DURATION = 900, PEAK = 46;
let started = 0;
const tick = (now) => {
  const t = Math.min(1, Math.max(0, (now - started) / DURATION));
  map.setAttribute("scale", (Math.sin(t * Math.PI) * PEAK).toFixed(1));  // rises to the peak and returns to zero
  if (t < 1) requestAnimationFrame(tick);
};
const shake = () => { if (calm) return; started = performance.now(); requestAnimationFrame(tick); };
frame.addEventListener("pointerenter", shake);
frame.addEventListener("focus", shake);
""",
        ),
        image(
            "Image displacement",
            "filter: url(#shift); inset: -8%;",
            "",
            "The strength of the displacement is tied to the pointer: none at the centre, growing as the pointer moves toward an edge.",
            after=svg_filter(
                '<filter id="shift"><feTurbulence type="turbulence" baseFrequency="0.008 0.02" numOctaves="1" seed="7"/><feDisplacementMap in="SourceGraphic" scale="0" xChannelSelector="R" yChannelSelector="B"/></filter>'
            ),
            js="""\
const frame = document.querySelector(".frame");
const map = document.querySelector("#shift feDisplacementMap");
frame.addEventListener("pointermove", (event) => {
  const box = frame.getBoundingClientRect();
  const x = (event.clientX - box.left) / box.width - 0.5, y = (event.clientY - box.top) / box.height - 0.5;
  map.setAttribute("scale", (Math.hypot(x, y) * 180).toFixed(1));
});
frame.addEventListener("pointerleave", () => map.setAttribute("scale", 0));
""",
        ),
        image(
            "Image liquid distortion",
            "filter: url(#water); inset: -6%;",
            "",
            "Seen through moving water: the noise that displaces the picture changes continuously, so the image never stops rippling.",
            after=svg_filter(
                '<filter id="water"><feTurbulence type="fractalNoise" baseFrequency="0.01 0.04" numOctaves="2" seed="5"><animate attributeName="baseFrequency" dur="9s" values="0.01 0.04;0.02 0.06;0.01 0.04" repeatCount="indefinite"/></feTurbulence><feDisplacementMap in="SourceGraphic" scale="22" xChannelSelector="R" yChannelSelector="G"/></filter>'
            ),
        ),
        image(
            "Image ripple",
            "",
            "",
            "Click the picture: rings spread from that point, and each ring brightens and blurs what lies beneath it, like a disturbance on water.",
            ".ring { position: absolute; width: 40px; height: 40px; margin: -20px; border-radius: 50%; border: 6px solid rgb(255 255 255 / .12); backdrop-filter: blur(3px) brightness(1.5); mask: radial-gradient(farthest-side, transparent calc(100% - 9px), #000 calc(100% - 8px)); animation: spread 1.3s ease-out forwards; animation-delay: var(--d); opacity: 0; pointer-events: none; }\n@keyframes spread { from { scale: .2; opacity: 1; } to { scale: 9; opacity: 0; } }\n",
            js="""\
const frame = document.querySelector(".frame");
const drop = (x, y) => {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  for (let i = 0; i < 3; i += 1) {
    const ring = document.createElement("i");
    ring.className = "ring";
    Object.assign(ring.style, { left: `${x}px`, top: `${y}px` });
    ring.style.setProperty("--d", `${i * 0.18}s`);
    ring.addEventListener("animationend", () => ring.remove());
    frame.append(ring);
  }
};
frame.addEventListener("click", (event) => {
  const box = frame.getBoundingClientRect();
  if (event.clientX || event.clientY) drop(event.clientX - box.left, event.clientY - box.top); else drop(box.width / 2, box.height / 2);
});
frame.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); frame.click(); } });
drop(frame.clientWidth / 2, frame.clientHeight / 2);
""",
        ),
        image(
            "Image reflection",
            "",
            "",
            "A flipped copy below the picture, fading quickly to nothing: the picture appears to stand on a glossy surface.",
            ".stage { align-content: center; gap: 4px; }\n.frame { width: 230px; height: 130px; cursor: default; }\n.mirror { width: 230px; height: 70px; border-radius: 18px; background: "
            + PHOTO
            + " center bottom / 230px 130px; scale: 1 -1; mask: linear-gradient(transparent 20%, rgb(0 0 0 / .5)); filter: blur(1px); }\n",
            after='<div class="mirror" aria-hidden="true"></div>',
        ),
        image(
            "Image light sweep",
            "",
            "",
            "A band of light crosses the picture once on hover, like a reflection passing over glass.",
            '.frame::after { content: ""; position: absolute; inset: 0; background: linear-gradient(105deg, transparent 38%, rgb(255 255 255 / .45) 50%, transparent 62%); translate: -110% 0; pointer-events: none; }\n.frame:hover::after, .frame:focus-visible::after { translate: 110% 0; transition: translate .9s var(--ease); }\n',
        ),
        image(
            "Image spotlight",
            "",
            "",
            "The picture is dark except for a circle around the pointer.",
            '.frame { --px: .5; --py: .5; }\n.frame::after { content: ""; position: absolute; inset: 0; background: radial-gradient(circle 80px at calc(var(--px) * 100%) calc(var(--py) * 100%), transparent 30%, rgb(3 6 16 / .88) 100%); pointer-events: none; }\n',
            js=pointer_js(".frame", ".frame"),
        ),
    ),
)
