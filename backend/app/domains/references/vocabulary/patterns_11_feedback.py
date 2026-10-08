"""Patterns 371-400: feedback and status."""

from app.domains.references.vocabulary.base import BTN, Item, Section

GLYPH = {"success": "✓", "danger": "×", "warning": "!", "accent": "i"}
MSG = """\
.msg { display: flex; gap: 12px; align-items: flex-start; width: min(440px, 100%); padding: 12px 14px; border-radius: 12px; --tone: var(--accent);
  border: 1px solid color-mix(in srgb, var(--tone) 45%, transparent); background: color-mix(in srgb, var(--tone) 10%, var(--surface)); }
.msg .g { display: grid; place-items: center; flex: none; width: 22px; height: 22px; border-radius: 50%; background: var(--tone); color: #0b0d12; font-size: 12px; font-weight: 800; }
.msg b { display: block; }
.msg p { margin: 2px 0 0; color: var(--muted); font-size: 14px; }
.msg .x { margin-left: auto; border: 0; background: none; color: var(--muted); font-size: 16px; }
"""
STATE = (
    BTN
    + """\
.state { display: grid; justify-items: center; gap: 8px; width: min(380px, 100%); padding: 28px 20px; text-align: center; border: 1px solid var(--border);
  border-radius: 18px; background: var(--surface); --tone: var(--accent); }
.state .orb { display: grid; place-items: center; width: 56px; height: 56px; margin-bottom: 6px; border-radius: 50%; font-size: 24px; font-weight: 800;
  background: color-mix(in srgb, var(--tone) 20%, transparent); color: var(--tone); }
.state h3 { margin: 0; font-size: 18px; }
.state p { margin: 0; color: var(--muted); max-width: 30ch; }
.state .btn { margin-top: 10px; }
"""
)
JOB = """\
.job { display: grid; grid-template-columns: auto 1fr auto; gap: 12px; align-items: center; width: min(440px, 100%); padding: 12px 14px;
  border: 1px solid var(--border); border-radius: 14px; background: var(--surface); --tone: var(--muted); }
.job .dot { display: grid; place-items: center; width: 30px; height: 30px; border-radius: 50%; background: color-mix(in srgb, var(--tone) 20%, transparent); color: var(--tone); font-weight: 800; }
.job b { display: block; }
.job small { color: var(--muted); }
.job .tag { padding: 2px 10px; border-radius: 99px; font-size: 12px; font-weight: 700; background: color-mix(in srgb, var(--tone) 20%, transparent); color: var(--tone); }
"""


def state(
    name: str,
    tone: str,
    glyph: str,
    title: str,
    text: str,
    action: str,
    note: str,
    role: str = "status",
    css: str = "",
) -> Item:
    button = f'<button class="btn">{action}</button>' if action else ""
    html = f'<section class="state" role="{role}" style="--tone:var(--{tone})"><div class="orb" aria-hidden="true">{glyph}</div><h3>{title}</h3><p>{text}</p>{button}</section>'
    return Item(name, html, STATE + css, note=note)


def job(
    name: str,
    tone: str,
    glyph: str,
    title: str,
    detail: str,
    tag: str,
    note: str,
    css: str = "",
    extra: str = "",
) -> Item:
    html = f'<div class="job" style="--tone:var(--{tone})"><span class="dot" aria-hidden="true">{glyph}</span><div><b>{title}</b><small>{detail}</small>{extra}</div><span class="tag">{tag}</span></div>'
    return Item(name, html, JOB + css, note=note)


def loader(name: str, html: str, css: str, note: str, js: str = "") -> Item:
    return Item(name, html, css, js, note)


SECTION = Section(
    "patterns",
    "Feedback & Status",
    371,
    (
        Item(
            "Toast notification",
            '<button class="btn fire">Save changes</button><div class="toasts" role="region" aria-label="Notifications" aria-live="polite"></div>',
            BTN
            + ".toasts { position: fixed; right: 16px; top: 16px; display: grid; gap: 8px; width: min(320px, calc(100% - 32px)); }\n.toast { display: flex; gap: 10px; align-items: center; padding: 12px 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); box-shadow: var(--shadow); animation: in .3s var(--ease); }\n.toast.out { animation: out .25s var(--ease) forwards; }\n.toast i { width: 8px; height: 8px; border-radius: 50%; background: var(--success); flex: none; }\n.toast span { flex: 1; }\n.toast button { border: 0; background: none; color: var(--muted); }\n@keyframes in { from { opacity: 0; translate: 20px 0; } }\n@keyframes out { to { opacity: 0; translate: 20px 0; } }\n",
            'const stack = document.querySelector(".toasts");\nconst LIFETIME = 4000, MAX = 3;\nlet count = 0;\nconst dismiss = (toast) => { toast.classList.add("out"); toast.addEventListener("animationend", () => toast.remove(), { once: true }); };\nconst notify = (text) => {\n  const toast = Object.assign(document.createElement("div"), { className: "toast" });\n  const close = Object.assign(document.createElement("button"), { textContent: "×" });\n  close.setAttribute("aria-label", "Dismiss");\n  close.addEventListener("click", () => dismiss(toast));\n  toast.append(document.createElement("i"), Object.assign(document.createElement("span"), { textContent: text }), close);\n  stack.prepend(toast);\n  while (stack.children.length > MAX) stack.lastElementChild.remove();  // never a wall of toasts\n  let timer = setTimeout(() => dismiss(toast), LIFETIME);\n  // Reading takes time: hovering or focusing pauses the countdown.\n  toast.addEventListener("pointerenter", () => clearTimeout(timer));\n  toast.addEventListener("pointerleave", () => { timer = setTimeout(() => dismiss(toast), LIFETIME); });\n};\ndocument.querySelector(".fire").addEventListener("click", () => { count += 1; notify(`Changes saved (${count})`); });\n',
            "Transient, stacked, capped at three, announced politely, paused while hovered.",
        ),
        Item(
            "Snackbar",
            '<button class="btn fire">Archive conversation</button><div class="snack" role="status" hidden><span>Conversation archived</span><button>Undo</button></div>',
            BTN
            + ".snack { position: fixed; left: 50%; bottom: 20px; translate: -50% 0; display: flex; align-items: center; gap: 16px; padding: 10px 10px 10px 16px; border-radius: 10px; background: var(--fg); color: var(--bg); box-shadow: var(--shadow); animation: up .25s var(--ease); white-space: nowrap; }\n.snack[hidden] { display: none; }\n.snack button { padding: 6px 12px; border: 0; border-radius: 7px; background: none; color: var(--primary); font-weight: 700; }\n@keyframes up { from { translate: -50% 20px; opacity: 0; } }\n",
            'const snack = document.querySelector(".snack");\nconst fire = document.querySelector(".fire");\nlet timer = null;\nfire.addEventListener("click", () => {\n  fire.disabled = true;\n  snack.hidden = false;\n  clearTimeout(timer);\n  timer = setTimeout(() => { snack.hidden = true; }, 5000);  // the action becomes final when this runs out\n});\nsnack.querySelector("button").addEventListener("click", () => { clearTimeout(timer); snack.hidden = true; fire.disabled = false; fire.focus(); });\n',
            "One line at the bottom with a single action, usually Undo, for a few seconds.",
        ),
        Item(
            "Banner",
            '<div class="banner" role="region" aria-label="Announcement"><span class="pill">New</span><p>Usage-based billing is now available on every plan.</p><a href="#">Learn more</a><button aria-label="Dismiss announcement">×</button></div>',
            ".banner { display: flex; align-items: center; gap: 12px; width: min(680px, 100%); padding: 10px 14px; border-radius: 12px; background: linear-gradient(90deg, color-mix(in srgb, var(--primary) 30%, var(--surface)), var(--surface)); border: 1px solid var(--border); }\n.pill { padding: 1px 9px; border-radius: 99px; background: var(--primary); color: #fff; font-size: 12px; font-weight: 700; }\n.banner p { flex: 1; margin: 0; }\n.banner a { color: var(--fg); font-weight: 600; }\n.banner button { border: 0; background: none; color: var(--muted); font-size: 18px; }\n",
            'const KEY = "banner.billing.dismissed";\nconst banner = document.querySelector(".banner");\nconst seen = () => { try { return localStorage.getItem(KEY) === "1"; } catch { return false; } };\nif (seen()) banner.remove();\nbanner.querySelector("button").addEventListener("click", () => { banner.remove(); try { localStorage.setItem(KEY, "1"); } catch { /* without storage it returns next visit */ } });\n',
            "Full-width, above the content, about the product rather than an action; once dismissed it stays dismissed.",
        ),
        Item(
            "Alert",
            '<div class="msg" role="alert" style="--tone:var(--danger)"><span class="g" aria-hidden="true">×</span><div><b>Payment failed</b><p>Your card was declined. Update your payment method to keep your workspace active.</p></div></div>',
            MSG,
            note="role=alert interrupts: reserve it for things that need attention now.",
        ),
        Item(
            "Inline alert",
            '<div class="fld"><label for="em">Email</label><input id="em" value="dana@northwind" aria-invalid="true" aria-describedby="em-e"><p class="ia" id="em-e"><span aria-hidden="true">!</span>Enter a full address, like dana@northwind.io.</p></div>',
            ".fld { display: grid; gap: 6px; width: min(320px, 100%); }\n.fld label { font-size: 13px; color: var(--muted); }\n.fld input { height: 42px; padding: 0 12px; border: 1px solid var(--danger); border-radius: 10px; background: var(--surface); }\n.ia { display: flex; gap: 6px; align-items: center; margin: 0; font-size: 13px; color: var(--danger); }\n.ia span { display: grid; place-items: center; width: 16px; height: 16px; border-radius: 50%; background: var(--danger); color: #1a0606; font-size: 10px; font-weight: 800; }\n",
            note="The message sits by the field it is about and is tied to it with aria-describedby.",
        ),
        Item(
            "Confirmation message",
            '<div class="msg" role="status" style="--tone:var(--success)"><span class="g" aria-hidden="true">✓</span><div><b>Invitation sent</b><p>Mika will get an email at mika@northwind.io. The link expires in 7 days.</p></div><button class="x" aria-label="Dismiss">×</button></div>',
            MSG,
            'document.querySelector(".msg .x").addEventListener("click", (event) => event.target.closest(".msg").remove());\n',
            "Says what happened and what follows from it, then gets out of the way.",
        ),
        state(
            "Success state",
            "success",
            "✓",
            "You’re all set",
            "Your workspace is ready and your team has been invited.",
            "Go to dashboard",
            "The end of a flow: what was achieved and the obvious next step.",
        ),
        state(
            "Error state",
            "danger",
            "×",
            "Something went wrong",
            "We could not load your projects. Your data is safe.",
            "Try again",
            "States the failure, reassures about what was not lost, offers the recovery.",
            "alert",
        ),
        state(
            "Warning state",
            "warning",
            "!",
            "Your trial ends tomorrow",
            "Add a payment method to keep your projects and members.",
            "Add payment method",
            "Trouble that has not happened yet, with the action that prevents it.",
        ),
        state(
            "Info state",
            "accent",
            "i",
            "Nothing to review",
            "When someone requests a review it will appear here.",
            "",
            "Explains an empty or neutral situation without implying a problem.",
        ),
        loader(
            "Loading state",
            '<section class="ld" aria-busy="true" aria-live="polite"><div class="sp"></div><h3>Loading your workspace</h3><p></p></section>',
            ".ld { display: grid; justify-items: center; gap: 8px; text-align: center; }\n.sp { width: 40px; height: 40px; border: 3px solid var(--surface-2); border-top-color: var(--primary); border-radius: 50%; animation: turn .8s linear infinite; }\n.ld h3 { margin: 8px 0 0; }\n.ld p { margin: 0; color: var(--muted); min-height: 22px; }\n@keyframes turn { to { rotate: 360deg; } }\n",
            "A spinner with words; if it takes long the message changes to say so.",
            'const hint = document.querySelector(".ld p");\n// Silence breeds doubt: after a few seconds, acknowledge the wait.\nsetTimeout(() => { hint.textContent = "This is taking longer than usual…"; }, 4000);\nsetTimeout(() => { hint.textContent = "Still working. You can keep this tab open."; }, 10000);\n',
        ),
        loader(
            "Skeleton loader",
            '<div class="sk" aria-busy="true" aria-label="Loading article"><div class="hero"></div><div class="l w70"></div><div class="l"></div><div class="l w90"></div><div class="row"><div class="av"></div><div class="l w40"></div></div></div>',
            ".sk { display: grid; gap: 12px; width: min(360px, 100%); padding: 16px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.sk > div, .sk .row > div { border-radius: 8px; background: var(--surface-2); animation: pulse 1.4s ease-in-out infinite; }\n.sk .hero { height: 120px; }\n.sk .l { height: 12px; }\n.w70 { width: 70%; } .w90 { width: 90%; } .w40 { width: 40%; }\n.sk .row { display: flex; gap: 10px; align-items: center; background: none; animation: none; }\n.sk .av { width: 32px; height: 32px; border-radius: 50% !important; flex: none; }\n@keyframes pulse { 50% { opacity: .45; } }\n",
            "Grey blocks in the shape of the content, pulsing; the layout does not jump when the real thing arrives.",
        ),
        loader(
            "Shimmer loader",
            '<div class="sh" aria-busy="true" aria-label="Loading list"><div></div><div></div><div></div></div>',
            ".sh { display: grid; gap: 10px; width: min(360px, 100%); }\n.sh div { height: 54px; border-radius: 12px; background: linear-gradient(100deg, var(--surface) 30%, color-mix(in srgb, var(--surface) 70%, white 12%) 50%, var(--surface) 70%) 0 0 / 300% 100%; animation: sweep 1.3s linear infinite; }\n.sh div:nth-child(2) { animation-delay: .12s; }\n.sh div:nth-child(3) { animation-delay: .24s; }\n@keyframes sweep { from { background-position: 150% 0; } to { background-position: -150% 0; } }\n",
            "A band of light sweeping across placeholders, staggered row by row.",
        ),
        loader(
            "Spinner",
            '<div class="row"><span class="s sm" role="status" aria-label="Loading"></span><span class="s" role="status" aria-label="Loading"></span><span class="s lg" role="status" aria-label="Loading"></span></div>',
            ".row { display: flex; gap: 28px; align-items: center; }\n.s { width: 24px; height: 24px; border: 3px solid color-mix(in srgb, var(--primary) 22%, transparent); border-top-color: var(--primary); border-radius: 50%; animation: turn .7s linear infinite; }\n.s.sm { width: 14px; height: 14px; border-width: 2px; }\n.s.lg { width: 44px; height: 44px; border-width: 4px; }\n@keyframes turn { to { rotate: 360deg; } }\n",
            "One element, a border with one coloured side, in three sizes.",
        ),
        loader(
            "Progress bar",
            '<div class="pb"><div class="lab"><span>Importing contacts</span><b>0%</b></div><div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="Importing contacts"><i></i></div><small></small></div>',
            ".pb { display: grid; gap: 8px; width: min(400px, 100%); }\n.lab { display: flex; justify-content: space-between; }\n.bar { height: 10px; border-radius: 99px; background: var(--surface-2); overflow: hidden; }\n.bar i { display: block; height: 100%; width: 0; border-radius: inherit; background: linear-gradient(90deg, var(--primary), var(--accent)); transition: width .3s var(--ease); }\n.pb small { color: var(--muted); }\n",
            "A labelled bar with the percentage and how much is left, driven by real counts.",
            'const TOTAL = 1240;\nlet done = 0;\nconst bar = document.querySelector(".bar");\nconst started = Date.now();\nconst timer = setInterval(() => {\n  done = Math.min(TOTAL, done + 37 + Math.floor(Math.random() * 40));\n  const share = done / TOTAL;\n  bar.firstElementChild.style.width = `${share * 100}%`;\n  bar.setAttribute("aria-valuenow", String(Math.round(share * 100)));\n  document.querySelector(".lab b").textContent = `${Math.round(share * 100)}%`;\n  // Time left is estimated from the pace so far.\n  const left = share > 0 ? Math.ceil(((Date.now() - started) / share) * (1 - share) / 1000) : null;\n  document.querySelector(".pb small").textContent = done === TOTAL ? `${TOTAL} contacts imported.` : `${done} of ${TOTAL}${left ? ` · about ${left}s left` : ""}`;\n  if (done === TOTAL) clearInterval(timer);\n}, 300);\n',
        ),
        loader(
            "Circular loader",
            '<div class="cl" role="status" aria-label="Loading"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>',
            ".cl { position: relative; width: 48px; height: 48px; }\n.cl i { position: absolute; left: 50%; top: 50%; width: 7px; height: 7px; margin: -3.5px; border-radius: 50%; background: var(--primary); animation: fade 1s linear infinite; }\n.cl i:nth-child(1) { transform: rotate(0deg) translateY(-20px); animation-delay: -.875s; }\n.cl i:nth-child(2) { transform: rotate(45deg) translateY(-20px); animation-delay: -.75s; }\n.cl i:nth-child(3) { transform: rotate(90deg) translateY(-20px); animation-delay: -.625s; }\n.cl i:nth-child(4) { transform: rotate(135deg) translateY(-20px); animation-delay: -.5s; }\n.cl i:nth-child(5) { transform: rotate(180deg) translateY(-20px); animation-delay: -.375s; }\n.cl i:nth-child(6) { transform: rotate(225deg) translateY(-20px); animation-delay: -.25s; }\n.cl i:nth-child(7) { transform: rotate(270deg) translateY(-20px); animation-delay: -.125s; }\n.cl i:nth-child(8) { transform: rotate(315deg) translateY(-20px); }\n@keyframes fade { from { opacity: 1; scale: 1.2; } to { opacity: .15; scale: .7; } }\n",
            "Eight dots on a circle fading in turn.",
        ),
        loader(
            "Determinate loader",
            '<div class="dt"><div class="steps"><i></i><i></i><i></i><i></i><i></i></div><p role="status"></p></div>',
            '.dt { display: grid; gap: 12px; justify-items: center; }\n.steps { display: flex; gap: 6px; }\n.steps i { width: 44px; height: 6px; border-radius: 99px; background: var(--surface-2); overflow: hidden; position: relative; }\n.steps i.done { background: var(--primary); }\n.steps i.now::after { content: ""; position: absolute; inset: 0; background: var(--primary); transform-origin: left; animation: fill 1.2s linear forwards; }\n.dt p { margin: 0; color: var(--muted); }\n@keyframes fill { from { scale: 0 1; } }\n',
            "Known length: segments fill one by one and the step is named.",
            'const NAMES = ["Uploading", "Scanning", "Converting", "Indexing", "Finishing"];\nconst segments = [...document.querySelectorAll(".steps i")];\nconst label = document.querySelector(".dt p");\nlet step = 0;\nconst render = () => {\n  segments.forEach((segment, i) => { segment.className = i < step ? "done" : i === step ? "now" : ""; });\n  label.textContent = step < NAMES.length ? `Step ${step + 1} of ${NAMES.length}: ${NAMES[step]}` : "Done";\n};\nconst timer = setInterval(() => { step += 1; render(); if (step === NAMES.length) clearInterval(timer); }, 1200);\nrender();\n',
        ),
        loader(
            "Indeterminate loader",
            '<div class="ind" role="progressbar" aria-label="Working" aria-busy="true"><i></i></div>',
            ".ind { width: min(360px, 100%); height: 6px; border-radius: 99px; background: var(--surface-2); overflow: hidden; }\n.ind i { display: block; width: 40%; height: 100%; border-radius: inherit; background: var(--primary); animation: run 1.3s cubic-bezier(.4, 0, .2, 1) infinite; }\n@keyframes run { from { translate: -100% 0; } to { translate: 250% 0; } }\n",
            "Unknown length: a segment that travels, never a bar that pretends to fill.",
        ),
        loader(
            "Upload progress",
            '<ul class="up"></ul><label class="btn">Choose files<input type="file" multiple hidden></label>',
            BTN
            + ".up { display: grid; gap: 8px; width: min(420px, 100%); margin: 0 0 14px; padding: 0; list-style: none; }\n.up li { display: grid; grid-template-columns: 1fr auto; gap: 6px 10px; padding: 10px 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); font-size: 14px; }\n.up li span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.up li small { color: var(--muted); font-variant-numeric: tabular-nums; }\n.up .bar { grid-column: 1 / -1; height: 4px; border-radius: 99px; background: var(--surface-2); overflow: hidden; }\n.up .bar i { display: block; height: 100%; width: 0; background: var(--primary); transition: width .2s; }\n.up li.done .bar i { background: var(--success); }\n.up li.fail .bar i { background: var(--danger); }\n.up button { border: 0; background: none; color: var(--primary); }\nbody { align-content: center; justify-items: center; }\n",
            "One row per file with its own bar, a finished state, a failed state with retry, and cancel.",
            'const list = document.querySelector(".up");\n// A stand-in for XMLHttpRequest.upload.onprogress: reports bytes sent, sometimes fails.\nconst send = (file, onProgress) => new Promise((resolve, reject) => {\n  let sent = 0;\n  const timer = setInterval(() => {\n    sent = Math.min(file.size, sent + Math.max(1, file.size / 14));\n    onProgress(sent);\n    if (sent >= file.size) { clearInterval(timer); (Math.random() > 0.2 ? resolve : reject)(); }\n  }, 160);\n});\nconst add = (file) => {\n  const row = document.createElement("li");\n  const status = document.createElement("small");\n  const fill = document.createElement("i");\n  const bar = Object.assign(document.createElement("div"), { className: "bar" });\n  bar.append(fill);\n  row.append(Object.assign(document.createElement("span"), { textContent: file.name }), status, bar);\n  list.append(row);\n  const run = async () => {\n    row.className = "";\n    try {\n      await send(file, (sent) => { fill.style.width = `${(sent / file.size) * 100}%`; status.textContent = `${Math.round((sent / file.size) * 100)}%`; });\n      row.className = "done";\n      status.textContent = "Uploaded";\n    } catch {\n      row.className = "fail";\n      const retry = Object.assign(document.createElement("button"), { textContent: "Retry" });\n      retry.addEventListener("click", run);\n      status.replaceChildren("Failed · ", retry);\n    }\n  };\n  run();\n};\ndocument.querySelector("input").addEventListener("change", (event) => { [...event.target.files].forEach(add); event.target.value = ""; });\nadd({ name: "q3-report.pdf", size: 284000 });\nadd({ name: "forecast.xlsx", size: 91000 });\n',
        ),
        job(
            "Processing state",
            "accent",
            "⟳",
            "Transcoding video",
            "Step 2 of 4 · about a minute left",
            "Processing",
            "Work is under way: say which step and roughly how long.",
            ".job .dot { animation: turn 1.2s linear infinite; }\n@keyframes turn { to { rotate: 360deg; } }\n",
        ),
        job(
            "Queued state",
            "muted",
            "≡",
            "Export to CSV",
            "3 jobs ahead of yours",
            "Queued",
            "Accepted but not started: the position in line is the useful fact.",
        ),
        job(
            "Pending state",
            "warning",
            "…",
            "Refund of $128.00",
            "Waiting for approval from Dana",
            "Pending",
            "Blocked on someone or something else: name who or what.",
            ".job .tag { animation: breathe 2s ease-in-out infinite; }\n@keyframes breathe { 50% { opacity: .55; } }\n",
        ),
        job(
            "Completed state",
            "success",
            "✓",
            "Backup finished",
            "2.4 GB · took 3m 12s · today 14:02",
            "Completed",
            "Done: when, how long it took and how big the result is.",
        ),
        job(
            "Failed state",
            "danger",
            "×",
            "Deploy #483 failed",
            "Tests failed in checkout.spec.ts",
            "Failed",
            "Failed: the reason in a phrase and the two things to do about it.",
            ".job a { display: inline-block; margin: 4px 12px 0 0; color: var(--fg); font-size: 13px; font-weight: 600; }\n",
            '<br><a href="#">View logs</a><a href="#">Retry</a>',
        ),
        Item(
            "Offline state",
            '<section class="state" role="status" style="--tone:var(--muted)"><div class="orb" aria-hidden="true">⌁</div><h3></h3><p></p><button class="btn">Try again</button></section>',
            STATE,
            'const title = document.querySelector(".state h3");\nconst text = document.querySelector(".state p");\nconst retry = document.querySelector(".state .btn");\nconst render = () => {\n  const online = navigator.onLine;\n  title.textContent = online ? "You’re back online" : "You’re offline";\n  text.textContent = online ? "Everything is up to date." : "Changes you make will be saved on this device and sent when the connection returns.";\n  retry.hidden = online;\n  document.querySelector(".state").style.setProperty("--tone", online ? "var(--success)" : "var(--muted)");\n};\naddEventListener("online", render);\naddEventListener("offline", render);\nretry.addEventListener("click", render);\nrender();\n',
            "Follows the browser's connectivity and says what happens to work done meanwhile.",
        ),
        Item(
            "Connection status",
            '<div class="conn" role="status"><i></i><span></span></div>',
            ".conn { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface); font-size: 13px; }\n.conn i { width: 8px; height: 8px; border-radius: 50%; background: var(--c); }\n.conn[data-s=connected] { --c: var(--success); }\n.conn[data-s=connecting] { --c: var(--warning); }\n.conn[data-s=connecting] i { animation: blink 1s steps(2) infinite; }\n.conn[data-s=disconnected] { --c: var(--danger); }\n@keyframes blink { 50% { opacity: .2; } }\n",
            '// The life of a live connection: connect, drop, retry with growing waits, reconnect.\nconst pill = document.querySelector(".conn");\nconst label = pill.querySelector("span");\nconst set = (state, text) => { pill.dataset.s = state; label.textContent = text; };\nlet attempt = 0;\nconst connect = () => {\n  set("connecting", attempt ? `Reconnecting (attempt ${attempt})…` : "Connecting…");\n  setTimeout(() => {\n    if (attempt > 0 && attempt < 3) { retry(); return; }  // the first two retries fail in this demo\n    attempt = 0;\n    set("connected", "Connected");\n    setTimeout(drop, 5000);\n  }, 900);\n};\nconst retry = () => {\n  attempt += 1;\n  const wait = Math.min(8, 2 ** (attempt - 1));\n  set("disconnected", `Connection lost. Retrying in ${wait}s`);\n  setTimeout(connect, wait * 1000);\n};\nconst drop = () => retry();\nconnect();\n',
            "Connected, connecting or lost, with the retry schedule visible.",
        ),
        Item(
            "Sync status",
            '<button class="sync" data-s="synced"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M20 11a8 8 0 0 0-14.500-4M4 4v4h4M4 13a8 8 0 0 0 14.500 4M20 20v-4h-4"/></svg><span></span></button>',
            ".sync { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); font-size: 13px; color: var(--muted); }\n.sync[data-s=syncing] svg { animation: turn 1s linear infinite; color: var(--accent); }\n.sync[data-s=synced] svg { color: var(--success); }\n.sync[data-s=error] { color: var(--danger); border-color: var(--danger); }\n@keyframes turn { to { rotate: 360deg; } }\n",
            'const button = document.querySelector(".sync");\nconst label = button.querySelector("span");\nconst relative = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });\nlet last = Date.now() - 3 * 60 * 1000;\nconst render = (state) => {\n  button.dataset.s = state;\n  label.textContent = state === "syncing" ? "Syncing…" : state === "error" ? "Sync failed · Retry" : `Synced ${relative.format(-Math.max(0, Math.round((Date.now() - last) / 60000)), "minute")}`;\n};\nbutton.addEventListener("click", () => {\n  if (button.dataset.s === "syncing") return;\n  render("syncing");\n  setTimeout(() => { if (Math.random() > 0.25) { last = Date.now(); render("synced"); } else render("error"); }, 1200);\n});\nrender("synced");\nsetInterval(() => { if (button.dataset.s === "synced") render("synced"); }, 30000);\n',
            "When data was last in step, a manual sync, and a failure that can be retried from the same control.",
        ),
        Item(
            "Save status",
            '<div class="sv"><input value="Untitled document" aria-label="Title"><span class="st" role="status" data-s="saved">Saved</span></div>',
            '.sv { display: flex; align-items: center; gap: 12px; width: min(420px, 100%); }\n.sv input { flex: 1; height: 42px; padding: 0 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }\n.st { font-size: 13px; color: var(--muted); white-space: nowrap; }\n.st[data-s=dirty] { color: var(--warning); }\n.st[data-s=saving]::before { content: ""; display: inline-block; width: 10px; height: 10px; margin-right: 6px; border: 2px solid var(--muted); border-top-color: transparent; border-radius: 50%; animation: turn .7s linear infinite; vertical-align: -1px; }\n.st[data-s=saved]::before { content: "✓ "; color: var(--success); }\n@keyframes turn { to { rotate: 360deg; } }\n',
            'const input = document.querySelector(".sv input");\nconst status = document.querySelector(".st");\nconst set = (state, text) => { status.dataset.s = state; status.textContent = text; };\nlet saved = input.value;\nconst save = () => { set("saving", "Saving…"); setTimeout(() => { saved = input.value; set("saved", "Saved"); }, 700); };\ninput.addEventListener("input", () => set(input.value === saved ? "saved" : "dirty", input.value === saved ? "Saved" : "Unsaved changes"));\ninput.addEventListener("keydown", (event) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") { event.preventDefault(); save(); } });\ninput.addEventListener("blur", () => { if (input.value !== saved) save(); });\n// Leaving with unsaved work asks first.\naddEventListener("beforeunload", (event) => { if (input.value !== saved) event.preventDefault(); });\n',
            "Unsaved, saving, saved, next to the thing being edited; ⌘/Ctrl+S saves and leaving unsaved warns.",
        ),
        Item(
            "Autosave indicator",
            '<div class="as"><textarea rows="4" aria-label="Notes" aria-describedby="asi">Meeting notes…</textarea><p id="asi" role="status">All changes saved</p></div>',
            ".as { display: grid; gap: 6px; width: min(420px, 100%); }\n.as textarea { padding: 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); resize: vertical; }\n.as p { margin: 0; font-size: 12px; color: var(--muted); text-align: right; }\n",
            'const area = document.querySelector(".as textarea");\nconst status = document.getElementById("asi");\nconst DELAY = 900;\nlet timer = null;\nconst save = () => {\n  status.textContent = "Saving…";\n  // Replace with the real request; keep the message honest about its outcome.\n  setTimeout(() => { status.textContent = `Saved at ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`; }, 400);\n};\n// Save once typing pauses, not on every keystroke.\narea.addEventListener("input", () => { status.textContent = "Editing…"; clearTimeout(timer); timer = setTimeout(save, DELAY); });\n',
            "Saves after typing pauses (debounced) and shows the time of the last save.",
        ),
        Item(
            "Health indicator",
            '<div class="hi"><div class="h" data-l="healthy"><i></i><div><b>Healthy</b><small>All checks passing</small></div></div><div class="h" data-l="degraded"><i></i><div><b>Degraded</b><small>Search is slow</small></div></div><div class="h" data-l="down"><i></i><div><b>Down</b><small>Payments unavailable</small></div></div></div>',
            '.hi { display: grid; gap: 10px; }\n.h { display: flex; gap: 12px; align-items: center; padding: 10px 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); min-width: 260px; }\n.h i { position: relative; width: 12px; height: 12px; border-radius: 50%; background: var(--c); }\n.h i::after { content: ""; position: absolute; inset: 0; border-radius: 50%; background: var(--c); animation: ping 2s ease-out infinite; }\n.h small { display: block; color: var(--muted); }\n[data-l=healthy] { --c: var(--success); }\n[data-l=degraded] { --c: var(--warning); }\n[data-l=degraded] i { border-radius: 2px; rotate: 45deg; }\n[data-l=down] { --c: var(--danger); border-color: var(--danger); }\n[data-l=down] i { border-radius: 2px; }\n[data-l=down] i::after { animation-duration: 1s; border-radius: 2px; }\n@keyframes ping { to { scale: 2.6; opacity: 0; } }\n',
            note="Three levels that differ in colour, shape and pulse speed, so colour is never the only cue.",
        ),
    ),
)
