"""Scaffolding shared by the effect entries.

An effect is shown on a neutral target so that the effect is the only thing
happening. The target, the stage and the few helpers below are repeated in
each entry; what differs between entries is the effect itself.
"""

from app.domains.references.vocabulary.base import Item

STAGE = ".stage { position: relative; display: grid; place-items: center; width: min(460px, 100%); height: 260px; }\n"
TARGET = (
    ".fx { display: grid; place-items: center; width: 210px; height: 124px; border: 1px solid var(--border); border-radius: 18px;\n"
    "  background: var(--surface); font-weight: 600; outline: none; cursor: pointer; user-select: none; }\n"
)
# A colourful tile, for effects that act on imagery (filters, masks, zooms).
PICTURE = (
    ".pic { background: radial-gradient(circle at 30% 30%, #f472b6, transparent 45%), radial-gradient(circle at 75% 65%, #22d3ee, transparent 50%),\n"
    "  linear-gradient(135deg, #312e81, #7c5cff); color: #fff; border: 0; }\n"
)
REPLAY_BTN = '<button class="replay">Replay</button>'
REPLAY_CSS = ".replay { position: absolute; bottom: 0; padding: 5px 14px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface-2); font-size: 13px; }\n"
# Restarts a CSS animation by removing and re-adding its class.
REPLAY_JS = """\
const target = document.querySelector(".fx");
const play = () => { target.classList.remove("go"); void target.offsetWidth; target.classList.add("go"); };
document.querySelector(".replay").addEventListener("click", play);
play();
"""
# Pointer position inside the stage, as pixels and as custom properties.
LOCAL_JS = """\
const stage = document.querySelector(".stage");
const local = (event) => { const box = stage.getBoundingClientRect(); return [event.clientX - box.left, event.clientY - box.top]; };
const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
"""
ON = ".fx:hover, .fx:focus-visible"


def target(label: str = "Hover me", cls: str = "", attrs: str = ' tabindex="0"') -> str:
    return f'<div class="fx {cls}"{attrs}>{label}</div>'


def staged(name: str, inner: str, css: str, note: str, js: str = "", base: str = TARGET) -> Item:
    return Item(name, f'<div class="stage">{inner}</div>', STAGE + base + css, js, note)


def hover(
    name: str,
    rest: str,
    active: str,
    note: str,
    cls: str = "",
    extra: str = "",
    label: str = "Hover me",
) -> Item:
    """An effect that is a resting state plus what changes on hover or focus."""
    change = f"{ON} {{ {active} }}\n" if active else ""
    css = f".fx {{ {rest} }}\n{change}{extra}"
    return staged(name, target(label, cls), (PICTURE if "pic" in cls else "") + css, note)


def press(
    name: str, rest: str, active: str, note: str, extra: str = "", label: str = "Press me"
) -> Item:
    change = f".fx:active {{ {active} }}\n" if active else ""
    css = f".fx {{ {rest} }}\n{change}{extra}"
    return staged(name, f'<button class="fx">{label}</button>', css, note)


def animated(
    name: str, rule: str, keyframes: str, note: str, label: str = "", cls: str = "", extra: str = ""
) -> Item:
    """A keyframe animation started by adding ``.go``, with a replay button."""
    css = (
        REPLAY_CSS
        + (PICTURE if "pic" in cls else "")
        + f".fx.go {{ {rule} }}\n{keyframes}\n{extra}"
    )
    return staged(name, target(label or name, cls) + REPLAY_BTN, css, note, REPLAY_JS)


def looping(name: str, inner: str, css: str, note: str, js: str = "") -> Item:
    """An effect that simply runs (loaders, backgrounds, ambient motion)."""
    return Item(name, f'<div class="stage">{inner}</div>', STAGE + css, js, note)


# Restarts the ``hit`` animation on every click and records where the click landed
# (--x, --y); a keyboard activation counts as the centre.
CLICK_JS = """\
const button = document.querySelector(".fx");
const hit = (event) => {
  const box = button.getBoundingClientRect();
  const pointer = event.clientX || event.clientY;
  button.style.setProperty("--x", `${pointer ? event.clientX - box.left : box.width / 2}px`);
  button.style.setProperty("--y", `${pointer ? event.clientY - box.top : box.height / 2}px`);
  button.classList.remove("hit");
  void button.offsetWidth;
  button.classList.add("hit");
};
button.addEventListener("click", hit);
"""
# Throws short-lived pieces out from a point; each removes itself when its animation ends.
BURST_JS = """\
const burst = (parent, x, y, count, build) => {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  for (let i = 0; i < count; i += 1) {
    const piece = document.createElement("i");
    piece.className = "bit";
    piece.style.left = `${x}px`; piece.style.top = `${y}px`;
    build(piece, i, count);
    piece.addEventListener("animationend", () => piece.remove());
    parent.append(piece);
  }
};
"""


def clicked(name: str, css: str, note: str, label: str = "Click me", js: str = "") -> Item:
    """An effect played each time the target is clicked."""
    return staged(name, f'<button class="fx">{label}</button>', css, note, CLICK_JS + js)


# --- Scroll-linked effects ----------------------------------------------------------

SCROLL_CSS = (
    ".scroller { width: min(460px, 100%); height: 300px; overflow: auto; border: 1px solid var(--border); border-radius: 20px; background: var(--surface); outline: none; }\n"
    ".pad { display: grid; place-items: center; height: 280px; color: var(--muted); font-size: 13px; }\n"
    ".slot { display: grid; place-items: center; height: 200px; }\n"
    # How far the element has come in: 0 entering at the bottom, 1 once a little past the middle.
    ".slot { --e: min(1, calc(var(--p, 0) * 2.2)); }\n"
)
# Writes --p on each slot: 0 as it enters at the bottom of the scroller, 1 as it leaves at the top.
# The slot (not the animated element) is measured, so the effect cannot disturb its own input.
SCROLL_JS = """\
const scroller = document.querySelector(".scroller");
const slots = [...scroller.querySelectorAll(".slot")];
const update = () => {
  const frame = scroller.getBoundingClientRect();
  for (const slot of slots) {
    const box = slot.getBoundingClientRect();
    const progress = (frame.bottom - box.top) / (frame.height + box.height);
    slot.style.setProperty("--p", Math.min(1, Math.max(0, progress)).toFixed(4));
  }
};
let queued = false;
scroller.addEventListener("scroll", () => {
  if (queued) return;
  queued = true;
  requestAnimationFrame(() => { queued = false; update(); });  // at most once per frame
}, { passive: true });
update();
"""


def scrolled(
    name: str, css: str, note: str, inner: str = "Scroll", cls: str = "", js: str = ""
) -> Item:
    """An effect driven by how far its element has travelled through the scroller."""
    html = (
        '<div class="scroller" tabindex="0"><div class="pad">Scroll down</div>'
        f'<div class="slot"><div class="fx {cls}">{inner}</div></div><div class="pad">Scroll back up</div></div>'
    )
    return Item(
        name,
        html,
        SCROLL_CSS + TARGET + (PICTURE if "pic" in cls else "") + css,
        SCROLL_JS + js,
        note,
    )


def pointer_js(area: str, target: str, measure: str = "") -> str:
    """Writes the pointer position onto ``target`` as --px/--py, each 0..1 across ``measure``.

    ``area`` is what listens. Measuring something other than the target matters
    when the target itself moves in response: it must not disturb its own input.
    """
    return f"""\
const area = document.querySelector("{area}");
const target = document.querySelector("{target}");
const measured = document.querySelector("{measure or target}");
const centre = () => {{ target.style.setProperty("--px", 0.5); target.style.setProperty("--py", 0.5); }};
area.addEventListener("pointermove", (event) => {{
  const box = measured.getBoundingClientRect();
  target.style.setProperty("--px", ((event.clientX - box.left) / box.width).toFixed(3));
  target.style.setProperty("--py", ((event.clientY - box.top) / box.height).toFixed(3));
}});
area.addEventListener("pointerleave", centre);
"""
