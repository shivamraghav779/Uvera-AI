"""Effects 231-250: shadows and depth."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import staged, target

# Shadows need a light surface to fall on, so this section uses a pale stage.
LIGHT = ".stage { border-radius: 18px; background: #e8eaf1; color: #0f172a; }\n.fx { border: 0; background: #fff; color: #0f172a; }\n"
DARK = ".stage { border-radius: 18px; background: #0b0b14; }\n"
INK = "15 23 42"  # the shadow colour: a blue-black reads better than pure black


def shade(
    name: str,
    rule: str,
    note: str,
    extra: str = "",
    label: str = "",
    js: str = "",
    inner: str = "",
    surface: str = LIGHT,
) -> Item:
    body = inner or target(label or name)
    return staged(name, body, surface + (f".fx {{ {rule} }}\n" if rule else "") + extra, note, js)


# A long shadow is one hard shadow per pixel of length.
LONG = ", ".join(f"{step}px {step}px 0 #c7cbd9" for step in range(1, 41))
ELEVATION = (
    f"0 0 0 1px rgb({INK} / .06)",
    f"0 1px 2px rgb({INK} / .1), 0 1px 3px rgb({INK} / .08)",
    f"0 4px 8px rgb({INK} / .1), 0 2px 4px rgb({INK} / .06)",
    f"0 12px 24px rgb({INK} / .14), 0 4px 8px rgb({INK} / .06)",
    f"0 28px 56px rgb({INK} / .22), 0 8px 16px rgb({INK} / .08)",
)

SECTION = Section(
    "effects",
    "Shadow & Depth Effects",
    231,
    (
        shade(
            "Soft shadow",
            f"box-shadow: 0 12px 32px rgb({INK} / .14);",
            "A large blur, a small offset and low opacity: the default shadow for cards.",
        ),
        shade(
            "Hard shadow",
            "border: 2px solid #0f172a; border-radius: 10px; box-shadow: 6px 6px 0 #0f172a;",
            "No blur at all: a solid offset copy, as in print and neo-brutalist layouts.",
        ),
        shade(
            "Long shadow",
            "",
            "A flat-design shadow running off at 45 degrees: forty stacked one-pixel steps, clipped by the tile.",
            f".tile {{ display: grid; place-items: center; width: 150px; height: 150px; overflow: hidden; border-radius: 30px; background: #7c5cff; color: #fff; font-size: 76px; font-weight: 800; text-shadow: {LONG.replace('#c7cbd9', '#5b3fd9')}; }}\n",
            inner='<div class="tile" aria-label="Long shadow">A</div>',
        ),
        shade(
            "Ambient shadow",
            f"box-shadow: 0 0 44px rgb({INK} / .16);",
            "No offset: light from everywhere, so the shadow is an even halo on all sides.",
        ),
        shade(
            "Inner shadow",
            f"background: #dfe2ec; box-shadow: inset 0 3px 8px rgb({INK} / .22), inset 0 -1px 0 rgb(255 255 255 / .9);",
            "An inset shadow presses the surface into the page: wells, tracks and input fields.",
        ),
        shade(
            "Outer glow",
            "background: var(--surface); color: var(--fg); box-shadow: 0 0 0 1px rgb(124 92 255 / .7), 0 0 34px rgb(124 92 255 / .65);",
            "A shadow used as light: no offset, a saturated colour, on a dark surface.",
            surface=DARK,
        ),
        shade(
            "Colored shadow",
            "background: #7c5cff; color: #fff; box-shadow: 0 18px 34px -10px rgb(124 92 255 / .75);",
            "The shadow takes the element's own colour, as if light passed through it. The negative spread keeps it narrower than the element.",
        ),
        shade(
            "Gradient shadow",
            "position: relative; background: #fff;",
            "box-shadow takes one colour, so the shadow here is a blurred gradient copy placed underneath.",
            '.fx::before { content: ""; position: absolute; inset: 10px 6px -12px; z-index: -1; border-radius: inherit; background: linear-gradient(90deg, #7c5cff, #22d3ee, #f472b6); filter: blur(18px); opacity: .85; }\n.stage { isolation: isolate; }\n',
        ),
        shade(
            "Dynamic shadow",
            f"box-shadow: calc(var(--sx, 0) * 1px) calc(var(--sy, 14) * 1px) 30px rgb({INK} / .22); transition: box-shadow .08s linear;",
            "The pointer is the light: the shadow is thrown to the opposite side and lengthens as the pointer moves away.",
            label="Move the light",
            js='const stage = document.querySelector(".stage");\nconst card = stage.querySelector(".fx");\nstage.addEventListener("pointermove", (event) => {\n  const box = card.getBoundingClientRect();\n  card.style.setProperty("--sx", ((box.left + box.width / 2 - event.clientX) / 6).toFixed(1));\n  card.style.setProperty("--sy", ((box.top + box.height / 2 - event.clientY) / 6).toFixed(1));\n});\n',
        ),
        shade(
            "Directional shadow",
            f"box-shadow: 14px 18px 28px rgb({INK} / .2), inset 1px 1px 0 #fff, inset -1px -1px 0 rgb({INK} / .08);",
            "One consistent light, here upper left: shadow falls lower right, and the lit and unlit edges agree with it.",
        ),
        shade(
            "Floating shadow",
            "animation: hover 3s ease-in-out infinite alternate;",
            "The shadow is separate from the object: as the object rises, the shadow on the ground shrinks and fades.",
            f".ground {{ position: absolute; bottom: 34px; width: 170px; height: 16px; border-radius: 50%; background: rgb({INK} / .3); filter: blur(8px); animation: ground 3s ease-in-out infinite alternate; }}\n@keyframes hover {{ from {{ translate: 0 0; }} to {{ translate: 0 -26px; }} }}\n@keyframes ground {{ from {{ scale: 1; opacity: 1; }} to {{ scale: .7; opacity: .45; }} }}\n",
            inner='<div class="fx">Floating shadow</div><i class="ground"></i>',
        ),
        shade(
            "Hover shadow",
            f"box-shadow: {ELEVATION[1]}; transition: box-shadow .25s var(--ease), translate .25s var(--ease);",
            "At rest it barely leaves the page; on hover it rises and the shadow deepens to match.",
            f".fx:hover, .fx:focus-visible {{ translate: 0 -4px; box-shadow: {ELEVATION[3]}; }}\n",
            label="Hover me",
        ),
        shade(
            "Press shadow",
            f"box-shadow: {ELEVATION[3]}; transition: box-shadow .1s, translate .1s;",
            "Pressing pushes it down onto the surface: the shadow tightens to almost nothing.",
            f".fx:active {{ translate: 0 3px; box-shadow: {ELEVATION[1]}; }}\n",
            inner='<button class="fx">Press me</button>',
        ),
        shade(
            "Layered shadow",
            f"box-shadow: 0 1px 1px rgb({INK} / .07), 0 2px 2px rgb({INK} / .07), 0 4px 4px rgb({INK} / .07), 0 8px 8px rgb({INK} / .07), 0 16px 16px rgb({INK} / .07), 0 32px 32px rgb({INK} / .07);",
            "Six shadows, each double the last: tight and dark near the edge, wide and faint further out, as real shadows are.",
        ),
        shade(
            "Multi-level shadow",
            "",
            "An elevation scale: the same surface at four heights, each with a consistent step in offset and blur.",
            ".levels { display: flex; gap: 22px; }\n.levels div { display: grid; place-items: center; width: 84px; height: 84px; border-radius: 16px; background: #fff; font-weight: 700; }\n"
            + "".join(
                f".levels div:nth-child({level}) {{ box-shadow: {ELEVATION[level]}; }}\n"
                for level in range(1, 5)
            ),
            inner='<div class="levels"><div>1</div><div>2</div><div>3</div><div>4</div></div>',
        ),
        shade(
            "Perspective shadow",
            "position: relative; width: 150px;",
            "The shadow is a skewed, flattened copy lying on the ground behind the object, cast by a low light.",
            f'.fx::after {{ content: ""; position: absolute; inset: 0; z-index: -1; border-radius: inherit; background: rgb({INK} / .28); filter: blur(5px); transform-origin: 50% 100%; transform: skewX(-42deg) scaleY(.42); }}\n.stage {{ isolation: isolate; }}\n',
        ),
        shade(
            "Contact shadow",
            f"box-shadow: 0 1px 1px rgb({INK} / .35), 0 2px 3px rgb({INK} / .25), 0 22px 40px -14px rgb({INK} / .28);",
            "A thin dark line exactly where the object meets the surface anchors it; the soft wide shadow alone would leave it hovering.",
        ),
        shade(
            "Ambient occlusion",
            "",
            "Where two surfaces come close, less light gets in: a narrow darkening along the join, not a cast shadow.",
            f".well {{ position: relative; display: grid; place-items: center; width: 280px; height: 170px; border-radius: 22px; background: #e8eaf1; box-shadow: inset 0 0 22px rgb({INK} / .16), inset 0 0 3px rgb({INK} / .3); }}\n"
            f".block {{ display: grid; place-items: center; width: 150px; height: 84px; border-radius: 12px; background: #fff; font-weight: 600; box-shadow: 0 0 0 1px rgb({INK} / .05), 0 0 10px 1px rgb({INK} / .22); }}\n",
            inner='<div class="well"><div class="block">Occlusion</div></div>',
        ),
        shade(
            "Depth blur",
            "",
            "Depth of field: only one layer is in focus and the others blur with distance from it. Hover or focus a layer to refocus.",
            ".layer { position: absolute; display: grid; place-items: center; width: 140px; height: 96px; border-radius: 16px; font-weight: 700; color: #fff; outline: none; cursor: pointer; transition: filter .35s var(--ease), scale .35s var(--ease); }\n"
            ".layer:nth-child(1) { left: 8%; top: 12%; background: #94a3b8; scale: .8; filter: blur(5px); }\n"
            ".layer:nth-child(2) { left: 34%; top: 28%; background: #7c5cff; }\n"
            ".layer:nth-child(3) { left: 58%; top: 44%; background: #0f172a; scale: 1.15; filter: blur(5px); }\n"
            "/* Whichever layer is pointed at comes into focus; the rest lose it. */\n"
            ".stage:has(.layer:hover) .layer:not(:hover), .stage:has(.layer:focus-visible) .layer:not(:focus-visible) { filter: blur(5px); }\n"
            ".stage .layer:hover, .stage .layer:focus-visible { filter: none; }\n",
            inner='<div class="layer" tabindex="0">Far</div><div class="layer" tabindex="0">Focus</div><div class="layer" tabindex="0">Near</div>',
        ),
        shade(
            "Elevation transition",
            "transition: box-shadow .35s var(--ease), translate .35s var(--ease); box-shadow: var(--shadow-level); translate: 0 calc(var(--level) * -3px);",
            "Changing height is animated: each click moves the surface to the next level, and shadow and lift travel together.",
            "".join(
                f'.fx[data-level="{level}"] {{ --level: {level}; --shadow-level: {ELEVATION[level]}; }}\n'
                for level in range(5)
            ),
            inner='<button class="fx" data-level="1">Level 1 · click</button>',
            js='const card = document.querySelector(".fx");\ncard.addEventListener("click", () => {\n  const level = (Number(card.dataset.level) + 1) % 5;\n  card.dataset.level = level;\n  card.textContent = `Level ${level} · click`;\n});\n',
        ),
    ),
)
