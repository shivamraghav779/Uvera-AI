"""Effects 71-100: entrance animations."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import animated

CLIP = ".stage { overflow: hidden; }\n"
DEEP = ".stage { perspective: 800px; }\n"


def enter(
    name: str,
    start: str,
    note: str,
    seconds: float = 0.6,
    ease: str = "var(--ease)",
    extra: str = "",
    origin: str = "",
) -> Item:
    """An entrance defined by where the element starts; it always ends at rest."""
    rule = f"animation: enter {seconds}s {ease} both;" + (
        f" transform-origin: {origin};" if origin else ""
    )
    return animated(name, rule, f"@keyframes enter {{ from {{ {start} }} }}", note, extra=extra)


def keyed(
    name: str,
    frames: str,
    note: str,
    seconds: float = 0.8,
    ease: str = "linear",
    extra: str = "",
    origin: str = "",
) -> Item:
    rule = f"animation: enter {seconds}s {ease} both;" + (
        f" transform-origin: {origin};" if origin else ""
    )
    return animated(name, rule, f"@keyframes enter {{ {frames} }}", note, extra=extra)


SECTION = Section(
    "effects",
    "Entrance Animations",
    71,
    (
        enter(
            "Fade in", "opacity: 0;", "Opacity alone: the quietest way to arrive.", 0.5, "ease-out"
        ),
        enter(
            "Fade up",
            "opacity: 0; translate: 0 24px;",
            "Fades while rising a short distance: the default for content.",
        ),
        enter(
            "Fade down",
            "opacity: 0; translate: 0 -24px;",
            "Fades while settling from above; suits things that drop from a header.",
        ),
        enter(
            "Fade left",
            "opacity: 0; translate: 32px 0;",
            "Fades in travelling leftwards, from the right.",
        ),
        enter(
            "Fade right",
            "opacity: 0; translate: -32px 0;",
            "Fades in travelling rightwards, from the left.",
        ),
        enter(
            "Scale in",
            "opacity: 0; scale: .85;",
            "Grows a little as it fades in: popovers and menus.",
            0.35,
        ),
        enter(
            "Scale up",
            "opacity: 0; scale: .4;",
            "Grows from its base, like something standing up.",
            origin="50% 100%",
        ),
        enter(
            "Scale down",
            "opacity: 0; scale: 1.35;",
            "Starts oversized and settles to its size, as if landing.",
        ),
        enter(
            "Slide in",
            "translate: -160% 0;",
            "Travels in from off-stage with no fade; the stage clips it.",
            extra=CLIP,
        ),
        enter("Slide down", "translate: 0 -220%;", "Enters from above the frame.", extra=CLIP),
        enter(
            "Slide up",
            "translate: 0 220%;",
            "Enters from below the frame: sheets and toasts.",
            extra=CLIP,
        ),
        enter(
            "Slide left",
            "translate: 160% 0;",
            "Enters from the right edge, moving left.",
            extra=CLIP,
        ),
        enter(
            "Slide right",
            "translate: -160% 0;",
            "Enters from the left edge, moving right.",
            extra=CLIP,
        ),
        enter("Zoom in", "scale: 0;", "Grows from a point to full size.", 0.5),
        enter(
            "Zoom out",
            "opacity: 0; scale: 2.4;",
            "The camera pulls back: it arrives from very close.",
            0.7,
        ),
        enter("Blur in", "opacity: 0; filter: blur(16px);", "Comes into focus as it appears.", 0.7),
        enter(
            "Blur out",
            "opacity: 0; filter: blur(22px); scale: 1.3;",
            "A wide soft glow that tightens into the element.",
            0.8,
        ),
        enter(
            "Rotate in",
            "opacity: 0; rotate: -120deg; scale: .6;",
            "Spins into place while growing.",
        ),
        enter(
            "Rotate out",
            "opacity: 0; rotate: 90deg;",
            "Swings in around its lower-left corner, like a hinged panel.",
            origin="0 100%",
        ),
        enter(
            "Flip in",
            "opacity: 0; transform: rotateX(-90deg);",
            "Tips up to face the viewer.",
            extra=DEEP,
        ),
        enter(
            "Flip horizontal",
            "transform: rotateY(-180deg); opacity: 0;",
            "Turns over around its vertical axis.",
            0.7,
            extra=DEEP,
        ),
        enter(
            "Flip vertical",
            "transform: rotateX(180deg); opacity: 0;",
            "Turns over around its horizontal axis.",
            0.7,
            extra=DEEP,
        ),
        enter(
            "Fold in",
            "transform: rotateX(-100deg); opacity: 0;",
            "Folds down from its top edge like a flap.",
            extra=DEEP,
            origin="50% 0",
        ),
        keyed(
            "Unfold in",
            "0% { clip-path: inset(0 0 100% 0); } 55% { clip-path: inset(0 0 50% 0); } 100% { clip-path: inset(0 0 0 0); }",
            "Opens downward in two stages, like a letter being unfolded.",
            0.7,
            "var(--ease)",
        ),
        enter(
            "Expand in",
            "clip-path: inset(50% 50% 50% 50% round 18px);",
            "Revealed outward from its centre.",
            0.6,
        ),
        enter(
            "Collapse in",
            "scale: 1.7 .04; opacity: .4;",
            "Begins as a wide line that draws in and gains its height.",
            0.6,
        ),
        enter(
            "Stretch in",
            "scale: 0 1;",
            "Extends sideways from its leading edge.",
            0.5,
            origin="0 50%",
        ),
        keyed(
            "Elastic in",
            "0% { scale: 0; } 55% { scale: 1.18; } 72% { scale: .92; } 86% { scale: 1.05; } 100% { scale: 1; }",
            "Overshoots and rings back to size like stretched rubber.",
            0.9,
            "ease-out",
        ),
        keyed(
            "Bounce in",
            "0% { translate: 0 -260px; animation-timing-function: ease-in; } 38% { translate: 0 0; animation-timing-function: ease-out; } 55% { translate: 0 -46px; animation-timing-function: ease-in; } 72% { translate: 0 0; animation-timing-function: ease-out; } 84% { translate: 0 -14px; animation-timing-function: ease-in; } 100% { translate: 0 0; }",
            "Drops in and bounces: ease-in on each fall, ease-out on each rise.",
            1.0,
            extra=CLIP,
        ),
        enter(
            "Spring in",
            "scale: .3; opacity: 0;",
            "A damped spring, expressed with the linear() easing function.",
            0.9,
            "linear(0, .55 12%, .98 25%, 1.14 36%, 1.05 48%, .97 60%, 1.01 76%, 1)",
        ),
    ),
)
