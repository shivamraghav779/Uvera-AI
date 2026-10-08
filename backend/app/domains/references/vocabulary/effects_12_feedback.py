"""Effects 301-325: notifications and feedback."""

from app.domains.references.vocabulary.base import Item, Section
from app.domains.references.vocabulary.fx import BURST_JS, REPLAY_BTN, REPLAY_CSS, REPLAY_JS, STAGE

CALM = 'const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;\n'

TOAST_HTML = '<div class="toast fx" role="status"><i class="ico" aria-hidden="true">✓</i><span><b>Saved</b><small>Your changes are live.</small></span></div>'
TOAST_CSS = """\
.toast { position: relative; display: flex; align-items: center; gap: 12px; width: 270px; padding: 12px 14px; overflow: hidden; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); box-shadow: var(--shadow); }
.toast .ico { display: grid; place-items: center; flex: none; width: 26px; height: 26px; border-radius: 50%; background: var(--success); color: #06281a; font-style: normal; font-weight: 800; }
.toast span { display: grid; }
.toast small { color: var(--muted); }
"""
BELL_HTML = (
    '<button class="bell" type="button" aria-label="Notifications, 3 unread"><svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M12 3a6 6 0 0 0-6 6v4l-2 3h16l-2-3V9a6 6 0 0 0-6-6zM10 19a2 2 0 0 0 4 0"/></svg><span class="badge">3</span></button>'
)
BELL_CSS = """\
.bell { position: relative; display: grid; place-items: center; width: 56px; height: 56px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }
.bell svg { width: 26px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.badge { position: absolute; top: -7px; right: -7px; display: grid; place-items: center; min-width: 22px; height: 22px; padding: 0 6px; border: 2px solid var(--bg); border-radius: 99px; background: var(--danger); color: #fff; font-size: 12px; font-weight: 700; }
"""
STATUS_CSS = ".status { display: flex; align-items: center; gap: 10px; padding: 8px 16px 8px 12px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface); font-weight: 600; }\n.dot { position: relative; width: 10px; height: 10px; border-radius: 50%; background: var(--tone); }\n"
CHECK_SVG = '<svg class="tick" viewBox="0 0 52 52" aria-hidden="true"><circle cx="26" cy="26" r="23"/><path d="M15 27l8 8 15-17"/></svg>'
CHECK_CSS = ".tick { width: 76px; overflow: visible; }\n.tick circle { fill: var(--success); }\n.tick path { fill: none; stroke: #06281a; stroke-width: 5; stroke-linecap: round; stroke-linejoin: round; }\n"


def toast(
    name: str, rule: str, frames: str, note: str, extra: str = "", js: str = REPLAY_JS
) -> Item:
    """A toast whose behaviour starts when ``.go`` is added."""
    css = (
        STAGE
        + TOAST_CSS
        + REPLAY_CSS
        + (f".toast.go {{ {rule} }}\n" if rule else "")
        + frames
        + extra
    )
    return Item(name, f'<div class="stage">{TOAST_HTML}{REPLAY_BTN}</div>', css, js, note)


def bell(name: str, css: str, note: str, js: str = "") -> Item:
    return Item(name, f'<div class="stage">{BELL_HTML}</div>', STAGE + BELL_CSS + css, js, note)


def status(
    name: str, label: str, tone: str, css: str, note: str, dot: str = '<i class="dot"></i>'
) -> Item:
    html = f'<div class="stage"><span class="status" role="status" style="--tone: {tone}">{dot}{label}</span></div>'
    return Item(name, html, STAGE + STATUS_CSS + css, "", note)


def played(name: str, inner: str, css: str, note: str, js: str = REPLAY_JS) -> Item:
    """Anything else that plays once on ``.go`` and can be replayed."""
    return Item(
        name, f'<div class="stage">{inner}{REPLAY_BTN}</div>', STAGE + REPLAY_CSS + css, js, note
    )


def banner(name: str, tone: str, icon: str, text: str, css: str, note: str) -> Item:
    html = f'<div class="stage"><div class="banner" role="status" style="--tone: {tone}"><b aria-hidden="true">{icon}</b>{text}</div></div>'
    base = ".banner { position: relative; display: flex; align-items: center; gap: 12px; width: 320px; padding: 14px 16px; overflow: hidden; border: 1px solid color-mix(in srgb, var(--tone) 45%, transparent); border-radius: 14px; background: color-mix(in srgb, var(--tone) 12%, var(--surface)); }\n.banner b { display: grid; place-items: center; flex: none; width: 26px; height: 26px; border-radius: 50%; background: var(--tone); color: #111; }\n"
    return Item(name, html, STAGE + base + css, "", note)


SECTION = Section(
    "effects",
    "Notification & Feedback Effects",
    301,
    (
        toast(
            "Toast slide-in",
            "animation: arrive .45s var(--ease) both;",
            "@keyframes arrive { from { translate: 130% 0; opacity: 0; } }\n",
            "Enters from the edge it is anchored to: the default toast entrance.",
            ".stage { overflow: hidden; }\n",
        ),
        toast(
            "Toast bounce-in",
            "animation: arrive .7s both;",
            "@keyframes arrive { 0% { translate: 0 160px; opacity: 0; animation-timing-function: ease-out; } 55% { translate: 0 -12px; opacity: 1; animation-timing-function: ease-in-out; } 78% { translate: 0 5px; } 100% { translate: 0 0; } }\n",
            "Comes up from below, overshoots and settles: more insistent than a slide.",
            ".stage { overflow: hidden; }\n",
        ),
        toast(
            "Toast glow",
            "animation: arrive .4s var(--ease) both, halo 1.6s .3s ease-out both;",
            "@keyframes arrive { from { scale: .92; opacity: 0; } }\n@keyframes halo { from { border-color: var(--success); box-shadow: 0 0 0 1px var(--success), 0 0 34px rgb(52 211 153 / .7); } }\n",
            "Arrives lit in its status colour, and the light dies away over the next second.",
        ),
        toast(
            "Toast pulse",
            "animation: nudge .5s ease-in-out 2;",
            "@keyframes nudge { 50% { scale: 1.05; } }\n",
            "A toast that is already on screen swells twice to ask for attention, without moving away.",
        ),
        toast(
            "Toast progress bar",
            "",
            "@keyframes drain { to { scale: 0 1; } }\n",
            "A bar along the bottom shows how long the toast has left. Hover or focus to pause it.",
            '.toast::after { content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 3px; background: var(--success); transform-origin: 0 50%; }\n.toast.go::after { animation: drain 4s linear forwards; }\n.toast:hover::after, .toast:focus-within::after { animation-play-state: paused; }\n',
        ),
        toast(
            "Toast auto-dismiss",
            "animation: arrive .4s var(--ease) both;",
            "@keyframes arrive { from { translate: 0 20px; opacity: 0; } }\n@keyframes depart { to { translate: 0 -14px; opacity: 0; } }\n",
            "Shown, held for three seconds, then removed on its own. Hovering holds it open; leaving restarts the wait.",
            ".toast.out { animation: depart .3s ease-in forwards; }\n",
            """\
const toast = document.querySelector(".toast");
const HOLD = 3000;
let timer;
const dismiss = () => { toast.classList.remove("go"); toast.classList.add("out"); };
const wait = () => { clearTimeout(timer); timer = setTimeout(dismiss, HOLD); };
const show = () => { toast.classList.remove("go", "out"); void toast.offsetWidth; toast.classList.add("go"); wait(); };
toast.addEventListener("pointerenter", () => clearTimeout(timer));
toast.addEventListener("pointerleave", () => { if (toast.classList.contains("go")) wait(); });
document.querySelector(".replay").addEventListener("click", show);
show();
""",
        ),
        bell(
            "Badge pulse",
            ".badge { animation: beat 1.4s ease-in-out infinite; }\n@keyframes beat { 0%, 100% { scale: 1; } 12% { scale: 1.25; } 24% { scale: 1; } 36% { scale: 1.18; } 48% { scale: 1; } }\n",
            "The count beats twice and rests, like a heartbeat.",
        ),
        bell(
            "Badge bounce",
            ".badge.hit { animation: jump .5s; }\n@keyframes jump { 0% { translate: 0 0; animation-timing-function: ease-out; } 35% { translate: 0 -12px; animation-timing-function: ease-in; } 65% { translate: 0 0; animation-timing-function: ease-out; } 82% { translate: 0 -4px; } 100% { translate: 0 0; } }\n",
            "The badge hops each time the count changes. Click the bell to add one.",
            'const button = document.querySelector(".bell");\nconst badge = button.querySelector(".badge");\nlet count = 3;\nbutton.addEventListener("click", () => {\n  count += 1;\n  badge.textContent = count > 9 ? "9+" : count;\n  button.setAttribute("aria-label", `Notifications, ${count} unread`);\n  badge.classList.remove("hit"); void badge.offsetWidth; badge.classList.add("hit");\n});\n',
        ),
        bell(
            "Badge shake",
            ".bell svg { transform-origin: 50% 10%; animation: swing 2.4s ease-in-out infinite; }\n.badge { animation: rattle 2.4s linear infinite; }\n@keyframes swing { 0%, 40%, 100% { rotate: 0deg; } 5%, 25% { rotate: 14deg; } 15%, 35% { rotate: -14deg; } }\n@keyframes rattle { 0%, 40%, 100% { translate: 0 0; } 5%, 25% { translate: 2px 0; } 15%, 35% { translate: -2px 0; } }\n",
            "The bell rings and the badge rattles with it, then both rest before ringing again.",
        ),
        bell(
            "Badge glow",
            ".badge { animation: halo 1.8s ease-in-out infinite alternate; }\n@keyframes halo { from { box-shadow: 0 0 0 0 rgb(248 113 113 / 0); } to { box-shadow: 0 0 14px 4px rgb(248 113 113 / .8); } }\n",
            "A halo in the badge's colour brightens and fades around it.",
        ),
        bell(
            "Notification ping",
            '.badge { min-width: 12px; width: 12px; height: 12px; padding: 0; border: 0; top: -4px; right: -4px; font-size: 0; }\n.badge::before { content: ""; position: absolute; inset: 0; border-radius: 50%; background: var(--danger); animation: ping 1.2s cubic-bezier(0, 0, .2, 1) infinite; }\n@keyframes ping { to { scale: 2.6; opacity: 0; } }\n',
            "An unread dot with a copy of itself expanding and fading behind it.",
        ),
        bell(
            "Notification ripple",
            '.bell::before, .bell::after { content: ""; position: absolute; inset: 0; border: 2px solid var(--accent); border-radius: inherit; animation: ripple 2.2s ease-out infinite; }\n.bell::after { animation-delay: -1.1s; }\n@keyframes ripple { from { opacity: .8; } to { scale: 1.9; opacity: 0; } }\n',
            "Outlines of the whole control spread outward in succession, like rings on water.",
        ),
        bell(
            "Notification burst",
            ".stage { overflow: hidden; }\n.bit { position: absolute; width: 7px; height: 7px; margin: -3.5px; border-radius: 50%; background: var(--tint); animation: fly .7s cubic-bezier(.2, .7, .3, 1) forwards; pointer-events: none; }\n@keyframes fly { to { translate: var(--dx) var(--dy); scale: 0; opacity: 0; } }\n",
            "A new notification throws off a ring of sparks from the badge. Click the bell to trigger one.",
            BURST_JS
            + 'const stage = document.querySelector(".stage");\nconst badge = stage.querySelector(".badge");\nconst TINTS = ["#f87171", "#fbbf24", "#22d3ee", "#ffffff"];\nconst fire = () => {\n  const box = badge.getBoundingClientRect(), frame = stage.getBoundingClientRect();\n  burst(stage, box.left - frame.left + box.width / 2, box.top - frame.top + box.height / 2, 14, (piece, i, count) => {\n    const angle = (i / count) * Math.PI * 2, reach = 40 + Math.random() * 30;\n    piece.style.setProperty("--dx", `${Math.cos(angle) * reach}px`);\n    piece.style.setProperty("--dy", `${Math.sin(angle) * reach}px`);\n    piece.style.setProperty("--tint", TINTS[i % TINTS.length]);\n  });\n};\nstage.querySelector(".bell").addEventListener("click", fire);\nfire();\n',
        ),
        played(
            "Success check animation",
            f'<div class="fx" role="status" aria-label="Success">{CHECK_SVG}</div>',
            CHECK_CSS
            + ".tick circle { transform-origin: center; }\n.tick path { stroke-dasharray: 36; stroke-dashoffset: 36; }\n.go .tick circle { animation: pop .45s cubic-bezier(.2, 1.5, .4, 1) both; }\n.go .tick path { animation: draw .35s .35s ease-out forwards; }\n@keyframes pop { from { scale: 0; } }\n@keyframes draw { to { stroke-dashoffset: 0; } }\n",
            "The disc pops in with a little overshoot, then the tick is drawn across it in one stroke.",
        ),
        played(
            "Success confetti",
            f'<div class="fx" role="status" aria-label="Success">{CHECK_SVG}</div>',
            CHECK_CSS
            + ".stage { overflow: hidden; }\n.bit { position: absolute; width: 8px; height: 12px; margin: -6px -4px; background: var(--tint); animation: toss var(--time) cubic-bezier(.15, .6, .4, 1) forwards; pointer-events: none; }\n/* Out and up quickly, then gravity: the second half of the path falls. */\n@keyframes toss { 45% { translate: var(--dx) var(--dy); rotate: var(--spin); opacity: 1; } 100% { translate: calc(var(--dx) * 1.25) calc(var(--dy) + 170px); rotate: calc(var(--spin) * 2.4); opacity: 0; } }\n",
            "Paper pieces are thrown up and outward from the tick, tumble, and fall.",
            BURST_JS
            + 'const stage = document.querySelector(".stage");\nconst TINTS = ["#7c5cff", "#22d3ee", "#f472b6", "#fbbf24", "#34d399"];\nconst celebrate = () => burst(stage, stage.clientWidth / 2, stage.clientHeight / 2, 36, (piece, i) => {\n  const angle = -Math.PI / 2 + (Math.random() - 0.5) * 2.4, reach = 60 + Math.random() * 110;\n  piece.style.setProperty("--dx", `${Math.cos(angle) * reach}px`);\n  piece.style.setProperty("--dy", `${Math.sin(angle) * reach}px`);\n  piece.style.setProperty("--spin", `${(Math.random() - 0.5) * 720}deg`);\n  piece.style.setProperty("--time", `${1.1 + Math.random() * 0.7}s`);\n  piece.style.setProperty("--tint", TINTS[i % TINTS.length]);\n});\ndocument.querySelector(".replay").addEventListener("click", celebrate);\ncelebrate();\n',
        ),
        played(
            "Success sparkle",
            f'<div class="fx spark" role="status" aria-label="Success">{CHECK_SVG}<i style="--x: -58px; --y: -34px; --d: 0s"></i><i style="--x: 56px; --y: -44px; --d: .15s"></i><i style="--x: 66px; --y: 26px; --d: .3s"></i><i style="--x: -50px; --y: 38px; --d: .45s"></i><i style="--x: 4px; --y: -64px; --d: .25s"></i></div>',
            CHECK_CSS
            + ".spark { position: relative; display: grid; place-items: center; }\n/* A four-pointed star, cut from a square. */\n.spark i { position: absolute; width: 16px; height: 16px; translate: var(--x) var(--y); background: #fde68a; clip-path: polygon(50% 0, 62% 38%, 100% 50%, 62% 62%, 50% 100%, 38% 62%, 0 50%, 38% 38%); scale: 0; }\n.spark.go i { animation: glint .9s var(--d) ease-in-out both; }\n@keyframes glint { 50% { scale: 1; rotate: 90deg; } 100% { scale: 0; rotate: 180deg; } }\n",
            "Small stars wink on and off around the tick, each at a slightly different moment.",
        ),
        played(
            "Error shake",
            '<label class="fx field">Email<input type="email" value="not-an-email" aria-invalid="true" aria-describedby="why"><small id="why">Enter a valid email address.</small></label>',
            ".field { display: grid; gap: 6px; width: 250px; font-size: 13px; font-weight: 600; }\n.field input { padding: 10px 12px; border: 1px solid var(--danger); border-radius: 10px; background: var(--surface); color: inherit; font: inherit; font-weight: 400; }\n.field small { color: var(--danger); font-weight: 400; }\n.field.go { animation: refuse .4s linear; }\n@keyframes refuse { 20%, 60% { translate: -7px 0; } 40%, 80% { translate: 7px 0; } }\n",
            "A quick side-to-side shake, the gesture for 'no': the field refuses the value. The message says why, so the motion is not the only signal.",
        ),
        banner(
            "Error pulse",
            "var(--danger)",
            "!",
            "Payment failed. Check the card details.",
            ".banner { animation: alarm 1.4s ease-out infinite; }\n@keyframes alarm { from { box-shadow: 0 0 0 0 rgb(248 113 113 / .6); } to { box-shadow: 0 0 0 14px rgb(248 113 113 / 0); } }\n",
            "Red rings leave the message and fade: something needs attention now.",
        ),
        banner(
            "Warning pulse",
            "var(--warning)",
            "!",
            "Storage is 92% full.",
            ".banner b { animation: caution 1.2s ease-in-out infinite alternate; }\n@keyframes caution { from { scale: .85; opacity: .6; } to { scale: 1.12; opacity: 1; } }\n",
            "Only the icon swells and dims: a steady caution that leaves the text still enough to read.",
        ),
        banner(
            "Warning glow",
            "var(--warning)",
            "!",
            "Your session expires in 2 minutes.",
            ".banner { animation: ember 2s ease-in-out infinite alternate; }\n@keyframes ember { from { box-shadow: 0 0 0 rgb(251 191 36 / 0); } to { box-shadow: 0 0 26px rgb(251 191 36 / .5), inset 0 0 14px rgb(251 191 36 / .15); border-color: var(--warning); } }\n",
            "An amber glow rises and falls around the whole message.",
        ),
        banner(
            "Info shimmer",
            "var(--accent)",
            "i",
            "A new version is available.",
            '.banner::after { content: ""; position: absolute; inset: 0; background: linear-gradient(100deg, transparent 35%, rgb(255 255 255 / .16) 50%, transparent 65%) 0 0 / 250% 100%; animation: glide 3s ease-in-out infinite; pointer-events: none; }\n@keyframes glide { from { background-position: 150% 0; } 60%, 100% { background-position: -100% 0; } }\n',
            "A pale band crosses the message every few seconds: noticeable, but in no hurry.",
        ),
        status(
            "Status breathing",
            "Online",
            "var(--success)",
            ".dot { animation: breathe 2.4s ease-in-out infinite alternate; }\n@keyframes breathe { from { opacity: .45; scale: .8; } to { opacity: 1; scale: 1.1; box-shadow: 0 0 10px var(--tone); } }\n",
            "A slow rise and fall: alive and well, nothing to do.",
        ),
        status(
            "Status blinking",
            "Recording",
            "var(--danger)",
            ".dot { animation: blink 1s steps(2, jump-none) infinite; }\n@keyframes blink { to { opacity: .15; } }\n",
            "Hard on and off with no fade, like an indicator lamp.",
        ),
        status(
            "Status orbit",
            "Syncing",
            "var(--accent)",
            '.dot { margin: 5px; }\n.dot::after { content: ""; position: absolute; inset: -6px; border-radius: 50%; border: 2px solid transparent; border-top-color: var(--tone); animation: orbit .9s linear infinite; }\n@keyframes orbit { to { rotate: 360deg; } }\n',
            "An arc circling the dot: work is in progress around a steady state.",
        ),
        status(
            "Status wave",
            "Live",
            "var(--danger)",
            ".bars { display: flex; align-items: center; gap: 3px; height: 16px; }\n.bars i { width: 3px; height: 100%; border-radius: 2px; background: var(--tone); animation: level .9s ease-in-out infinite alternate; }\n.bars i:nth-child(2) { animation-delay: -.3s; }\n.bars i:nth-child(3) { animation-delay: -.6s; }\n.bars i:nth-child(4) { animation-delay: -.15s; }\n@keyframes level { from { scale: 1 .25; } to { scale: 1 1; } }\n",
            "Level bars moving out of step: audio or data is flowing right now.",
            dot='<span class="bars" aria-hidden="true"><i></i><i></i><i></i><i></i></span>',
        ),
    ),
)
