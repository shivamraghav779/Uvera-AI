"""Effects 376-400: modals, drawers, sheets, popovers and tooltips."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.effects_07_background import GRAIN
from app.domains.references.vocabulary.fx import STAGE

# Easing curves written with linear(): a damped spring and a ball that bounces to rest.
SPRING = "linear(0, .55 12%, .98 25%, 1.14 36%, 1.05 48%, .97 60%, 1.01 76%, 1)"
BOUNCE = "linear(0, .06 9%, .25 18%, .56 27%, 1 36.4%, .81 45.5%, .77 50%, .81 54.5%, 1 63.6%, .94 72.7%, 1 81.8%, .98 90.9%, 1)"

# A miniature application: a page, a veil over it, and the layer that opens above both.
APP_CSS = """\
.app { overflow: hidden; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); }
.page { position: absolute; inset: 0; display: grid; align-content: start; justify-items: start; gap: 10px; padding: 20px; transition: all .35s var(--ease); }
.page h3 { margin: 0; }
.page p { margin: 0; color: var(--muted); font-size: 13px; }
.open, .close { padding: 8px 14px; border: 0; border-radius: 10px; background: var(--primary); color: #fff; font-weight: 600; }
.close { background: var(--surface); border: 1px solid var(--border); color: inherit; }
.veil { position: absolute; inset: 0; background: rgb(3 6 16 / .6); opacity: 0; pointer-events: none; transition: opacity .3s; }
.on .veil { opacity: 1; pointer-events: auto; }
.layer { position: absolute; display: grid; gap: 10px; justify-items: start; padding: 18px; background: var(--surface-2); border: 1px solid var(--border); box-shadow: 0 24px 60px rgb(0 0 0 / .5); visibility: hidden; }
.layer h4 { margin: 0; font-size: 15px; }
.layer p { margin: 0; color: var(--muted); font-size: 13px; }
"""
SHAPES = {
    "modal": ".layer { inset: 0; margin: auto; width: 250px; height: fit-content; border-radius: 16px; }\n",
    "drawer": ".layer { top: 0; right: 0; bottom: 0; width: 210px; align-content: start; border-width: 0 0 0 1px; }\n",
    "sheet": ".layer { left: 0; right: 0; bottom: 0; border-width: 1px 0 0; border-radius: 18px 18px 0 0; }\n",
}
TITLES = {"modal": "Delete project?", "drawer": "Filters", "sheet": "Share"}
PAGE_HTML = '<div class="page"><h3>Workspace</h3><p>The page underneath stays where it is.</p><button class="open">Open</button></div><div class="veil"></div>'
# Opening moves focus into the layer and makes the page inert; closing gives focus back
# to the button that opened it. Escape and a click on the veil both close.
APP_JS = """\
const app = document.querySelector(".app");
const page = app.querySelector(".page");
const opener = app.querySelector(".open");
const layer = app.querySelector(".layer");
const show = () => { app.classList.add("on"); page.inert = true; layer.querySelector(".close").focus({ preventScroll: true }); };
const hide = () => {
  if (!app.classList.contains("on")) return;
  app.classList.remove("on"); page.inert = false; opener.focus({ preventScroll: true });
};
opener.addEventListener("click", show);
layer.querySelector(".close").addEventListener("click", hide);
app.querySelector(".veil").addEventListener("click", hide);
app.addEventListener("keydown", (event) => { if (event.key === "Escape") hide(); });
show();  // the demo opens itself once so the effect is seen on load
"""
OPEN = "opacity: 1; translate: 0 0; scale: 1; rotate: 0deg; filter: none; visibility: visible;"


def overlay(
    name: str,
    kind: str,
    closed: str,
    note: str,
    extra: str = "",
    ease: str = "var(--ease)",
    seconds: float = 0.35,
    js: str = "",
    grip: bool = False,
) -> Item:
    """A layer described by its closed state; opening transitions every property back to rest.

    Closing always uses the plain ease and is quicker: springs and bounces are for arrivals.
    """
    title = TITLES[kind]
    handle = '<button class="grip" aria-label="Drag to resize or dismiss"></button>' if grip else ""
    html = (
        f'<div class="stage app">{PAGE_HTML}<div class="layer" role="dialog" aria-modal="true" aria-label="{title}">{handle}'
        f'<h4>{title}</h4><p>Escape, the button or the backdrop closes this.</p><button class="close">Close</button></div></div>'
    )
    css = (
        STAGE
        + APP_CSS
        + SHAPES[kind]
        + f".layer {{ {closed} transition: all .22s ease-in, visibility 0s .22s; }}\n"
        + f".on .layer {{ {OPEN} transition: all {seconds}s {ease}, visibility 0s; }}\n"
        + extra
    )
    return Item(name, html, css, APP_JS + js, note)


POP_CSS = """\
.anchor { position: relative; }
.trigger { padding: 9px 16px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); font-weight: 600; }
.pop { position: absolute; left: 0; top: calc(100% + 8px); display: grid; gap: 2px; width: 180px; padding: 6px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); box-shadow: 0 16px 40px rgb(0 0 0 / .5); visibility: hidden; }
.pop button { padding: 8px 10px; border: 0; border-radius: 8px; background: none; color: inherit; text-align: left; }
.pop button:hover, .pop button:focus-visible { background: var(--surface); outline: none; }
"""
POP_HTML = '<div class="stage"><div class="anchor"><button class="trigger" aria-haspopup="true" aria-expanded="false" aria-controls="menu">Options</button><div class="pop" id="menu"><button>Rename</button><button>Duplicate</button><button>Archive</button></div></div></div>'
POP_JS = """\
const anchor = document.querySelector(".anchor");
const trigger = anchor.querySelector(".trigger");
const set = (open) => { trigger.setAttribute("aria-expanded", open); if (open) anchor.querySelector(".pop button").focus({ preventScroll: true }); };
trigger.addEventListener("click", () => set(trigger.getAttribute("aria-expanded") !== "true"));
document.addEventListener("click", (event) => { if (!anchor.contains(event.target)) set(false); });
anchor.addEventListener("keydown", (event) => { if (event.key === "Escape") { set(false); trigger.focus(); } });
set(true);  // the demo opens itself once so the effect is seen on load
"""


def popover(
    name: str,
    closed: str,
    note: str,
    origin: str = "0 0",
    ease: str = "var(--ease)",
    seconds: float = 0.2,
) -> Item:
    css = (
        STAGE
        + ".stage { align-content: start; padding-top: 30px; }\n"
        + POP_CSS
        + f".pop {{ {closed} transform-origin: {origin}; transition: all .12s ease-in, visibility 0s .12s; }}\n"
        + f'.trigger[aria-expanded="true"] + .pop {{ {OPEN} transition: all {seconds}s {ease}, visibility 0s; }}\n'
    )
    return Item(name, POP_HTML, css, POP_JS, note)


TIP_CSS = """\
.tipped { position: relative; }
.tipped button { width: 44px; height: 44px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); font-size: 18px; }
.tip { position: absolute; left: 50%; bottom: calc(100% + 10px); padding: 6px 10px; border-radius: 8px; background: #f8fafc; color: #0f172a; font-size: 12px; font-weight: 600; white-space: nowrap; pointer-events: none; }
.tip::after { content: ""; position: absolute; left: 50%; top: 100%; margin-left: -5px; border: 5px solid transparent; border-top-color: #f8fafc; }
"""
TIP_HTML = '<div class="stage"><div class="tipped"><button aria-describedby="tip" aria-label="Copy link">⧉</button><span class="tip" id="tip" role="tooltip">Copy link</span></div></div>'


def tooltip(
    name: str, closed: str, note: str, ease: str = "var(--ease)", seconds: float = 0.18
) -> Item:
    """Shown on hover and on keyboard focus, after a short delay so that passing over does not trigger it."""
    css = (
        STAGE
        + TIP_CSS
        + f".tip {{ translate: -50% 0; transform-origin: 50% 100%; {closed} transition: all .1s ease-in; }}\n"
        + f".tipped:hover .tip, .tipped:focus-within .tip {{ opacity: 1; translate: -50% 0; scale: 1; transition: all {seconds}s {ease} .25s; }}\n"
    )
    return Item(name, TIP_HTML, css, "", note)


GRIP_CSS = '.grip { justify-self: center; width: 44px; height: 5px; margin: -6px 0 2px; padding: 0; border: 0; border-radius: 99px; background: var(--muted); cursor: grab; touch-action: none; }\n.grip::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 30px; }\n'

SECTION = Section(
    "effects",
    "Modal / Drawer Effects",
    376,
    (
        overlay(
            "Modal fade",
            "modal",
            "opacity: 0;",
            "Opacity only: the dialog is simply there. The least distracting choice.",
            seconds=0.25,
        ),
        overlay(
            "Modal scale",
            "modal",
            "opacity: 0; scale: .9;",
            "Grows a little as it fades in, so it seems to come forward from the page.",
        ),
        overlay(
            "Modal slide",
            "modal",
            "opacity: 0; translate: 0 40px;",
            "Rises into place from slightly below.",
        ),
        overlay(
            "Modal blur",
            "modal",
            "opacity: 0; filter: blur(14px); scale: 1.06;",
            "Comes into focus as it appears, settling from a touch too large.",
            seconds=0.45,
        ),
        overlay(
            "Modal zoom",
            "modal",
            "opacity: 0; scale: .1; transform-origin: 14% 62%;",
            "Expands out of the button that opened it: the transform origin is placed over the trigger.",
            ".on .layer { transform-origin: 14% 62%; }\n",
            seconds=0.4,
        ),
        overlay(
            "Modal spring",
            "modal",
            "opacity: 0; scale: .6;",
            "Overshoots its size and rings back, on a spring curve written with linear().",
            ease=SPRING,
            seconds=0.7,
        ),
        overlay(
            "Modal bounce",
            "modal",
            "translate: 0 -260px;",
            "Dropped in from above and bounces to rest.",
            ease=BOUNCE,
            seconds=0.9,
        ),
        overlay(
            "Modal backdrop blur",
            "modal",
            "opacity: 0; scale: .95;",
            "The page behind goes out of focus: the dialog separates from it without the screen getting much darker.",
            ".veil { background: rgb(3 6 16 / .25); backdrop-filter: blur(8px); }\n",
        ),
        overlay(
            "Modal backdrop dim",
            "modal",
            "opacity: 0; scale: .95;",
            "A plain dark scrim: the page is still recognisable but clearly out of play.",
            ".veil { background: rgb(3 6 16 / .8); }\n",
        ),
        overlay(
            "Modal backdrop gradient",
            "modal",
            "opacity: 0; scale: .95;",
            "The scrim is a coloured gradient, dark at the edges and tinted behind the dialog.",
            ".veil { background: radial-gradient(circle at 50% 50%, rgb(124 92 255 / .55), rgb(3 6 16 / .9) 75%); }\n",
        ),
        overlay(
            "Modal backdrop noise",
            "modal",
            "opacity: 0; scale: .95;",
            "Grain over a dim scrim gives the backdrop a frosted, physical surface.",
            f".veil {{ background: {GRAIN}, rgb(3 6 16 / .7); background-blend-mode: overlay; backdrop-filter: blur(3px); }}\n",
        ),
        overlay(
            "Drawer slide",
            "drawer",
            "translate: 100% 0;",
            "A panel enters from the edge it is attached to.",
        ),
        overlay(
            "Drawer spring",
            "drawer",
            "translate: 100% 0;",
            "The drawer overshoots a little past its stop and springs back. The extra width on its far side keeps a gap from showing.",
            ".layer { margin-right: -30px; padding-right: 48px; }\n",
            ease=SPRING,
            seconds=0.7,
        ),
        overlay(
            "Drawer bounce",
            "drawer",
            "translate: 100% 0;",
            "Slides in and rebounds off its stop a couple of times.",
            ease=BOUNCE,
            seconds=0.8,
        ),
        overlay(
            "Drawer blur",
            "drawer",
            "translate: 100% 0; opacity: 0;",
            "A translucent drawer: the page behind it blurs through the panel as it comes in.",
            ".layer { background: rgb(27 31 48 / .55); backdrop-filter: blur(16px) saturate(1.4); }\n.page { background: radial-gradient(circle at 80% 40%, rgb(34 211 238 / .5), transparent 40%), radial-gradient(circle at 60% 90%, rgb(244 114 182 / .5), transparent 40%); }\n",
        ),
        overlay(
            "Drawer expansion",
            "drawer",
            "translate: 100% 0;",
            "The drawer does not cover the page: the page shrinks back and aside to make room for it.",
            ".on .page { scale: .5; translate: 10px 0; border-radius: 22px; opacity: .7; }\n.veil { background: none; }\n.page { background: var(--surface); transform-origin: 0 50%; }\n.app { background: #05060c; }\n",
            seconds=0.4,
        ),
        overlay(
            "Bottom-sheet spring",
            "sheet",
            "translate: 0 100%;",
            "Comes up from the bottom edge and settles with a small overshoot. The extra padding below keeps a gap from showing.",
            ".layer { margin-bottom: -30px; padding-bottom: 48px; }\n",
            ease=SPRING,
            seconds=0.7,
        ),
        overlay(
            "Bottom-sheet drag",
            "sheet",
            "translate: 0 100%;",
            "The sheet follows the finger: drag the handle down and let go. Past a third of its height it dismisses; short of that it returns.",
            GRIP_CSS,
            js="""\
const grip = layer.querySelector(".grip");
let from = 0, offset = 0, dragging = false;
grip.addEventListener("pointerdown", (event) => {
  dragging = true; from = event.clientY;
  grip.setPointerCapture(event.pointerId);
  layer.style.transition = "none";  // follow the pointer exactly while dragging
});
grip.addEventListener("pointermove", (event) => {
  if (!dragging) return;
  offset = Math.max(0, event.clientY - from);
  layer.style.translate = `0 ${offset}px`;
});
const release = () => {
  if (!dragging) return;
  dragging = false;
  layer.style.transition = ""; layer.style.translate = "";  // hand back to the stylesheet, which animates the rest
  if (offset > layer.offsetHeight / 3) hide();
  offset = 0;
};
grip.addEventListener("pointerup", release);
grip.addEventListener("pointercancel", release);
grip.addEventListener("keydown", (event) => { if (event.key === "ArrowDown") hide(); });
""",
            grip=True,
        ),
        Item(
            "Bottom-sheet snap",
            '<div class="stage app"><div class="page"><h3>Map</h3><p>The sheet rests at one of three heights.</p></div>'
            '<div class="layer" role="region" aria-label="Places"><button class="grip" aria-label="Resize sheet: arrow up and down"></button><h4>Nearby places</h4><p>Peek, half and full.</p><p>Drag the handle and release: the sheet settles at whichever height is nearest.</p><p>More results appear at full height.</p></div></div>',
            STAGE
            + APP_CSS
            + SHAPES["sheet"]
            + GRIP_CSS
            + ".layer { visibility: visible; height: 230px; align-content: start; translate: 0 var(--y, 150px); transition: translate .35s "
            + SPRING
            + "; }\n",
            """\
const layer = document.querySelector(".layer");
const grip = layer.querySelector(".grip");
const SNAPS = [150, 80, 0];  // distance pushed down: peek, half, full
let current = 0, from = 0, start = 0, dragging = false;
const settle = (index) => { current = index; layer.style.setProperty("--y", `${SNAPS[index]}px`); };
const nearest = (y) => SNAPS.reduce((best, snap, index) => (Math.abs(snap - y) < Math.abs(SNAPS[best] - y) ? index : best), 0);
grip.addEventListener("pointerdown", (event) => {
  dragging = true; from = event.clientY; start = SNAPS[current];
  grip.setPointerCapture(event.pointerId);
  layer.style.transition = "none";
});
grip.addEventListener("pointermove", (event) => {
  if (!dragging) return;
  const y = Math.min(SNAPS[0], Math.max(0, start + event.clientY - from));
  layer.style.setProperty("--y", `${y}px`);
});
const release = () => {
  if (!dragging) return;
  dragging = false;
  layer.style.transition = "";
  settle(nearest(parseFloat(layer.style.getPropertyValue("--y"))));
};
grip.addEventListener("pointerup", release);
grip.addEventListener("pointercancel", release);
grip.addEventListener("keydown", (event) => {
  if (event.key === "ArrowUp") settle(Math.min(SNAPS.length - 1, current + 1));
  if (event.key === "ArrowDown") settle(Math.max(0, current - 1));
});
grip.addEventListener("click", () => { if (!dragging) settle((current + 1) % SNAPS.length); });
settle(1);
""",
            "A sheet with three resting heights. Drag and release and it springs to the nearest; a click or the arrow keys step through them.",
        ),
        popover(
            "Popover scale",
            "opacity: 0; scale: .85;",
            "Grows out of the corner nearest its trigger, so it visibly belongs to the button.",
        ),
        popover(
            "Popover fade",
            "opacity: 0;",
            "Appears in place with no movement: for dense interfaces where menus open constantly.",
            seconds=0.15,
        ),
        popover(
            "Popover slide",
            "opacity: 0; translate: 0 -10px;",
            "Drops a short way from the trigger as it fades in.",
        ),
        tooltip("Tooltip fade", "opacity: 0;", "Fades in after a short delay, and leaves at once."),
        tooltip(
            "Tooltip slide",
            "opacity: 0; translate: -50% 6px;",
            "Moves a few pixels away from its target as it appears, in the direction it points.",
        ),
        tooltip(
            "Tooltip spring",
            "opacity: 0; scale: .5;",
            "Pops out from its arrow tip with a springy overshoot.",
            ease=SPRING,
            seconds=0.5,
        ),
    ),
)
