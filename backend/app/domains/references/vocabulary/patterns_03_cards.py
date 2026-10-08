"""Patterns 81-120: cards and containers."""

from app.domains.references.vocabulary.base import BTN, CARD, Item, Section

TITLE = "<h3>Quarterly revenue</h3><p>Up 12.4% on last quarter across every region.</p>"
PILL = ".pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }\n"


def card(name: str, body: str, css: str, note: str, cls: str = "", js: str = "") -> Item:
    return Item(name, f'<article class="card {cls}">{body}</article>', CARD + css, js, note)


def state(
    name: str, tone: str, glyph: str, title: str, text: str, note: str, role: str = "status"
) -> Item:
    """A card whose whole purpose is to report one state."""
    html = f'<article class="card st" role="{role}"><span class="glyph" aria-hidden="true">{glyph}</span><div><h3>{title}</h3><p>{text}</p></div></article>'
    css = (
        CARD
        + f"""\
.st {{ display: flex; gap: 14px; align-items: flex-start; --tone: var(--{tone});
  border-color: color-mix(in srgb, var(--tone) 45%, transparent); background: color-mix(in srgb, var(--tone) 9%, var(--surface)); }}
.glyph {{ display: grid; place-items: center; flex: none; width: 34px; height: 34px; border-radius: 10px; font-weight: 800;
  background: color-mix(in srgb, var(--tone) 22%, transparent); color: var(--tone); }}
"""
    )
    return Item(name, html, css, note=note)


SECTION = Section(
    "patterns",
    "Cards & Containers",
    81,
    (
        card(
            "Standard card",
            TITLE,
            "",
            "Border, surface and one soft shadow: the default container.",
        ),
        card(
            "Elevated card",
            TITLE,
            ".elev { border-color: transparent; box-shadow: 0 2px 4px rgb(0 0 0 / .3), 0 24px 48px -16px rgb(0 0 0 / .7); }\n",
            "Depth from shadow alone; use for the one thing that floats above the page.",
            "elev",
        ),
        card(
            "Flat card",
            TITLE,
            ".flat { border: 0; box-shadow: none; background: var(--surface-2); }\n",
            "A tinted block with no border or shadow, for dense grids.",
            "flat",
        ),
        Item(
            "Glass card",
            f'<div class="bg"><article class="card glass">{TITLE}</article></div>',
            CARD
            + """\
.bg { display: grid; place-items: center; width: min(460px, 100%); height: 260px; border-radius: var(--radius);
  background: radial-gradient(circle at 20% 20%, #7c5cff, transparent 55%), radial-gradient(circle at 80% 70%, #22d3ee, transparent 55%), #0b0d12; }
.glass { width: 300px; background: rgb(255 255 255 / .08); border-color: rgb(255 255 255 / .22); backdrop-filter: blur(20px) saturate(1.4);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / .25), 0 20px 40px -20px rgb(0 0 0 / .6); }
.glass p { color: rgb(255 255 255 / .75); }
""",
            note="Blur and saturation of the backdrop, a hairline light border and an inner highlight.",
        ),
        Item(
            "Frosted card",
            f'<div class="bg"><article class="card frost">{TITLE}</article></div>',
            CARD
            + """\
.bg { display: grid; place-items: center; width: min(460px, 100%); height: 260px; border-radius: var(--radius);
  background: linear-gradient(135deg, #f472b6, #7c5cff 50%, #22d3ee); }
.frost { width: 300px; background: rgb(20 24 33 / .55); border-color: rgb(255 255 255 / .1); backdrop-filter: blur(28px) brightness(.9); }
.frost::before { content: ""; position: absolute; inset: 0; border-radius: inherit; opacity: .12; pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)'/%3E%3C/svg%3E"); }
.frost { position: relative; }
""",
            note="Heavier blur with a dark tint and a little grain: opaque enough for body text.",
        ),
        card(
            "Gradient card",
            TITLE,
            ".grad { border: 0; background: linear-gradient(140deg, #4f46e5, #7c5cff 45%, #22d3ee); }\n.grad p { color: rgb(255 255 255 / .85); }\n",
            "A full gradient fill for a single promotional card, not a grid of them.",
            "grad",
        ),
        card(
            "Interactive card",
            f'<a href="#" class="cover" aria-label="Open Quarterly revenue"></a>{TITLE}',
            """\
.act { position: relative; transition: translate .2s var(--ease), border-color .2s, box-shadow .2s; }
.act:hover, .act:focus-within { translate: 0 -3px; border-color: var(--primary); box-shadow: 0 18px 36px -14px rgb(0 0 0 / .7); }
.cover { position: absolute; inset: 0; border-radius: inherit; }
.cover:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
""",
            "The whole card is one link (a stretched anchor), so there is a single, large target.",
            "act",
        ),
        Item(
            "Hover card",
            '<p class="text">Reviewed by <span class="hc" tabindex="0">@dana<span class="pop" role="tooltip"><strong>Dana Whitfield</strong><br>Design lead · 142 reviews</span></span> yesterday.</p>',
            """\
.text { color: var(--muted); }
.hc { position: relative; color: var(--primary); cursor: pointer; }
.pop { position: absolute; left: 0; bottom: calc(100% + 10px); width: 220px; padding: 12px; border: 1px solid var(--border); border-radius: 12px;
  background: var(--surface-2); color: var(--fg); box-shadow: var(--shadow); opacity: 0; translate: 0 6px; pointer-events: none;
  transition: opacity .15s .25s, translate .15s .25s; }
.hc:hover .pop, .hc:focus .pop { opacity: 1; translate: 0 0; pointer-events: auto; }
""",
            note="A preview that opens after a short delay on hover or focus, so passing over it does nothing.",
        ),
        card(
            "Expandable card",
            '<h3>Deployment #482</h3><p>Succeeded in 2m 14s.</p><div class="more" hidden><p>Build 41s · Tests 58s · Upload 35s</p></div><button class="tog" aria-expanded="false">Show details</button>',
            """\
.more { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border); }
.tog { margin-top: 12px; padding: 0; border: 0; background: none; color: var(--primary); font-weight: 600; }
""",
            "Secondary detail stays out of the way until asked for.",
            js="""\
const toggle = document.querySelector(".tog");
const more = document.querySelector(".more");
toggle.addEventListener("click", () => {
  more.hidden = !more.hidden;
  toggle.setAttribute("aria-expanded", String(!more.hidden));
  toggle.textContent = more.hidden ? "Show details" : "Hide details";
});
""",
        ),
        Item(
            "Expand/collapse card",
            '<details class="card fold" open><summary>Shipping address</summary><div class="inner"><p>48 Harbour Road, Bristol BS1 4RN</p></div></details>',
            CARD
            + """\
.fold { padding: 0; }
.fold summary { display: flex; justify-content: space-between; padding: 16px 20px; font-weight: 600; cursor: pointer; list-style: none; }
.fold summary::after { content: ""; width: 9px; height: 9px; border: solid var(--muted); border-width: 0 2px 2px 0; rotate: 45deg; transition: rotate .2s var(--ease); }
.fold[open] summary::after { rotate: -135deg; }
.fold .inner { padding: 0 20px 18px; }
.fold::details-content { block-size: 0; overflow: hidden; transition: block-size .3s var(--ease), content-visibility .3s allow-discrete; }
.fold[open]::details-content { block-size: auto; }
:root { interpolate-size: allow-keywords; }
""",
            note="Native <details> with an animated height where the browser supports it.",
        ),
        card(
            "Horizontal card",
            '<div class="thumb"></div><div><h3>Team offsite</h3><p>Lisbon · 14–17 May</p></div>',
            ".hz { display: flex; gap: 16px; align-items: center; width: min(420px, 100%); padding: 12px; }\n.thumb { flex: none; width: 96px; height: 72px; border-radius: 10px; background: linear-gradient(135deg, #f472b6, #7c5cff); }\n",
            "Media left, text right; the list-row form of a card.",
            "hz",
        ),
        card(
            "Vertical card",
            '<div class="thumb"></div><div class="pad"><h3>Team offsite</h3><p>Lisbon · 14–17 May</p></div>',
            ".vt { width: 260px; padding: 0; overflow: hidden; }\n.thumb { height: 140px; background: linear-gradient(135deg, #22d3ee, #7c5cff); }\n.pad { padding: 16px; }\n",
            "Media on top, text below; the grid form of a card.",
            "vt",
        ),
        card(
            "Media card",
            '<div class="shot"><span class="pill">Video · 4:12</span></div><div class="pad"><h3>Designing with tokens</h3><p>How one palette becomes forty themes.</p></div>',
            PILL
            + """\
.media { width: 300px; padding: 0; overflow: hidden; }
.shot { position: relative; aspect-ratio: 16 / 9; background: linear-gradient(160deg, #1e1b4b, #7c5cff); overflow: hidden; }
.shot::after { content: ""; position: absolute; inset: 0; background: radial-gradient(circle at 30% 30%, rgb(255 255 255 / .25), transparent 50%);
  transition: scale .5s var(--ease); }
.media:hover .shot::after { scale: 1.2; }
.shot .pill { position: absolute; left: 10px; bottom: 10px; background: rgb(0 0 0 / .6); color: #fff; z-index: 1; }
.pad { padding: 16px; }
""",
            "A fixed-ratio media area with a caption pill; the image moves slightly on hover.",
            "media",
        ),
        card(
            "Profile card",
            '<span class="ava">DW</span><h3>Dana Whitfield</h3><p>Design lead · Bristol</p><dl><div><dt>Projects</dt><dd>18</dd></div><div><dt>Reviews</dt><dd>142</dd></div><div><dt>Joined</dt><dd>2021</dd></div></dl>',
            """\
.prof { width: 280px; text-align: center; }
.ava { display: grid; place-items: center; width: 64px; height: 64px; margin: 0 auto 12px; border-radius: 50%; font-weight: 700;
  background: linear-gradient(135deg, var(--primary), var(--accent)); box-shadow: 0 0 0 4px var(--surface), 0 0 0 5px var(--border); }
.prof dl { display: flex; margin: 16px 0 0; padding-top: 14px; border-top: 1px solid var(--border); }
.prof dl div { flex: 1; }
.prof dt { font-size: 12px; color: var(--muted); }
.prof dd { margin: 0; font-weight: 700; }
""",
            "Identity first, then three figures at most.",
            "prof",
        ),
        card(
            "Product card",
            '<div class="shot2"><span class="pill">New</span></div><div class="pad"><h3>Arc desk lamp</h3><p>Brushed aluminium</p><div class="buy"><strong>$149</strong><button class="btn">Add</button></div></div>',
            BTN
            + PILL
            + """\
.prod { width: 260px; padding: 0; overflow: hidden; }
.shot2 { position: relative; aspect-ratio: 4 / 3; background: linear-gradient(180deg, #232a3b, #141821); }
.shot2::before { content: ""; position: absolute; left: 50%; top: 50%; width: 90px; height: 90px; translate: -50% -50%; border-radius: 50% 50% 12px 12px;
  background: linear-gradient(160deg, #e8ebf2, #8b93a7); }
.shot2 .pill { position: absolute; top: 10px; left: 10px; background: var(--primary); color: #fff; }
.pad { padding: 14px 16px 16px; }
.buy { display: flex; align-items: center; justify-content: space-between; margin-top: 12px; }
.buy strong { font-size: 18px; }
.buy .btn { height: 34px; }
""",
            "Image, name, one attribute, price and the buy action on one line.",
            "prod",
        ),
        card(
            "Pricing card",
            '<span class="pill">Most popular</span><h3>Team</h3><p class="price"><strong>$24</strong> / seat / month</p><ul><li>Unlimited projects</li><li>SSO and audit log</li><li>Priority support</li></ul><button class="btn">Start free trial</button>',
            BTN
            + PILL
            + """\
.plan { width: 290px; border-color: var(--primary); box-shadow: 0 0 0 1px var(--primary), 0 24px 48px -24px color-mix(in srgb, var(--primary) 60%, transparent); }
.plan .pill { background: color-mix(in srgb, var(--primary) 22%, transparent); color: var(--primary); margin-bottom: 10px; }
.price { margin: 6px 0 14px; }
.price strong { font-size: 34px; color: var(--fg); letter-spacing: -.02em; }
.plan ul { margin: 0 0 18px; padding: 0; list-style: none; display: grid; gap: 8px; }
.plan li::before { content: "✓"; margin-right: 8px; color: var(--success); }
.plan .btn { width: 100%; }
""",
            "The recommended plan is the one with the ring, the badge and the filled button.",
            "plan",
        ),
        card(
            "Feature card",
            '<span class="ico">⚡</span><h3>Instant previews</h3><p>Every branch gets its own URL the moment you push.</p>',
            ".feat { width: 280px; }\n.ico { display: grid; place-items: center; width: 40px; height: 40px; margin-bottom: 14px; border-radius: 11px; background: color-mix(in srgb, var(--primary) 20%, transparent); }\n",
            "Icon tile, a benefit as the title, one sentence of proof.",
            "feat",
        ),
        card(
            "Statistic card",
            '<p class="label">Active users</p><p class="big">48,291</p><p class="sub">in the last 30 days</p>',
            ".stat .label { font-size: 13px; }\n.stat .big { margin: 4px 0; font-size: 36px; font-weight: 700; color: var(--fg); letter-spacing: -.02em; font-variant-numeric: tabular-nums; }\n.stat .sub { font-size: 13px; }\n.stat { width: 240px; }\n",
            "One number, what it counts, over what period.",
            "stat",
        ),
        card(
            "KPI card",
            '<p class="label">Monthly recurring revenue</p><p class="big">$182.4k</p><p class="delta up">▲ 8.2% <span>vs last month</span></p><div class="target"><i style="width:76%"></i></div><p class="sub">76% of $240k target</p>',
            """\
.kpi { width: 280px; }
.kpi .label, .kpi .sub { font-size: 13px; }
.kpi .big { margin: 4px 0; font-size: 34px; font-weight: 700; color: var(--fg); font-variant-numeric: tabular-nums; }
.delta { font-size: 13px; font-weight: 600; }
.delta.up { color: var(--success); }
.delta span { color: var(--muted); font-weight: 400; }
.target { height: 6px; margin: 14px 0 6px; border-radius: 99px; background: var(--surface-2); overflow: hidden; }
.target i { display: block; height: 100%; border-radius: inherit; background: var(--primary); }
""",
            "A figure with its change and its distance from target: value, direction, goal.",
            "kpi",
        ),
        card(
            "Metric card",
            '<div class="head"><p class="label">Response time</p><span class="unit">p95</span></div><p class="big">212<small>ms</small></p>'
            '<svg viewBox="0 0 120 32" preserveAspectRatio="none" aria-hidden="true"><polyline points="0,22 12,20 24,24 36,14 48,18 60,10 72,15 84,8 96,12 108,5 120,9"/></svg>',
            """\
.metric { width: 260px; }
.head { display: flex; justify-content: space-between; }
.unit { padding: 1px 8px; border-radius: 6px; background: var(--surface-2); font: 11px var(--mono); color: var(--muted); }
.metric .big { margin: 4px 0 10px; font-size: 32px; font-weight: 700; color: var(--fg); }
.metric small { margin-left: 3px; font-size: 14px; color: var(--muted); font-weight: 500; }
.metric svg { width: 100%; height: 36px; }
.metric polyline { fill: none; stroke: var(--accent); stroke-width: 2; stroke-linejoin: round; vector-effect: non-scaling-stroke; }
""",
            "A measurement with its unit and a sparkline of the recent trend.",
            "metric",
        ),
        card(
            "Comparison card",
            '<h3>This week vs last</h3><div class="cmp"><div><small>This week</small><strong>1,284</strong><i style="--w:100%"></i></div><div><small>Last week</small><strong>1,031</strong><i style="--w:80%" class="dim"></i></div></div><p class="up">+24.5% sign-ups</p>',
            """\
.cmp { display: grid; gap: 12px; margin: 14px 0; }
.cmp div { display: grid; grid-template-columns: 1fr auto; gap: 4px; }
.cmp small { color: var(--muted); }
.cmp i { grid-column: 1 / -1; height: 8px; width: var(--w); border-radius: 99px; background: var(--primary); }
.cmp i.dim { background: var(--border); }
.up { color: var(--success) !important; font-weight: 600; }
""",
            "Two values on a shared scale, with the difference stated in words.",
        ),
        card(
            "Timeline card",
            '<h3>Order #2041</h3><ol class="tl"><li class="done"><b>Placed</b><span>Mon 09:14</span></li><li class="done"><b>Packed</b><span>Mon 15:02</span></li><li class="now"><b>In transit</b><span>Tue 07:40</span></li><li><b>Delivered</b><span>Expected Wed</span></li></ol>',
            """\
.tl { margin: 14px 0 0; padding: 0; list-style: none; }
.tl li { position: relative; display: flex; justify-content: space-between; padding: 0 0 16px 24px; color: var(--muted); }
.tl li::before { content: ""; position: absolute; left: 4px; top: 5px; width: 9px; height: 9px; border-radius: 50%; border: 2px solid var(--border); background: var(--surface); z-index: 1; }
.tl li::after { content: ""; position: absolute; left: 8px; top: 14px; bottom: -4px; width: 1px; background: var(--border); }
.tl li:last-child { padding-bottom: 0; }
.tl li:last-child::after { display: none; }
.tl .done::before { background: var(--primary); border-color: var(--primary); }
.tl .now::before { border-color: var(--primary); box-shadow: 0 0 0 4px color-mix(in srgb, var(--primary) 25%, transparent); }
.tl .now b, .tl .done b { color: var(--fg); }
.tl span { font-size: 13px; }
""",
            "A short vertical sequence with past, current and future steps distinguished.",
        ),
        card(
            "Activity card",
            '<div class="acti"><span class="ava2">MK</span><p><strong>Mika</strong> commented on <strong>Pricing page</strong><br><small>“Can we test the annual toggle first?”</small></p><time>2m</time></div>',
            ".acti { display: flex; gap: 12px; align-items: flex-start; }\n.ava2 { display: grid; place-items: center; flex: none; width: 34px; height: 34px; border-radius: 50%; background: var(--surface-2); font-size: 12px; font-weight: 700; }\n.acti p { flex: 1; color: var(--fg) !important; }\n.acti small { color: var(--muted); }\n.acti time { font-size: 12px; color: var(--muted); }\n",
            "Who did what to which thing, when, with a quote of the content if there is any.",
        ),
        card(
            "Notification card",
            '<div class="noti"><span class="dotn"></span><div><h3>Build failed on main</h3><p>2 tests in checkout.spec.ts did not pass.</p><div class="acts"><button>View log</button><button>Dismiss</button></div></div></div>',
            """\
.noti { display: flex; gap: 12px; }
.dotn { flex: none; width: 8px; height: 8px; margin-top: 7px; border-radius: 50%; background: var(--primary); box-shadow: 0 0 0 4px color-mix(in srgb, var(--primary) 25%, transparent); }
.acts { display: flex; gap: 8px; margin-top: 12px; }
.acts button { padding: 5px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); font-size: 13px; }
.acts button:first-child { border-color: var(--primary); }
""",
            "An unread dot, the event, and the two things one can do about it.",
        ),
        card(
            "Insight card",
            '<p class="eyebrow">Insight</p><h3>Checkout drop-off doubles on mobile</h3><p>62% abandon at the address step on screens under 400px, against 31% on desktop.</p><a href="#">See the funnel →</a>',
            ".ins { border-left: 3px solid var(--accent); }\n.eyebrow { font-size: 11px !important; letter-spacing: .1em; text-transform: uppercase; color: var(--accent) !important; margin-bottom: 6px !important; }\n.ins a { display: inline-block; margin-top: 12px; color: var(--fg); font-weight: 600; }\n",
            "A finding stated as a headline, the evidence, and where to look next.",
            "ins",
        ),
        card(
            "Recommendation card",
            '<p class="eyebrow">Recommended</p><h3>Enable two-factor sign-in</h3><p>3 admins still sign in with a password only.</p><div class="row"><button class="btn">Turn on</button><button class="later">Not now</button></div>',
            BTN
            + ".eyebrow { font-size: 11px !important; letter-spacing: .1em; text-transform: uppercase; color: var(--warning) !important; margin-bottom: 6px !important; }\n.row { display: flex; gap: 10px; align-items: center; margin-top: 14px; }\n.later { border: 0; background: none; color: var(--muted); }\n",
            "A suggested next step with the reason and an easy refusal.",
        ),
        card(
            "AI response card",
            '<header><span class="spark">✦</span><strong>Assistant</strong><span class="model">sonnet</span></header><p>Revenue grew 12.4% quarter on quarter, driven mostly by the EU region <sup>1</sup>.</p>'
            '<footer><button aria-label="Good answer">👍</button><button aria-label="Bad answer">👎</button><button>Copy</button><button>Regenerate</button></footer>',
            """\
.aic header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.spark { display: grid; place-items: center; width: 24px; height: 24px; border-radius: 8px; background: linear-gradient(135deg, var(--primary), var(--accent)); font-size: 12px; }
.model { margin-left: auto; padding: 1px 8px; border-radius: 6px; background: var(--surface-2); font: 11px var(--mono); color: var(--muted); }
.aic p { color: var(--fg) !important; }
.aic sup { padding: 0 5px; border-radius: 5px; background: color-mix(in srgb, var(--accent) 22%, transparent); color: var(--accent); font-size: 11px; }
.aic footer { display: flex; gap: 6px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border); }
.aic footer button { padding: 4px 10px; border: 0; border-radius: 7px; background: var(--surface-2); font-size: 13px; }
""",
            "The answer, which model wrote it, its citations, and feedback and retry controls.",
            "aic",
        ),
        card(
            "Prompt card",
            '<p class="eyebrow">Prompt</p><h3>Summarise this quarter for the board</h3><p>Three bullets, one risk, no jargon.</p><div class="chips"><span>Finance</span><span>Summary</span></div>',
            ".pc { cursor: pointer; transition: border-color .15s, translate .15s var(--ease); }\n.pc:hover { border-color: var(--primary); translate: 0 -2px; }\n.eyebrow { font-size: 11px !important; letter-spacing: .1em; text-transform: uppercase; margin-bottom: 6px !important; }\n.chips { display: flex; gap: 6px; margin-top: 12px; }\n.chips span { padding: 2px 9px; border-radius: 99px; background: var(--surface-2); font-size: 12px; color: var(--muted); }\n",
            "A reusable prompt: its title, a line of what it asks for, and tags.",
            "pc",
        ),
        card(
            "Conversation card",
            '<div class="cv"><div><h3>Q3 board summary</h3><p>Sure — here is a tighter version with the risk first…</p></div><div class="meta"><time>14:02</time><span class="count">3</span></div></div>',
            ".cv { display: flex; gap: 12px; justify-content: space-between; }\n.cv p { display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }\n.meta { display: grid; justify-items: end; gap: 6px; flex: none; }\n.meta time { font-size: 12px; color: var(--muted); }\n.count { display: grid; place-items: center; min-width: 20px; height: 20px; padding: 0 6px; border-radius: 99px; background: var(--primary); color: #fff; font-size: 11px; font-weight: 700; }\n",
            "Title, last message clamped to one line, time, and an unread count.",
        ),
        card(
            "Document card",
            '<div class="docp"><i></i><i></i><i></i><i></i></div><h3>Product requirements v4</h3><p>Edited 3 hours ago by Mika</p>',
            ".doc { width: 240px; }\n.docp { display: grid; gap: 7px; height: 110px; margin-bottom: 14px; padding: 14px; border-radius: 10px; background: #f5f6fa; align-content: start; }\n.docp i { height: 6px; border-radius: 3px; background: #cfd4e2; }\n.docp i:first-child { width: 55%; height: 9px; background: #8b93a7; }\n.docp i:last-child { width: 70%; }\n",
            "A miniature of the page stands in for a thumbnail.",
            "doc",
        ),
        card(
            "File card",
            '<div class="file"><span class="ext">PDF</span><div><h3>invoice-2041.pdf</h3><p>284 KB · Modified today</p></div><button aria-label="More actions">⋯</button></div>',
            ".file { display: flex; gap: 12px; align-items: center; }\n.ext { display: grid; place-items: center; flex: none; width: 42px; height: 50px; border-radius: 8px 14px 8px 8px; background: color-mix(in srgb, var(--danger) 22%, transparent); color: var(--danger); font: 700 11px var(--mono); }\n.file div { flex: 1; min-width: 0; }\n.file h3 { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }\n.file button { border: 0; background: none; color: var(--muted); font-size: 18px; }\n",
            "Type badge, truncated name, size and date, overflow menu.",
        ),
        card(
            "Integration card",
            '<div class="integ"><span class="logo">S</span><div><h3>Slack</h3><p>Post deploy updates to a channel.</p></div><label class="sw"><input type="checkbox" checked aria-label="Enable Slack"><i></i></label></div>',
            """\
.integ { display: flex; gap: 14px; align-items: center; }
.logo { display: grid; place-items: center; flex: none; width: 42px; height: 42px; border-radius: 12px; background: #4a154b; color: #fff; font-weight: 800; }
.integ div { flex: 1; }
.sw input { position: absolute; opacity: 0; }
.sw i { display: block; width: 40px; height: 24px; padding: 3px; border-radius: 99px; background: var(--surface-2); transition: background .2s; cursor: pointer; }
.sw i::before { content: ""; display: block; width: 18px; height: 18px; border-radius: 50%; background: #fff; transition: translate .2s var(--ease); }
.sw input:checked + i { background: var(--success); }
.sw input:checked + i::before { translate: 16px 0; }
.sw input:focus-visible + i { outline: 2px solid var(--accent); outline-offset: 2px; }
""",
            "A third-party service with what connecting it does and a switch for it.",
        ),
        card(
            "Status card",
            '<div class="sta"><span class="live"></span><div><h3>API</h3><p>Operational · 99.98% over 90 days</p></div></div><div class="bars">'
            + "".join(f'<i class="{"bad" if i == 21 else ""}"></i>' for i in range(30))
            + "</div>",
            ".sta { display: flex; gap: 12px; align-items: center; margin-bottom: 14px; }\n.live { width: 10px; height: 10px; border-radius: 50%; background: var(--success); box-shadow: 0 0 0 4px color-mix(in srgb, var(--success) 25%, transparent); }\n.bars { display: flex; gap: 3px; }\n.bars i { flex: 1; height: 26px; border-radius: 3px; background: var(--success); opacity: .85; }\n.bars i.bad { background: var(--warning); }\n",
            "Current state of a service and a strip of its recent days.",
        ),
        state(
            "Alert card",
            "accent",
            "i",
            "Scheduled maintenance",
            "The API will be read-only on Sunday 02:00–03:00 UTC.",
            "Neutral information that needs attention but is not a problem.",
        ),
        state(
            "Warning card",
            "warning",
            "!",
            "Storage almost full",
            "You have used 92% of your 50 GB plan.",
            "Something will go wrong if nothing is done; say what and by when.",
            "alert",
        ),
        state(
            "Success card",
            "success",
            "✓",
            "Payment received",
            "Receipt #8841 was sent to billing@northwind.io.",
            "Confirms a completed action with the detail someone might need later.",
        ),
        state(
            "Error card",
            "danger",
            "×",
            "Import failed",
            "Row 214 has no email address. Fix the file and upload it again.",
            "What failed, why, and how to recover, in that order.",
            "alert",
        ),
        card(
            "Empty-state card",
            '<div class="empty"><div class="art"></div><h3>No reports yet</h3><p>Reports you create will appear here.</p><button class="btn">Create a report</button></div>',
            BTN
            + ".empty { display: grid; justify-items: center; gap: 6px; padding: 18px 0; text-align: center; }\n.art { width: 72px; height: 72px; margin-bottom: 8px; border-radius: 20px; border: 2px dashed var(--border); background: radial-gradient(circle, color-mix(in srgb, var(--primary) 30%, transparent) 0 30%, transparent 31%); }\n.empty .btn { margin-top: 12px; }\n",
            "Says what belongs here and offers the action that fills it.",
        ),
        card(
            "Skeleton card",
            '<div class="sk" aria-busy="true" aria-label="Loading"><i class="a"></i><i class="l w60"></i><i class="l"></i><i class="l w80"></i></div>',
            """\
.sk { display: grid; gap: 10px; }
.sk i { display: block; border-radius: 6px; background: linear-gradient(90deg, var(--surface-2) 25%, color-mix(in srgb, var(--surface-2) 70%, white 10%) 37%, var(--surface-2) 63%);
  background-size: 400% 100%; animation: shimmer 1.4s ease infinite; }
.sk .a { width: 44px; height: 44px; border-radius: 50%; }
.sk .l { height: 12px; }
.sk .w60 { width: 60%; }
.sk .w80 { width: 80%; }
@keyframes shimmer { from { background-position: 100% 0; } to { background-position: 0 0; } }
""",
            "The shape of the content that is coming, with a light sweeping across it.",
        ),
        Item(
            "Bento card",
            '<div class="bento"><article class="b wide"><h3>Ship faster</h3><p>Previews on every push.</p></article><article class="b tall"><h3>99.99%</h3><p>Uptime</p></article><article class="b"><h3>42ms</h3><p>Edge latency</p></article><article class="b"><h3>SOC 2</h3><p>Type II</p></article></div>',
            """\
.bento { display: grid; grid-template-columns: repeat(3, 1fr); grid-auto-rows: 110px; gap: 12px; width: min(540px, 100%); }
.b { display: flex; flex-direction: column; justify-content: flex-end; padding: 16px; border: 1px solid var(--border); border-radius: 20px;
  background: var(--surface); transition: border-color .2s, translate .2s var(--ease); }
.b:hover { border-color: var(--primary); translate: 0 -2px; }
.b h3 { margin: 0; font-size: 20px; }
.b p { margin: 0; color: var(--muted); font-size: 13px; }
.wide { grid-column: span 2; background: linear-gradient(140deg, color-mix(in srgb, var(--primary) 35%, var(--surface)), var(--surface)); }
.tall { grid-row: span 2; }
""",
            note="Cells of different spans on one grid; one or two are larger and carry the message.",
        ),
    ),
)
