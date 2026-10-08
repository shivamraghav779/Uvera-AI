"""Effects 151-180: text."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import REPLAY_BTN, REPLAY_CSS, STAGE

TX = ".tx { margin: 0; font-size: 40px; font-weight: 800; letter-spacing: -.02em; line-height: 1.15; text-align: center; }\n"
CALM = 'const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\n'
# Splits text into spans that know their index; the phrase stays readable to assistive tech.
SPLIT = """\
const split = (element, pattern) => {
  const parts = element.textContent.split(pattern).filter((part) => part !== "");
  element.setAttribute("aria-label", element.textContent);
  element.replaceChildren(...parts.map((part, i) => {
    const piece = Object.assign(document.createElement("span"), { textContent: part });
    piece.setAttribute("aria-hidden", "true");
    piece.style.setProperty("--i", i);
    if (/^\\s+$/.test(part)) piece.style.whiteSpace = "pre";
    return piece;
  }));
  return parts.length;
};
"""
REPLAY = """\
const element = document.querySelector(".tx");
const play = () => { element.classList.remove("go"); void element.offsetWidth; element.classList.add("go"); };
document.querySelector(".replay").addEventListener("click", play);
"""
PIECES = ".tx span { display: inline-block; }\n"


def text(
    name: str,
    css: str,
    note: str,
    content: str = "Designed with care",
    js: str = "",
    replay: bool = False,
    attrs: str = "",
    after: str = "",
) -> Item:
    html = f'<div class="stage"><h2 class="tx"{attrs}>{content}</h2>{after}{REPLAY_BTN if replay else ""}</div>'
    return Item(name, html, STAGE + TX + (REPLAY_CSS if replay else "") + css, js, note)


def stagger(
    name: str,
    start: str,
    note: str,
    by: str = '""',
    content: str = "Designed with care",
    step: int = 35,
    extra: str = "",
) -> Item:
    """Pieces of the text play the same entrance one after another."""
    css = (
        PIECES
        + f".tx.go span {{ animation: piece .6s var(--ease) both; animation-delay: calc(var(--i) * {step}ms); }}\n@keyframes piece {{ from {{ {start} }} }}\n"
        + extra
    )
    return text(
        name, css, note, content, SPLIT + REPLAY + f"split(element, {by});\nplay();\n", replay=True
    )


SCRAMBLE = (
    CALM
    + """\
const element = document.querySelector(".tx");
const FINAL = element.textContent;
element.setAttribute("aria-label", FINAL);
const random = (set) => set[Math.floor(Math.random() * set.length)];
// Runs `frameOf(step)` until it returns the finished text; one text update per animation frame.
const run = (frameOf) => {
  if (calm) { element.textContent = FINAL; return; }
  let step = 0;
  const tick = () => {
    const text = frameOf(step++);
    element.textContent = text;
    if (text !== FINAL) requestAnimationFrame(tick);
  };
  tick();
};
"""
)

SECTION = Section(
    "effects",
    "Text Effects",
    151,
    (
        text(
            "Typewriter effect",
            '.tx { font-family: var(--mono); font-size: 26px; min-height: 1.2em; }\n.tx::after { content: ""; display: inline-block; width: .55em; height: 1.05em; margin-left: 2px; vertical-align: text-bottom; background: var(--accent); animation: blink 1s steps(2) infinite; }\n@keyframes blink { 50% { opacity: 0; } }\n',
            "Characters appear one at a time behind a block caret, with a slightly uneven rhythm.",
            "",
            CALM
            + 'const element = document.querySelector(".tx");\nconst PHRASE = "Hello. I write myself.";\nelement.setAttribute("aria-label", PHRASE);\nconst type = (index = 0) => {\n  if (calm) { element.textContent = PHRASE; return; }\n  element.textContent = PHRASE.slice(0, index);\n  if (index < PHRASE.length) setTimeout(() => type(index + 1), 45 + Math.random() * 70 + (PHRASE[index - 1] === "." ? 350 : 0));  // a pause after a full stop\n};\ndocument.querySelector(".replay").addEventListener("click", () => type());\ntype();\n',
            replay=True,
        ),
        stagger(
            "Character fade-in",
            "opacity: 0;",
            "Each character fades in a moment after the one before.",
        ),
        stagger(
            "Character slide-in",
            "opacity: 0; translate: 0 .6em;",
            "Characters rise into the line one by one.",
        ),
        stagger(
            "Character blur-in",
            "opacity: 0; filter: blur(10px); scale: 1.4;",
            "Characters condense out of a blur in sequence.",
            step=45,
        ),
        stagger(
            "Word-by-word reveal",
            "opacity: 0; translate: 0 .4em; filter: blur(4px);",
            "Words arrive one at a time: reads naturally, unlike per-letter effects.",
            by="/(\\s+)/",
            content="Every word in its own time",
            step=110,
        ),
        stagger(
            "Line-by-line reveal",
            "translate: 0 105%;",
            "Each line slides up from behind its own clipping edge.",
            by='"|"',
            content="First this line|then the second|and then the last.",
            step=140,
            extra=".tx { font-size: 30px; }\n.tx span { display: block; }\n.tx { overflow: hidden; }\n.tx span { clip-path: inset(0); }\n",
        ),
        text(
            "Text scrambling",
            ".tx { font-family: var(--mono); font-size: 30px; cursor: pointer; }\n",
            "On hover every character flickers through random glyphs and settles at its own moment.",
            "HOVER TO SCRAMBLE",
            SCRAMBLE
            + 'const GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ#%&@$";\nconst start = () => {\n  // Each character gets its own number of frames before it locks.\n  const locks = [...FINAL].map(() => 6 + Math.floor(Math.random() * 22));\n  run((step) => [...FINAL].map((char, i) => (char === " " || step >= locks[i] ? char : random(GLYPHS))).join(""));\n};\nelement.addEventListener("pointerenter", start);\nelement.addEventListener("focus", start);\n',
            attrs=' tabindex="0"',
        ),
        text(
            "Text decoding",
            ".tx { font-family: var(--mono); font-size: 28px; }\n",
            "Resolved strictly left to right out of a stream of digits, like a cipher being read.",
            "ACCESS GRANTED",
            SCRAMBLE
            + 'const start = () => run((step) => {\n  const solved = Math.floor(step / 3);  // one more character every third frame\n  return [...FINAL].map((char, i) => (i < solved || char === " " ? char : random("01"))).join("");\n});\ndocument.querySelector(".replay").addEventListener("click", start);\nstart();\n',
            replay=True,
        ),
        text(
            "Text glitch",
            ".tx { position: relative; }\n.tx::before, .tx::after { content: attr(data-text); position: absolute; inset: 0; }\n.tx::before { color: #22d3ee; animation: slice-a 2.4s steps(1) infinite; }\n.tx::after { color: #f43f5e; animation: slice-b 2.4s steps(1) infinite; }\n@keyframes slice-a { 0%, 100% { clip-path: inset(0 0 100% 0); } 10% { clip-path: inset(12% 0 60% 0); translate: -4px 0; } 14% { clip-path: inset(64% 0 8% 0); translate: 4px 0; } 18% { clip-path: inset(0 0 100% 0); } 62% { clip-path: inset(40% 0 36% 0); translate: -3px 0; } 66% { clip-path: inset(0 0 100% 0); } }\n@keyframes slice-b { 0%, 100% { clip-path: inset(0 0 100% 0); } 11% { clip-path: inset(52% 0 20% 0); translate: 4px 0; } 15% { clip-path: inset(6% 0 78% 0); translate: -4px 0; } 19% { clip-path: inset(0 0 100% 0); } 63% { clip-path: inset(18% 0 62% 0); translate: 3px 0; } 67% { clip-path: inset(0 0 100% 0); } }\n@media (prefers-reduced-motion: reduce) { .tx::before, .tx::after { animation: none; } }\n",
            "Two coloured copies, each showing a different horizontal slice, jump sideways in short bursts.",
            "SIGNAL LOST",
            attrs=' data-text="SIGNAL LOST"',
        ),
        text(
            "Text flicker",
            ".tx { color: #fecdd3; text-shadow: 0 0 6px #f43f5e, 0 0 24px #f43f5e, 0 0 48px #e11d48; animation: flicker 4s linear infinite; }\n@keyframes flicker { 0%, 18%, 22%, 25%, 53%, 57%, 100% { opacity: 1; } 20%, 24%, 55% { opacity: .35; text-shadow: none; } }\n@media (prefers-reduced-motion: reduce) { .tx { animation: none; } }\n",
            "A neon sign with a loose connection: steady, with brief irregular dropouts.",
            "OPEN LATE",
        ),
        text(
            "Text shimmer",
            ".tx { color: transparent; background: linear-gradient(100deg, var(--muted) 35%, #fff 50%, var(--muted) 65%) 100% 0 / 250% 100%; -webkit-background-clip: text; background-clip: text; animation: shimmer 2.4s linear infinite; }\n@keyframes shimmer { to { background-position: -150% 0; } }\n",
            "A highlight passes across the letters: the standard 'working on it' text.",
            "Generating…",
        ),
        text(
            "Text glow",
            ".tx { color: #fff; animation: glow 2.6s ease-in-out infinite alternate; }\n@keyframes glow { from { text-shadow: 0 0 4px rgb(124 92 255 / .6); } to { text-shadow: 0 0 10px #7c5cff, 0 0 30px #7c5cff, 0 0 60px #22d3ee; } }\n",
            "Layered text shadows breathing in and out.",
        ),
        text(
            "Text gradient shift",
            ".tx { color: transparent; background: linear-gradient(90deg, #7c5cff, #22d3ee, #f472b6, #fbbf24, #7c5cff) 0 0 / 300% 100%; -webkit-background-clip: text; background-clip: text; animation: flow 6s linear infinite; }\n@keyframes flow { to { background-position: 300% 0; } }\n",
            "A gradient clipped to the glyphs and scrolled through them without end.",
        ),
        text(
            "Text color sweep",
            ".tx { cursor: pointer; color: transparent; background: linear-gradient(90deg, var(--accent) 50%, var(--fg) 50%) 100% 0 / 200% 100%; -webkit-background-clip: text; background-clip: text; transition: background-position .5s var(--ease); }\n.tx:hover, .tx:focus-visible { background-position: 0 0; }\n",
            "On hover a new colour wipes through the text from the left.",
            "Hover this line",
            attrs=' tabindex="0"',
        ),
        text(
            "Text highlight sweep",
            ".tx mark { color: inherit; background: linear-gradient(color-mix(in srgb, var(--warning) 55%, transparent), color-mix(in srgb, var(--warning) 55%, transparent)) 0 85% / 0% 45% no-repeat; }\n.tx.go mark { animation: mark .7s .3s var(--ease) forwards; }\n@keyframes mark { to { background-size: 100% 45%; } }\n",
            "A marker stroke is drawn behind one phrase.",
            "The <mark>important part</mark> is this",
            REPLAY + "play();\n",
            replay=True,
        ),
        text(
            "Text underline animation",
            ".tx { font-size: 26px; font-weight: 600; }\n.tx a { color: inherit; text-decoration: none; background: linear-gradient(var(--accent), var(--accent)) 0 100% / 0 2px no-repeat; transition: background-size .35s var(--ease); padding-bottom: 3px; }\n.tx a:hover, .tx a:focus-visible { background-size: 100% 2px; }\n",
            "An underline grows from the left on hover: a background, so it follows the text across line breaks.",
            'Read the <a href="#">full announcement</a>',
        ),
        text(
            "Animated underline",
            '.tx { font-size: 26px; font-weight: 600; }\n.tx a { position: relative; color: inherit; text-decoration: none; }\n.tx a::after { content: ""; position: absolute; left: 0; right: 0; bottom: -4px; height: 2px; background: var(--accent); transform-origin: right; transition: scale .35s var(--ease); }\n/* Leaving to the right and returning from the left: the origin flips with the state. */\n.tx a:hover::after, .tx a:focus-visible::after { animation: redraw .7s var(--ease); }\n@keyframes redraw { 0% { scale: 1 1; transform-origin: right; } 45% { scale: 0 1; transform-origin: right; } 46% { scale: 0 1; transform-origin: left; } 100% { scale: 1 1; transform-origin: left; } }\n',
            "The existing underline retracts to the right and is redrawn from the left.",
            'Read the <a href="#">full announcement</a>',
        ),
        text(
            "Text shadow movement",
            ".tx { font-size: 54px; text-shadow: var(--sx, 6px) var(--sy, 6px) 0 var(--primary), calc(var(--sx, 6px) * 2) calc(var(--sy, 6px) * 2) 0 color-mix(in srgb, var(--accent) 60%, transparent); transition: text-shadow .1s linear; }\n",
            "The shadow falls away from the pointer, as though the pointer were a lamp.",
            "SHADOW",
            'const stage = document.querySelector(".stage");\nconst element = stage.querySelector(".tx");\nstage.addEventListener("pointermove", (event) => {\n  const box = element.getBoundingClientRect();\n  element.style.setProperty("--sx", `${((box.left + box.width / 2 - event.clientX) / 14).toFixed(1)}px`);\n  element.style.setProperty("--sy", `${((box.top + box.height / 2 - event.clientY) / 14).toFixed(1)}px`);\n});\n',
        ),
        text(
            "Text extrusion",
            ".tx { font-size: 60px; color: #fff; cursor: pointer; transition: text-shadow .3s var(--ease), translate .3s var(--ease); text-shadow: 1px 1px 0 #5b3fd9, 2px 2px 0 #5b3fd9, 3px 3px 0 #5b3fd9; }\n.tx:hover, .tx:focus-visible { translate: -5px -5px; text-shadow: 1px 1px 0 #5b3fd9, 2px 2px 0 #5b3fd9, 3px 3px 0 #5b3fd9, 4px 4px 0 #5b3fd9, 5px 5px 0 #5b3fd9, 6px 6px 0 #5b3fd9, 7px 7px 0 #5b3fd9, 8px 8px 0 #5b3fd9, 14px 14px 20px rgb(0 0 0 / .6); }\n",
            "Stacked one-pixel shadows give the letters thickness; hovering pulls them further off the page.",
            "DEPTH",
            attrs=' tabindex="0"',
        ),
        text(
            "Text distortion",
            ".tx { font-size: 50px; filter: url(#warp); }\n",
            "An SVG turbulence filter displaces the glyphs, with the noise slowly changing.",
            "LIQUID",
            after='<svg width="0" height="0" aria-hidden="true"><filter id="warp"><feTurbulence type="fractalNoise" baseFrequency="0.012 0.04" numOctaves="2" seed="3"><animate attributeName="baseFrequency" dur="6s" values="0.012 0.04;0.02 0.07;0.012 0.04" repeatCount="indefinite"/></feTurbulence><feDisplacementMap in="SourceGraphic" scale="14"/></filter></svg>',
        ),
        text(
            "Text wave",
            PIECES
            + ".tx span { animation: wave 1.6s ease-in-out infinite; animation-delay: calc(var(--i) * 70ms); }\n@keyframes wave { 0%, 60%, 100% { translate: 0 0; } 30% { translate: 0 -.3em; } }\n@media (prefers-reduced-motion: reduce) { .tx span { animation: none; } }\n",
            "A ripple travels along the letters, each lifting slightly after its neighbour.",
            "Wavelength",
            SPLIT + 'split(document.querySelector(".tx"), "");\n',
        ),
        text(
            "Text bounce",
            PIECES
            + ".tx.go span { animation: drop .8s both; animation-delay: calc(var(--i) * 55ms); }\n@keyframes drop { 0% { translate: 0 -1.6em; opacity: 0; animation-timing-function: ease-in; } 45% { translate: 0 0; opacity: 1; animation-timing-function: ease-out; } 65% { translate: 0 -.35em; animation-timing-function: ease-in; } 82% { translate: 0 0; animation-timing-function: ease-out; } 92% { translate: 0 -.1em; } 100% { translate: 0 0; } }\n",
            "Letters fall into the line and bounce to rest, one after another.",
            "Bounce!",
            SPLIT + REPLAY + 'split(element, "");\nplay();\n',
            replay=True,
        ),
        text(
            "Text stretch",
            ".tx { font-size: 46px; cursor: pointer; transition: letter-spacing .5s var(--ease), scale .5s var(--ease); }\n.tx:hover, .tx:focus-visible { letter-spacing: .35em; scale: 1 1.25; }\n",
            "Hovering pulls the word wide and tall.",
            "STRETCH",
            attrs=' tabindex="0"',
        ),
        text(
            "Text morph",
            ".morph { position: relative; height: 1.2em; width: 100%; filter: url(#goo); }\n.morph span { position: absolute; inset: 0; text-align: center; }\n",
            "One word melts into the next: both are blurred as they cross and a threshold filter fuses the shapes.",
            '<span class="morph"><span></span><span></span></span>',
            CALM
            + 'const WORDS = ["Design", "Build", "Ship", "Repeat"];\nconst [a, b] = document.querySelectorAll(".morph span");\ndocument.querySelector(".tx").setAttribute("aria-label", WORDS.join(", "));\nconst HOLD = 1200, MORPH = 900;\nlet index = 0, started = performance.now();\nconst setBlend = (t) => {\n  // As one word sharpens the other blurs away; the alpha threshold in the filter fuses them in between.\n  b.style.filter = `blur(${Math.min(8 / Math.max(t, 0.001) - 8, 100)}px)`; b.style.opacity = `${Math.pow(t, 0.4) * 100}%`;\n  a.style.filter = `blur(${Math.min(8 / Math.max(1 - t, 0.001) - 8, 100)}px)`; a.style.opacity = `${Math.pow(1 - t, 0.4) * 100}%`;\n};\nconst show = () => { a.textContent = WORDS[index % WORDS.length]; b.textContent = WORDS[(index + 1) % WORDS.length]; };\nconst frame = (now) => {\n  const elapsed = now - started;\n  if (elapsed > HOLD + MORPH) { index += 1; started = now; show(); }\n  setBlend(calm ? 0 : Math.max(0, (elapsed - HOLD) / MORPH));\n  requestAnimationFrame(frame);\n};\nshow();\nrequestAnimationFrame(frame);\n',
            after='<svg width="0" height="0" aria-hidden="true"><filter id="goo"><feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 255 -140"/></filter></svg>',
        ),
        text(
            "Text scramble-to-normal",
            ".tx { font-family: var(--mono); font-size: 28px; }\n",
            "Begins as noise and clears up in random order until the message can be read.",
            "Order from chaos",
            SCRAMBLE
            + 'const GLYPHS = "!<>-_\\\\/[]{}=+*^?#";\nconst start = () => {\n  // A random order in which positions become correct.\n  const order = [...FINAL].map((_, i) => i).sort(() => Math.random() - 0.5);\n  const rank = new Map(order.map((position, i) => [position, i]));\n  run((step) => [...FINAL].map((char, i) => (char === " " || rank.get(i) < step / 2 ? char : random(GLYPHS))).join(""));\n};\ndocument.querySelector(".replay").addEventListener("click", start);\nstart();\n',
            replay=True,
        ),
        text(
            "Text blur-to-sharp",
            ".tx.go { animation: focus 1.1s var(--ease) both; }\n@keyframes focus { from { filter: blur(18px); opacity: 0; letter-spacing: .3em; } }\n",
            "The whole line pulls into focus while its letters draw together.",
            "Coming into focus",
            REPLAY + "play();\n",
            replay=True,
        ),
        text(
            "Text mask reveal",
            '@property --m { syntax: "<percentage>"; inherits: false; initial-value: 120%; }\n.tx { mask: linear-gradient(100deg, #000 calc(var(--m) - 20%), transparent var(--m)); }\n.tx.go { animation: wipe 1.1s var(--ease) both; }\n@keyframes wipe { from { --m: 0%; } }\n',
            "A slanted, soft-edged wipe uncovers the text.",
            "Revealed by a mask",
            REPLAY + "play();\n",
            replay=True,
        ),
        text(
            "Text clipping reveal",
            ".tx { clip-path: inset(0 0 0 0); }\n.tx span { display: block; }\n.tx.go span { animation: up .8s var(--ease) both; }\n@keyframes up { from { translate: 0 110%; } }\n",
            "The line rises through a hard clipping edge, as if from behind the baseline.",
            "<span>Rising into view</span>",
            REPLAY + "play();\n",
            replay=True,
        ),
        text(
            "Text split reveal",
            ".tx { position: relative; font-size: 46px; cursor: pointer; }\n.tx .top, .tx .bot { display: block; transition: translate .5s var(--ease); }\n.tx .top { clip-path: inset(0 0 50% 0); }\n.tx .bot { position: absolute; inset: 0; clip-path: inset(50% 0 0 0); }\n.tx .in { position: absolute; inset: 0; display: grid; place-items: center; font-size: 16px; font-weight: 600; letter-spacing: .2em; color: var(--accent); scale: 1 0; transition: scale .4s var(--ease); }\n.tx:hover .top, .tx:focus-visible .top { translate: 0 -34%; }\n.tx:hover .bot, .tx:focus-visible .bot { translate: 0 34%; }\n.tx:hover .in, .tx:focus-visible .in { scale: 1 1; }\n",
            "The word is cut along its middle; the halves part to show a second line between them.",
            '<span class="top" aria-hidden="true">OPEN UP</span><span class="bot" aria-hidden="true">OPEN UP</span><span class="in">THERE IS MORE INSIDE</span>',
            attrs=' tabindex="0" aria-label="Open up: there is more inside"',
        ),
        text(
            "Text kinetic typography",
            ".tx { font-size: 58px; height: 1.2em; }\n.tx span { display: inline-block; }\n.k0 { animation: k-pop .5s var(--ease) both; }\n.k1 { animation: k-slide .5s var(--ease) both; color: var(--accent); }\n.k2 { animation: k-spin .6s var(--ease) both; font-style: italic; }\n.k3 { animation: k-slam .45s cubic-bezier(.2, 1.6, .4, 1) both; color: var(--primary); letter-spacing: .08em; }\n@keyframes k-pop { from { scale: 0; } }\n@keyframes k-slide { from { translate: -1.5em 0; opacity: 0; } }\n@keyframes k-spin { from { rotate: -200deg; scale: .2; opacity: 0; } }\n@keyframes k-slam { from { scale: 4; opacity: 0; } }\n",
            "Words appear in rhythm, each with its own entrance and styling: type as animation.",
            "",
            CALM
            + 'const BEATS = [["Make", 0], ["it", 1], ["move", 2], ["NOW.", 3]];\nconst element = document.querySelector(".tx");\nelement.setAttribute("aria-label", BEATS.map(([word]) => word).join(" "));\nlet beat = 0;\nconst next = () => {\n  const [word, style] = BEATS[beat % BEATS.length];\n  const piece = Object.assign(document.createElement("span"), { textContent: word, className: calm ? "" : `k${style}` });\n  piece.setAttribute("aria-hidden", "true");\n  element.replaceChildren(piece);  // one word on screen at a time, on the beat\n  beat += 1;\n};\nnext();\nsetInterval(next, calm ? 1400 : 700);\n',
        ),
    ),
)
