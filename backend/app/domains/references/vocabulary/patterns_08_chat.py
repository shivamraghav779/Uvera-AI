"""Patterns 271-300: chat and communication."""

from app.domains.references.vocabulary.base import Item, Section

B = """\
.chat { display: flex; flex-direction: column; gap: 8px; width: min(420px, 100%); }
.b { max-width: 78%; padding: 9px 13px; border-radius: 18px; line-height: 1.45; background: var(--surface-2); align-self: flex-start; }
.b.me { align-self: flex-end; background: var(--primary); color: #fff; }
.av { display: grid; place-items: center; flex: none; width: 30px; height: 30px; border-radius: 50%; font-size: 11px; font-weight: 700;
  background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; }
.meta { font-size: 11px; color: var(--muted); }
"""
LIST = """\
.cl { width: min(360px, 100%); margin: 0; padding: 6px; list-style: none; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }
.cl li { display: grid; grid-template-columns: auto 1fr auto; gap: 10px; align-items: center; padding: 9px; border-radius: 10px; }
.cl li:hover { background: var(--surface-2); }
.cl b { display: block; }
.cl small { display: block; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cl li > div { min-width: 0; }
"""
PEOPLE = [
    ("DW", "Dana Whitfield", "Can you review the pricing page?", "2m", 3),
    ("MT", "Mika Tanaka", "Shipped! 🎉", "1h", 0),
    ("RS", "Ravi Shah", "Let’s sync tomorrow", "3h", 1),
    ("SO", "Sam Okafor", "Thanks for the notes", "Mon", 0),
]


def rows(extra: str = "") -> str:
    return "".join(
        f'<li data-unread="{u}" data-name="{n.lower()}"><span class="av">{i}</span><div><b>{n}</b><small>{m}</small></div><span class="meta">{t}</span>{extra}</li>'
        for i, n, m, t, u in PEOPLE
    )


SECTION = Section(
    "patterns",
    "Chat & Communication",
    271,
    (
        Item(
            "Chat bubble",
            '<div class="chat"><div class="b">Did the deploy go out?</div><div class="b me">Yes — live since 14:02.</div></div>',
            B
            + ".b { border-bottom-left-radius: 6px; }\n.b.me { border-bottom-left-radius: 18px; border-bottom-right-radius: 6px; }\n",
            note="Incoming left and neutral, outgoing right and coloured; the tail corner is the squared one.",
        ),
        Item(
            "Grouped messages",
            '<div class="chat grp"><div class="b first">Morning!</div><div class="b mid">Quick question about the invoice</div><div class="b last">Is the PO number required?</div><div class="b me first">Hey 👋</div><div class="b me last">Only for orders over $5k.</div></div>',
            B
            + ".grp { gap: 2px; }\n.grp .b { border-radius: 6px 18px 18px 6px; }\n.grp .b.first { border-top-left-radius: 18px; }\n.grp .b.last { border-bottom-left-radius: 18px; margin-bottom: 8px; }\n.grp .b.me { border-radius: 18px 6px 6px 18px; }\n.grp .b.me.first { border-top-right-radius: 18px; }\n.grp .b.me.last { border-bottom-right-radius: 18px; }\n",
            note="Consecutive messages from one person sit tight together and share one rounded outline.",
        ),
        Item(
            "Message thread",
            '<div class="thr"><div class="root"><span class="av">DW</span><div><b>Dana</b> <span class="meta">10:14</span><p>Should we delay the launch to Thursday?</p><button aria-expanded="true" aria-controls="replies">3 replies</button></div></div><div class="replies" id="replies"><div><span class="av">MT</span><p><b>Mika</b> Thursday works for eng.</p></div><div><span class="av">RS</span><p><b>Ravi</b> Marketing needs 24h notice.</p></div><div><span class="av">DW</span><p><b>Dana</b> Thursday it is.</p></div></div></div>',
            B
            + ".thr { width: min(440px, 100%); }\n.root { display: flex; gap: 10px; }\n.root p { margin: 2px 0 6px; }\n.root button { padding: 0; border: 0; background: none; color: var(--primary); font-weight: 600; font-size: 13px; }\n.replies { display: grid; gap: 10px; margin: 10px 0 0 14px; padding-left: 24px; border-left: 2px solid var(--border); }\n.replies[hidden] { display: none; }\n.replies div { display: flex; gap: 10px; align-items: flex-start; }\n.replies .av { width: 24px; height: 24px; font-size: 9px; }\n.replies p { margin: 2px 0 0; font-size: 14px; }\n",
            'const button = document.querySelector(".root button");\nconst replies = document.getElementById("replies");\nbutton.addEventListener("click", () => {\n  replies.hidden = !replies.hidden;\n  button.setAttribute("aria-expanded", String(!replies.hidden));\n  button.textContent = replies.hidden ? `Show ${replies.children.length} replies` : `${replies.children.length} replies`;\n});\n',
            "Replies hang from their parent on an indented rail and collapse to a count.",
        ),
        Item(
            "Thread sidebar",
            '<div class="ts"><main><div class="b">Should we delay the launch?</div><button class="open">3 replies →</button></main><aside hidden aria-label="Thread"><header><b>Thread</b><button aria-label="Close thread">×</button></header><div class="b">Should we delay the launch?</div><div class="b me">Thursday works for eng.</div><div class="b">Marketing needs 24h notice.</div></aside></div>',
            B
            + ".ts { display: flex; width: min(600px, 100%); height: 300px; border: 1px solid var(--border); border-radius: 16px; overflow: hidden; background: var(--surface); }\n.ts main { flex: 1; display: flex; flex-direction: column; gap: 8px; padding: 16px; align-items: flex-start; }\n.ts .open { border: 0; background: none; color: var(--primary); font-weight: 600; }\n.ts aside { width: 260px; display: flex; flex-direction: column; gap: 8px; padding: 0 12px 12px; border-left: 1px solid var(--border); background: var(--bg); animation: slide .25s var(--ease); }\n.ts aside[hidden] { display: none; }\n.ts aside header { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; }\n.ts aside header button { border: 0; background: none; color: var(--muted); font-size: 18px; }\n@keyframes slide { from { translate: 30px 0; opacity: 0; } }\n",
            'const aside = document.querySelector(".ts aside");\nconst opener = document.querySelector(".ts .open");\nopener.addEventListener("click", () => { aside.hidden = false; aside.querySelector("button").focus(); });\naside.querySelector("button").addEventListener("click", () => { aside.hidden = true; opener.focus(); });\n',
            "A thread opens in a column beside the main conversation instead of replacing it.",
        ),
        Item(
            "Reply composer",
            '<form class="rc"><div class="quote" hidden><span>Replying to <b>Dana</b>: “Should we delay the launch?”</span><button type="button" aria-label="Cancel reply">×</button></div><div class="line"><textarea rows="1" placeholder="Write a reply…" aria-label="Reply"></textarea><button disabled aria-label="Send">↑</button></div></form><button class="start">Reply to Dana</button>',
            ".rc { width: min(440px, 100%); border: 1px solid var(--border); border-radius: 16px; background: var(--surface); overflow: hidden; }\n.rc:focus-within { border-color: var(--primary); }\n.quote { display: flex; justify-content: space-between; gap: 8px; padding: 8px 12px; border-left: 3px solid var(--primary); background: var(--surface-2); font-size: 13px; color: var(--muted); }\n.quote[hidden] { display: none; }\n.quote b { color: var(--fg); }\n.quote button { border: 0; background: none; color: var(--muted); }\n.line { display: flex; align-items: flex-end; gap: 8px; padding: 8px; }\n.line textarea { flex: 1; max-height: 140px; padding: 6px; border: 0; outline: 0; background: none; resize: none; }\n.line button { width: 34px; height: 34px; border: 0; border-radius: 50%; background: var(--primary); color: #fff; }\n.line button:disabled { opacity: .35; }\n.start { margin-top: 12px; border: 0; background: none; color: var(--primary); }\nbody { align-content: center; justify-items: center; }\n",
            'const form = document.querySelector(".rc");\nconst quote = form.querySelector(".quote");\nconst area = form.querySelector("textarea");\nconst send = form.querySelector(".line button");\nconst fit = () => { area.style.height = "auto"; area.style.height = `${area.scrollHeight}px`; send.disabled = !area.value.trim(); };\ndocument.querySelector(".start").addEventListener("click", () => { quote.hidden = false; area.focus(); });\nquote.querySelector("button").addEventListener("click", () => { quote.hidden = true; area.focus(); });\narea.addEventListener("input", fit);\narea.addEventListener("keydown", (event) => {\n  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); form.requestSubmit(); }\n  if (event.key === "Escape") quote.hidden = true;\n});\nform.addEventListener("submit", (event) => { event.preventDefault(); if (!area.value.trim()) return; area.value = ""; quote.hidden = true; fit(); });\n',
            "The message being answered is quoted above the field and can be dismissed.",
        ),
        Item(
            "Mention system",
            '<p class="mt">Thanks <a class="mention" href="#" data-id="dana">@Dana</a> and <a class="mention me" href="#" data-id="you">@you</a> — <a class="mention grp" href="#">@design-team</a> please review by Friday.</p>',
            ".mt { max-width: 420px; line-height: 1.8; }\n.mention { padding: 1px 6px; border-radius: 6px; background: color-mix(in srgb, var(--primary) 20%, transparent); color: var(--primary); font-weight: 600; text-decoration: none; }\n.mention:hover { background: color-mix(in srgb, var(--primary) 35%, transparent); }\n.mention.me { background: color-mix(in srgb, var(--warning) 25%, transparent); color: var(--warning); }\n.mention.grp { background: color-mix(in srgb, var(--accent) 20%, transparent); color: var(--accent); }\n",
            note="Mentions render as chips: a person, yourself (highlighted differently) and a group.",
        ),
        Item(
            "Reaction picker",
            '<div class="rp"><div class="b">Shipped the new dashboard!</div><div class="bar" role="toolbar" aria-label="React"><button aria-label="Like">👍</button><button aria-label="Love">❤️</button><button aria-label="Laugh">😂</button><button aria-label="Celebrate">🎉</button><button aria-label="Eyes">👀</button></div><div class="got" aria-live="polite"></div></div>',
            B
            + ".rp { position: relative; display: grid; gap: 8px; padding-top: 44px; }\n.bar { position: absolute; top: 0; left: 0; display: flex; gap: 2px; padding: 4px; border: 1px solid var(--border); border-radius: 999px; background: var(--surface); box-shadow: var(--shadow); }\n.bar button { width: 34px; height: 34px; border: 0; border-radius: 50%; background: none; font-size: 18px; transition: scale .15s var(--ease), translate .15s var(--ease); }\n.bar button:hover, .bar button:focus-visible { scale: 1.4; translate: 0 -5px; }\n.got { min-height: 26px; font-size: 20px; }\n",
            'const got = document.querySelector(".got");\ndocument.querySelector(".bar").addEventListener("click", (event) => { const button = event.target.closest("button"); if (button) got.textContent = button.textContent; });\n',
            "A row of the most used reactions; the one under the pointer lifts and grows.",
        ),
        Item(
            "Message reactions",
            '<div class="mr"><div class="b">Shipped the new dashboard!</div><div class="rx"><button aria-pressed="true" data-n="4">🎉 <span>4</span></button><button aria-pressed="false" data-n="2">👍 <span>2</span></button><button aria-pressed="false" data-n="1">👀 <span>1</span></button></div></div>',
            B
            + '.mr { display: grid; gap: 6px; }\n.rx { display: flex; gap: 6px; }\n.rx button { display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px; border: 1px solid var(--border); border-radius: 999px; background: var(--surface); font-size: 13px; }\n.rx button[aria-pressed="true"] { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 20%, transparent); }\n.rx span { font-variant-numeric: tabular-nums; font-weight: 600; }\n',
            'document.querySelectorAll(".rx button").forEach((button) => button.addEventListener("click", () => {\n  const mine = button.getAttribute("aria-pressed") === "true";\n  const count = Number(button.dataset.n) + (mine ? -1 : 1);\n  button.dataset.n = String(count);\n  button.setAttribute("aria-pressed", String(!mine));\n  if (count === 0) button.remove(); else button.querySelector("span").textContent = String(count);  // a reaction nobody holds disappears\n}));\n',
            "Counted reactions under a message; yours are outlined and toggle on click.",
        ),
        Item(
            "Read receipts",
            '<div class="chat"><div class="b me">Sent the contract over.</div><div class="rr" data-s="sent"><svg viewBox="0 0 22 12" width="20" height="11" aria-hidden="true"><path d="M1 6l4 4 7-9"/><path class="two" d="M9 10l1 0 7-9"/></svg><span></span></div><button class="adv">Advance status</button></div>',
            B
            + ".rr { display: flex; align-items: center; gap: 5px; align-self: flex-end; font-size: 11px; color: var(--muted); }\n.rr path { fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }\n.rr .two { opacity: 0; }\n.rr[data-s=delivered] .two, .rr[data-s=read] .two { opacity: 1; }\n.rr[data-s=read] svg { color: var(--accent); }\n.adv { align-self: flex-end; border: 0; background: none; color: var(--primary); font-size: 13px; }\n",
            'const STATES = [["sent", "Sent"], ["delivered", "Delivered"], ["read", "Read 14:06"]];\nconst receipt = document.querySelector(".rr");\nlet index = 0;\nconst render = () => { receipt.dataset.s = STATES[index][0]; receipt.querySelector("span").textContent = STATES[index][1]; };\ndocument.querySelector(".adv").addEventListener("click", () => { index = (index + 1) % STATES.length; render(); });\nrender();\n',
            "One tick sent, two delivered, coloured when read, always with the word beside the icon.",
        ),
        Item(
            "Typing indicator",
            '<div class="chat"><div class="b ty" role="status" aria-label="Dana is typing"><i></i><i></i><i></i></div><span class="meta">Dana is typing…</span></div>',
            B
            + ".ty { display: flex; gap: 4px; padding: 13px 14px; }\n.ty i { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); animation: hop 1.2s ease-in-out infinite; }\n.ty i:nth-child(2) { animation-delay: .15s; }\n.ty i:nth-child(3) { animation-delay: .3s; }\n@keyframes hop { 0%, 60%, 100% { translate: 0 0; opacity: .5; } 30% { translate: 0 -5px; opacity: 1; } }\n",
            note="Three dots bouncing in sequence inside a bubble, with a spoken label.",
        ),
        Item(
            "Presence indicator",
            '<div class="pr"><span class="av on">DW</span><span class="av away">MT</span><span class="av busy">RS</span><span class="av off">SO</span></div>',
            B
            + '.pr { display: flex; gap: 16px; }\n.pr .av { position: relative; width: 44px; height: 44px; font-size: 13px; }\n.pr .av::after { content: ""; position: absolute; right: -1px; bottom: -1px; width: 12px; height: 12px; border-radius: 50%; border: 3px solid var(--bg); background: var(--c); }\n.on { --c: var(--success); }\n.away { --c: var(--warning); }\n.busy { --c: var(--danger); }\n.off { --c: var(--muted); }\n.off::after { background: var(--bg) !important; box-shadow: inset 0 0 0 2px var(--muted); }\n',
            note="A dot on the avatar: available, away, busy, offline (hollow, so it differs by shape too).",
        ),
        Item(
            "Online status",
            '<div class="os"><span class="av">DW</span><div><b>Dana Whitfield</b><small><i class="dot"></i><span></span></small></div></div>',
            B
            + ".os { display: flex; gap: 12px; align-items: center; }\n.os small { display: flex; align-items: center; gap: 6px; color: var(--muted); }\n.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); }\n.dot.live { background: var(--success); box-shadow: 0 0 0 0 var(--success); animation: ping 2s ease-out infinite; }\n@keyframes ping { to { box-shadow: 0 0 0 8px transparent; } }\n",
            'const dot = document.querySelector(".dot");\nconst label = document.querySelector(".os small span");\nconst lastSeen = Date.now() - 4 * 60 * 1000;\nconst relative = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });\n// The browser\'s own connectivity stands in for the other person\'s presence feed here.\nconst render = () => {\n  const online = navigator.onLine;\n  dot.classList.toggle("live", online);\n  label.textContent = online ? "Online now" : `Last seen ${relative.format(-Math.round((Date.now() - lastSeen) / 60000), "minute")}`;\n};\naddEventListener("online", render);\naddEventListener("offline", render);\nrender();\n',
            "Online now with a pulse, otherwise 'last seen' as a relative time.",
        ),
        Item(
            "Voice message",
            '<div class="vm b me"><button aria-label="Play voice message">▶</button><div class="wave" role="slider" aria-label="Position" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" tabindex="0"></div><span class="t">0:14</span></div>',
            B
            + ".vm { display: flex; align-items: center; gap: 10px; width: 280px; max-width: none; }\n.vm button { flex: none; width: 34px; height: 34px; border: 0; border-radius: 50%; background: rgb(255 255 255 / .22); color: #fff; }\n.wave { flex: 1; display: flex; align-items: center; gap: 2px; height: 30px; cursor: pointer; }\n.wave i { flex: 1; border-radius: 2px; background: rgb(255 255 255 / .4); }\n.wave i.played { background: #fff; }\n.t { font: 11px var(--mono); }\n",
            'const DURATION = 14;\nconst wave = document.querySelector(".wave");\nconst button = document.querySelector(".vm button");\nconst time = document.querySelector(".vm .t");\n// Bar heights would come from the audio\'s peaks; a fixed shape stands in.\nconst bars = Array.from({ length: 36 }, (_, i) => { const bar = document.createElement("i"); bar.style.height = `${20 + Math.abs(Math.sin(i * 0.9) * Math.cos(i * 0.31)) * 80}%`; wave.append(bar); return bar; });\nlet position = 0, timer = null;\nconst render = () => {\n  bars.forEach((bar, i) => bar.classList.toggle("played", i / bars.length < position));\n  const left = Math.round(DURATION * (1 - position));\n  time.textContent = `0:${String(left).padStart(2, "0")}`;\n  wave.setAttribute("aria-valuenow", String(Math.round(position * 100)));\n};\nconst stop = () => { clearInterval(timer); timer = null; button.textContent = "▶"; button.setAttribute("aria-label", "Play voice message"); };\nbutton.addEventListener("click", () => {\n  if (timer) { stop(); return; }\n  if (position >= 1) position = 0;\n  button.textContent = "❚❚";\n  button.setAttribute("aria-label", "Pause voice message");\n  timer = setInterval(() => { position = Math.min(1, position + 0.1 / DURATION); render(); if (position >= 1) stop(); }, 100);\n});\nwave.addEventListener("click", (event) => { const box = wave.getBoundingClientRect(); position = (event.clientX - box.left) / box.width; render(); });\nwave.addEventListener("keydown", (event) => { if (event.key === "ArrowRight") position = Math.min(1, position + 0.05); else if (event.key === "ArrowLeft") position = Math.max(0, position - 0.05); else return; render(); });\nrender();\n',
            "A waveform that doubles as the scrubber, with play, pause and time remaining.",
        ),
        Item(
            "Audio player",
            '<div class="ap"><button class="pp" aria-label="Play">▶</button><div class="mid"><b>Weekly sync — 14 May</b><input type="range" min="0" max="1000" value="0" aria-label="Seek"><div class="tm"><span class="cur">0:00</span><span class="dur">0:00</span></div></div><button class="rate" aria-label="Playback speed">1×</button><audio preload="metadata"></audio></div>',
            ".ap { display: flex; align-items: center; gap: 12px; width: min(440px, 100%); padding: 12px 14px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.pp { flex: none; width: 42px; height: 42px; border: 0; border-radius: 50%; background: var(--primary); color: #fff; }\n.mid { flex: 1; min-width: 0; display: grid; gap: 4px; }\n.mid input { width: 100%; accent-color: var(--primary); }\n.tm { display: flex; justify-content: space-between; font: 11px var(--mono); color: var(--muted); }\n.rate { flex: none; width: 40px; height: 28px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); font-size: 12px; }\n",
            '// A one-second tone generated in the page, so the player has something real to play offline.\nconst tone = () => {\n  const rate = 8000, seconds = 3, samples = rate * seconds;\n  const buffer = new ArrayBuffer(44 + samples * 2), view = new DataView(buffer);\n  const text = (offset, value) => [...value].forEach((char, i) => view.setUint8(offset + i, char.charCodeAt(0)));\n  text(0, "RIFF"); view.setUint32(4, 36 + samples * 2, true); text(8, "WAVEfmt "); view.setUint32(16, 16, true);\n  view.setUint16(20, 1, true); view.setUint16(22, 1, true); view.setUint32(24, rate, true); view.setUint32(28, rate * 2, true);\n  view.setUint16(32, 2, true); view.setUint16(34, 16, true); text(36, "data"); view.setUint32(40, samples * 2, true);\n  for (let i = 0; i < samples; i += 1) view.setInt16(44 + i * 2, Math.sin(i / rate * 2 * Math.PI * 330) * 6000 * (1 - i / samples), true);\n  return URL.createObjectURL(new Blob([buffer], { type: "audio/wav" }));\n};\nconst audio = document.querySelector(".ap audio");\nconst play = document.querySelector(".pp");\nconst seek = document.querySelector(".ap input");\nconst clock = (seconds) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}`;\naudio.src = tone();\naudio.addEventListener("loadedmetadata", () => { document.querySelector(".dur").textContent = clock(audio.duration); });\naudio.addEventListener("timeupdate", () => { seek.value = String((audio.currentTime / audio.duration) * 1000 || 0); document.querySelector(".cur").textContent = clock(audio.currentTime); });\nconst sync = () => { play.textContent = audio.paused ? "▶" : "❚❚"; play.setAttribute("aria-label", audio.paused ? "Play" : "Pause"); };\naudio.addEventListener("play", sync); audio.addEventListener("pause", sync); audio.addEventListener("ended", sync);\nplay.addEventListener("click", () => { if (audio.paused) audio.play().catch(() => {}); else audio.pause(); });\nseek.addEventListener("input", () => { audio.currentTime = (seek.value / 1000) * audio.duration; });\nconst RATES = [1, 1.5, 2];\ndocument.querySelector(".rate").addEventListener("click", (event) => { audio.playbackRate = RATES[(RATES.indexOf(audio.playbackRate) + 1) % RATES.length]; event.target.textContent = `${audio.playbackRate}×`; });\n',
            "A real <audio> element driven by custom controls: play, seek, time and playback speed.",
        ),
        Item(
            "Video message",
            '<div class="vd"><div class="clip" tabindex="0" role="button" aria-label="Play video message, 0:42"><span class="play">▶</span><span class="len">0:42</span><div class="ring"></div></div></div>',
            ".vd { display: grid; place-items: center; }\n.clip { position: relative; display: grid; place-items: center; width: 180px; height: 180px; border-radius: 50%; overflow: hidden; cursor: pointer; background: radial-gradient(circle at 35% 30%, #a78bfa, #1e1b4b); }\n.play { display: grid; place-items: center; width: 52px; height: 52px; border-radius: 50%; background: rgb(0 0 0 / .45); color: #fff; backdrop-filter: blur(6px); transition: scale .2s var(--ease); }\n.clip:hover .play { scale: 1.1; }\n.len { position: absolute; bottom: 22px; padding: 1px 8px; border-radius: 99px; background: rgb(0 0 0 / .55); font: 11px var(--mono); color: #fff; }\n.ring { position: absolute; inset: 0; border-radius: 50%; padding: 4px; background: conic-gradient(var(--accent) var(--p, 0%), transparent 0); mask: linear-gradient(#000 0 0) content-box exclude, linear-gradient(#000 0 0); }\n.clip.playing .play { opacity: 0; }\n",
            'const clip = document.querySelector(".clip");\nlet progress = 0, timer = null;\nconst toggle = () => {\n  if (timer) { clearInterval(timer); timer = null; clip.classList.remove("playing"); return; }\n  if (progress >= 100) progress = 0;\n  clip.classList.add("playing");\n  timer = setInterval(() => {\n    progress += 1;\n    clip.style.setProperty("--p", `${progress}%`);\n    if (progress >= 100) { clearInterval(timer); timer = null; clip.classList.remove("playing"); }\n  }, 60);\n};\nclip.addEventListener("click", toggle);\nclip.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); toggle(); } });\n',
            "A round video note whose border fills as it plays.",
        ),
        Item(
            "Attachment preview",
            '<div class="att"><figure><div class="img"></div><figcaption>mockup-v3.png<small>1.2 MB</small></figcaption><button aria-label="Remove mockup-v3.png">×</button></figure><figure><div class="doc">PDF</div><figcaption>contract.pdf<small>284 KB</small></figcaption><button aria-label="Remove contract.pdf">×</button></figure></div>',
            ".att { display: flex; gap: 10px; }\n.att figure { position: relative; width: 150px; margin: 0; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: var(--surface); }\n.img { height: 90px; background: linear-gradient(135deg, #f472b6, #7c5cff 60%, #22d3ee); }\n.doc { display: grid; place-items: center; height: 90px; background: var(--surface-2); color: var(--danger); font: 700 14px var(--mono); }\n.att figcaption { padding: 8px 10px; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.att small { display: block; color: var(--muted); }\n.att button { position: absolute; top: 6px; right: 6px; width: 22px; height: 22px; border: 0; border-radius: 50%; background: rgb(0 0 0 / .6); color: #fff; line-height: 1; }\n",
            'document.querySelector(".att").addEventListener("click", (event) => event.target.closest("button")?.closest("figure").remove());\n',
            "Thumbnails of what is about to be sent, each with its size and a remove button.",
        ),
        Item(
            "Link preview",
            '<a class="lp" href="#"><div class="img"></div><div class="tx"><small>northwind.io</small><b>Designing with tokens</b><p>How one palette becomes forty themes without forty stylesheets.</p></div></a>',
            ".lp { display: grid; grid-template-columns: 120px 1fr; width: min(420px, 100%); border: 1px solid var(--border); border-left: 3px solid var(--primary); border-radius: 12px; overflow: hidden; background: var(--surface); color: var(--fg); text-decoration: none; transition: background .15s; }\n.lp:hover { background: var(--surface-2); }\n.lp .img { background: linear-gradient(135deg, #1e1b4b, #7c5cff); }\n.tx { padding: 10px 12px; min-width: 0; }\n.tx small { color: var(--muted); }\n.tx b { display: block; }\n.tx p { margin: 2px 0 0; color: var(--muted); font-size: 13px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }\n",
            note="An unfurled link: site, title and a two-line description beside its image.",
        ),
        Item(
            "Rich message card",
            '<div class="rmc"><header><span class="av">⚙</span><b>Deploy bot</b><span class="meta">14:02</span></header><h4>Deploy #482 succeeded</h4><dl><div><dt>Branch</dt><dd>main</dd></div><div><dt>Duration</dt><dd>2m 14s</dd></div><div><dt>Tests</dt><dd>412 passed</dd></div></dl><footer><button>View logs</button><button>Roll back</button></footer></div>',
            B
            + ".rmc { width: min(380px, 100%); padding: 12px 14px; border: 1px solid var(--border); border-left: 3px solid var(--success); border-radius: 12px; background: var(--surface); }\n.rmc header { display: flex; align-items: center; gap: 8px; }\n.rmc header .meta { margin-left: auto; }\n.rmc .av { width: 24px; height: 24px; }\n.rmc h4 { margin: 10px 0; }\n.rmc dl { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 0 0 12px; }\n.rmc dt { font-size: 11px; color: var(--muted); }\n.rmc dd { margin: 0; font-weight: 600; font-size: 14px; }\n.rmc footer { display: flex; gap: 8px; }\n.rmc footer button { padding: 5px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); font-size: 13px; }\n",
            note="A structured message from an integration: a title, a few fields, actions.",
        ),
        Item(
            "System message",
            '<div class="chat"><div class="b">See you at 3.</div><p class="sys">Dana added Mika to the conversation</p><p class="sys">Conversation renamed to <b>Launch week</b></p></div>',
            B
            + ".sys { align-self: center; margin: 4px 0; padding: 2px 12px; border-radius: 99px; background: var(--surface); color: var(--muted); font-size: 12px; text-align: center; }\n.sys b { color: var(--fg); }\n",
            note="Events, not speech: centred, small and without a bubble or an author.",
        ),
        Item(
            "Pinned message",
            '<div class="pin"><div class="pinbar"><span>📌</span><div><small>Pinned by Dana</small><p>Launch is Thursday 10:00 UTC. Freeze is Wednesday 18:00.</p></div><button aria-label="Unpin">×</button></div><div class="chat"><div class="b">Got it.</div><div class="b me">Freeze reminder set.</div></div></div>',
            B
            + ".pin { width: min(420px, 100%); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; background: var(--surface); }\n.pinbar { display: flex; gap: 10px; align-items: flex-start; padding: 10px 12px; border-bottom: 1px solid var(--border); background: color-mix(in srgb, var(--warning) 10%, var(--surface)); }\n.pinbar div { flex: 1; }\n.pinbar small { color: var(--muted); }\n.pinbar p { margin: 0; font-size: 14px; }\n.pinbar button { border: 0; background: none; color: var(--muted); }\n.pin .chat { padding: 14px; width: auto; }\n",
            'document.querySelector(".pinbar button").addEventListener("click", (event) => event.target.closest(".pinbar").remove());\n',
            "One message held at the top of the conversation, saying who pinned it.",
        ),
        Item(
            "Message search",
            '<div class="ms2"><label><input type="search" placeholder="Search in conversation" aria-label="Search in conversation"><span class="n"></span><button aria-label="Previous match">↑</button><button aria-label="Next match">↓</button></label><div class="chat"><div class="b">The launch checklist is in the launch folder.</div><div class="b me">Is the launch still Thursday?</div><div class="b">Yes, launch at 10:00.</div></div></div>',
            B
            + ".ms2 { display: grid; gap: 12px; width: min(420px, 100%); }\n.ms2 label { display: flex; align-items: center; gap: 6px; padding: 0 8px 0 12px; height: 40px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.ms2 input { flex: 1; min-width: 0; border: 0; outline: 0; background: none; }\n.ms2 .n { font: 11px var(--mono); color: var(--muted); }\n.ms2 label button { width: 26px; height: 26px; border: 0; border-radius: 7px; background: var(--surface-2); }\n.ms2 mark { background: color-mix(in srgb, var(--warning) 45%, transparent); color: inherit; border-radius: 3px; }\n.ms2 mark.cur { background: var(--warning); color: #1a1205; }\n",
            'const input = document.querySelector(".ms2 input");\nconst counter = document.querySelector(".ms2 .n");\nconst bubbles = [...document.querySelectorAll(".ms2 .b")];\nconst originals = bubbles.map((bubble) => bubble.textContent);\nlet marks = [], current = 0;\nconst show = () => { marks.forEach((mark, i) => mark.classList.toggle("cur", i === current)); marks[current]?.scrollIntoView({ block: "nearest" }); counter.textContent = marks.length ? `${current + 1}/${marks.length}` : input.value ? "0" : ""; };\nconst search = () => {\n  const query = input.value.trim();\n  bubbles.forEach((bubble, i) => {\n    bubble.textContent = originals[i];\n    if (!query) return;\n    const parts = originals[i].split(new RegExp(`(${query.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&")})`, "gi"));  // escaped: the query is text, not a pattern\n    bubble.replaceChildren(...parts.map((part, j) => j % 2 ? Object.assign(document.createElement("mark"), { textContent: part }) : part));\n  });\n  marks = [...document.querySelectorAll(".ms2 mark")];\n  current = 0;\n  show();\n};\nconst [previous, next] = document.querySelectorAll(".ms2 label button");\nconst step = (delta) => { if (marks.length) { current = (current + delta + marks.length) % marks.length; show(); } };\nprevious.addEventListener("click", () => step(-1));\nnext.addEventListener("click", () => step(1));\ninput.addEventListener("input", search);\ninput.addEventListener("keydown", (event) => { if (event.key === "Enter") step(event.shiftKey ? -1 : 1); });\n',
            "Find within one conversation: matches are highlighted, counted and stepped through.",
        ),
        Item(
            "Chat search",
            '<div class="cs"><input type="search" placeholder="Search people and messages" aria-label="Search chats"><ul class="cl">'
            + rows()
            + '</ul><p class="none" hidden>No conversations match.</p></div>',
            B
            + LIST
            + ".cs { display: grid; gap: 8px; width: min(360px, 100%); }\n.cs input { height: 40px; padding: 0 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.none { margin: 0; text-align: center; color: var(--muted); }\n",
            'const items = [...document.querySelectorAll(".cs li")];\nconst none = document.querySelector(".none");\ndocument.querySelector(".cs input").addEventListener("input", (event) => {\n  const query = event.target.value.trim().toLowerCase();\n  let shown = 0;\n  for (const item of items) { item.hidden = !item.textContent.toLowerCase().includes(query); if (!item.hidden) shown += 1; }\n  none.hidden = shown > 0;\n});\n',
            "Search across all conversations by person or message text, with an empty result stated.",
        ),
        Item(
            "Conversation filter",
            '<div class="cfl"><div class="tabs" role="tablist"><button role="tab" aria-selected="true" data-f="all">All</button><button role="tab" aria-selected="false" data-f="unread">Unread <span></span></button><button role="tab" aria-selected="false" data-f="mentions">Mentions</button></div><ul class="cl">'
            + rows()
            + "</ul></div>",
            B
            + LIST
            + '.cfl { display: grid; gap: 8px; width: min(360px, 100%); }\n.tabs { display: flex; gap: 4px; }\n.tabs button { padding: 5px 12px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface); color: var(--muted); font-size: 13px; }\n.tabs button[aria-selected="true"] { background: var(--fg); color: var(--bg); border-color: var(--fg); }\n.tabs span { font-weight: 700; }\n',
            'const tabs = [...document.querySelectorAll(".cfl [role=tab]")];\nconst items = [...document.querySelectorAll(".cfl li")];\nconst TESTS = { all: () => true, unread: (item) => Number(item.dataset.unread) > 0, mentions: (item) => item.dataset.name.startsWith("dana") };\ntabs[1].querySelector("span").textContent = String(items.filter(TESTS.unread).length);\ntabs.forEach((tab) => tab.addEventListener("click", () => {\n  tabs.forEach((item) => item.setAttribute("aria-selected", String(item === tab)));\n  items.forEach((item) => { item.hidden = !TESTS[tab.dataset.f](item); });\n}));\n',
            "All, Unread (with its count) and Mentions as pill tabs above the list.",
        ),
        Item(
            "Conversation labels",
            '<ul class="cl lb">'
            + "".join(
                f'<li><span class="av">{i}</span><div><b>{n}</b><small>{m}</small></div><span class="tag {c}">{t}</span></li>'
                for (i, n, m, _, _), (t, c) in zip(
                    PEOPLE,
                    [("Customer", "a"), ("Internal", "b"), ("Urgent", "c"), ("Billing", "d")],
                    strict=True,
                )
            )
            + "</ul>",
            B
            + LIST
            + ".tag { padding: 1px 9px; border-radius: 6px; font-size: 11px; font-weight: 700; background: color-mix(in srgb, var(--c) 20%, transparent); color: var(--c); }\n.a { --c: var(--accent); }\n.b { --c: var(--primary); }\n.c { --c: var(--danger); }\n.d { --c: var(--warning); }\n",
            note="A coloured, named label on each conversation for triage.",
        ),
        Item(
            "Unread counter",
            '<ul class="cl uc">' + rows('<i class="cnt"></i>') + "</ul>",
            B
            + LIST
            + '.uc li { grid-template-columns: auto 1fr auto auto; }\n.cnt { display: grid; place-items: center; min-width: 20px; height: 20px; padding: 0 6px; border-radius: 99px; background: var(--primary); color: #fff; font: 700 11px var(--font); font-style: normal; }\n.cnt:empty { display: none; }\n.uc li[data-unread="0"] b { font-weight: 500; }\n.uc li:not([data-unread="0"]) small { color: var(--fg); }\n',
            'document.querySelectorAll(".uc li").forEach((item) => {\n  const count = Number(item.dataset.unread);\n  item.querySelector(".cnt").textContent = count > 99 ? "99+" : count > 0 ? String(count) : "";\n  // Opening a conversation reads it.\n  item.addEventListener("click", () => { item.dataset.unread = "0"; item.querySelector(".cnt").textContent = ""; });\n});\n',
            "A count pill on unread conversations, capped at 99+, cleared when opened.",
        ),
        Item(
            "Notification badge",
            '<div class="nb"><button aria-label="Notifications, 3 unread"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M6 9a6 6 0 1 1 12 0c0 6 2.500 7 2.500 7h-17S6 15 6 9zM10 20a2 2 0 0 0 4 0"/></svg><i>3</i></button><button aria-label="Messages, new activity"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M4 5h16v11H9l-5 4z"/></svg><i class="dot"></i></button></div>',
            ".nb { display: flex; gap: 16px; }\n.nb button { position: relative; display: grid; place-items: center; width: 44px; height: 44px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.nb i { position: absolute; top: -5px; right: -5px; display: grid; place-items: center; min-width: 18px; height: 18px; padding: 0 5px; border-radius: 99px; background: var(--danger); color: #fff; font: 700 10px var(--font); box-shadow: 0 0 0 2px var(--bg); }\n.nb i.dot { min-width: 10px; width: 10px; height: 10px; padding: 0; top: -3px; right: -3px; }\n",
            note="A count when the number matters, a plain dot when only 'something new' does; both in the accessible name.",
        ),
        Item(
            "Message timestamp",
            '<div class="chat"><div class="b">Did the deploy go out?</div><time class="stamp" datetime="">—</time><div class="b me">Yes — live now.</div><time class="stamp me" datetime="">—</time></div>',
            B
            + ".stamp { font-size: 11px; color: var(--muted); margin: -4px 6px 4px; cursor: default; }\n.stamp.me { align-self: flex-end; }\n",
            'const relative = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });\nconst stamps = [...document.querySelectorAll(".stamp")];\nconst times = [Date.now() - 26 * 60 * 1000, Date.now() - 40 * 1000];\nconst label = (at) => {\n  const seconds = Math.round((Date.now() - at) / 1000);\n  if (seconds < 60) return "just now";\n  if (seconds < 3600) return relative.format(-Math.floor(seconds / 60), "minute");\n  if (seconds < 86400) return relative.format(-Math.floor(seconds / 3600), "hour");\n  return new Date(at).toLocaleDateString(undefined, { day: "numeric", month: "short" });\n};\nconst render = () => stamps.forEach((stamp, i) => {\n  stamp.textContent = label(times[i]);\n  stamp.dateTime = new Date(times[i]).toISOString();\n  stamp.title = new Date(times[i]).toLocaleString();  // the exact time on hover\n});\nrender();\nsetInterval(render, 30000);\n',
            "Relative while recent, a date when old, the exact time on hover, kept current on a timer.",
        ),
        Item(
            "Message grouping",
            '<div class="mg"></div>',
            B
            + ".mg { display: grid; gap: 2px; width: min(420px, 100%); }\n.mg .head { display: flex; gap: 8px; align-items: baseline; margin-top: 12px; }\n.mg .head:first-child { margin-top: 0; }\n.mg p { margin: 0; padding: 1px 0 1px 38px; }\n.mg .head + p { margin-top: -22px; }\n.mg .av { margin-right: 0; }\n.mg .head b { margin-left: 0; }\n",
            '// Messages by the same person within five minutes share one header.\nconst WINDOW = 5 * 60 * 1000;\nconst messages = [["Dana", 0, "Morning!"], ["Dana", 1, "Quick question about the invoice"], ["Dana", 2, "Is the PO number required?"], ["Mika", 3, "Only above $5k."], ["Dana", 30, "Perfect, thanks."]];\nconst root = document.querySelector(".mg");\nlet previous = null;\nfor (const [author, minute, text] of messages) {\n  const at = minute * 60 * 1000;\n  if (!previous || previous.author !== author || at - previous.at > WINDOW) {\n    const head = document.createElement("div");\n    head.className = "head";\n    head.append(Object.assign(document.createElement("span"), { className: "av", textContent: author[0] }), Object.assign(document.createElement("b"), { textContent: author }), Object.assign(document.createElement("span"), { className: "meta", textContent: `10:${String(minute).padStart(2, "0")}` }));\n    root.append(head);\n  }\n  root.append(Object.assign(document.createElement("p"), { textContent: text }));\n  previous = { author, at };\n}\n',
            "The grouping rule itself: same author within five minutes means no repeated avatar or name.",
        ),
        Item(
            "Chat divider",
            '<div class="chat"><div class="b">See you tomorrow.</div><div class="dv" role="separator"><span>Today</span></div><div class="b me">Morning!</div><div class="dv new" role="separator"><span>New messages</span></div><div class="b">Did you see the report?</div></div>',
            B
            + '.dv { display: flex; align-items: center; gap: 10px; margin: 6px 0; font-size: 12px; color: var(--muted); }\n.dv::before, .dv::after { content: ""; flex: 1; height: 1px; background: var(--border); }\n.dv.new { color: var(--danger); }\n.dv.new::before, .dv.new::after { background: color-mix(in srgb, var(--danger) 50%, transparent); }\n',
            note="A labelled rule between days, and a coloured one where unread messages begin.",
        ),
        Item(
            "Conversation summary",
            '<aside class="sum"><header><span class="spark">✦</span><b>Summary</b><small>42 messages · 3 people</small></header><ul><li>Launch moves to <b>Thursday 10:00 UTC</b>.</li><li>Code freeze is Wednesday 18:00.</li><li>Ravi needs the press copy by Tuesday.</li></ul><footer><b>Open questions</b><p>Who is on call during launch?</p></footer></aside>',
            ".sum { width: min(400px, 100%); border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.sum header { display: flex; align-items: center; gap: 8px; padding: 12px 14px; border-bottom: 1px solid var(--border); }\n.sum header small { margin-left: auto; color: var(--muted); }\n.spark { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 7px; font-size: 11px; color: #fff; background: linear-gradient(135deg, var(--primary), var(--accent)); }\n.sum ul { margin: 0; padding: 12px 14px 12px 32px; display: grid; gap: 6px; }\n.sum footer { padding: 12px 14px; border-top: 1px solid var(--border); background: var(--surface-2); border-radius: 0 0 16px 16px; }\n.sum footer p { margin: 4px 0 0; color: var(--muted); font-size: 14px; }\n",
            note="A long thread condensed: what was decided, then what is still open.",
        ),
    ),
)
