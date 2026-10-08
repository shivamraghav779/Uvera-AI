"""Effects 121-150: scroll.

Most of these are *scroll-linked*: a number, ``--p``, says how far the element
has travelled through its scroller (0 entering, 1 leaving) and CSS turns that
number into the effect. ``--e`` is the same journey compressed so the effect is
complete around the middle of the view.
"""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import SCROLL_CSS, TARGET, scrolled

LONG = "".join(
    f"<p>{line}</p>"
    for line in [
        "Scroll this panel.",
        "Motion here follows the scroll position,",
        "not a clock.",
        "Stop, and it stops.",
        "Go back, and it rewinds.",
        "That is what scroll-linked means.",
        "Keep going.",
        "Nearly there.",
        "The end.",
    ]
)
PANEL = ".scroller { width: min(460px, 100%); height: 300px; overflow: auto; border: 1px solid var(--border); border-radius: 20px; background: var(--surface); outline: none; position: relative; }\n.scroller p { margin: 0; padding: 34px 28px; font-size: 20px; color: var(--muted); }\n"
RAF = 'let queued = false;\nconst onScroll = (run) => scroller.addEventListener("scroll", () => { if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; run(); }); } }, { passive: true });\n'
SPLIT_JS = """\
// Split the text into pieces, each knowing its place in the sequence.
const split = (element, pattern) => {
  const parts = element.textContent.split(pattern).filter((part) => part !== "");
  element.setAttribute("aria-label", element.textContent);  // read as one phrase, not piece by piece
  element.replaceChildren(...parts.map((part, i) => {
    const piece = Object.assign(document.createElement("span"), { textContent: part });
    piece.setAttribute("aria-hidden", "true");
    piece.style.setProperty("--i", i);
    return piece;
  }));
  element.style.setProperty("--n", parts.length);
};
"""
# Each piece lights up when the progress passes its share of the sequence.
PIECE_CSS = ".fx { width: 340px; height: auto; border: 0; background: none; font-size: 26px; line-height: 1.3; text-align: center; display: block; cursor: default; }\n.fx span { opacity: clamp(.12, calc(var(--e) * var(--n) * 1.15 - var(--i)), 1); }\n"


def panel(name: str, body: str, css: str, js: str, note: str) -> Item:
    return Item(
        name,
        f'<div class="scroller" tabindex="0">{body}</div>',
        PANEL + css,
        'const scroller = document.querySelector(".scroller");\n' + js,
        note,
    )


SECTION = Section(
    "effects",
    "Scroll Effects",
    121,
    (
        Item(
            "Scroll reveal",
            '<div class="scroller" tabindex="0"><div class="pad">Scroll down</div><div class="slot"><div class="fx">Revealed once</div></div><div class="slot"><div class="fx">And this</div></div><div class="pad">End</div></div>',
            SCROLL_CSS
            + TARGET
            + ".fx { opacity: 0; translate: 0 30px; transition: opacity .6s var(--ease), translate .6s var(--ease); }\n.fx.in { opacity: 1; translate: 0 0; }\n@media (prefers-reduced-motion: reduce) { .fx { opacity: 1; translate: 0 0; } }\n",
            'const scroller = document.querySelector(".scroller");\n// Fires once per element, the first time enough of it is on screen, then stops watching it.\nconst observer = new IntersectionObserver((entries) => {\n  for (const entry of entries) if (entry.isIntersecting) { entry.target.classList.add("in"); observer.unobserve(entry.target); }\n}, { root: scroller, threshold: 0.5 });\nscroller.querySelectorAll(".fx").forEach((element) => observer.observe(element));\n',
            "Not scroll-linked: an IntersectionObserver adds a class the first time the element is seen, and CSS does the rest.",
        ),
        scrolled(
            "Scroll fade",
            ".fx { opacity: var(--e); }\n",
            "Opacity follows the journey: transparent entering, solid by the middle.",
        ),
        scrolled(
            "Scroll slide",
            ".fx { translate: calc((1 - var(--e)) * -120px) 0; opacity: var(--e); }\n",
            "Slides in from the side as far as it has been scrolled.",
        ),
        scrolled(
            "Scroll scale",
            ".fx { scale: calc(.5 + var(--e) * .5); }\n",
            "Grows from half size to full as it comes in.",
        ),
        scrolled(
            "Scroll zoom",
            ".slot { overflow: hidden; }\n.fx { scale: calc(1 + var(--p) * 1.2); }\n",
            "Keeps enlarging all the way through, as if the camera moves toward it.",
            cls="pic",
            inner="",
        ),
        scrolled(
            "Scroll blur",
            ".fx { filter: blur(calc((1 - var(--e)) * 14px)); }\n",
            "Sharpens as it approaches the middle of the view.",
        ),
        scrolled(
            "Scroll rotate",
            ".fx { width: 120px; height: 120px; rotate: calc(var(--p) * 360deg); }\n",
            "One full turn over its whole journey.",
            inner="↻",
        ),
        scrolled(
            "Scroll parallax",
            ".fx { position: relative; overflow: hidden; }\n.fx b { position: absolute; inset: -40% 0; background: radial-gradient(circle at 50% 50%, rgb(255 255 255 / .5), transparent 30%); translate: 0 calc((var(--p) - .5) * -90px); }\n.fx span { position: relative; }\n",
            "A layer inside moves against the scroll, slower than the frame that holds it.",
            cls="pic",
            inner="<b></b><span>Parallax</span>",
        ),
        scrolled(
            "Scroll depth shift",
            ".fx { scale: calc(.86 + var(--e) * .14); box-shadow: 0 calc(var(--e) * 34px) calc(var(--e) * 60px) calc(var(--e) * -18px) rgb(0 0 0 / .9); }\n",
            "Rises off the page: larger, with a longer shadow, the further in it is.",
        ),
        scrolled(
            "Scroll perspective",
            ".slot { perspective: 700px; }\n.fx { transform: rotateX(calc((1 - var(--e)) * 70deg)); transform-origin: 50% 100%; opacity: calc(.3 + var(--e) * .7); }\n",
            "Tilted back when it enters and upright by the middle.",
        ),
        scrolled(
            "Scroll horizontal translation",
            ".slot { overflow: hidden; }\n.fx { width: max-content; height: auto; border: 0; background: none; font-size: 54px; font-weight: 800; white-space: nowrap; translate: calc((.5 - var(--p)) * 420px) 0; cursor: default; }\n",
            "Vertical scrolling moves a line of text sideways.",
            inner="Sideways · while · scrolling · down",
        ),
        scrolled(
            "Scroll vertical translation",
            ".fx { translate: 0 calc((var(--p) - .5) * 110px); }\n",
            "Drifts in the scroll direction, so it passes more slowly than the page.",
        ),
        scrolled(
            "Scroll opacity mapping",
            ".fx { opacity: calc(1 - max(var(--p) - .5, .5 - var(--p)) * 2); }\n",
            "Brightest at the centre of the view and fading toward both edges.",
        ),
        scrolled(
            "Scroll color transition",
            ".fx { border: 0; color: #fff; background: color-mix(in oklab, #7c5cff calc((1 - var(--p)) * 100%), #f472b6); }\n",
            "One colour at the bottom of the view, another at the top, mixed in between.",
        ),
        scrolled(
            "Scroll gradient transition",
            ".fx { border: 0; color: #fff; background: linear-gradient(calc(var(--p) * 360deg), #7c5cff, #22d3ee, #f472b6); }\n",
            "The gradient's angle is tied to the scroll position.",
        ),
        scrolled(
            "Scroll image zoom",
            ".fx { overflow: hidden; padding: 0; background: none; }\n.fx b { width: 100%; height: 100%; scale: calc(1.6 - var(--e) * .6); }\n",
            "The frame stays the same size while the picture inside it settles from zoomed-in.",
            inner='<b class="pic"></b>',
            js="",
        ),
        scrolled(
            "Scroll image pan",
            ".fx { border: 0; background: linear-gradient(90deg, #7c5cff, #22d3ee, #f472b6, #fbbf24, #34d399) calc(var(--p) * 100%) 0 / 300% 100%; }\n",
            "A picture wider than its frame slides across it as the page scrolls.",
            inner="",
        ),
        scrolled(
            "Scroll mask reveal",
            ".fx { mask: linear-gradient(90deg, #000 calc(var(--e) * 120% - 20%), transparent calc(var(--e) * 120%)); }\n",
            "A soft-edged wipe uncovers it from one side.",
            cls="pic",
            inner="Masked",
        ),
        scrolled(
            "Scroll clip-path reveal",
            ".fx { clip-path: circle(calc(var(--e) * 75%) at 50% 50%); }\n",
            "A circle opens from the centre until the whole element shows.",
            cls="pic",
            inner="Clipped",
        ),
        scrolled(
            "Scroll text reveal",
            ".fx { width: 360px; height: auto; border: 0; font-size: 34px; font-weight: 800; cursor: default; color: transparent; background: linear-gradient(90deg, var(--fg) calc(var(--e) * 100%), color-mix(in srgb, var(--fg) 18%, transparent) calc(var(--e) * 100%)); -webkit-background-clip: text; background-clip: text; }\n",
            "Text fills with colour from left to right as it is scrolled into view.",
            inner="Read as you scroll",
        ),
        scrolled(
            "Scroll character reveal",
            PIECE_CSS,
            "Characters light up one after another.",
            inner="Letter by letter",
            js=SPLIT_JS + 'split(document.querySelector(".fx"), "");\n',
        ),
        scrolled(
            "Scroll word reveal",
            PIECE_CSS,
            "Words light up one after another: the readable version of the same idea.",
            inner="Every word arrives in its own time",
            js=SPLIT_JS + 'split(document.querySelector(".fx"), /(\\s+)/);\n',
        ),
        scrolled(
            "Scroll line reveal",
            PIECE_CSS
            + ".fx span { display: block; translate: 0 calc((1 - clamp(0, calc(var(--e) * var(--n) * 1.15 - var(--i)), 1)) * 14px); }\n",
            "Whole lines rise and brighten in turn.",
            inner="First the opening line|then the middle one|and the last line.",
            js=SPLIT_JS + 'split(document.querySelector(".fx"), "|");\n',
        ),
        panel(
            "Scroll progress-linked animation",
            '<div class="bar"><i></i></div><svg class="ring" viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="16" pathLength="1"/></svg>'
            + LONG,
            ".bar { position: sticky; top: 0; z-index: 2; height: 4px; background: var(--surface-2); }\n.bar i { display: block; height: 100%; width: calc(var(--read, 0) * 100%); background: linear-gradient(90deg, var(--primary), var(--accent)); }\n.ring { position: sticky; top: 16px; float: right; margin: 12px; width: 44px; height: 44px; rotate: -90deg; }\n.ring circle { fill: none; stroke: var(--accent); stroke-width: 4; stroke-linecap: round; stroke-dasharray: 1; stroke-dashoffset: calc(1 - var(--read, 0)); }\n",
            RAF
            + 'const update = () => scroller.style.setProperty("--read", (scroller.scrollTop / (scroller.scrollHeight - scroller.clientHeight)).toFixed(4));\nonScroll(update);\nupdate();\n',
            "How far the container has been scrolled, 0 to 1, drives a reading bar and a ring.",
        ),
        panel(
            "Scroll velocity animation",
            LONG,
            ".scroller p { transform: skewY(calc(var(--v, 0) * 1deg)); transition: transform .2s ease-out; transform-origin: 0 50%; }\n",
            'let last = scroller.scrollTop, stamp = performance.now(), settle = null;\nscroller.addEventListener("scroll", () => {\n  const now = performance.now();\n  // Speed in pixels per millisecond, signed by direction and capped.\n  const velocity = (scroller.scrollTop - last) / Math.max(1, now - stamp);\n  last = scroller.scrollTop; stamp = now;\n  scroller.style.setProperty("--v", Math.max(-8, Math.min(8, velocity * 4)).toFixed(2));\n  clearTimeout(settle);\n  settle = setTimeout(() => scroller.style.setProperty("--v", "0"), 90);  // back to rest when scrolling stops\n}, { passive: true });\n',
            "The faster the scroll, the more the content leans; it straightens when the scrolling stops.",
        ),
        Item(
            "Scroll inertia",
            '<div class="frame" tabindex="0"><div class="track">' + LONG + "</div></div>",
            ".frame { width: min(460px, 100%); height: 300px; overflow: hidden; border: 1px solid var(--border); border-radius: 20px; background: var(--surface); outline: none; touch-action: none; }\n.track { will-change: transform; }\n.track p { margin: 0; padding: 34px 28px; font-size: 20px; color: var(--muted); }\n",
            'const frame = document.querySelector(".frame");\nconst track = frame.querySelector(".track");\nconst calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\nlet target = 0, current = 0;\nconst limit = () => track.scrollHeight - frame.clientHeight;\nconst move = (delta) => { target = Math.max(0, Math.min(limit(), target + delta)); };\nframe.addEventListener("wheel", (event) => { event.preventDefault(); move(event.deltaY); }, { passive: false });\nframe.addEventListener("keydown", (event) => { const step = { ArrowDown: 60, ArrowUp: -60, PageDown: 240, PageUp: -240 }[event.key]; if (step) { event.preventDefault(); move(step); } });\n// The position eases toward where the wheel asked it to be, so motion continues after the input stops.\nconst frameLoop = () => {\n  current += (target - current) * (calm ? 1 : 0.09);\n  track.style.transform = `translateY(${-current.toFixed(2)}px)`;\n  requestAnimationFrame(frameLoop);\n};\nframeLoop();\n',
            "Scrolling sets a destination and the content glides to it. It replaces native scrolling, so use it sparingly.",
        ),
        panel(
            "Scroll overshoot",
            LONG,
            ".scroller p { translate: 0 var(--push, 0px); }\n.scroller.rest p { transition: translate .7s linear(0, .55 12%, .98 25%, 1.14 36%, 1.05 48%, .97 60%, 1.01 76%, 1); }\n",
            'let last = scroller.scrollTop, timer = null;\nscroller.addEventListener("scroll", () => {\n  const delta = scroller.scrollTop - last;\n  last = scroller.scrollTop;\n  // While moving, content is dragged a little behind; when it stops, a spring returns it past zero and back.\n  scroller.classList.remove("rest");\n  scroller.style.setProperty("--push", `${Math.max(-26, Math.min(26, delta * 1.4))}px`);\n  clearTimeout(timer);\n  timer = setTimeout(() => { scroller.classList.add("rest"); scroller.style.setProperty("--push", "0px"); }, 80);\n}, { passive: true });\n',
            "Content trails the scroll and springs back past its place when the scrolling ends.",
        ),
        panel(
            "Scroll sticky transformation",
            '<header class="hd"><b>Northwind</b><span>Quarterly review</span></header>' + LONG,
            ".hd { position: sticky; top: 0; z-index: 2; display: flex; align-items: baseline; gap: 12px; padding: calc(24px - var(--s, 0) * 14px) 28px; background: color-mix(in srgb, var(--surface) calc(60% + var(--s, 0) * 35%), transparent); backdrop-filter: blur(calc(var(--s, 0) * 12px)); border-bottom: 1px solid color-mix(in srgb, var(--border) calc(var(--s, 0) * 100%), transparent); }\n.hd b { font-size: calc(30px - var(--s, 0) * 12px); }\n.hd span { color: var(--muted); opacity: calc(1 - var(--s, 0)); }\n",
            RAF
            + '// 0 at the top, 1 once the first 120px have been scrolled.\nconst update = () => scroller.style.setProperty("--s", Math.min(1, scroller.scrollTop / 120).toFixed(3));\nonScroll(update);\nupdate();\n',
            "A header that stays put but shrinks, frosts and gains a border over the first stretch of scrolling.",
        ),
        panel(
            "Scroll pinning",
            '<p>Scroll down.</p><section class="pin"><div class="held"><span class="step">1</span><h3></h3></div></section><p>Released: normal scrolling resumes.</p>',
            ".pin { height: 900px; }\n.held { position: sticky; top: 0; height: 298px; display: grid; place-items: center; align-content: center; gap: 12px; }\n.step { display: grid; place-items: center; width: 64px; height: 64px; border-radius: 50%; background: var(--primary); color: #fff; font-size: 24px; font-weight: 800; }\n.held h3 { margin: 0; font-size: 24px; }\n",
            RAF
            + 'const STEPS = ["Plan the work", "Build it", "Ship it"];\nconst pin = scroller.querySelector(".pin");\nconst update = () => {\n  // Progress through the tall section while its sticky child is held in view.\n  const progress = Math.min(0.999, Math.max(0, (scroller.scrollTop - pin.offsetTop) / (pin.offsetHeight - scroller.clientHeight)));\n  const index = Math.floor(progress * STEPS.length);\n  pin.querySelector(".step").textContent = String(index + 1);\n  pin.querySelector("h3").textContent = STEPS[index];\n};\nonScroll(update);\nupdate();\n',
            "A tall section holds a sticky child in place; the scroll distance steps through content instead of moving the page.",
        ),
        scrolled(
            "Scroll morphing",
            ".fx { width: calc(120px + var(--e) * 90px); height: 120px; border-radius: calc(60px - var(--e) * 42px); border: 0; color: #fff; background: color-mix(in oklab, #22d3ee calc((1 - var(--e)) * 100%), #7c5cff); }\n",
            "A circle becomes a rounded rectangle and changes colour along the way.",
            inner="",
        ),
    ),
)
