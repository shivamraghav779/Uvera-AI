"""Effects 326-350: cards."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import STAGE, pointer_js

ART = "radial-gradient(circle at 30% 30%, #f472b6, transparent 45%), radial-gradient(circle at 75% 65%, #22d3ee, transparent 50%), linear-gradient(135deg, #312e81, #7c5cff)"
BODY = '<div class="body"><h3>Aurora plan</h3><p>Everything a small team needs.</p></div>'
CARD_HTML = f'<article class="card" tabindex="0"><div class="art"></div>{BODY}</article>'
CARD_CSS = f"""\
.card {{ position: relative; width: 230px; overflow: hidden; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); outline: none; cursor: pointer; }}
.art {{ height: 92px; background: {ART}; }}
.body {{ padding: 14px 16px 16px; }}
.card h3 {{ margin: 0 0 4px; font-size: 15px; }}
.card p {{ margin: 0; color: var(--muted); font-size: 13px; }}
"""
ON = ".card:hover, .card:focus-visible"
EASE = "transition: all .3s var(--ease);"
DEFAULTS = "--px: .5; --py: .5;"


def card(
    name: str,
    rest: str,
    active: str,
    note: str,
    extra: str = "",
    html: str = CARD_HTML,
    js: str = "",
) -> Item:
    """A card effect: its resting declarations and what hover or focus changes."""
    css = (
        STAGE
        + CARD_CSS
        + (f".card {{ {rest} }}\n" if rest else "")
        + (f"{ON} {{ {active} }}\n" if active else "")
        + extra
    )
    return Item(name, f'<div class="stage">{html}</div>', css, js, note)


def stacked() -> str:
    return "".join(
        f'<article class="card" style="--n: {n}"><div class="art"></div><div class="body"><h3>Card {3 - n}</h3></div></article>'
        for n in (2, 1, 0)
    )


SECTION = Section(
    "effects",
    "Card Effects",
    326,
    (
        card(
            "Card lift",
            EASE,
            "translate: 0 -8px; box-shadow: 0 22px 40px rgb(0 0 0 / .45);",
            "Rises toward the viewer and its shadow deepens to match: the standard 'this is clickable'.",
        ),
        card(
            "Card tilt",
            EASE,
            "rotate: -2.5deg; translate: 0 -4px;",
            "A slight turn, as though picked up by one corner: informal and playful.",
        ),
        card(
            "Card rotate",
            EASE + " transform: perspective(800px);",
            "transform: perspective(800px) rotateY(-18deg);",
            "Swings on its vertical axis like a door ajar, showing it has a side.",
        ),
        card(
            "Card scale",
            EASE,
            "scale: 1.06;",
            "Simply gets a little bigger. Keep it small, or neighbours will be overlapped.",
        ),
        card(
            "Card glow",
            EASE,
            "border-color: var(--primary); box-shadow: 0 0 0 1px var(--primary), 0 0 36px rgb(124 92 255 / .55);",
            "Stays put and lights up: its edge and the space around it take the brand colour.",
        ),
        card(
            "Card shadow expansion",
            EASE + " box-shadow: 0 2px 6px rgb(0 0 0 / .3);",
            "box-shadow: 0 30px 60px -10px rgb(0 0 0 / .7), 0 0 0 1px rgb(255 255 255 / .06);",
            "Nothing moves except the shadow, which spreads wide: height suggested without displacement.",
        ),
        card(
            "Card border illumination",
            DEFAULTS
            + " border-color: transparent; background: linear-gradient(var(--surface), var(--surface)) padding-box, radial-gradient(200px circle at calc(var(--px) * 100%) calc(var(--py) * 100%), var(--accent), var(--border) 75%) border-box;",
            "",
            "The border is brightest where the pointer is nearest and falls back to the plain hairline elsewhere.",
            js=pointer_js(".stage", ".card"),
        ),
        card(
            "Card gradient shift",
            "border: 0; color: #fff; background: linear-gradient(120deg, #312e81, #7c5cff, #22d3ee, #f472b6) 0 0 / 300% 100%; transition: background-position .8s var(--ease);",
            "background-position: 100% 0;",
            "The card's own gradient slides to a different part of itself, so the colours change under the content.",
            ".art { display: none; }\n.card p { color: rgb(255 255 255 / .8); }\n.body { padding: 34px 20px; }\n",
        ),
        card(
            "Card background morph",
            "",
            "",
            "A soft shape in the background moves, grows and changes outline on hover, while the content stays still.",
            '.art { display: none; }\n.body { position: relative; padding: 40px 20px; }\n.card::before { content: ""; position: absolute; left: -20%; top: -30%; width: 70%; aspect-ratio: 1; border-radius: 60% 40% 55% 45% / 50% 60% 40% 50%; background: linear-gradient(135deg, #7c5cff, #f472b6); filter: blur(18px); opacity: .7; transition: all .8s var(--ease); }\n'
            + f"{ON.replace('.card:hover', '.card:hover::before').replace('.card:focus-visible', '.card:focus-visible::before')} {{ left: 45%; top: 20%; width: 90%; border-radius: 40% 60% 35% 65% / 60% 35% 65% 40%; background: linear-gradient(135deg, #22d3ee, #7c5cff); rotate: 80deg; }}\n",
        ),
        card(
            "Card image zoom",
            "",
            "",
            "The picture enlarges inside its frame; the frame clips it, so the card's own size does not change.",
            ".art { transition: scale .6s var(--ease); }\n.card:hover .art, .card:focus-visible .art { scale: 1.15; }\n",
        ),
        card(
            "Card image pan",
            "",
            "",
            "The picture is larger than its window and slides sideways on hover, as a slow camera move.",
            f".art {{ background: {ART}; background-size: 170% 100%; background-position: 0 0; transition: background-position 1.2s var(--ease); }}\n.card:hover .art, .card:focus-visible .art {{ background-position: 100% 0; }}\n",
        ),
        card(
            "Card content reveal",
            "height: 190px;",
            "",
            "At rest only the title shows; on hover a panel slides up over the picture with the rest.",
            ".art { height: 100%; }\n.body { position: absolute; left: 0; right: 0; bottom: 0; background: rgb(15 18 30 / .88); backdrop-filter: blur(8px); translate: 0 calc(100% - 46px); transition: translate .4s var(--ease); }\n.card:hover .body, .card:focus-visible .body { translate: 0 0; }\n.body p { padding-top: 6px; }\n",
            html='<article class="card" tabindex="0"><div class="art"></div><div class="body"><h3>Aurora plan</h3><p>Everything a small team needs: unlimited projects, shared boards and priority support.</p></div></article>',
        ),
        card(
            "Card action reveal",
            "",
            "",
            "Actions stay out of sight until the card is hovered or anything inside it has focus, keeping a grid of cards quiet.",
            ".acts { position: absolute; top: 10px; right: 10px; display: flex; gap: 6px; opacity: 0; translate: 0 -6px; transition: all .25s var(--ease); }\n.acts button { width: 30px; height: 30px; border: 0; border-radius: 9px; background: rgb(15 18 30 / .8); color: #fff; }\n.card:hover .acts, .card:focus-within .acts { opacity: 1; translate: 0 0; }\n",
            html=f'<article class="card"><div class="art"></div><div class="acts"><button aria-label="Favourite">♥</button><button aria-label="Share">↗</button><button aria-label="More">⋯</button></div>{BODY}</article>',
        ),
        card(
            "Card expansion",
            "",
            "",
            "Click to open: a grid row animates from 0fr to 1fr, so the extra content's natural height is reached without measuring it.",
            '.more { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .4s var(--ease); }\n.more > div { overflow: hidden; }\n.more p { padding: 0 16px 16px; }\n.card[aria-expanded="true"] .more { grid-template-rows: 1fr; }\n.art { height: 60px; }\n',
            html=f'<article class="card" role="button" tabindex="0" aria-expanded="false"><div class="art"></div>{BODY}<div class="more"><div><p>Unlimited projects, shared boards and priority support.</p></div></div></article>',
            js='const card = document.querySelector(".card");\nconst toggle = () => card.setAttribute("aria-expanded", card.getAttribute("aria-expanded") !== "true");\ncard.addEventListener("click", toggle);\ncard.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); toggle(); } });\n',
        ),
        card(
            "Card collapse",
            "",
            "",
            "The reverse: it starts open, and a click folds it down to its heading. The chevron turns to show which way it will go.",
            '.head { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 14px 16px; border: 0; background: none; color: inherit; font: inherit; font-weight: 600; }\n.head::after { content: "⌄"; transition: rotate .3s var(--ease); }\n.head[aria-expanded="true"]::after { rotate: 180deg; }\n.more { display: grid; grid-template-rows: 0fr; transition: grid-template-rows .4s var(--ease); }\n.more > div { overflow: hidden; }\n.more p { padding: 0 16px 16px; }\n.head[aria-expanded="true"] + .more { grid-template-rows: 1fr; }\n',
            html='<article class="card"><button class="head" aria-expanded="true" aria-controls="details">Aurora plan</button><div class="more" id="details"><div><p>Unlimited projects, shared boards and priority support for the whole team.</p></div></div></article>',
            js='const head = document.querySelector(".head");\nhead.addEventListener("click", () => head.setAttribute("aria-expanded", head.getAttribute("aria-expanded") !== "true"));\n',
        ),
        card(
            "Card flip",
            "overflow: visible; border: 0; background: none; height: 170px; perspective: 900px;",
            "",
            "Two faces back to back; hovering or focusing turns the card over to show the other side.",
            ".inner { position: relative; width: 100%; height: 100%; transform-style: preserve-3d; transition: transform .7s var(--ease); }\n.face { position: absolute; inset: 0; display: grid; place-items: center; padding: 16px; border: 1px solid var(--border); border-radius: 18px; backface-visibility: hidden; text-align: center; font-weight: 600; }\n"
            + f".front {{ background: {ART}; color: #fff; }}\n.back {{ background: var(--surface); transform: rotateY(180deg); }}\n.card:hover .inner, .card:focus-visible .inner {{ transform: rotateY(180deg); }}\n",
            html='<article class="card" tabindex="0"><div class="inner"><div class="face front">Aurora plan</div><div class="face back">$12 per seat, billed monthly</div></div></article>',
        ),
        card(
            "Card 3D tilt",
            DEFAULTS
            + " transform: perspective(700px) rotateX(calc((.5 - var(--py)) * 24deg)) rotateY(calc((var(--px) - .5) * 24deg)); transition: transform .15s ease-out;",
            "",
            "The card leans toward the pointer on both axes, as if balanced on a point under its centre.",
            js=pointer_js(".card", ".card"),
        ),
        card(
            "Card parallax",
            DEFAULTS + " height: 180px; background: #0b1020;",
            "",
            "Layers inside the card shift by different amounts as the pointer moves: the further 'forward' a layer is, the more it travels.",
            ".layer { position: absolute; transition: translate .15s ease-out; translate: calc((var(--px) - .5) * var(--depth)) calc((var(--py) - .5) * var(--depth)); }\n"
            ".l1 { --depth: -14px; inset: -10%; background: radial-gradient(circle at 70% 30%, #7c5cff, transparent 55%); }\n"
            ".l2 { --depth: 26px; left: 14%; top: 22%; width: 70px; height: 70px; border-radius: 50%; background: #22d3ee; }\n"
            ".l3 { --depth: 54px; right: 12%; bottom: 16%; width: 46px; height: 46px; border-radius: 12px; background: #f472b6; rotate: 16deg; }\n"
            ".l4 { --depth: 80px; left: 16px; bottom: 14px; font-weight: 700; color: #fff; }\n",
            html='<article class="card" tabindex="0"><i class="layer l1"></i><i class="layer l2"></i><i class="layer l3"></i><span class="layer l4">Parallax</span></article>',
            js=pointer_js(".card", ".card"),
        ),
        card(
            "Card magnetic movement",
            DEFAULTS
            + " translate: calc((var(--px) - .5) * 46px) calc((var(--py) - .5) * 46px); transition: translate .25s ease-out;",
            "",
            "The card drifts a short way toward the pointer wherever it is in the surrounding area, and springs back when it leaves.",
            js=pointer_js(".stage", ".card", ".stage"),
        ),
        card(
            "Card hover spotlight",
            DEFAULTS,
            "",
            "A pool of light follows the pointer across the card's surface, as though a torch were held over it.",
            '.card::after { content: ""; position: absolute; inset: 0; background: radial-gradient(170px circle at calc(var(--px) * 100%) calc(var(--py) * 100%), rgb(255 255 255 / .22), transparent 70%); opacity: 0; transition: opacity .3s; pointer-events: none; }\n.card:hover::after { opacity: 1; }\n',
            js=pointer_js(".card", ".card"),
        ),
        card(
            "Card cursor glow",
            DEFAULTS + " overflow: visible;",
            "",
            "The light is behind the card, not on it: a coloured glow follows the pointer and shows around the edges.",
            '.card::before { content: ""; position: absolute; left: calc(var(--px) * 100%); top: calc(var(--py) * 100%); z-index: -1; width: 190px; height: 190px; margin: -95px; border-radius: 50%; background: radial-gradient(circle, var(--primary), var(--accent) 45%, transparent 70%); filter: blur(22px); opacity: 0; transition: opacity .3s; }\n.stage:hover .card::before { opacity: .9; }\n.stage { isolation: isolate; }\n.art { border-radius: 17px 17px 0 0; }\n.card > * { position: relative; }\n.card { background: var(--surface); }\n',
            js=pointer_js(".stage", ".card"),
        ),
        card(
            "Card shimmer",
            "",
            "",
            "A narrow band of light crosses the card once each time it is hovered.",
            '.card::after { content: ""; position: absolute; inset: 0; background: linear-gradient(105deg, transparent 40%, rgb(255 255 255 / .3) 50%, transparent 60%); translate: -100% 0; pointer-events: none; }\n.card:hover::after, .card:focus-visible::after { translate: 100% 0; transition: translate .8s var(--ease); }\n',
        ),
        card(
            "Card reflection",
            "margin-bottom: 70px; -webkit-box-reflect: below 6px linear-gradient(transparent 35%, rgb(0 0 0 / .55));",
            "",
            "A fading mirror image beneath the card, as if it stood on a polished floor. Uses -webkit-box-reflect (Chromium and Safari); elsewhere the card simply has no reflection.",
            ".art { height: 64px; }\n.card p { display: none; }\n",
        ),
        card(
            "Card distortion",
            "",
            "animation: jelly .7s both;",
            "On hover the card wobbles like jelly: it is squashed and skewed in alternating directions that die away.",
            "@keyframes jelly { 0%, 100% { transform: none; } 20% { transform: scale(1.08, .92) skewX(-5deg); } 40% { transform: scale(.94, 1.06) skewX(4deg); } 60% { transform: scale(1.03, .97) skewX(-2deg); } 80% { transform: scale(.99, 1.01) skewX(1deg); } }\n",
        ),
        card(
            "Card depth stacking",
            "position: absolute; width: 190px; transition: all .4s var(--ease); translate: 0 calc(var(--n) * -12px); scale: calc(1 - var(--n) * .06); filter: brightness(calc(1 - var(--n) * .22));",
            "",
            "A pile seen from the front: each card behind is smaller, higher and dimmer. Hovering the pile fans it out.",
            ".art { height: 70px; }\n.pile { position: relative; display: grid; place-items: center; width: 100%; height: 100%; outline: none; }\n.pile:hover .card, .pile:focus-visible .card { translate: calc((var(--n) - 1) * -120px) 0; rotate: calc((var(--n) - 1) * -6deg); scale: 1; filter: none; }\n",
            html=f'<div class="pile" tabindex="0">{stacked()}</div>',
        ),
    ),
)
