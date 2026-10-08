"""Effects 251-270: borders and edges."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import REPLAY_BTN, REPLAY_CSS, REPLAY_JS, staged, target

# An animatable angle, and the two-background trick behind every gradient border:
# the fill is painted to the padding box and the gradient to the border box.
ANGLE = '@property --a { syntax: "<angle>"; inherits: false; initial-value: 0deg; }\n'
FILL = "linear-gradient(var(--surface), var(--surface)) padding-box"
SPIN = "@keyframes spin { to { --a: 360deg; } }\n"
# An SVG rectangle laid exactly over the element, for borders that are drawn as strokes.
OUTLINE_SVG = (
    '<svg class="outline" aria-hidden="true"><rect x="1" y="1" rx="17" pathLength="100"/></svg>'
)
OUTLINE_CSS = ".fx { position: relative; border-color: transparent; }\n.outline { position: absolute; inset: -1px; width: calc(100% + 2px); height: calc(100% + 2px); overflow: visible; pointer-events: none; }\n.outline rect { width: calc(100% - 2px); height: calc(100% - 2px); fill: none; stroke: var(--accent); stroke-width: 2; }\n"


def edge(
    name: str,
    rule: str,
    note: str,
    extra: str = "",
    label: str = "",
    js: str = "",
    inner: str = "",
    replay: bool = False,
) -> Item:
    body = inner or target(label or name)
    css = (REPLAY_CSS if replay else "") + (f".fx {{ {rule} }}\n" if rule else "") + extra
    return staged(
        name, body + (REPLAY_BTN if replay else ""), css, note, js or (REPLAY_JS if replay else "")
    )


def outlined(label: str) -> str:
    return f'<div class="fx" tabindex="0">{label}{OUTLINE_SVG}</div>'


SECTION = Section(
    "effects",
    "Border & Edge Effects",
    251,
    (
        edge(
            "Animated border",
            "border: 0; background: linear-gradient(90deg, var(--accent) 50%, transparent 50%) 0 0 / 16px 2px repeat-x, linear-gradient(90deg, var(--accent) 50%, transparent 50%) 0 100% / 16px 2px repeat-x, linear-gradient(0deg, var(--accent) 50%, transparent 50%) 0 0 / 2px 16px repeat-y, linear-gradient(0deg, var(--accent) 50%, transparent 50%) 100% 0 / 2px 16px repeat-y, var(--surface); border-radius: 0; animation: march .6s linear infinite;",
            "Marching ants: four dashed strips, one per side, each sliding one dash length per loop so the dashes circulate.",
            "@keyframes march { to { background-position: 16px 0, -16px 100%, 0 -16px, 100% 16px; } }\n",
        ),
        edge(
            "Gradient border",
            f"border: 2px solid transparent; background: {FILL}, linear-gradient(135deg, #7c5cff, #22d3ee, #f472b6) border-box;",
            "A transparent border with the gradient painted underneath it; unlike border-image, this keeps the rounded corners.",
        ),
        edge(
            "Rainbow border",
            f"border: 3px solid transparent; background: {FILL}, conic-gradient(from var(--a), #ef4444, #f59e0b, #eab308, #22c55e, #06b6d4, #6366f1, #d946ef, #ef4444) border-box; animation: spin 5s linear infinite;",
            "The whole spectrum around the edge as a conic gradient, turning slowly.",
            ANGLE + SPIN,
        ),
        edge(
            "Glow border",
            "border-color: #a78bfa; box-shadow: 0 0 0 1px rgb(124 92 255 / .5), 0 0 18px rgb(124 92 255 / .7), inset 0 0 14px rgb(124 92 255 / .25);",
            "The border is the light source: glow spreads outward and a little inward.",
        ),
        edge(
            "Pulsing border",
            "border: 2px solid var(--primary); animation: throb 1.8s ease-in-out infinite alternate;",
            "The border itself brightens and dims in place: attention without movement.",
            "@keyframes throb { from { border-color: rgb(124 92 255 / .25); } to { border-color: #c4b5fd; box-shadow: 0 0 14px rgb(124 92 255 / .6); } }\n",
        ),
        edge(
            "Rotating border",
            f"border: 2px solid transparent; background: {FILL}, conic-gradient(from var(--a), transparent 0 70%, #22d3ee 88%, #fff 96%, transparent) border-box; animation: spin 3s linear infinite;",
            "A comet of light orbits the edge: a conic gradient that is mostly transparent, with its start angle animated.",
            ANGLE + SPIN,
        ),
        edge(
            "Moving border",
            "position: relative;",
            "A point of light travels along the border itself, following the rounded corners, by using the outline as a motion path.",
            '.fx::after { content: ""; position: absolute; left: 0; top: 0; width: 10px; height: 10px; border-radius: 50%; background: #fff; box-shadow: 0 0 10px 3px var(--accent), 0 0 24px 8px rgb(34 211 238 / .5); offset-path: inset(0 round 18px); offset-distance: 0%; animation: travel 4s linear infinite; }\n@keyframes travel { to { offset-distance: 100%; } }\n',
        ),
        edge(
            "Border sweep",
            f"border: 2px solid transparent; background: {FILL}, linear-gradient(100deg, var(--border) 40%, #fff 50%, var(--border) 60%) 100% 0 / 300% 100% border-box; transition: background-position .9s var(--ease);",
            "On hover a highlight crosses the border once from left to right.",
            ".fx:hover, .fx:focus-visible { background-position: 0 0, 0 0; }\n",
            label="Hover me",
        ),
        edge(
            "Border trace",
            "",
            "A short segment of stroke runs round the outline without end: a dash pattern with one dash, and its offset animated.",
            OUTLINE_CSS
            + ".outline rect { stroke-dasharray: 18 82; animation: trace 2.4s linear infinite; filter: drop-shadow(0 0 4px var(--accent)); }\n.fx { border-color: var(--border); }\n@keyframes trace { to { stroke-dashoffset: -100; } }\n",
            inner=outlined("Border trace"),
        ),
        edge(
            "Border draw",
            "",
            "The outline is drawn from nothing to complete, like a pen going round once. pathLength makes the dash maths independent of size.",
            OUTLINE_CSS
            + ".outline rect { stroke-dasharray: 100; stroke-dashoffset: 100; }\n.fx.go .outline rect { animation: draw 1.4s var(--ease) forwards; }\n@keyframes draw { to { stroke-dashoffset: 0; } }\n",
            inner=outlined("Border draw"),
            replay=True,
        ),
        edge(
            "Border dissolve",
            f"border: 2px solid transparent; background: {FILL}, conic-gradient(from -90deg, transparent var(--a), var(--accent) calc(var(--a) + 40deg)) border-box;",
            "The border is eaten away around the perimeter with a soft leading edge until none is left.",
            ANGLE
            + ".fx.go { animation: erase 1.6s .4s ease-in-out both; }\n@keyframes erase { from { --a: -40deg; } to { --a: 360deg; } }\n",
            replay=True,
        ),
        edge(
            "Border shimmer",
            f"border: 2px solid transparent; background: {FILL}, linear-gradient(100deg, #3b3566 30%, #c4b5fd 50%, #3b3566 70%) 0 0 / 250% 100% border-box; animation: glint 2.5s linear infinite;",
            "A band of light slides continuously through the border colour.",
            "@keyframes glint { from { background-position: 0 0, 150% 0; } to { background-position: 0 0, -100% 0; } }\n",
        ),
        edge(
            "Border pulse",
            "border-color: var(--primary); animation: ring 1.8s ease-out infinite;",
            "Rings leave the border and expand outward as they fade: a radar ping.",
            "@keyframes ring { from { box-shadow: 0 0 0 0 rgb(124 92 255 / .7); } to { box-shadow: 0 0 0 16px rgb(124 92 255 / 0); } }\n",
        ),
        edge(
            "Border highlight",
            f"border: 1px solid transparent; background: {FILL}, linear-gradient(rgb(255 255 255 / .5), rgb(255 255 255 / .06) 40%, rgb(255 255 255 / .04)) border-box;",
            "A one-pixel border that is bright at the top and fades down the sides, as if lit from above: the standard dark-mode card edge.",
        ),
        edge(
            "Border illumination",
            f"border: 1px solid transparent; background: {FILL}, radial-gradient(160px circle at var(--x, 50%) var(--y, -40px), #fff, var(--accent) 30%, var(--border) 70%) border-box;",
            "Only the part of the border nearest the pointer lights up, as if the pointer were a torch held to the edge.",
            label="Move near the edge",
            js='const stage = document.querySelector(".stage");\nconst card = stage.querySelector(".fx");\nstage.addEventListener("pointermove", (event) => {\n  const box = card.getBoundingClientRect();\n  card.style.setProperty("--x", `${event.clientX - box.left}px`);\n  card.style.setProperty("--y", `${event.clientY - box.top}px`);\n});\n',
        ),
        edge(
            "Neon edge",
            "border: 2px solid #fff; color: #fff; background: transparent; box-shadow: 0 0 4px #fff, 0 0 12px #f0abfc, 0 0 28px #d946ef, 0 0 56px #c026d3, inset 0 0 4px #fff, inset 0 0 12px #f0abfc, inset 0 0 28px rgb(217 70 239 / .5); text-shadow: 0 0 8px #f0abfc;",
            "A white-hot tube with coloured light falling off in layers on both sides.",
        ),
        edge(
            "Soft edge glow",
            "position: relative; border: 0;",
            "No visible border: a blurred gradient behind the element shows only as a soft rim of light.",
            '.fx::before { content: ""; position: absolute; inset: -2px; z-index: -1; border-radius: inherit; background: linear-gradient(135deg, #7c5cff, #22d3ee); filter: blur(12px); opacity: .8; }\n.stage { isolation: isolate; }\n',
        ),
        edge(
            "Gradient edge",
            "border: 0; border-radius: 0; background: linear-gradient(90deg, transparent, var(--accent), transparent) 50% 100% / 100% 2px no-repeat, linear-gradient(90deg, transparent, rgb(255 255 255 / .25), transparent) 50% 0 / 100% 1px no-repeat;",
            "Edges that fade out toward their ends instead of meeting at corners: section dividers and header underlines.",
        ),
        edge(
            "Dynamic radius",
            "transition: border-radius .45s var(--ease); border-radius: var(--r, 18px);",
            "The corner radius responds to the pointer: square when it is far away, fully round as it reaches the centre.",
            label="Come closer",
            js='const stage = document.querySelector(".stage");\nconst card = stage.querySelector(".fx");\nstage.addEventListener("pointermove", (event) => {\n  const box = card.getBoundingClientRect();\n  const distance = Math.hypot(event.clientX - box.left - box.width / 2, event.clientY - box.top - box.height / 2);\n  card.style.setProperty("--r", `${Math.max(0, 62 - distance / 2.5).toFixed(0)}px`);\n});\nstage.addEventListener("pointerleave", () => card.style.removeProperty("--r"));\n',
        ),
        edge(
            "Morphing corners",
            "animation: corners 8s ease-in-out infinite;",
            "Each corner has its own horizontal and vertical radius; animating all eight values makes the outline flow between shapes.",
            "@keyframes corners { 0%, 100% { border-radius: 18px; } 25% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; } 50% { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; } 75% { border-radius: 8px 60px 8px 60px; } }\n",
        ),
    ),
)
