"""Building blocks of the house design vocabulary.

Every entry is a small, complete piece of front-end code for one named
pattern or effect: markup, styles and (only where behaviour needs it) a
script. Entries share one set of design tokens so they compose; the tokens
are inlined into each entry's standalone page, so every entry runs on its own.

Like the rest of the reference library this is reading material for people
building the platform's patterns. Nothing here is rendered by generated UIs
or shown to the model.
"""

import re
from dataclasses import dataclass

_NOT_SLUG = re.compile(r"[^a-z0-9]+")


def slug(text: str) -> str:
    return _NOT_SLUG.sub("-", text.lower()).strip("-")


# Design tokens every entry is written against. They mirror the platform's theme
# tokens (--g-primary, --g-surface, ...): porting an entry means renaming these.
TOKENS_CSS = """\
:root {
  --bg: #0b0d12; --surface: #141821; --surface-2: #1b2130; --border: #262d3d;
  --fg: #e8ebf2; --muted: #8b93a7; --primary: #7c5cff; --primary-fg: #ffffff;
  --accent: #22d3ee; --success: #34d399; --warning: #fbbf24; --danger: #f87171;
  --radius: 14px; --ease: cubic-bezier(.2, .8, .2, 1);
  --shadow: 0 1px 2px rgb(0 0 0 / .3), 0 12px 32px -12px rgb(0 0 0 / .5);
  --font: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, monospace;
}
*, *::before, *::after { box-sizing: border-box; }
body {
  margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 32px;
  background: var(--bg); color: var(--fg); font: 15px/1.5 var(--font);
}
button, input, select, textarea { font: inherit; color: inherit; }
button { cursor: pointer; }
/* The hidden attribute always wins, whatever display a component sets. */
[hidden] { display: none !important; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; }
}
"""

# --- Reusable atoms (copied into the entries that use them) ---------------------------

BTN = """\
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 40px;
  padding: 0 16px; border: 1px solid transparent; border-radius: 10px; background: var(--primary);
  color: var(--primary-fg); font-weight: 600; white-space: nowrap;
  transition: transform .15s var(--ease), background .15s, box-shadow .15s, opacity .15s, border-color .15s; }
.btn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.btn:disabled { opacity: .5; cursor: not-allowed; }
"""
BTN_GHOST = """\
.btn-ghost { background: transparent; color: var(--fg); border-color: var(--border); }
.btn-ghost:hover { background: var(--surface-2); }
"""
CARD = """\
.card { width: min(360px, 100%); padding: 20px; border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--surface); box-shadow: var(--shadow); }
.card h3 { margin: 0 0 6px; font-size: 16px; }
.card p { margin: 0; color: var(--muted); }
"""
CARD_HTML = (
    '<article class="card"><h3>Quarterly revenue</h3>'
    "<p>Up 12.4% on last quarter across every region.</p></article>"
)
FIELD = """\
.field { display: grid; gap: 6px; width: min(340px, 100%); }
.field label { font-size: 13px; color: var(--muted); }
.input { height: 42px; width: 100%; padding: 0 12px; border: 1px solid var(--border); border-radius: 10px;
  background: var(--surface); color: var(--fg); transition: border-color .15s, box-shadow .15s; }
.input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 30%, transparent); }
.input::placeholder { color: var(--muted); }
"""
PANEL = """\
.panel { width: min(520px, 100%); border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--surface); box-shadow: var(--shadow); overflow: hidden; }
"""
STACK = ".stack { display: grid; gap: 12px; width: min(420px, 100%); }\n"
ROW = ".row { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }\n"
MUTED = ".muted { color: var(--muted); font-size: 13px; }\n"


@dataclass(frozen=True, slots=True)
class Item:
    """One vocabulary entry as its author writes it."""

    name: str
    html: str
    css: str
    js: str = ""
    # What it is for or what to watch for when using it; one sentence.
    note: str = ""


@dataclass(frozen=True, slots=True)
class Section:
    # "patterns", "effects" or "recipes".
    group: str
    title: str
    # Number of the section's first item in its list (1-based, as in the brief).
    start: int
    items: tuple[Item, ...]


def scoped(js: str) -> str:
    """The entry's script in a scope of its own, so pasting several entries into
    one page (or meeting a browser global such as ``top``) cannot clash."""
    body = "\n".join(f"  {line}" if line else "" for line in js.strip().splitlines())
    return f"(() => {{\n{body}\n}})();"


def standalone_page(title: str, item: Item) -> str:
    """A complete document that shows the entry by itself."""
    script = f"\n<script>\n{scoped(item.js)}\n</script>" if item.js.strip() else ""
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n<style>\n{TOKENS_CSS}\n{item.css.strip()}\n</style>\n</head>\n"
        f"<body>\n{item.html.strip()}{script}\n</body>\n</html>\n"
    )
