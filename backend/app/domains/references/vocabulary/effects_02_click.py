"""Effects 41-70: click and press."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import BURST_JS, clicked, press, staged

FAST = "transition: all .12s var(--ease);"
SPRING = "cubic-bezier(.34, 1.56, .64, 1)"
SOLID = ".fx { background: var(--primary); color: #fff; border: 0; }\n"
REL = ".fx { position: relative; overflow: hidden; isolation: isolate; }\n"
BIT = ".stage { overflow: visible; }\n.fx { position: relative; }\n.bit { position: absolute; margin: 0; pointer-events: none; }\n"
POINT = 'const at = () => [parseFloat(button.style.getPropertyValue("--x")), parseFloat(button.style.getPropertyValue("--y"))];\n'


def toggled(name: str, label: str, css: str, js: str, note: str) -> Item:
    return staged(name, f'<button class="fx">{label}</button>', css, note, js)


SECTION = Section(
    "effects",
    "Click & Press Effects",
    41,
    (
        press("Press scale", FAST, "scale: 1.05;", "Swells for as long as it is held."),
        press("Press shrink", FAST, "scale: .94;", "The standard press: a small, quick shrink."),
        press(
            "Press bounce",
            f"transition: scale .45s {SPRING};",
            "scale: .88; transition-duration: .08s;",
            "Goes down fast and comes back with an overshoot.",
        ),
        clicked(
            "Press ripple",
            REL
            + '.fx::after { content: ""; position: absolute; left: var(--x); top: var(--y); width: 10px; height: 10px; margin: -5px; border-radius: 50%; background: currentColor; opacity: 0; }\n.fx.hit::after { animation: ripple .6s ease-out; }\n@keyframes ripple { from { opacity: .35; scale: 0; } to { opacity: 0; scale: 50; } }\n',
            "A circle of ink spreads from where the press landed.",
            "Press me",
        ),
        press(
            "Press wave",
            "position: relative;",
            "",
            "Rings travel outward for as long as the button is held.",
            extra='.fx::before, .fx::after { content: ""; position: absolute; inset: 0; border-radius: inherit; border: 2px solid var(--primary); opacity: 0; }\n.fx:active::before { animation: wave 1s ease-out infinite; }\n.fx:active::after { animation: wave 1s ease-out .5s infinite; }\n@keyframes wave { from { opacity: .8; scale: 1; } to { opacity: 0; scale: 1.5; } }\n',
        ),
        press(
            "Press glow",
            FAST,
            "box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 35%, transparent), 0 0 40px var(--accent); border-color: var(--accent);",
            "Lights up while pressed.",
        ),
        press(
            "Press shadow compression",
            FAST + " box-shadow: 0 14px 28px -8px rgb(0 0 0 / .8);",
            "box-shadow: 0 2px 4px rgb(0 0 0 / .6); translate: 0 4px;",
            "The shadow collapses as the element meets the surface.",
        ),
        press(
            "Press depth compression",
            "background: var(--primary); color: #fff; border: 0; box-shadow: 0 8px 0 color-mix(in srgb, var(--primary) 55%, black); transition: translate .08s, box-shadow .08s;",
            "translate: 0 6px; box-shadow: 0 2px 0 color-mix(in srgb, var(--primary) 55%, black);",
            "A thick edge under the button squashes: a physical key.",
        ),
        press(
            "Press rotation",
            f"transition: rotate .35s {SPRING};",
            "rotate: -6deg; transition-duration: .08s;",
            "Twists under the finger and swings back.",
        ),
        press(
            "Press elastic deformation",
            f"transition: transform .5s {SPRING};",
            "transform: scale(1.08, .9); transition-duration: .08s;",
            "Squashes wide and flat like rubber, then rebounds.",
        ),
        clicked(
            "Click pulse",
            ".fx.hit { animation: pulse .5s var(--ease); }\n@keyframes pulse { 40% { scale: 1.08; box-shadow: 0 0 0 10px color-mix(in srgb, var(--primary) 30%, transparent); } }\n",
            "One beat: a swell with a ring that fades.",
        ),
        clicked(
            "Click burst",
            BIT
            + ".bit { width: 3px; height: 14px; border-radius: 2px; background: var(--warning); transform-origin: 50% 100%; rotate: var(--a); animation: ray .5s ease-out forwards; }\n@keyframes ray { from { translate: 0 0; opacity: 1; } to { translate: calc(sin(var(--a)) * 60px) calc(cos(var(--a)) * -60px); opacity: 0; scale: 1 .3; } }\n",
            "Short rays shoot out in every direction.",
            js=BURST_JS
            + POINT
            + 'button.addEventListener("click", () => burst(button, ...at(), 10, (piece, i, count) => piece.style.setProperty("--a", `${(360 / count) * i}deg`)));\n',
        ),
        clicked(
            "Click particles",
            BIT
            + ".bit { width: 8px; height: 8px; border-radius: 50%; animation: fly .8s cubic-bezier(.2, .7, .3, 1) forwards; }\n@keyframes fly { to { translate: var(--tx) var(--ty); opacity: 0; scale: .2; } }\n",
            "Coloured dots scatter and fall.",
            js=BURST_JS
            + POINT
            + 'const COLOURS = ["#7c5cff", "#22d3ee", "#f472b6", "#fbbf24", "#34d399"];\nbutton.addEventListener("click", () => burst(button, ...at(), 16, (piece, i) => {\n  const angle = Math.random() * Math.PI * 2, distance = 40 + Math.random() * 60;\n  piece.style.background = COLOURS[i % COLOURS.length];\n  piece.style.setProperty("--tx", `${Math.cos(angle) * distance}px`);\n  piece.style.setProperty("--ty", `${Math.sin(angle) * distance + 30}px`);  // gravity pulls them down a little\n}));\n',
        ),
        clicked(
            "Click spark",
            BIT
            + ".bit { width: 2px; height: 2px; border-radius: 50%; background: #fff; box-shadow: 0 0 6px 2px var(--warning); animation: spark .35s ease-out forwards; }\n@keyframes spark { to { translate: var(--tx) var(--ty); opacity: 0; } }\n",
            "A few bright points flick off the surface and are gone.",
            js=BURST_JS
            + POINT
            + 'button.addEventListener("click", () => burst(button, ...at(), 7, (piece) => {\n  const angle = -Math.PI / 2 + (Math.random() - 0.5) * 1.8;  // mostly upward\n  piece.style.setProperty("--tx", `${Math.cos(angle) * 34}px`);\n  piece.style.setProperty("--ty", `${Math.sin(angle) * 34}px`);\n}));\n',
        ),
        clicked(
            "Click ring expansion",
            '.fx { position: relative; }\n.fx::after { content: ""; position: absolute; inset: 0; border-radius: inherit; border: 2px solid var(--accent); opacity: 0; }\n.fx.hit::after { animation: ring .6s ease-out; }\n@keyframes ring { from { opacity: 1; inset: 0; } to { opacity: 0; inset: -28px; } }\n',
            "An outline of the element expands and fades.",
        ),
        clicked(
            "Click radial wave",
            REL
            + '.fx::before { content: ""; position: absolute; inset: 0; z-index: -1; background: radial-gradient(circle at var(--x) var(--y), var(--primary) 0, var(--primary) var(--r, 0%), transparent calc(var(--r, 0%) + 1%)); }\n.fx.hit::before { animation: fill .5s ease-out forwards; }\n.fx.hit { color: #fff; transition: color .3s; }\n@property --r { syntax: "<percentage>"; inherits: false; initial-value: 0%; }\n@keyframes fill { to { --r: 150%; } }\n',
            "Colour floods the element outward from the click point and stays.",
        ),
        clicked(
            "Click color flash",
            ".fx.hit { animation: flash .4s ease-out; }\n@keyframes flash { 0% { background: var(--fg); color: var(--bg); } }\n",
            "Inverts for an instant, then returns.",
        ),
        clicked(
            "Click gradient flash",
            REL
            + '.fx::before { content: ""; position: absolute; inset: 0; z-index: -1; background: linear-gradient(100deg, transparent 20%, #7c5cff, #22d3ee, #f472b6, transparent 80%); translate: -100% 0; }\n.fx.hit::before { animation: sweep .6s var(--ease); }\n@keyframes sweep { to { translate: 100% 0; } }\n',
            "A band of gradient light crosses the surface once.",
        ),
        toggled(
            "Click icon morph",
            '<svg viewBox="0 0 24 24" width="28" height="28" aria-hidden="true"><path d="M5 12 L12 12 L19 12 M12 5 L12 12 L12 19"/></svg>',
            '.fx { width: 72px; height: 72px; border-radius: 50%; }\n.fx path { fill: none; stroke: currentColor; stroke-width: 2.500; stroke-linecap: round; stroke-linejoin: round; transition: d .35s var(--ease); }\n.fx[aria-pressed="true"] { background: var(--success); border-color: var(--success); color: #05130d; }\n.fx[aria-pressed="true"] path { d: path("M5 12 L10 17 L19 7 M10 17 L10 17 L10 17"); }\n',
            'const button = document.querySelector(".fx");\nbutton.setAttribute("aria-pressed", "false");\nbutton.setAttribute("aria-label", "Add");\nbutton.addEventListener("click", () => { const on = button.getAttribute("aria-pressed") !== "true"; button.setAttribute("aria-pressed", String(on)); button.setAttribute("aria-label", on ? "Added" : "Add"); });\n',
            "A plus becomes a tick by animating the path itself (the two shapes share the same commands).",
        ),
        toggled(
            "Click label morph",
            '<span class="a">Subscribe</span><span class="b">Subscribed ✓</span>',
            '.fx { position: relative; overflow: hidden; width: 190px; height: 52px; }\n.fx span { position: absolute; inset: 0; display: grid; place-items: center; transition: translate .35s var(--ease), opacity .25s; }\n.fx .b { translate: 0 100%; opacity: 0; }\n.fx[aria-pressed="true"] { background: var(--primary); color: #fff; border-color: var(--primary); }\n.fx[aria-pressed="true"] .a { translate: 0 -100%; opacity: 0; }\n.fx[aria-pressed="true"] .b { translate: 0 0; opacity: 1; }\n',
            'const button = document.querySelector(".fx");\nbutton.setAttribute("aria-pressed", "false");\nbutton.addEventListener("click", () => button.setAttribute("aria-pressed", String(button.getAttribute("aria-pressed") !== "true")));\n',
            "The old label leaves upward as the new one rises into its place.",
        ),
        toggled(
            "Click loading transition",
            "<span>Submit</span>",
            SOLID
            + '.fx { width: 180px; height: 52px; transition: width .35s var(--ease), border-radius .35s var(--ease), background .3s; }\n.fx span { transition: opacity .15s; }\n.fx[data-s=busy] { width: 52px; border-radius: 50%; cursor: progress; }\n.fx[data-s=busy] span { opacity: 0; }\n.fx[data-s=busy]::after { content: ""; position: absolute; width: 20px; height: 20px; border: 2.500px solid rgb(255 255 255 / .35); border-top-color: #fff; border-radius: 50%; animation: turn .7s linear infinite; }\n.fx[data-s=done] { background: var(--success); color: #05130d; }\n@keyframes turn { to { rotate: 360deg; } }\n',
            'const button = document.querySelector(".fx");\nconst label = button.querySelector("span");\nbutton.addEventListener("click", () => {\n  if (button.dataset.s) return;\n  button.dataset.s = "busy";\n  button.setAttribute("aria-busy", "true");\n  setTimeout(() => {  // stands in for the request\n    button.dataset.s = "done";\n    button.removeAttribute("aria-busy");\n    label.textContent = "Done ✓";\n    setTimeout(() => { delete button.dataset.s; label.textContent = "Submit"; }, 1400);\n  }, 1400);\n});\n',
            "The button collapses into a spinner, then opens again as a confirmation.",
        ),
        toggled(
            "Click state transformation",
            "Follow",
            '.fx { width: 150px; height: 46px; border-radius: 99px; transition: background .25s, color .25s, border-color .25s, width .3s var(--ease); background: var(--primary); color: #fff; border-color: var(--primary); }\n.fx[aria-pressed="true"] { width: 170px; background: transparent; color: var(--fg); border-color: var(--border); }\n.fx[aria-pressed="true"]:hover { border-color: var(--danger); color: var(--danger); }\n',
            'const button = document.querySelector(".fx");\nbutton.setAttribute("aria-pressed", "false");\nconst label = () => { button.textContent = button.getAttribute("aria-pressed") !== "true" ? "Follow" : button.matches(":hover") ? "Unfollow" : "Following"; };\nbutton.addEventListener("click", () => { button.setAttribute("aria-pressed", String(button.getAttribute("aria-pressed") !== "true")); label(); });\n// Once on, hovering shows what the next click will do.\nbutton.addEventListener("pointerenter", label);\nbutton.addEventListener("pointerleave", label);\n',
            "The control changes what it is: a filled call to action becomes a quiet state, with the undo revealed on hover.",
        ),
        clicked(
            "Click confirmation animation",
            ".fx { width: 84px; height: 84px; border-radius: 50%; }\n.fx svg { width: 44px; height: 44px; }\n.fx circle, .fx path { fill: none; stroke: var(--success); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 1; stroke-dashoffset: 1; }\n.fx.hit circle { animation: draw .5s var(--ease) forwards; }\n.fx.hit path { animation: draw .35s .4s var(--ease) forwards; }\n@keyframes draw { to { stroke-dashoffset: 0; } }\n",
            "A circle draws itself, then the tick inside it: the stroke is revealed by animating its dash offset.",
            '<svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="20" pathLength="1"/><path d="M15 25l6 6 12-13" pathLength="1"/></svg>',
        ),
        clicked(
            "Click success burst",
            BIT
            + SOLID
            + ".fx.hit { background: var(--success); color: #05130d; transition: background .2s; }\n.bit { width: 8px; height: 12px; border-radius: 2px; animation: confetti 1s cubic-bezier(.2, .7, .3, 1) forwards; }\n@keyframes confetti { to { translate: var(--tx) var(--ty); rotate: var(--r); opacity: 0; } }\n",
            "Confetti rises from the button, turns as it falls, and the button turns green.",
            "Complete",
            BURST_JS
            + 'const COLOURS = ["#7c5cff", "#22d3ee", "#f472b6", "#fbbf24", "#34d399"];\nbutton.addEventListener("click", () => burst(button, button.offsetWidth / 2, button.offsetHeight / 2, 28, (piece, i) => {\n  const angle = -Math.PI / 2 + (Math.random() - 0.5) * 2.4, distance = 70 + Math.random() * 90;\n  piece.style.background = COLOURS[i % COLOURS.length];\n  piece.style.setProperty("--tx", `${Math.cos(angle) * distance}px`);\n  piece.style.setProperty("--ty", `${Math.sin(angle) * distance + 80}px`);\n  piece.style.setProperty("--r", `${(Math.random() - 0.5) * 720}deg`);\n}));\n',
        ),
        clicked(
            "Click shake",
            ".fx.hit { animation: shake .4s; border-color: var(--danger); }\n@keyframes shake { 20% { translate: -8px 0; } 40% { translate: 7px 0; } 60% { translate: -5px 0; } 80% { translate: 3px 0; } }\n",
            "A quick side-to-side refusal: 'no'.",
            "Wrong password",
        ),
        clicked(
            "Click wobble",
            ".fx.hit { animation: wobble .7s var(--ease); transform-origin: 50% 100%; }\n@keyframes wobble { 20% { rotate: -7deg; } 40% { rotate: 5deg; } 60% { rotate: -3deg; } 80% { rotate: 2deg; } }\n",
            "Rocks about its base and settles.",
        ),
        clicked(
            "Click bounce-back",
            ".fx.hit { animation: back .5s cubic-bezier(.3, 1.6, .5, 1); }\n@keyframes back { 0% { scale: .85; } }\n",
            "Starts squeezed and returns past its size before settling.",
        ),
        clicked(
            "Click spring-back",
            ".fx.hit { animation: spring .9s linear; }\n/* A damped spring sampled into keyframes. */\n@keyframes spring { 0% { translate: 0 14px; } 18% { translate: 0 -8px; } 36% { translate: 0 4.500px; } 54% { translate: 0 -2.500px; } 72% { translate: 0 1.200px; } 88% { translate: 0 -.500px; } 100% { translate: 0 0; } }\n",
            "Pushed down, it oscillates back to rest with shrinking swings.",
        ),
        clicked(
            "Click ripple trail",
            REL
            + '.fx::before, .fx::after { content: ""; position: absolute; left: var(--x); top: var(--y); width: 10px; height: 10px; margin: -5px; border-radius: 50%; border: 2px solid var(--accent); opacity: 0; }\n.fx.hit::before { animation: rip .7s ease-out; }\n.fx.hit::after { animation: rip .7s .18s ease-out; }\n@keyframes rip { from { opacity: .9; scale: 0; } to { opacity: 0; scale: 30; } }\n',
            "Two rings leave the click point one after the other, like drops in water.",
        ),
        clicked(
            "Click shockwave",
            '.stage { overflow: visible; }\n.fx { position: relative; z-index: 1; }\n.fx::after { content: ""; position: absolute; left: 50%; top: 50%; width: 20px; height: 20px; margin: -10px; border-radius: 50%; border: 3px solid var(--fg); opacity: 0; pointer-events: none; }\n.fx.hit { animation: thump .5s var(--ease); }\n.fx.hit::after { animation: shock .7s cubic-bezier(.1, .8, .3, 1); }\n@keyframes thump { 15% { scale: .9; } 45% { scale: 1.06; } }\n@keyframes shock { from { opacity: .9; scale: 1; border-width: 6px; } to { opacity: 0; scale: 22; border-width: 0; } }\n',
            "The element thumps and a large ring races far beyond it.",
        ),
    ),
)
