"""Effects 101-120: exit animations."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import REPLAY_BTN, REPLAY_CSS, animated, staged

CLIP = ".stage { overflow: hidden; }\n"
DEEP = ".stage { perspective: 800px; }\n"
# Exits accelerate away (ease-in): the opposite of entrances.
OUT = "cubic-bezier(.5, 0, .9, .4)"


def leave(
    name: str,
    end: str,
    note: str,
    seconds: float = 0.5,
    ease: str = OUT,
    extra: str = "",
    origin: str = "",
) -> Item:
    """An exit defined by where the element ends up; ``both`` keeps it gone afterwards."""
    rule = f"animation: leave {seconds}s {ease} .5s both;" + (
        f" transform-origin: {origin};" if origin else ""
    )
    return animated(name, rule, f"@keyframes leave {{ to {{ {end} }} }}", note, extra=extra)


def keyed(
    name: str, frames: str, note: str, seconds: float = 0.8, ease: str = "linear", extra: str = ""
) -> Item:
    return animated(
        name,
        f"animation: leave {seconds}s {ease} .5s both;",
        f"@keyframes leave {{ {frames} }}",
        note,
        extra=extra,
    )


SECTION = Section(
    "effects",
    "Exit Animations",
    101,
    (
        leave("Fade out", "opacity: 0;", "Simply stops being there.", 0.35, "ease-in"),
        leave("Fade downward", "opacity: 0; translate: 0 26px;", "Sinks as it fades: dismissed."),
        leave(
            "Fade upward",
            "opacity: 0; translate: 0 -26px;",
            "Lifts as it fades: sent or completed.",
        ),
        leave("Fade left", "opacity: 0; translate: -34px 0;", "Leaves toward the left."),
        leave("Fade right", "opacity: 0; translate: 34px 0;", "Leaves toward the right."),
        leave(
            "Scale out",
            "opacity: 0; scale: .85;",
            "Shrinks slightly as it fades: the mirror of scale in.",
            0.3,
        ),
        leave("Zoom out", "opacity: 0; scale: 0;", "Recedes to a point."),
        leave("Slide out", "translate: 170% 0;", "Travels off-stage with no fade.", extra=CLIP),
        leave(
            "Blur out", "opacity: 0; filter: blur(16px);", "Goes out of focus and disappears.", 0.6
        ),
        leave(
            "Rotate out", "opacity: 0; rotate: 120deg; scale: .6;", "Spins away while shrinking."
        ),
        leave(
            "Flip out",
            "opacity: 0; transform: rotateX(90deg);",
            "Tips back until it is edge-on.",
            extra=DEEP,
        ),
        leave(
            "Fold out",
            "opacity: 0; transform: rotateX(-100deg);",
            "Folds up against its top edge.",
            extra=DEEP,
            origin="50% 0",
        ),
        leave(
            "Collapse out", "scale: 1.6 .04; opacity: 0;", "Flattens into a line that fades.", 0.5
        ),
        keyed(
            "Shrink away",
            "60% { scale: .5; opacity: 1; } 100% { scale: .5; opacity: 0; translate: 0 60px; }",
            "Shrinks first, then drops out of view.",
            0.7,
            "ease-in",
        ),
        leave(
            "Stretch away",
            "scale: 2.4 .1; opacity: 0; filter: blur(4px);",
            "Pulled thin sideways until nothing is left.",
            0.5,
        ),
        keyed(
            "Elastic exit",
            "20% { scale: 1.12; } 100% { scale: 0; opacity: 0; }",
            "Draws back a little first, then snaps away.",
            0.6,
            "ease-in",
        ),
        keyed(
            "Bounce exit",
            "0% { translate: 0 0; animation-timing-function: ease-out; } 25% { translate: 0 -34px; animation-timing-function: ease-in; } 45% { translate: 0 0; animation-timing-function: ease-out; } 60% { translate: 0 -12px; animation-timing-function: ease-in; } 100% { translate: 0 260px; opacity: 0; }",
            "A hop or two, then it falls out of the frame.",
            1.0,
            extra=CLIP,
        ),
        leave(
            "Spring exit",
            "scale: 0; opacity: 0;",
            "A spring wound backwards: it swells before collapsing.",
            0.7,
            "linear(0, -.14 24%, -.05 40%, .3 62%, 1)",
        ),
        leave(
            "Dissolve",
            "opacity: 0; filter: blur(8px) saturate(0); scale: 1.05; letter-spacing: .3em;",
            "Loses colour and focus and thins out, as if evaporating.",
            0.9,
            "ease-in",
        ),
        staged(
            "Particle dissolve",
            '<div class="fx">Particle dissolve</div>' + REPLAY_BTN,
            REPLAY_CSS
            + ".stage { overflow: visible; }\n.fx { position: relative; }\n.fx.gone { visibility: hidden; }\n.grain { position: absolute; background: var(--surface-2); border-radius: 2px; animation: scatter 1s cubic-bezier(.3, .6, .4, 1) forwards; animation-delay: var(--d); }\n@keyframes scatter { to { translate: var(--tx) var(--ty); opacity: 0; scale: .2; } }\n",
            "The element is replaced by a grid of fragments that drift away from one side to the other.",
            """\
const stage = document.querySelector(".stage");
const target = stage.querySelector(".fx");
const COLS = 14, ROWS = 8;
const play = () => {
  stage.querySelectorAll(".grain").forEach((grain) => grain.remove());
  target.classList.remove("gone");
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  setTimeout(() => {
    const box = target.getBoundingClientRect(), frame = stage.getBoundingClientRect();
    const w = box.width / COLS, h = box.height / ROWS;
    for (let row = 0; row < ROWS; row += 1) for (let col = 0; col < COLS; col += 1) {
      const grain = document.createElement("i");
      grain.className = "grain";
      Object.assign(grain.style, { left: `${box.left - frame.left + col * w}px`, top: `${box.top - frame.top + row * h}px`, width: `${w + 0.5}px`, height: `${h + 0.5}px` });
      // Fragments leave in a wave from left to right, drifting up and to the right.
      grain.style.setProperty("--d", `${(col / COLS) * 0.5 + Math.random() * 0.1}s`);
      grain.style.setProperty("--tx", `${30 + Math.random() * 70}px`);
      grain.style.setProperty("--ty", `${-20 - Math.random() * 60}px`);
      grain.addEventListener("animationend", () => grain.remove());
      stage.append(grain);
    }
    target.classList.add("gone");
  }, 500);
};
document.querySelector(".replay").addEventListener("click", play);
play();
""",
        ),
    ),
)
