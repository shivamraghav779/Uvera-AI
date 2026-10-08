"""Patterns 191-220: selection and controls."""

from app.domains.references.vocabulary.base import Item, Section

HIDE = ".vh { position: absolute; opacity: 0; pointer-events: none; }\n"
CHIP = (
    HIDE
    + """\
.chips { display: flex; flex-wrap: wrap; gap: 8px; border: 0; padding: 0; margin: 0; max-width: 460px; }
.chips legend { margin-bottom: 10px; color: var(--muted); font-size: 13px; padding: 0; }
.chips span { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border: 1px solid var(--border); border-radius: 999px;
  background: var(--surface); color: var(--muted); cursor: pointer; transition: background .15s, color .15s, border-color .15s; user-select: none; }
.chips span:hover { color: var(--fg); }
.chips input:checked + span { background: color-mix(in srgb, var(--primary) 22%, transparent); border-color: var(--primary); color: var(--fg); }
.chips input:focus-visible + span { outline: 2px solid var(--accent); outline-offset: 2px; }
"""
)


def chips(
    name: str,
    legend: str,
    kind: str,
    options: list[str],
    note: str,
    css: str = "",
    checked: int = 0,
) -> Item:
    body = "".join(
        f'<label><input class="vh" type="{kind}" name="c" value="{o}"{" checked" if i == checked else ""}><span>{o}</span></label>'
        for i, o in enumerate(options)
    )
    return Item(
        name,
        f'<fieldset class="chips"><legend>{legend}</legend>{body}</fieldset>',
        CHIP + css,
        note=note,
    )


RATING_CSS = (
    HIDE
    + """\
.rate { display: inline-flex; flex-direction: row-reverse; border: 0; padding: 0; margin: 0; }
.rate legend { float: left; width: 100%; margin-bottom: 8px; color: var(--muted); font-size: 13px; }
.rate label { padding: 2px; font-size: 30px; line-height: 1; cursor: pointer; color: var(--border); transition: color .12s, scale .12s var(--ease); }
/* Reversed order lets "this and every earlier one" be a sibling selector. */
.rate input:checked ~ label, .rate label:hover, .rate label:hover ~ label { color: var(--tone); }
.rate label:active { scale: .85; }
.rate input:focus-visible + label { outline: 2px solid var(--accent); border-radius: 6px; }
"""
)


def rating(name: str, legend: str, glyph: str, tone: str, note: str, count: int = 5) -> Item:
    body = "".join(
        f'<input class="vh" type="radio" name="r" id="r{i}" value="{i}"{" checked" if i == 4 else ""}><label for="r{i}" aria-label="{i} of {count}">{glyph}</label>'
        for i in range(count, 0, -1)
    )
    return Item(
        name,
        f'<fieldset class="rate" style="--tone:{tone}"><legend>{legend}</legend>{body}</fieldset>',
        RATING_CSS,
        note=note,
    )


CARDS = (
    HIDE
    + """\
.opts { display: grid; gap: 10px; border: 0; padding: 0; margin: 0; width: min(440px, 100%); }
.opts legend { margin-bottom: 10px; color: var(--muted); font-size: 13px; padding: 0; }
.opts .o { display: flex; gap: 12px; align-items: center; padding: 12px 14px; border: 1px solid var(--border); border-radius: 12px;
  background: var(--surface); cursor: pointer; transition: border-color .15s, background .15s; }
.opts .o:hover { border-color: color-mix(in srgb, var(--primary) 50%, var(--border)); }
.opts input:checked + .o { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 12%, var(--surface)); }
.opts input:focus-visible + .o { outline: 2px solid var(--accent); outline-offset: 2px; }
.opts b { display: block; }
.opts small { color: var(--muted); }
.opts .lead { flex: none; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; background: var(--surface-2); font-weight: 700; }
.opts .tail { margin-left: auto; font: 12px var(--mono); color: var(--muted); white-space: nowrap; }
"""
)


def cards(
    name: str,
    legend: str,
    options: list[tuple[str, str, str, str]],
    note: str,
    css: str = "",
    kind: str = "radio",
) -> Item:
    """Selectable cards: (lead glyph, title, description, trailing text)."""
    body = "".join(
        f'<label><input class="vh" type="{kind}" name="o"{" checked" if i == 0 else ""}><span class="o">'
        f'<span class="lead" data-i="{i}">{lead}</span><span><b>{title}</b><small>{text}</small></span><span class="tail">{tail}</span></span></label>'
        for i, (lead, title, text, tail) in enumerate(options)
    )
    return Item(
        name,
        f'<fieldset class="opts"><legend>{legend}</legend>{body}</fieldset>',
        CARDS + css,
        note=note,
    )


SLIDER = """\
.sl { display: grid; gap: 8px; width: min(340px, 100%); }
.sl label { display: flex; justify-content: space-between; font-size: 13px; color: var(--muted); }
.sl output { color: var(--fg); font-weight: 700; font-variant-numeric: tabular-nums; }
.sl input[type=range] { appearance: none; width: 100%; height: 6px; border-radius: 99px; outline: none;
  background: linear-gradient(90deg, var(--primary) var(--fill, 50%), var(--surface-2) var(--fill, 50%)); }
.sl input[type=range]::-webkit-slider-thumb { appearance: none; width: 20px; height: 20px; border-radius: 50%; background: #fff; border: 0;
  box-shadow: 0 2px 6px rgb(0 0 0 / .5); cursor: grab; }
.sl input[type=range]::-moz-range-thumb { width: 20px; height: 20px; border-radius: 50%; background: #fff; border: 0; }
.sl input[type=range]:focus-visible { box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 50%, transparent); }
"""

SECTION = Section(
    "patterns",
    "Selection & Controls",
    191,
    (
        Item(
            "Checkbox",
            '<label class="cb"><input type="checkbox" checked><span></span>Email me product updates</label>',
            '.cb { display: inline-flex; align-items: center; gap: 10px; cursor: pointer; }\n.cb input { position: absolute; opacity: 0; }\n.cb span { display: grid; place-items: center; width: 20px; height: 20px; border: 1.5px solid var(--border); border-radius: 6px; background: var(--surface); transition: background .15s, border-color .15s; }\n.cb span::after { content: ""; width: 10px; height: 6px; border: solid #fff; border-width: 0 0 2px 2px; rotate: -45deg; translate: 0 -1px; scale: 0; transition: scale .15s var(--ease); }\n.cb input:checked + span { background: var(--primary); border-color: var(--primary); }\n.cb input:checked + span::after { scale: 1; }\n.cb input:focus-visible + span { outline: 2px solid var(--accent); outline-offset: 2px; }\n',
            note="A real checkbox, hidden, with a drawn box; the tick scales in.",
        ),
        Item(
            "Radio button",
            '<fieldset class="rb"><legend>Billing</legend><label><input type="radio" name="b" checked><span></span>Monthly</label><label><input type="radio" name="b"><span></span>Yearly (save 20%)</label></fieldset>',
            '.rb { display: grid; gap: 10px; border: 0; padding: 0; }\n.rb legend { margin-bottom: 8px; color: var(--muted); font-size: 13px; }\n.rb label { display: flex; align-items: center; gap: 10px; cursor: pointer; }\n.rb input { position: absolute; opacity: 0; }\n.rb span { display: grid; place-items: center; width: 20px; height: 20px; border: 1.5px solid var(--border); border-radius: 50%; background: var(--surface); transition: border-color .15s; }\n.rb span::after { content: ""; width: 10px; height: 10px; border-radius: 50%; background: var(--primary); scale: 0; transition: scale .15s var(--ease); }\n.rb input:checked + span { border-color: var(--primary); }\n.rb input:checked + span::after { scale: 1; }\n.rb input:focus-visible + span { outline: 2px solid var(--accent); outline-offset: 2px; }\n',
            note="Grouped in a fieldset with a legend; arrow keys move between options natively.",
        ),
        Item(
            "Switch",
            '<label class="sw"><input type="checkbox" role="switch" checked><i></i>Dark mode</label>',
            '.sw { display: inline-flex; align-items: center; gap: 12px; cursor: pointer; }\n.sw input { position: absolute; opacity: 0; }\n.sw i { width: 44px; height: 26px; padding: 3px; border-radius: 99px; background: var(--surface-2); transition: background .2s; }\n.sw i::before { content: ""; display: block; width: 20px; height: 20px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgb(0 0 0 / .4); transition: translate .22s var(--ease); }\n.sw input:checked + i { background: var(--primary); }\n.sw input:checked + i::before { translate: 18px 0; }\n.sw input:focus-visible + i { outline: 2px solid var(--accent); outline-offset: 2px; }\n',
            note="role=switch on a checkbox: takes effect immediately, unlike a checkbox in a form.",
        ),
        Item(
            "Toggle",
            '<button class="tgl" aria-pressed="false"><span class="on">On</span><span class="off">Off</span></button>',
            '.tgl { position: relative; display: grid; grid-template-columns: 1fr 1fr; width: 120px; height: 38px; padding: 3px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }\n.tgl::before { content: ""; position: absolute; top: 3px; bottom: 3px; left: 3px; width: calc(50% - 3px); border-radius: 7px; background: var(--surface-2); translate: 100% 0; transition: translate .22s var(--ease), background .22s; }\n.tgl[aria-pressed="true"]::before { translate: 0 0; background: var(--success); }\n.tgl span { position: relative; display: grid; place-items: center; font-weight: 600; color: var(--muted); }\n.tgl[aria-pressed="true"] .on, .tgl[aria-pressed="false"] .off { color: var(--fg); }\n',
            'const toggle = document.querySelector(".tgl");\ntoggle.addEventListener("click", () => toggle.setAttribute("aria-pressed", String(toggle.getAttribute("aria-pressed") !== "true")));\n',
            "A two-position button with both states written out, for when 'on' needs naming.",
        ),
        Item(
            "Slider",
            '<div class="sl"><label for="s">Volume <output>60</output></label><input id="s" type="range" min="0" max="100" value="60"></div>',
            SLIDER,
            'const input = document.getElementById("s");\nconst output = document.querySelector(".sl output");\nconst update = () => { output.textContent = input.value; input.style.setProperty("--fill", `${((input.value - input.min) / (input.max - input.min)) * 100}%`); };\ninput.addEventListener("input", update);\nupdate();\n',
            "Native range input with the filled part drawn by a CSS variable.",
        ),
        Item(
            "Range slider",
            '<div class="sl"><label for="s">Team size <output></output></label><input id="s" type="range" min="1" max="6" step="1" value="3" list="ticks"><datalist id="ticks"><option value="1" label="1"></option><option value="2" label="5"></option><option value="3" label="10"></option><option value="4" label="25"></option><option value="5" label="50"></option><option value="6" label="100+"></option></datalist><div class="ticks"><span>1</span><span>5</span><span>10</span><span>25</span><span>50</span><span>100+</span></div></div>',
            SLIDER
            + ".ticks { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); }\n",
            'const STEPS = ["1 person", "Up to 5", "Up to 10", "Up to 25", "Up to 50", "100 or more"];\nconst input = document.getElementById("s");\nconst output = document.querySelector(".sl output");\nconst update = () => { output.textContent = STEPS[input.value - 1]; input.setAttribute("aria-valuetext", STEPS[input.value - 1]); input.style.setProperty("--fill", `${((input.value - 1) / 5) * 100}%`); };\ninput.addEventListener("input", update);\nupdate();\n',
            "Discrete, labelled stops on an uneven scale; aria-valuetext says what each stop means.",
        ),
        Item(
            "Dual range slider",
            '<div class="dual"><div class="head"><span>Price</span><output></output></div><div class="track"><i></i><input type="range" min="0" max="500" step="10" value="80" aria-label="Minimum price"><input type="range" min="0" max="500" step="10" value="320" aria-label="Maximum price"></div></div>',
            '.dual { width: min(340px, 100%); display: grid; gap: 14px; }\n.head { display: flex; justify-content: space-between; font-size: 13px; color: var(--muted); }\n.head output { color: var(--fg); font-weight: 700; }\n.track { position: relative; height: 20px; }\n.track::before, .track i { content: ""; position: absolute; top: 7px; height: 6px; border-radius: 99px; }\n.track::before { inset-inline: 0; background: var(--surface-2); }\n.track i { background: var(--primary); left: var(--from); right: calc(100% - var(--to)); }\n.track input { position: absolute; inset: 0; width: 100%; margin: 0; appearance: none; background: none; pointer-events: none; }\n.track input::-webkit-slider-thumb { appearance: none; pointer-events: auto; width: 20px; height: 20px; border-radius: 50%; background: #fff; box-shadow: 0 2px 6px rgb(0 0 0 / .5); cursor: grab; }\n.track input::-moz-range-thumb { pointer-events: auto; width: 20px; height: 20px; border: 0; border-radius: 50%; background: #fff; }\n.track input:focus-visible::-webkit-slider-thumb { outline: 2px solid var(--accent); }\n',
            """\
const [low, high] = document.querySelectorAll(".track input");
const track = document.querySelector(".track");
const output = document.querySelector(".head output");
const GAP = 20;  // the two thumbs never cross
const update = (moved) => {
  if (Number(high.value) - Number(low.value) < GAP) {
    if (moved === low) low.value = Number(high.value) - GAP; else high.value = Number(low.value) + GAP;
  }
  track.style.setProperty("--from", `${(low.value / low.max) * 100}%`);
  track.style.setProperty("--to", `${(high.value / high.max) * 100}%`);
  output.textContent = `$${low.value} – $${high.value}`;
};
low.addEventListener("input", () => update(low));
high.addEventListener("input", () => update(high));
update();
""",
            "Two overlaid range inputs sharing one track, kept a minimum distance apart.",
        ),
        Item(
            "Stepper",
            '<div class="stp" role="group" aria-label="Guests"><button aria-label="Fewer guests">−</button><output aria-live="polite">2</output><button aria-label="More guests">+</button></div>',
            ".stp { display: inline-flex; align-items: center; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); overflow: hidden; }\n.stp button { width: 44px; height: 44px; border: 0; background: none; font-size: 20px; }\n.stp button:hover:not(:disabled) { background: var(--surface-2); }\n.stp button:disabled { opacity: .3; }\n.stp output { min-width: 44px; text-align: center; font-weight: 700; font-variant-numeric: tabular-nums; }\n",
            'const MIN = 1, MAX = 8;\nconst output = document.querySelector(".stp output");\nconst [minus, plus] = document.querySelectorAll(".stp button");\nlet value = 2;\nconst render = () => { output.textContent = String(value); minus.disabled = value <= MIN; plus.disabled = value >= MAX; };\nminus.addEventListener("click", () => { value -= 1; render(); });\nplus.addEventListener("click", () => { value += 1; render(); });\nrender();\n',
            "Minus, value, plus; the buttons disable at the bounds and changes are announced.",
        ),
        Item(
            "Quantity selector",
            '<div class="qty"><span>Arc desk lamp</span><div class="stp" role="group" aria-label="Quantity"><button aria-label="Remove one">−</button><output>1</output><button aria-label="Add one">+</button></div><strong></strong></div>',
            ".qty { display: grid; grid-template-columns: 1fr auto auto; gap: 16px; align-items: center; width: min(420px, 100%); padding: 12px 14px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.stp { display: inline-flex; align-items: center; border: 1px solid var(--border); border-radius: 999px; }\n.stp button { width: 32px; height: 32px; border: 0; background: none; border-radius: 50%; }\n.stp button:hover { background: var(--surface-2); }\n.stp output { min-width: 28px; text-align: center; font-weight: 700; }\n.qty strong { min-width: 64px; text-align: right; font-variant-numeric: tabular-nums; }\n",
            'const PRICE = 149;\nconst output = document.querySelector(".qty output");\nconst total = document.querySelector(".qty strong");\nconst [minus, plus] = document.querySelectorAll(".qty button");\nlet quantity = 1;\nconst render = () => {\n  output.textContent = String(quantity);\n  total.textContent = `$${(quantity * PRICE).toLocaleString()}`;\n  minus.textContent = quantity === 1 ? "×" : "−";  // at one, the minus becomes remove\n  minus.setAttribute("aria-label", quantity === 1 ? "Remove item" : "Remove one");\n};\nminus.addEventListener("click", () => { if (quantity === 1) document.querySelector(".qty").remove(); else { quantity -= 1; render(); } });\nplus.addEventListener("click", () => { quantity = Math.min(99, quantity + 1); render(); });\nrender();\n',
            "A stepper tied to a line total; at one, minus turns into remove.",
        ),
        Item(
            "Rating control",
            '<div class="rc"><span id="rl">How likely are you to recommend us?</span><div role="radiogroup" aria-labelledby="rl">'
            + "".join(
                f'<button role="radio" aria-checked="{"true" if i == 8 else "false"}">{i}</button>'
                for i in range(11)
            )
            + '</div><div class="ends"><span>Not at all</span><span>Extremely</span></div></div>',
            '.rc { display: grid; gap: 10px; width: min(480px, 100%); }\n.rc > span { color: var(--muted); font-size: 14px; }\n.rc [role=radiogroup] { display: grid; grid-template-columns: repeat(11, 1fr); gap: 4px; }\n.rc button { height: 38px; border: 1px solid var(--border); border-radius: 9px; background: var(--surface); font-weight: 600; font-variant-numeric: tabular-nums; }\n.rc button:hover { border-color: var(--primary); }\n.rc button[aria-checked="true"] { background: var(--primary); border-color: var(--primary); color: #fff; }\n.ends { display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); }\n',
            'const options = [...document.querySelectorAll(".rc button")];\nconst choose = (option) => options.forEach((item) => { item.setAttribute("aria-checked", String(item === option)); item.tabIndex = item === option ? 0 : -1; });\noptions.forEach((option, index) => {\n  option.addEventListener("click", () => choose(option));\n  option.addEventListener("keydown", (event) => {\n    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;\n    if (!step) return;\n    const next = options[Math.min(options.length - 1, Math.max(0, index + step))];\n    choose(next);\n    next.focus();\n  });\n});\nchoose(options[8]);\n',
            "A 0–10 scale with worded ends, built as a radio group with arrow-key movement.",
        ),
        rating(
            "Star rating",
            "Rate this report",
            "★",
            "#fbbf24",
            "Five radios in reverse order, so 'this star and all before it' is pure CSS.",
        ),
        rating(
            "Heart rating",
            "How much did you like it?",
            "♥",
            "#f43f5e",
            "The same control with hearts: warmer, for consumer products.",
        ),
        Item(
            "Emoji rating",
            '<fieldset class="er"><legend>How was your experience?</legend>'
            + "".join(
                f'<label><input class="vh" type="radio" name="e"{" checked" if i == 3 else ""}><span aria-hidden="true">{e}</span><small>{t}</small></label>'
                for i, (e, t) in enumerate(
                    [
                        ("😠", "Awful"),
                        ("🙁", "Poor"),
                        ("😐", "Okay"),
                        ("🙂", "Good"),
                        ("😍", "Great"),
                    ]
                )
            )
            + "</fieldset>",
            HIDE
            + ".er { display: flex; gap: 6px; border: 0; padding: 0; }\n.er legend { margin-bottom: 10px; color: var(--muted); font-size: 13px; }\n.er label { display: grid; justify-items: center; gap: 4px; padding: 10px; border-radius: 14px; cursor: pointer; }\n.er span { font-size: 30px; filter: grayscale(1); opacity: .55; transition: filter .15s, opacity .15s, scale .15s var(--ease); }\n.er small { font-size: 11px; color: var(--muted); }\n.er label:hover span { scale: 1.15; opacity: 1; }\n.er input:checked ~ span { filter: none; opacity: 1; scale: 1.2; }\n.er input:checked ~ small { color: var(--fg); }\n.er input:focus-visible ~ span { outline: 2px solid var(--accent); border-radius: 50%; }\n",
            note="Faces with a word under each; unselected ones are greyed so the choice stands out.",
        ),
        Item(
            "Color swatches",
            '<fieldset class="swc"><legend>Colour: <b>Violet</b></legend>'
            + "".join(
                f'<label><input class="vh" type="radio" name="col" value="{n}"{" checked" if i == 0 else ""}><span style="background:{c}"></span></label>'
                for i, (n, c) in enumerate(
                    [
                        ("Violet", "#7c5cff"),
                        ("Cyan", "#22d3ee"),
                        ("Mint", "#34d399"),
                        ("Amber", "#fbbf24"),
                        ("Rose", "#f472b6"),
                        ("Graphite", "#3f4657"),
                    ]
                )
            )
            + "</fieldset>",
            HIDE
            + ".swc { display: flex; gap: 10px; border: 0; padding: 0; }\n.swc legend { margin-bottom: 10px; color: var(--muted); font-size: 13px; }\n.swc legend b { color: var(--fg); }\n.swc span { display: block; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; box-shadow: 0 0 0 2px var(--bg), 0 0 0 3px transparent; transition: box-shadow .15s, scale .15s var(--ease); }\n.swc span:hover { scale: 1.1; }\n.swc input:checked + span { box-shadow: 0 0 0 2px var(--bg), 0 0 0 4px var(--fg); }\n.swc input:focus-visible + span { box-shadow: 0 0 0 2px var(--bg), 0 0 0 4px var(--accent); }\n",
            'const name = document.querySelector(".swc legend b");\ndocument.querySelectorAll(".swc input").forEach((input) => input.addEventListener("change", () => { name.textContent = input.value; }));\n',
            "Colour alone is never the label: the chosen colour's name is written out.",
        ),
        chips(
            "Chip selector",
            "Interests",
            "checkbox",
            ["Design", "Engineering", "Product", "Data", "Marketing", "Research"],
            "Checkbox chips: any number can be on.",
        ),
        Item(
            "Filter chips",
            '<div class="fc"><fieldset class="chips"><legend>Filter by status</legend>'
            + "".join(
                f'<label><input class="vh" type="checkbox" value="{s}"{" checked" if s == "Open" else ""}><span>{s}</span></label>'
                for s in ["Open", "In review", "Blocked", "Done"]
            )
            + '</fieldset><button class="clear">Clear</button><p role="status"></p></div>',
            CHIP
            + '.fc { display: grid; gap: 10px; justify-items: start; }\n.chips input:checked + span::before { content: "✓"; }\n.clear { border: 0; background: none; color: var(--primary); }\n.fc p { margin: 0; color: var(--muted); font-size: 13px; }\n',
            'const boxes = [...document.querySelectorAll(".fc input")];\nconst status = document.querySelector(".fc p");\nconst clear = document.querySelector(".clear");\nconst update = () => {\n  const active = boxes.filter((box) => box.checked).map((box) => box.value);\n  status.textContent = active.length ? `Showing: ${active.join(", ")}` : "Showing everything";\n  clear.hidden = active.length === 0;\n};\nboxes.forEach((box) => box.addEventListener("change", update));\nclear.addEventListener("click", () => { boxes.forEach((box) => { box.checked = false; }); update(); });\nupdate();\n',
            "Active filters carry a tick, are summarised in words, and can be cleared at once.",
        ),
        chips(
            "Choice chips",
            "Size",
            "radio",
            ["XS", "S", "M", "L", "XL"],
            "Radio chips: exactly one is on.",
            checked=2,
        ),
        Item(
            "Tags",
            '<ul class="tags" aria-label="Tags"><li class="t1">Bug</li><li class="t2">Frontend</li><li class="t3">Needs review</li><li class="t4">v2.4</li></ul>',
            ".tags { display: flex; flex-wrap: wrap; gap: 6px; margin: 0; padding: 0; list-style: none; }\n.tags li { padding: 2px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; --c: var(--muted); background: color-mix(in srgb, var(--c) 18%, transparent); color: var(--c); }\n.t1 { --c: var(--danger); }\n.t2 { --c: var(--accent); }\n.t3 { --c: var(--warning); }\n.t4 { --c: var(--primary); }\n",
            note="Read-only labels; one custom property sets both the tint and the text colour.",
        ),
        Item(
            "Multi-tag selector",
            '<div class="mts"><div class="chosen" aria-live="polite"></div><fieldset><legend>Add tags</legend>'
            + "".join(
                f'<label><input type="checkbox" value="{t}"{" checked" if t in ("Design", "Urgent") else ""}> {t}</label>'
                for t in ["Design", "Engineering", "Urgent", "Customer", "Internal"]
            )
            + "</fieldset></div>",
            ".mts { display: grid; gap: 12px; width: min(360px, 100%); }\n.chosen { display: flex; flex-wrap: wrap; gap: 6px; min-height: 28px; }\n.chosen span { display: inline-flex; gap: 4px; align-items: center; padding: 2px 4px 2px 10px; border-radius: 99px; background: color-mix(in srgb, var(--primary) 22%, transparent); font-size: 13px; }\n.chosen button { width: 18px; height: 18px; padding: 0; border: 0; border-radius: 50%; background: none; color: var(--muted); }\n.chosen em { color: var(--muted); font-size: 13px; font-style: normal; }\n.mts fieldset { display: grid; gap: 6px; border: 1px solid var(--border); border-radius: 12px; padding: 12px; }\n.mts legend { padding: 0 6px; color: var(--muted); font-size: 12px; }\n",
            'const boxes = [...document.querySelectorAll(".mts input")];\nconst chosen = document.querySelector(".chosen");\nconst render = () => {\n  const on = boxes.filter((box) => box.checked);\n  chosen.replaceChildren(...(on.length ? on.map((box) => {\n    const chip = document.createElement("span");\n    const remove = Object.assign(document.createElement("button"), { type: "button", textContent: "×" });\n    remove.setAttribute("aria-label", `Remove ${box.value}`);\n    remove.addEventListener("click", () => { box.checked = false; render(); });\n    chip.append(box.value, remove);\n    return chip;\n  }) : [Object.assign(document.createElement("em"), { textContent: "No tags" })]));\n};\nboxes.forEach((box) => box.addEventListener("change", render));\nrender();\n',
            "A checklist and its result as removable chips, kept in step in both directions.",
        ),
        Item(
            "Calendar selector",
            '<div class="cal"><header><button aria-label="Previous month">‹</button><strong aria-live="polite"></strong><button aria-label="Next month">›</button></header><div class="dow"></div><div class="grid" role="grid"></div></div>',
            '.cal { width: 290px; padding: 14px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.cal header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }\n.cal header button { width: 28px; height: 28px; border: 0; border-radius: 8px; background: var(--surface-2); }\n.dow, .cal .grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }\n.dow span { text-align: center; font-size: 11px; color: var(--muted); padding: 4px 0; }\n.cal .grid button { aspect-ratio: 1; border: 0; border-radius: 9px; background: none; }\n.cal .grid button:hover { background: var(--surface-2); }\n.cal .grid .today { box-shadow: inset 0 0 0 1px var(--primary); }\n.cal .grid [aria-selected="true"] { background: var(--primary); color: #fff; }\n.cal .grid button:disabled { opacity: .3; }\n',
            """\
const root = document.querySelector(".cal");
const title = root.querySelector("strong");
const grid = root.querySelector(".grid");
const today = new Date(); today.setHours(0, 0, 0, 0);
const view = new Date(today.getFullYear(), today.getMonth(), 1);
let selected = new Date(today);
root.querySelector(".dow").append(...["M", "T", "W", "T", "F", "S", "S"].map((day) => Object.assign(document.createElement("span"), { textContent: day })));
const render = (focusDay) => {
  title.textContent = view.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  grid.replaceChildren();
  for (let i = 0; i < (view.getDay() + 6) % 7; i += 1) grid.append(document.createElement("span"));
  const days = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
  for (let day = 1; day <= days; day += 1) {
    const date = new Date(view.getFullYear(), view.getMonth(), day);
    const button = Object.assign(document.createElement("button"), { type: "button", textContent: String(day) });
    button.disabled = date < today;  // past days cannot be booked
    if (+date === +today) button.classList.add("today");
    button.setAttribute("aria-selected", String(+date === +selected));
    button.setAttribute("aria-label", date.toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" }));
    button.tabIndex = +date === +selected ? 0 : -1;
    button.addEventListener("click", () => { selected = date; render(day); });
    grid.append(button);
    if (day === focusDay) queueMicrotask(() => button.focus());
  }
};
// Arrow keys move by day and week within the month shown.
grid.addEventListener("keydown", (event) => {
  const step = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[event.key];
  if (!step) return;
  event.preventDefault();
  const buttons = [...grid.querySelectorAll("button")];
  buttons[buttons.indexOf(document.activeElement) + step]?.focus();
});
const [previous, next] = root.querySelectorAll("header button");
previous.addEventListener("click", () => { view.setMonth(view.getMonth() - 1); render(); });
next.addEventListener("click", () => { view.setMonth(view.getMonth() + 1); render(); });
render();
""",
            "A month grid with today marked, past days disabled and arrow-key movement.",
        ),
        Item(
            "Time slot selector",
            '<fieldset class="slots"><legend>Thursday 14 May</legend>'
            + "".join(
                f'<label><input class="vh" type="radio" name="t" {"disabled" if t in ("10:00", "13:30") else ""}{" checked" if t == "11:00" else ""}><span>{t}</span></label>'
                for t in [
                    "09:00",
                    "09:30",
                    "10:00",
                    "10:30",
                    "11:00",
                    "11:30",
                    "13:00",
                    "13:30",
                    "14:00",
                    "14:30",
                    "15:00",
                    "15:30",
                ]
            )
            + "</fieldset>",
            HIDE
            + ".slots { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; width: min(380px, 100%); border: 0; padding: 0; }\n.slots legend { margin-bottom: 10px; font-weight: 600; }\n.slots span { display: block; padding: 9px 0; text-align: center; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); cursor: pointer; font-variant-numeric: tabular-nums; }\n.slots span:hover { border-color: var(--primary); }\n.slots input:checked + span { background: var(--primary); border-color: var(--primary); color: #fff; }\n.slots input:disabled + span { opacity: .35; text-decoration: line-through; cursor: not-allowed; border-color: var(--border); }\n.slots input:focus-visible + span { outline: 2px solid var(--accent); outline-offset: 2px; }\n",
            note="A grid of times; taken slots are struck through and cannot be focused or chosen.",
        ),
        Item(
            "Seat selector",
            '<div class="seats"><div class="screen">Screen</div><div class="map" role="group" aria-label="Seats"></div><p role="status"></p></div>',
            '.seats { display: grid; gap: 14px; justify-items: center; }\n.screen { width: 240px; padding: 4px; text-align: center; font-size: 11px; letter-spacing: .2em; text-transform: uppercase; color: var(--muted); border-top: 3px solid var(--border); border-radius: 50% 50% 0 0 / 14px 14px 0 0; }\n.map { display: grid; grid-template-columns: repeat(8, 28px); gap: 6px; }\n.map button { height: 26px; border: 0; border-radius: 7px 7px 4px 4px; background: var(--surface-2); font-size: 0; }\n.map button:nth-child(8n + 4) { margin-right: 10px; }\n.map button:hover:not(:disabled) { background: color-mix(in srgb, var(--primary) 50%, var(--surface-2)); }\n.map button[aria-pressed="true"] { background: var(--primary); }\n.map button:disabled { background: var(--border); opacity: .45; cursor: not-allowed; }\n.seats p { margin: 0; color: var(--muted); font-size: 14px; }\n',
            """\
const map = document.querySelector(".map");
const status = document.querySelector(".seats p");
const TAKEN = new Set(["A3", "A4", "B6", "C1", "C2", "D5", "D6", "D7"]);
const LIMIT = 4;
const PRICE = 12;
for (const row of "ABCD") for (let seat = 1; seat <= 8; seat += 1) {
  const id = `${row}${seat}`;
  const button = Object.assign(document.createElement("button"), { type: "button", textContent: id });
  button.dataset.id = id;
  button.disabled = TAKEN.has(id);
  button.setAttribute("aria-pressed", "false");
  button.setAttribute("aria-label", `Seat ${id}${TAKEN.has(id) ? ", taken" : ""}`);
  map.append(button);
}
const chosen = () => [...map.querySelectorAll('[aria-pressed="true"]')];
map.addEventListener("click", (event) => {
  const seat = event.target.closest("button");
  if (!seat) return;
  const on = seat.getAttribute("aria-pressed") === "true";
  if (!on && chosen().length >= LIMIT) { status.textContent = `You can choose up to ${LIMIT} seats.`; return; }
  seat.setAttribute("aria-pressed", String(!on));
  const seats = chosen().map((item) => item.dataset.id);
  status.textContent = seats.length ? `${seats.join(", ")} · $${seats.length * PRICE}` : "Choose your seats.";
});
status.textContent = "Choose your seats.";
""",
            "Toggle buttons on a seat map with taken seats disabled, a limit, and a running total.",
        ),
        Item(
            "Permission selector",
            '<table class="perm"><caption>Permissions</caption><thead><tr><th scope="col">Resource</th><th scope="col">View</th><th scope="col">Edit</th><th scope="col">Admin</th></tr></thead><tbody>'
            + "".join(
                f'<tr><th scope="row">{r}</th>'
                + "".join(
                    f'<td><input type="checkbox" aria-label="{r}: {p}"{" checked" if j <= d else ""}></td>'
                    for j, p in enumerate(["view", "edit", "admin"])
                )
                + "</tr>"
                for r, d in [("Projects", 1), ("Billing", 0), ("Members", 2)]
            )
            + "</tbody></table>",
            ".perm { width: min(420px, 100%); border-collapse: collapse; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: var(--surface); }\n.perm caption { text-align: left; margin-bottom: 8px; color: var(--muted); font-size: 13px; }\n.perm th, .perm td { padding: 10px 14px; border-bottom: 1px solid var(--border); text-align: center; }\n.perm th[scope=row], .perm th:first-child { text-align: left; font-weight: 500; }\n.perm thead th { font-size: 12px; color: var(--muted); background: var(--surface-2); }\n.perm tr:last-child > * { border-bottom: 0; }\n.perm input { width: 16px; height: 16px; accent-color: var(--primary); }\n",
            """\
// Permissions are cumulative: edit implies view, admin implies both.
document.querySelectorAll(".perm tbody tr").forEach((row) => {
  const boxes = [...row.querySelectorAll("input")];
  boxes.forEach((box, level) => box.addEventListener("change", () => {
    boxes.forEach((other, i) => { if (box.checked ? i < level : i > level) other.checked = box.checked; });
  }));
});
""",
            "A resource-by-level matrix in a real table; higher levels tick the lower ones they imply.",
        ),
        cards(
            "Role selector",
            "Role",
            [
                ("A", "Admin", "Everything, including billing and members", ""),
                ("E", "Editor", "Create and change content", ""),
                ("V", "Viewer", "Read and comment only", ""),
            ],
            "Each role is a card that states what it allows.",
        ),
        cards(
            "Priority selector",
            "Priority",
            [
                ("!", "Urgent", "Drop everything", "P0"),
                ("↑", "High", "This week", "P1"),
                ("→", "Normal", "This cycle", "P2"),
                ("↓", "Low", "When there is time", "P3"),
            ],
            "Ordered levels with a colour that escalates.",
            '.lead[data-i="0"] { background: color-mix(in srgb, var(--danger) 25%, transparent); color: var(--danger); }\n.lead[data-i="1"] { background: color-mix(in srgb, var(--warning) 25%, transparent); color: var(--warning); }\n.lead[data-i="2"] { background: color-mix(in srgb, var(--accent) 22%, transparent); color: var(--accent); }\n',
        ),
        cards(
            "Status selector",
            "Status",
            [
                ("●", "To do", "Not started", ""),
                ("●", "In progress", "Someone is on it", ""),
                ("●", "In review", "Waiting for approval", ""),
                ("●", "Done", "Shipped", ""),
            ],
            "Workflow states, each with its own dot colour.",
            '.lead { background: none !important; width: 16px !important; }\n.lead[data-i="0"] { color: var(--muted); }\n.lead[data-i="1"] { color: var(--accent); }\n.lead[data-i="2"] { color: var(--warning); }\n.lead[data-i="3"] { color: var(--success); }\n',
        ),
        Item(
            "Category selector",
            '<fieldset class="cat"><legend>What are you building?</legend>'
            + "".join(
                f'<label><input class="vh" type="radio" name="k"{" checked" if i == 0 else ""}><span><b>{g}</b>{n}</span></label>'
                for i, (g, n) in enumerate(
                    [
                        ("◧", "Website"),
                        ("▦", "Dashboard"),
                        ("◫", "Mobile app"),
                        ("◈", "Online store"),
                        ("◉", "Internal tool"),
                        ("✦", "Something else"),
                    ]
                )
            )
            + "</fieldset>",
            HIDE
            + ".cat { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; width: min(460px, 100%); border: 0; padding: 0; }\n.cat legend { margin-bottom: 12px; font-weight: 600; }\n.cat span { display: grid; justify-items: center; gap: 8px; padding: 18px 8px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); cursor: pointer; font-size: 14px; transition: border-color .15s, translate .15s var(--ease); }\n.cat b { font-size: 24px; color: var(--muted); }\n.cat span:hover { translate: 0 -2px; }\n.cat input:checked + span { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 12%, var(--surface)); }\n.cat input:checked + span b { color: var(--primary); }\n.cat input:focus-visible + span { outline: 2px solid var(--accent); outline-offset: 2px; }\n",
            note="Large tiles with a glyph and a name: an onboarding question, one answer.",
        ),
        cards(
            "Model selector",
            "Model",
            [
                ("O", "Opus", "Most capable; slower", "$15 / M"),
                ("S", "Sonnet", "Balanced speed and quality", "$3 / M"),
                ("H", "Haiku", "Fastest and cheapest", "$0.8 / M"),
            ],
            "Each model with its trade-off in a phrase and its price.",
        ),
        cards(
            "Provider selector",
            "Provider",
            [
                ("A", "Anthropic", "Connected · 3 models", "Default"),
                ("G", "Google", "Connected · 2 models", ""),
                ("M", "Mistral", "Add an API key to use", "Set up"),
            ],
            "Where requests go; unconfigured providers say what is missing.",
        ),
        cards(
            "Tool selector",
            "Tools the agent may use",
            [
                ("⌕", "Web search", "Look things up online", "Read"),
                ("▤", "Files", "Read documents you attach", "Read"),
                ("⟳", "Code runner", "Execute code in a sandbox", "Write"),
                ("✉", "Email", "Send messages on your behalf", "Write"),
            ],
            "Checkbox cards: several can be on, and each states whether it reads or acts.",
            ".tail { padding: 1px 8px; border-radius: 6px; background: var(--surface-2); }\n",
            "checkbox",
        ),
    ),
)
