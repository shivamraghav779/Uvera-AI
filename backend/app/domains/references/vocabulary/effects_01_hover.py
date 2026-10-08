"""Effects 1-40: hover and pointer."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import LOCAL_JS, PICTURE, hover, staged

T = "transition: all .28s var(--ease);"
GRID = "".join("<i></i>" for _ in range(54))
GRID_CSS = ".dots { display: grid; grid-template-columns: repeat(9, 1fr); gap: 20px; }\n.dots i { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); transition: translate .15s ease-out, scale .15s ease-out, background .15s; }\n"
# Calls back with every grid item and its distance from the pointer.
NEAR_JS = (
    LOCAL_JS
    + """\
const items = [...stage.querySelectorAll(".near")];
const eachNear = (callback) => {
  stage.addEventListener("pointermove", (event) => {
    for (const item of items) {
      const box = item.getBoundingClientRect();
      const dx = event.clientX - (box.left + box.width / 2), dy = event.clientY - (box.top + box.height / 2);
      callback(item, Math.hypot(dx, dy), dx, dy);
    }
  });
  stage.addEventListener("pointerleave", () => items.forEach((item) => callback(item, Infinity, 0, 0)));
};
"""
)
FOLLOW_JS = (
    LOCAL_JS
    + """\
// A follower that eases toward the pointer each frame instead of jumping to it.
const follow = (element, ease = 0.18) => {
  let x = stage.clientWidth / 2, y = stage.clientHeight / 2, tx = x, ty = y;
  stage.addEventListener("pointermove", (event) => { [tx, ty] = local(event); });
  const frame = () => {
    x += (tx - x) * (calm ? 1 : ease); y += (ty - y) * (calm ? 1 : ease);
    element.style.translate = `${x}px ${y}px`;
    requestAnimationFrame(frame);
  };
  frame();
};
"""
)
VARS_JS = (
    LOCAL_JS
    + 'stage.addEventListener("pointermove", (event) => { const [x, y] = local(event); stage.style.setProperty("--x", `${x}px`); stage.style.setProperty("--y", `${y}px`); });\n'
)
AREA = ".stage { border: 1px solid var(--border); border-radius: 20px; background: var(--surface); overflow: hidden; }\n"
CARDS = '<div class="near card">A</div><div class="near card">B</div><div class="near card">C</div>'
CARDS_CSS = ".stage { grid-template-columns: repeat(3, auto); gap: 18px; place-content: center; }\n.card { display: grid; place-items: center; width: 110px; height: 110px; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); font-weight: 700; transition: box-shadow .15s, scale .15s ease-out, filter .15s; }\n"


def cursor(name: str, inner: str, css: str, js: str, note: str) -> Item:
    return staged(name, inner, AREA + css, note, js, base="")


SECTION = Section(
    "effects",
    "Hover & Pointer Effects",
    1,
    (
        hover(
            "Hover lift",
            T,
            "translate: 0 -6px; box-shadow: 0 18px 30px -14px rgb(0 0 0 / .7);",
            "Rises a few pixels with a shadow that lengthens beneath it.",
        ),
        hover("Hover scale", T, "scale: 1.06;", "Grows slightly from its centre."),
        hover(
            "Hover shrink", T, "scale: .95;", "Pulls in a little, as if pressed toward the page."
        ),
        hover(
            "Hover tilt",
            T + " transform-style: preserve-3d;",
            "transform: perspective(700px) rotateX(10deg) rotateY(-10deg);",
            "Leans back on two axes in perspective.",
        ),
        hover(
            "Hover rotate",
            T,
            "rotate: 5deg;",
            "Turns a few degrees; playful, for tags and stickers.",
        ),
        hover(
            "Hover skew", T, "transform: skewX(-8deg);", "Slants, suggesting speed or direction."
        ),
        hover(
            "Hover glow",
            T,
            "box-shadow: 0 0 0 1px var(--primary), 0 0 32px color-mix(in srgb, var(--primary) 70%, transparent);",
            "A coloured halo spreads outward.",
        ),
        hover(
            "Hover shadow expansion",
            T + " box-shadow: 0 2px 4px rgb(0 0 0 / .4);",
            "box-shadow: 0 6px 10px rgb(0 0 0 / .35), 0 30px 60px -12px rgb(0 0 0 / .8);",
            "The shadow grows without the element moving.",
        ),
        hover(
            "Hover border glow",
            T,
            "border-color: var(--accent); box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 22%, transparent), inset 0 0 18px color-mix(in srgb, var(--accent) 14%, transparent);",
            "The edge lights up with a soft ring around it.",
        ),
        hover(
            "Hover background shift",
            "background: linear-gradient(90deg, var(--primary) 50%, var(--surface) 50%) 100% 0 / 200% 100%; transition: background-position .4s var(--ease), color .4s;",
            "background-position: 0 0; color: #fff;",
            "A fill sweeps in from one side by sliding an oversized background.",
        ),
        hover(
            "Hover gradient shift",
            "border: 0; color: #fff; background: linear-gradient(120deg, #7c5cff, #22d3ee, #f472b6, #7c5cff) 0 0 / 300% 100%; transition: background-position .8s var(--ease);",
            "background-position: 100% 0;",
            "The gradient travels across the surface.",
        ),
        hover(
            "Hover color transition",
            "transition: background .3s, color .3s, border-color .3s;",
            "background: var(--primary); color: #fff; border-color: var(--primary);",
            "Fill, text and border change together.",
        ),
        hover(
            "Hover opacity change",
            "opacity: .55; transition: opacity .25s;",
            "opacity: 1;",
            "Dim at rest, full strength on attention.",
        ),
        hover(
            "Hover blur reveal",
            "filter: blur(7px); transition: filter .35s var(--ease);",
            "filter: blur(0);",
            "Content is out of focus until hovered.",
            cls="pic",
            label="Revealed",
        ),
        hover(
            "Hover saturation boost",
            "filter: saturate(.25); transition: filter .35s;",
            "filter: saturate(1.5);",
            "Nearly grey at rest, vivid on hover.",
            cls="pic",
            label="",
        ),
        hover(
            "Hover brightness boost",
            "transition: filter .25s;",
            "filter: brightness(1.3);",
            "Simply lighter: the cheapest way to say 'interactive'.",
            cls="pic",
            label="",
        ),
        hover(
            "Hover contrast boost",
            "filter: contrast(.8); transition: filter .25s;",
            "filter: contrast(1.35);",
            "Tones separate and the image snaps.",
            cls="pic",
            label="",
        ),
        hover(
            "Hover depth shift",
            T + " position: relative;",
            "translate: -5px -5px;",
            "The face slides up and left, uncovering a solid layer behind it.",
            extra='.fx::after { content: ""; position: absolute; inset: 0; z-index: -1; border-radius: inherit; background: var(--primary); transition: translate .28s var(--ease); }\n.fx:hover::after, .fx:focus-visible::after { translate: 10px 10px; }\n.stage { isolation: isolate; }\n',
        ),
        hover(
            "Hover perspective shift",
            "transition: transform .5s var(--ease); transform: perspective(900px) rotateY(0); transform-origin: left center;",
            "transform: perspective(300px) rotateY(18deg);",
            "Swings open like a door as the perspective tightens.",
        ),
        hover(
            "Hover parallax",
            "position: relative; overflow: hidden;",
            "",
            "Layers inside shift by different amounts on hover.",
            cls="pic",
            label='<b class="far"></b><span class="near">Depth</span>',
            extra=".far { position: absolute; inset: -20%; background: radial-gradient(circle at 60% 40%, rgb(255 255 255 / .35), transparent 40%); transition: translate .5s var(--ease); }\n.near { position: relative; transition: translate .5s var(--ease); }\n.fx:hover .far, .fx:focus-visible .far { translate: -14px -8px; }\n.fx:hover .near, .fx:focus-visible .near { translate: 8px 4px; }\n",
        ),
        cursor(
            "Cursor spotlight",
            "<p>Move the pointer</p>",
            '.stage::before { content: ""; position: absolute; inset: 0; background: radial-gradient(180px circle at var(--x, 50%) var(--y, 50%), color-mix(in srgb, var(--primary) 55%, transparent), transparent 70%); }\n.stage p { position: relative; color: var(--muted); }\n',
            VARS_JS,
            "A pool of light centred on the pointer.",
        ),
        cursor(
            "Cursor glow",
            '<i class="blob"></i><p>Move the pointer</p>',
            ".blob { position: absolute; left: 0; top: 0; width: 120px; height: 120px; margin: -60px; border-radius: 50%; background: var(--accent); filter: blur(40px); opacity: .7; pointer-events: none; }\n.stage p { position: relative; color: var(--muted); }\n",
            FOLLOW_JS + 'follow(stage.querySelector(".blob"), 0.12);\n',
            "A blurred blob trails the pointer with a little lag.",
        ),
        cursor(
            "Cursor halo",
            '<i class="ring"></i><i class="dot"></i>',
            ".stage { cursor: none; }\n.ring, .dot { position: absolute; left: 0; top: 0; border-radius: 50%; pointer-events: none; }\n.ring { width: 44px; height: 44px; margin: -22px; border: 1.500px solid var(--fg); opacity: .6; }\n.dot { width: 6px; height: 6px; margin: -3px; background: var(--fg); }\n",
            FOLLOW_JS
            + 'follow(stage.querySelector(".ring"), 0.14);\nfollow(stage.querySelector(".dot"), 1);\n',
            "A precise dot with a ring that catches up: two followers at different speeds.",
        ),
        cursor(
            "Cursor trail",
            "",
            ".stage i { position: absolute; left: 0; top: 0; width: 10px; height: 10px; margin: -5px; border-radius: 50%; background: var(--accent); pointer-events: none; animation: fade .6s linear forwards; }\n@keyframes fade { to { opacity: 0; scale: .2; } }\n",
            LOCAL_JS
            + 'let last = 0;\nstage.addEventListener("pointermove", (event) => {\n  if (calm || event.timeStamp - last < 24) return;  // at most one dot per frame or so\n  last = event.timeStamp;\n  const [x, y] = local(event);\n  const dot = document.createElement("i");\n  dot.style.translate = `${x}px ${y}px`;\n  dot.addEventListener("animationend", () => dot.remove());  // every dot cleans up after itself\n  stage.append(dot);\n});\n',
            "Dots dropped along the path fade and shrink away.",
        ),
        cursor(
            "Cursor magnetic pull",
            '<button class="near mag">Magnet</button>',
            ".mag { width: 110px; height: 110px; border: 0; border-radius: 50%; background: var(--primary); color: #fff; font-weight: 700; transition: translate .3s var(--ease); }\n",
            NEAR_JS
            + "const RADIUS = 130;\neachNear((item, distance, dx, dy) => { const pull = distance < RADIUS ? (1 - distance / RADIUS) * 0.45 : 0; item.style.translate = `${dx * pull}px ${dy * pull}px`; });\n",
            "Within a radius the element leans toward the pointer; beyond it, it rests.",
        ),
        cursor(
            "Cursor attraction",
            f'<div class="dots">{GRID.replace("<i>", '<i class="near">')}</div>',
            GRID_CSS,
            NEAR_JS
            + 'const RADIUS = 110;\neachNear((item, distance, dx, dy) => { const pull = distance < RADIUS ? (1 - distance / RADIUS) * 0.5 : 0; item.style.translate = `${dx * pull}px ${dy * pull}px`; item.style.background = pull ? "var(--accent)" : ""; });\n',
            "A field of points drawn toward the pointer.",
        ),
        cursor(
            "Cursor repulsion",
            f'<div class="dots">{GRID.replace("<i>", '<i class="near">')}</div>',
            GRID_CSS,
            NEAR_JS
            + "const RADIUS = 90;\neachNear((item, distance, dx, dy) => {\n  const push = distance < RADIUS ? (1 - distance / RADIUS) * 26 : 0;\n  const angle = Math.atan2(dy, dx);\n  item.style.translate = `${-Math.cos(angle) * push}px ${-Math.sin(angle) * push}px`;  // directly away from the pointer\n});\n",
            "The same field pushed away, leaving a clearing around the pointer.",
        ),
        cursor(
            "Cursor distortion",
            '<p class="txt">Bend the light</p><i class="lens"></i>',
            ".txt { font-size: 38px; font-weight: 800; letter-spacing: -.02em; }\n.lens { position: absolute; left: 0; top: 0; width: 110px; height: 110px; margin: -55px; border-radius: 50%; pointer-events: none; backdrop-filter: hue-rotate(70deg) saturate(1.8) contrast(1.3) blur(1.500px); scale: 1.08; border: 1px solid rgb(255 255 255 / .25); }\n",
            FOLLOW_JS + 'follow(stage.querySelector(".lens"), 0.25);\n',
            "A lens that follows the pointer and alters whatever is beneath it with backdrop filters.",
        ),
        cursor(
            "Cursor enlargement",
            '<i class="cur"></i><button class="t">Hover a button</button><a class="t" href="#">or a link</a>',
            ".stage { cursor: none; grid-auto-flow: column; gap: 24px; place-content: center; }\n.cur { position: absolute; left: 0; top: 0; width: 14px; height: 14px; margin: -7px; border-radius: 50%; background: var(--fg); mix-blend-mode: difference; pointer-events: none; transition: scale .25s var(--ease); z-index: 2; }\n.cur.big { scale: 4; }\n.t { padding: 10px 18px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); color: var(--fg); cursor: none; }\n",
            FOLLOW_JS
            + 'const cursor = stage.querySelector(".cur");\nfollow(cursor, 0.3);\n// The cursor swells over anything that can be acted on.\nstage.addEventListener("pointerover", (event) => cursor.classList.toggle("big", Boolean(event.target.closest("a, button"))));\n',
            "A custom cursor that grows over interactive elements, inverting what it covers.",
        ),
        cursor(
            "Cursor morph",
            '<i class="cur"></i><button class="t">Primary</button><button class="t wide">A wider button</button>',
            ".stage { grid-auto-flow: column; gap: 24px; place-content: center; }\n.cur { position: absolute; left: 0; top: 0; width: 16px; height: 16px; border-radius: 16px; background: color-mix(in srgb, var(--primary) 35%, transparent); border: 1px solid var(--primary); pointer-events: none; transition: width .25s var(--ease), height .25s var(--ease), border-radius .25s var(--ease), translate .25s var(--ease); }\n.cur.free { transition: width .25s var(--ease), height .25s var(--ease), border-radius .25s var(--ease); }\n.t { position: relative; padding: 12px 20px; border: 1px solid var(--border); border-radius: 12px; background: none; color: var(--fg); }\n",
            LOCAL_JS
            + 'const cursor = stage.querySelector(".cur");\nlet locked = null;\nstage.addEventListener("pointermove", (event) => {\n  const target = event.target.closest(".t");\n  if (target) {\n    // Over a control the cursor takes the control\'s place and shape.\n    const box = target.getBoundingClientRect(), frame = stage.getBoundingClientRect();\n    Object.assign(cursor.style, { width: `${box.width}px`, height: `${box.height}px`, borderRadius: "12px", translate: `${box.left - frame.left}px ${box.top - frame.top}px` });\n    cursor.classList.remove("free");\n    locked = target;\n    return;\n  }\n  const [x, y] = local(event);\n  if (locked) { locked = null; Object.assign(cursor.style, { width: "", height: "", borderRadius: "" }); }\n  cursor.classList.add("free");\n  cursor.style.translate = `${x - 8}px ${y - 8}px`;\n});\n',
            "Over a control the cursor snaps to its outline and becomes its highlight.",
        ),
        cursor(
            "Cursor-follow gradient",
            "<p>Move the pointer</p>",
            ".stage { background: conic-gradient(from var(--angle, 0deg) at 50% 50%, #7c5cff, #22d3ee, #f472b6, #7c5cff); }\n.stage p { padding: 6px 14px; border-radius: 99px; background: rgb(0 0 0 / .45); color: #fff; }\n",
            LOCAL_JS
            + 'stage.addEventListener("pointermove", (event) => {\n  const [x, y] = local(event);\n  // The gradient turns to face the pointer.\n  stage.style.setProperty("--angle", `${Math.atan2(y - stage.clientHeight / 2, x - stage.clientWidth / 2) * (180 / Math.PI) + 90}deg`);\n});\n',
            "A conic gradient rotates to point at the pointer.",
        ),
        cursor(
            "Cursor-follow shadow",
            '<div class="lit">Light source</div>',
            ".lit { display: grid; place-items: center; width: 190px; height: 110px; border-radius: 18px; background: var(--surface-2); font-weight: 700; box-shadow: var(--sx, 0px) var(--sy, 14px) 30px -6px rgb(0 0 0 / .8); transition: box-shadow .1s linear; }\n",
            LOCAL_JS
            + 'const card = stage.querySelector(".lit");\nstage.addEventListener("pointermove", (event) => {\n  const box = card.getBoundingClientRect();\n  // The pointer is the light: the shadow falls on the opposite side.\n  card.style.setProperty("--sx", `${((box.left + box.width / 2 - event.clientX) / 8).toFixed(1)}px`);\n  card.style.setProperty("--sy", `${((box.top + box.height / 2 - event.clientY) / 8).toFixed(1)}px`);\n});\n',
            "The shadow falls away from the pointer, as if it were the light.",
        ),
        cursor(
            "Cursor-follow image",
            '<ul><li data-h="250">Aurora</li><li data-h="20">Ember</li><li data-h="170">Lagoon</li></ul><i class="peek"></i>',
            ".stage ul { margin: 0; padding: 0; list-style: none; font-size: 30px; font-weight: 800; }\n.stage li { padding: 4px 0; color: var(--muted); transition: color .2s; cursor: default; }\n.stage li:hover { color: var(--fg); }\n.peek { position: absolute; left: 0; top: 0; width: 150px; height: 100px; margin: -50px 0 0 24px; border-radius: 12px; pointer-events: none; opacity: 0; scale: .8; transition: opacity .2s, scale .25s var(--ease); background: linear-gradient(135deg, hsl(var(--h) 72% 58%), hsl(calc(var(--h) + 55) 70% 32%)); }\n.peek.on { opacity: 1; scale: 1; }\n",
            FOLLOW_JS
            + 'const peek = stage.querySelector(".peek");\nfollow(peek, 0.2);\nstage.querySelectorAll("li").forEach((item) => {\n  item.addEventListener("pointerenter", () => { peek.style.setProperty("--h", item.dataset.h); peek.classList.add("on"); });\n  item.addEventListener("pointerleave", () => peek.classList.remove("on"));\n});\n',
            "Hovering a title floats its picture beside the pointer.",
        ),
        cursor(
            "Cursor-follow particle",
            "<p>Move the pointer</p>",
            ".stage p { color: var(--muted); }\n.stage i { position: absolute; left: 0; top: 0; width: 6px; height: 6px; margin: -3px; border-radius: 50%; pointer-events: none; animation: fly .8s ease-out forwards; }\n@keyframes fly { to { translate: var(--tx) var(--ty); opacity: 0; scale: .3; } }\n",
            LOCAL_JS
            + 'const COLOURS = ["#7c5cff", "#22d3ee", "#f472b6", "#fbbf24"];\nlet last = 0;\nstage.addEventListener("pointermove", (event) => {\n  if (calm || event.timeStamp - last < 30) return;\n  last = event.timeStamp;\n  const [x, y] = local(event);\n  const spark = document.createElement("i");\n  spark.style.left = `${x}px`; spark.style.top = `${y}px`;\n  spark.style.background = COLOURS[Math.floor(Math.random() * COLOURS.length)];\n  // Each spark drifts off in its own direction, falling slightly.\n  spark.style.setProperty("--tx", `${(Math.random() - 0.5) * 80}px`);\n  spark.style.setProperty("--ty", `${Math.random() * 60 + 10}px`);\n  spark.addEventListener("animationend", () => spark.remove());\n  stage.append(spark);\n});\n',
            "Sparks are emitted at the pointer and drift away as they fade.",
        ),
        cursor(
            "Cursor-follow blur",
            '<p class="txt">Frosted lens</p><i class="frost"></i>',
            PICTURE
            + ".stage { background: radial-gradient(circle at 30% 30%, #f472b6, transparent 45%), radial-gradient(circle at 75% 65%, #22d3ee, transparent 50%), linear-gradient(135deg, #312e81, #7c5cff); }\n.txt { font-size: 34px; font-weight: 800; color: #fff; }\n.frost { position: absolute; left: 0; top: 0; width: 120px; height: 120px; margin: -60px; border-radius: 50%; pointer-events: none; backdrop-filter: blur(10px); border: 1px solid rgb(255 255 255 / .3); background: rgb(255 255 255 / .06); }\n",
            FOLLOW_JS + 'follow(stage.querySelector(".frost"), 0.2);\n',
            "A disc of frosted glass follows the pointer, blurring what lies under it.",
        ),
        cursor(
            "Cursor-follow spotlight",
            '<p class="txt">Find the text in the dark</p>',
            '.stage { background: #000; }\n.txt { font-size: 26px; font-weight: 800; color: #fff; }\n.stage::after { content: ""; position: absolute; inset: 0; background: #000; mask: radial-gradient(110px circle at var(--x, -200px) var(--y, -200px), transparent 30%, #000 100%); pointer-events: none; }\n',
            VARS_JS,
            "A flashlight: everything is dark except a soft-edged circle around the pointer.",
        ),
        cursor(
            "Cursor proximity glow",
            CARDS,
            CARDS_CSS,
            NEAR_JS
            + "const RADIUS = 170;\neachNear((item, distance) => {\n  const strength = Math.max(0, 1 - distance / RADIUS);\n  item.style.boxShadow = `0 0 ${strength * 40}px color-mix(in srgb, var(--accent) ${Math.round(strength * 90)}%, transparent)`;\n});\n",
            "Each card glows more the nearer the pointer comes to it.",
        ),
        cursor(
            "Cursor proximity scale",
            CARDS,
            CARDS_CSS,
            NEAR_JS
            + "const RADIUS = 170;\neachNear((item, distance) => { item.style.scale = String(1 + Math.max(0, 1 - distance / RADIUS) * 0.28); });\n",
            "Items swell as the pointer approaches, like a dock.",
        ),
        cursor(
            "Cursor proximity blur",
            CARDS,
            CARDS_CSS,
            NEAR_JS
            + "const RADIUS = 200;\neachNear((item, distance) => { item.style.filter = `blur(${Math.min(6, Math.max(0, distance === Infinity ? 0 : (distance / RADIUS) * 5 - 1)).toFixed(1)}px)`; });\n",
            "Whatever is far from the pointer goes out of focus.",
        ),
        cursor(
            "Cursor proximity displacement",
            '<h2 class="word">'
            + "".join(f'<span class="near">{c}</span>' for c in "DISPLACE")
            + "</h2>",
            ".word { margin: 0; font-size: 54px; font-weight: 800; letter-spacing: .04em; }\n.word span { display: inline-block; transition: translate .2s ease-out, color .2s; }\n",
            NEAR_JS
            + 'const RADIUS = 100;\neachNear((item, distance, dx, dy) => {\n  const push = distance < RADIUS ? (1 - distance / RADIUS) * 30 : 0;\n  const angle = Math.atan2(dy, dx);\n  item.style.translate = `${-Math.cos(angle) * push}px ${-Math.sin(angle) * push}px`;\n  item.style.color = push ? "var(--accent)" : "";\n});\n',
            "Letters are nudged out of the pointer's way and settle back behind it.",
        ),
    ),
)
