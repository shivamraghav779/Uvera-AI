"""Patterns 221-270: interfaces specific to AI products."""

from app.domains.references.vocabulary.base import Item, Section

BOX = """\
.box { width: min(520px, 100%); border: 1px solid var(--border); border-radius: 16px; background: var(--surface); overflow: hidden; }
.box > header { display: flex; align-items: center; gap: 8px; padding: 12px 14px; border-bottom: 1px solid var(--border); font-weight: 600; }
.box > header small { margin-left: auto; font-weight: 400; color: var(--muted); }
.pad { padding: 14px; }
.spark { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 7px; font-size: 11px; color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--accent)); flex: none; }
.mono { font: 12px var(--mono); color: var(--muted); }
.chipx { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border: 1px solid var(--border); border-radius: 999px;
  background: var(--surface); color: var(--fg); font-size: 13px; cursor: pointer; transition: border-color .15s, background .15s; }
.chipx:hover { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 12%, var(--surface)); }
"""
CHAT = (
    BOX
    + """\
.log { display: flex; flex-direction: column; gap: 10px; padding: 14px; height: 250px; overflow: auto; }
.msg { max-width: 82%; padding: 9px 13px; border-radius: 16px; line-height: 1.45; }
.msg.user { align-self: flex-end; background: var(--primary); color: #fff; border-bottom-right-radius: 5px; }
.msg.ai { align-self: flex-start; background: var(--surface-2); border-bottom-left-radius: 5px; }
.composer { display: flex; gap: 8px; padding: 10px; border-top: 1px solid var(--border); }
.composer input { flex: 1; min-width: 0; height: 40px; padding: 0 14px; border: 1px solid var(--border); border-radius: 999px; background: var(--bg); outline: none; }
.composer input:focus { border-color: var(--primary); }
.composer button { width: 40px; height: 40px; border: 0; border-radius: 50%; background: var(--primary); color: #fff; }
.composer button:disabled { opacity: .4; }
"""
)
# A stand-in for a model: answers word by word. Replace `reply` with a real stream.
STREAM_JS = """\
const reply = async function* (prompt) {
  const text = `Here is a short answer about “${prompt}”. Streaming shows each word as it arrives, so the reader can start before the end.`;
  for (const word of text.split(" ")) { await new Promise((resolve) => setTimeout(resolve, 45)); yield `${word} `; }
};
"""
CHAT_JS = (
    STREAM_JS
    + """\
const log = document.querySelector(".log");
const form = document.querySelector(".composer");
const input = form.querySelector("input");
const send = form.querySelector("button");
const add = (role, text) => { const bubble = Object.assign(document.createElement("div"), { className: `msg ${role}`, textContent: text }); log.append(bubble); log.scrollTop = log.scrollHeight; return bubble; };
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const prompt = input.value.trim();
  if (!prompt || send.disabled) return;
  input.value = "";
  send.disabled = true;  // one answer at a time
  add("user", prompt);
  const bubble = add("ai", "");
  bubble.setAttribute("aria-busy", "true");
  for await (const chunk of reply(prompt)) { bubble.textContent += chunk; log.scrollTop = log.scrollHeight; }
  bubble.removeAttribute("aria-busy");
  send.disabled = false;
  input.focus();
});
"""
)
CHAT_HTML = (
    '<div class="log" aria-live="polite"><div class="msg ai">Hi! Ask me about your data.</div><div class="msg user">What changed in Q3?</div>'
    '<div class="msg ai">Revenue grew 12.4%, led by EMEA.</div></div>'
    '<form class="composer"><input placeholder="Message" aria-label="Message"><button aria-label="Send">↑</button></form>'
)
# Word-level difference of two texts (longest common subsequence).
DIFF_JS = """\
const diffWords = (before, after) => {
  const a = before.split(/(\\s+)/), b = after.split(/(\\s+)/);
  const table = Array.from({ length: a.length + 1 }, () => new Uint16Array(b.length + 1));
  for (let i = a.length - 1; i >= 0; i -= 1) for (let j = b.length - 1; j >= 0; j -= 1)
    table[i][j] = a[i] === b[j] ? table[i + 1][j + 1] + 1 : Math.max(table[i + 1][j], table[i][j + 1]);
  const parts = [];
  let i = 0, j = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) { parts.push(["same", a[i]]); i += 1; j += 1; }
    else if (table[i + 1][j] >= table[i][j + 1]) { parts.push(["del", a[i]]); i += 1; }
    else { parts.push(["ins", b[j]]); j += 1; }
  }
  while (i < a.length) parts.push(["del", a[i++]]);
  while (j < b.length) parts.push(["ins", b[j++]]);
  return parts;
};
const renderDiff = (target, before, after) => target.replaceChildren(...diffWords(before, after).map(([kind, text]) =>
  kind === "same" ? document.createTextNode(text) : Object.assign(document.createElement(kind), { textContent: text })));
"""
DIFF_CSS = "ins { background: color-mix(in srgb, var(--success) 25%, transparent); color: var(--success); text-decoration: none; border-radius: 3px; }\ndel { background: color-mix(in srgb, var(--danger) 22%, transparent); color: var(--danger); border-radius: 3px; }\n"


def box(
    name: str, title: str, body: str, css: str, note: str, js: str = "", aside: str = ""
) -> Item:
    head = f'<header><span class="spark">✦</span>{title}{f"<small>{aside}</small>" if aside else ""}</header>'
    return Item(name, f'<section class="box">{head}{body}</section>', BOX + css, js, note)


def chips(name: str, lead: str, options: list[str], note: str, css: str = "") -> Item:
    body = "".join(f'<button class="chipx">{o}</button>' for o in options)
    html = f'<div class="sug"><p>{lead}</p><div>{body}</div><output></output></div>'
    js = 'const output = document.querySelector(".sug output");\ndocument.querySelector(".sug div").addEventListener("click", (event) => {\n  const chip = event.target.closest("button");\n  if (chip) output.textContent = `→ ${chip.textContent}`;  // hand the text to the composer here\n});\n'
    return Item(
        name,
        html,
        BOX
        + ".sug { display: grid; gap: 10px; width: min(520px, 100%); }\n.sug p { margin: 0; color: var(--muted); font-size: 13px; }\n.sug div { display: flex; flex-wrap: wrap; gap: 8px; }\n.sug output { color: var(--muted); font-size: 13px; min-height: 20px; }\n"
        + css,
        js,
        note,
    )


TL = """\
.tl { margin: 0; padding: 14px; list-style: none; }
.tl li { position: relative; padding: 0 0 16px 26px; }
.tl li:last-child { padding-bottom: 0; }
.tl li::before { content: ""; position: absolute; left: 4px; top: 5px; width: 10px; height: 10px; border-radius: 50%; background: var(--border); z-index: 1; }
.tl li::after { content: ""; position: absolute; left: 8.5px; top: 14px; bottom: -4px; width: 1px; background: var(--border); }
.tl li:last-child::after { display: none; }
.tl li.done::before { background: var(--success); }
.tl li.run::before { background: var(--accent); box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 25%, transparent); animation: pulse 1.2s ease-in-out infinite; }
.tl li.fail::before { background: var(--danger); }
.tl b { display: block; font-weight: 600; }
.tl small { color: var(--muted); }
@keyframes pulse { 50% { box-shadow: 0 0 0 7px transparent; } }
"""

SECTION = Section(
    "patterns",
    "AI-Specific UI",
    221,
    (
        box(
            "AI chat interface",
            "Assistant",
            CHAT_HTML,
            CHAT.replace(BOX, ""),
            "Messages, a streaming reply and a composer that locks while the answer arrives.",
            CHAT_JS,
            "sonnet",
        ),
        Item(
            "AI copilot panel",
            '<div class="shell"><main><h3>Q3 report</h3><p>Revenue grew across every region, with EMEA ahead of plan…</p></main><aside class="box cop"><header><span class="spark">✦</span>Copilot</header><div class="pad"><p class="ctx">Using: <b>Q3 report</b></p><button class="chipx">Summarise this page</button><button class="chipx">Find risks</button><button class="chipx">Draft an email</button></div></aside></div>',
            BOX
            + ".shell { display: grid; grid-template-columns: 1fr 240px; gap: 12px; width: min(680px, 100%); }\n.shell main { padding: 18px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.shell main h3 { margin: 0 0 8px; }\n.shell main p { margin: 0; color: var(--muted); }\n.cop { width: auto; }\n.cop .pad { display: grid; gap: 8px; justify-items: start; }\n.ctx { margin: 0 0 4px; font-size: 12px; color: var(--muted); }\n.ctx b { color: var(--fg); }\n",
            note="Docked beside the work, it says what it can see and offers actions on that.",
        ),
        Item(
            "AI assistant sidebar",
            '<div class="frame"><div class="page">Your app</div><aside class="box side" aria-label="Assistant"><header><span class="spark">✦</span>Assistant<button class="x" aria-label="Close assistant">×</button></header>'
            + CHAT_HTML
            + '</aside><button class="fab" aria-label="Open assistant" hidden>✦</button></div>',
            CHAT
            + ".frame { position: relative; display: flex; width: min(700px, 100%); height: 400px; border: 1px solid var(--border); border-radius: 16px; overflow: hidden; }\n.page { flex: 1; display: grid; place-items: center; color: var(--muted); }\n.side { width: 300px; border-width: 0 0 0 1px; border-radius: 0; display: flex; flex-direction: column; }\n.side .log { flex: 1; height: auto; }\n.side header .x { margin-left: auto; border: 0; background: none; color: var(--muted); font-size: 18px; }\n.fab { position: absolute; right: 16px; bottom: 16px; width: 48px; height: 48px; border: 0; border-radius: 50%; background: linear-gradient(135deg, var(--primary), var(--accent)); color: #fff; }\n",
            CHAT_JS
            + 'const side = document.querySelector(".side");\nconst fab = document.querySelector(".fab");\nside.querySelector(".x").addEventListener("click", () => { side.hidden = true; fab.hidden = false; fab.focus(); });\nfab.addEventListener("click", () => { side.hidden = false; fab.hidden = true; input.focus(); });\n',
            "A chat column on the trailing edge that collapses to a floating button.",
        ),
        Item(
            "AI command bar",
            '<div class="cb"><label><span class="spark">✦</span><input placeholder="Ask or type a command…" aria-label="Ask or type a command"><kbd>⌘K</kbd></label><ul><li data-kind="ask"><b>Ask AI</b><span></span></li><li><b>Create chart</b><span>Command</span></li><li><b>Go to Settings</b><span>Navigate</span></li></ul></div>',
            BOX
            + '.cb { width: min(520px, 100%); border: 1px solid var(--border); border-radius: 16px; background: var(--surface); box-shadow: var(--shadow); overflow: hidden; }\n.cb label { display: flex; align-items: center; gap: 10px; height: 52px; padding: 0 14px; border-bottom: 1px solid var(--border); }\n.cb input { flex: 1; border: 0; outline: 0; background: none; font-size: 16px; }\n.cb kbd { font: 11px var(--mono); color: var(--muted); border: 1px solid var(--border); border-radius: 5px; padding: 1px 6px; }\n.cb ul { margin: 0; padding: 6px; list-style: none; }\n.cb li { display: flex; justify-content: space-between; gap: 12px; padding: 9px 10px; border-radius: 9px; }\n.cb li span { color: var(--muted); font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.cb li[aria-selected="true"] { background: color-mix(in srgb, var(--primary) 22%, transparent); }\n',
            'const input = document.querySelector(".cb input");\nconst items = [...document.querySelectorAll(".cb li")];\nlet active = 0;\nconst render = () => {\n  const query = input.value.trim();\n  // Free text is always answerable: the first row asks the model with exactly what was typed.\n  items[0].querySelector("span").textContent = query ? `“${query}”` : "Type a question";\n  items.forEach((item, i) => {\n    item.hidden = i > 0 && query !== "" && !item.textContent.toLowerCase().includes(query.toLowerCase());\n    item.setAttribute("aria-selected", String(i === active));\n  });\n};\ninput.addEventListener("input", () => { active = 0; render(); });\ninput.addEventListener("keydown", (event) => {\n  const shown = items.filter((item) => !item.hidden);\n  if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;\n  event.preventDefault();\n  const next = (shown.indexOf(items[active]) + (event.key === "ArrowDown" ? 1 : -1) + shown.length) % shown.length;\n  active = items.indexOf(shown[next]);\n  render();\n});\ndocument.addEventListener("keydown", (event) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); input.focus(); } });\nrender();\n',
            "One field for questions and commands; whatever is typed can always be asked.",
        ),
        Item(
            "AI prompt composer",
            '<form class="pc"><div class="att"></div><textarea rows="2" placeholder="Describe what you want to build…" aria-label="Prompt"></textarea><footer><label class="clip">＋ Attach<input type="file" multiple hidden></label><select aria-label="Model"><option>Sonnet</option><option>Opus</option><option>Haiku</option></select><span class="count mono"></span><button disabled>Generate</button></footer></form>',
            BOX
            + ".pc { width: min(560px, 100%); padding: 12px; border: 1px solid var(--border); border-radius: 18px; background: var(--surface); }\n.pc:focus-within { border-color: var(--primary); }\n.pc textarea { width: 100%; border: 0; outline: 0; background: none; resize: none; padding: 4px; max-height: 200px; }\n.att { display: flex; flex-wrap: wrap; gap: 6px; }\n.att span { padding: 2px 4px 2px 10px; border-radius: 8px; background: var(--surface-2); font-size: 12px; }\n.att button { border: 0; background: none; color: var(--muted); }\n.pc footer { display: flex; align-items: center; gap: 10px; margin-top: 8px; }\n.clip { cursor: pointer; color: var(--muted); font-size: 13px; }\n.pc select { height: 30px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); }\n.count { margin-left: auto; }\n.pc footer > button { height: 34px; padding: 0 16px; border: 0; border-radius: 10px; background: var(--primary); color: #fff; font-weight: 600; }\n.pc footer > button:disabled { opacity: .4; }\n",
            'const form = document.querySelector(".pc");\nconst area = form.querySelector("textarea");\nconst files = form.querySelector(\'input[type="file"]\');\nconst tray = form.querySelector(".att");\nconst count = form.querySelector(".count");\nconst submit = form.querySelector("footer > button");\nconst LIMIT = 4000;\nconst update = () => {\n  area.style.height = "auto";\n  area.style.height = `${area.scrollHeight}px`;\n  count.textContent = `${area.value.length} / ${LIMIT}`;\n  count.style.color = area.value.length > LIMIT ? "var(--danger)" : "";\n  submit.disabled = area.value.trim() === "" || area.value.length > LIMIT;\n};\nfiles.addEventListener("change", () => {\n  for (const file of files.files) {\n    const chip = document.createElement("span");\n    const remove = Object.assign(document.createElement("button"), { type: "button", textContent: "×" });\n    remove.setAttribute("aria-label", `Remove ${file.name}`);\n    remove.addEventListener("click", () => chip.remove());\n    chip.append(file.name, remove);\n    tray.append(chip);\n  }\n  files.value = "";\n});\narea.addEventListener("input", update);\narea.addEventListener("keydown", (event) => { if ((event.metaKey || event.ctrlKey) && event.key === "Enter" && !submit.disabled) form.requestSubmit(); });\nform.addEventListener("submit", (event) => event.preventDefault());\nupdate();\n',
            "Text, attachments, model choice and a character budget in one composer; ⌘/Ctrl+Enter submits.",
        ),
        chips(
            "Prompt suggestions",
            "Try asking",
            [
                "Summarise last week’s sales",
                "Which customers are at risk?",
                "Draft a renewal email",
                "Explain this chart",
            ],
            "Starting points shown before the first message; clicking one fills the composer.",
        ),
        Item(
            "Prompt templates",
            '<div class="tpl"><ul>'
            + "".join(
                f'<li><button data-t="{t}"><b>{n}</b><small>{d}</small></button></li>'
                for n, d, t in [
                    (
                        "Summary",
                        "Condense a document",
                        "Summarise {{text}} in three bullet points.",
                    ),
                    ("Rewrite", "Change tone or length", "Rewrite {{text}} to sound {{tone}}."),
                    (
                        "Extract",
                        "Pull out structured data",
                        "Extract {{fields}} from {{text}} as JSON.",
                    ),
                ]
            )
            + '</ul><form class="fill"></form><pre class="out"></pre></div>',
            BOX
            + '.tpl { display: grid; gap: 12px; width: min(520px, 100%); }\n.tpl ul { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 0; padding: 0; list-style: none; }\n.tpl li button { width: 100%; text-align: left; padding: 10px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.tpl li button[aria-pressed="true"] { border-color: var(--primary); }\n.tpl small { display: block; color: var(--muted); }\n.fill { display: grid; gap: 8px; }\n.fill label { display: grid; gap: 4px; font-size: 12px; color: var(--muted); }\n.fill input { height: 36px; padding: 0 10px; border: 1px solid var(--border); border-radius: 9px; background: var(--surface); }\n.out { margin: 0; padding: 12px; border-radius: 12px; background: var(--surface-2); font: 13px/1.5 var(--mono); white-space: pre-wrap; min-height: 44px; }\n',
            'const buttons = [...document.querySelectorAll(".tpl li button")];\nconst form = document.querySelector(".fill");\nconst out = document.querySelector(".out");\nlet template = "";\nconst render = () => {\n  const values = Object.fromEntries(new FormData(form));\n  out.textContent = template.replace(/\\{\\{(\\w+)\\}\\}/g, (_, name) => values[name] || `{{${name}}}`);  // unfilled variables stay visible\n};\nconst pick = (button) => {\n  buttons.forEach((item) => item.setAttribute("aria-pressed", String(item === button)));\n  template = button.dataset.t;\n  const names = [...new Set([...template.matchAll(/\\{\\{(\\w+)\\}\\}/g)].map((match) => match[1]))];\n  form.replaceChildren(...names.map((name) => {\n    const label = document.createElement("label");\n    label.append(name, Object.assign(document.createElement("input"), { name }));\n    return label;\n  }));\n  render();\n};\nbuttons.forEach((button) => button.addEventListener("click", () => pick(button)));\nform.addEventListener("input", render);\npick(buttons[0]);\n',
            "Pick a template and a form appears for its variables; the filled prompt previews live.",
        ),
        Item(
            "Prompt history",
            '<div class="ph"><input placeholder="Type, or press ↑ for earlier prompts" aria-label="Prompt" aria-describedby="phh"><p id="phh" class="mono"></p></div>',
            BOX
            + ".ph { display: grid; gap: 8px; width: min(460px, 100%); }\n.ph input { height: 44px; padding: 0 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); outline: none; }\n.ph input:focus { border-color: var(--primary); }\n.ph p { margin: 0; }\n",
            'const input = document.querySelector(".ph input");\nconst hint = document.getElementById("phh");\nconst history = ["Summarise the Q3 report", "List customers at risk", "Draft a renewal email"];\nlet cursor = history.length;  // one past the newest: the draft being typed\nlet draft = "";\nconst show = () => { hint.textContent = cursor === history.length ? `${history.length} earlier prompts` : `${cursor + 1} of ${history.length}`; };\ninput.addEventListener("keydown", (event) => {\n  if (event.key === "ArrowUp" && cursor > 0) {\n    if (cursor === history.length) draft = input.value;  // keep what was being typed\n    cursor -= 1;\n  } else if (event.key === "ArrowDown" && cursor < history.length) cursor += 1;\n  else if (event.key === "Enter" && input.value.trim()) {\n    if (history.at(-1) !== input.value.trim()) history.push(input.value.trim());\n    cursor = history.length;\n    draft = input.value = "";\n    show();\n    return;\n  } else return;\n  event.preventDefault();\n  input.value = cursor === history.length ? draft : history[cursor];\n  show();\n});\nshow();\n',
            "Up and down recall earlier prompts like a shell, without losing the draft in progress.",
        ),
        Item(
            "Conversation history",
            '<nav class="ch" aria-label="Conversations"><input placeholder="Search conversations" aria-label="Search conversations"><div class="groups"></div></nav>',
            BOX
            + '.ch { width: 280px; padding: 10px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.ch input { width: 100%; height: 36px; padding: 0 12px; margin-bottom: 8px; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); }\n.ch h4 { margin: 12px 8px 4px; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }\n.ch a { display: block; padding: 8px; border-radius: 8px; color: var(--fg); text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.ch a:hover, .ch a[aria-current="page"] { background: var(--surface-2); }\n.ch em { display: block; padding: 8px; color: var(--muted); font-style: normal; }\n',
            'const DAY = 86400000;\nconst now = Date.now();\nconst items = [["Q3 board summary", 0], ["Pricing experiment ideas", 0], ["Churn analysis", 1], ["SQL for cohort table", 3], ["Onboarding email copy", 9], ["Roadmap narrative", 40]].map(([title, ago]) => ({ title, at: now - ago * DAY }));\nconst bucket = (at) => { const days = Math.floor((now - at) / DAY); return days < 1 ? "Today" : days < 2 ? "Yesterday" : days < 8 ? "Previous 7 days" : "Older"; };\nconst groups = document.querySelector(".groups");\nconst render = (query = "") => {\n  const shown = items.filter((item) => item.title.toLowerCase().includes(query.toLowerCase()));\n  const nodes = [];\n  let last = "";\n  shown.forEach((item, index) => {\n    const name = bucket(item.at);\n    if (name !== last) nodes.push(Object.assign(document.createElement("h4"), { textContent: name }));\n    last = name;\n    const link = Object.assign(document.createElement("a"), { href: "#", textContent: item.title });\n    if (index === 0 && !query) link.setAttribute("aria-current", "page");\n    nodes.push(link);\n  });\n  groups.replaceChildren(...(nodes.length ? nodes : [Object.assign(document.createElement("em"), { textContent: "No conversations found" })]));\n};\ndocument.querySelector(".ch input").addEventListener("input", (event) => render(event.target.value));\nrender();\n',
            "Past conversations grouped by recency (today, yesterday, this week, older) with search.",
        ),
        Item(
            "AI response streaming",
            '<div class="st"><p class="outp" aria-live="polite" aria-busy="false"></p><div class="row"><button class="go">Ask</button><button class="stop" hidden>Stop</button><span class="mono"></span></div></div>',
            BOX
            + '.st { display: grid; gap: 12px; width: min(500px, 100%); }\n.outp { min-height: 96px; margin: 0; padding: 14px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.outp[aria-busy="true"]::after { content: ""; display: inline-block; width: 8px; height: 1em; margin-left: 2px; vertical-align: text-bottom; background: var(--accent); animation: blink 1s steps(2) infinite; }\n.row { display: flex; gap: 10px; align-items: center; }\n.row button { height: 36px; padding: 0 16px; border: 0; border-radius: 10px; background: var(--primary); color: #fff; font-weight: 600; }\n.row .stop { background: var(--surface-2); color: var(--fg); }\n@keyframes blink { 50% { opacity: 0; } }\n',
            STREAM_JS
            + 'const out = document.querySelector(".outp");\nconst go = document.querySelector(".go");\nconst stop = document.querySelector(".stop");\nconst meta = document.querySelector(".st .mono");\nlet controller = null;\ngo.addEventListener("click", async () => {\n  controller = new AbortController();\n  out.textContent = "";\n  out.setAttribute("aria-busy", "true");\n  go.hidden = true; stop.hidden = false;\n  const started = performance.now();\n  let words = 0;\n  for await (const chunk of reply("streaming")) {\n    if (controller.signal.aborted) break;  // with fetch, pass the signal and the stream ends itself\n    out.textContent += chunk;\n    words += 1;\n    meta.textContent = `${words} words · ${((performance.now() - started) / 1000).toFixed(1)}s`;\n  }\n  out.setAttribute("aria-busy", "false");\n  go.hidden = false; stop.hidden = true;\n  go.textContent = "Ask again";\n});\nstop.addEventListener("click", () => controller?.abort());\n',
            "Text appears as it arrives with a caret; a Stop button aborts and keeps what was written.",
        ),
        Item(
            "Token counter",
            '<div class="tc"><textarea rows="3" aria-label="Prompt">Summarise the attached report for the board in three bullet points.</textarea><div class="bar" role="meter" aria-valuemin="0" aria-valuemax="200" aria-label="Tokens used"><i></i></div><p><span class="n"></span><span class="cost mono"></span></p></div>',
            BOX
            + ".tc { display: grid; gap: 8px; width: min(440px, 100%); }\n.tc textarea { padding: 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); resize: none; }\n.bar { height: 6px; border-radius: 99px; background: var(--surface-2); overflow: hidden; }\n.bar i { display: block; height: 100%; width: 0; background: var(--success); transition: width .2s, background .2s; }\n.tc p { display: flex; justify-content: space-between; margin: 0; font-size: 13px; color: var(--muted); }\n",
            'const area = document.querySelector(".tc textarea");\nconst meter = document.querySelector(".tc .bar");\nconst LIMIT = 200;\nconst PRICE_PER_MILLION = 3;\n// An estimate: about four characters per token for English. Use the provider\'s tokenizer for an exact count.\nconst estimate = (text) => Math.ceil(text.length / 4);\nconst update = () => {\n  const tokens = estimate(area.value);\n  const share = Math.min(1, tokens / LIMIT);\n  meter.firstElementChild.style.width = `${share * 100}%`;\n  meter.firstElementChild.style.background = share > 0.9 ? "var(--danger)" : share > 0.7 ? "var(--warning)" : "var(--success)";\n  meter.setAttribute("aria-valuenow", String(tokens));\n  document.querySelector(".tc .n").textContent = `~${tokens} of ${LIMIT} tokens`;\n  document.querySelector(".tc .cost").textContent = `≈ $${((tokens / 1e6) * PRICE_PER_MILLION).toFixed(6)}`;\n};\narea.addEventListener("input", update);\nupdate();\n',
            "A live estimate of tokens against a budget, with colour as it fills and the cost it implies.",
        ),
        Item(
            "Context indicator",
            '<button class="cx" aria-expanded="false"><svg viewBox="0 0 36 36" width="22" height="22" aria-hidden="true"><circle cx="18" cy="18" r="15" class="tr"/><circle cx="18" cy="18" r="15" class="fl" pathLength="100" stroke-dasharray="62 100"/></svg>62% of context used</button><ul class="cxl" hidden><li><span>System prompt</span><b>1.2k</b></li><li><span>Conversation</span><b>48k</b></li><li><span>3 files</span><b>71k</b></li><li><span>Free</span><b>76k</b></li></ul>',
            BOX
            + ".cx { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px 6px 8px; border: 1px solid var(--border); border-radius: 999px; background: var(--surface); font-size: 13px; }\n.cx circle { fill: none; stroke-width: 4; }\n.cx .tr { stroke: var(--surface-2); }\n.cx .fl { stroke: var(--warning); stroke-linecap: round; transform: rotate(-90deg); transform-origin: center; }\n.cxl { width: 240px; margin: 8px 0 0; padding: 8px 12px; list-style: none; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); }\n.cxl[hidden] { display: none; }\n.cxl li { display: flex; justify-content: space-between; padding: 5px 0; font-size: 13px; color: var(--muted); }\n.cxl b { color: var(--fg); font-variant-numeric: tabular-nums; }\nbody { align-content: center; justify-items: center; }\n",
            'const button = document.querySelector(".cx");\nconst list = document.querySelector(".cxl");\nbutton.addEventListener("click", () => { list.hidden = !list.hidden; button.setAttribute("aria-expanded", String(!list.hidden)); });\n',
            "A ring showing how full the context window is, opening to what is taking the space.",
        ),
        Item(
            "Model selector",
            '<div class="msel"><button aria-haspopup="listbox" aria-expanded="false"><span class="spark">✦</span><b>Sonnet</b><small>Balanced</small></button><ul role="listbox" hidden>'
            + "".join(
                f'<li role="option" tabindex="-1" aria-selected="{"true" if n == "Sonnet" else "false"}" data-n="{n}" data-d="{d}"><b>{n}</b><small>{d}</small><span class="mono">{c}</span></li>'
                for n, d, c in [
                    ("Opus", "Most capable", "200k"),
                    ("Sonnet", "Balanced", "200k"),
                    ("Haiku", "Fastest", "200k"),
                ]
            )
            + "</ul></div>",
            BOX
            + '.msel { position: relative; height: 230px; }\n.msel > button { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.msel small { color: var(--muted); }\n.msel ul { position: absolute; top: 48px; left: 0; width: 280px; margin: 0; padding: 6px; list-style: none; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); box-shadow: var(--shadow); }\n.msel ul[hidden] { display: none; }\n.msel li { display: grid; grid-template-columns: 1fr auto; padding: 8px 10px; border-radius: 8px; cursor: pointer; }\n.msel li small { grid-column: 1; }\n.msel li span { grid-row: 1 / 3; grid-column: 2; align-self: center; }\n.msel li:hover, .msel li:focus, .msel li[aria-selected="true"] { background: color-mix(in srgb, var(--primary) 20%, transparent); outline: none; }\n',
            'const root = document.querySelector(".msel");\nconst button = root.querySelector("button");\nconst list = root.querySelector("ul");\nconst options = [...list.children];\nconst set = (open) => { list.hidden = !open; button.setAttribute("aria-expanded", String(open)); if (open) (options.find((o) => o.getAttribute("aria-selected") === "true") ?? options[0]).focus(); };\nconst choose = (option) => {\n  options.forEach((item) => item.setAttribute("aria-selected", String(item === option)));\n  button.querySelector("b").textContent = option.dataset.n;\n  button.querySelector("small").textContent = option.dataset.d;\n  set(false);\n  button.focus();\n};\nbutton.addEventListener("click", () => set(list.hidden));\nlist.addEventListener("click", (event) => { const option = event.target.closest("li"); if (option) choose(option); });\nlist.addEventListener("keydown", (event) => {\n  const index = options.indexOf(document.activeElement);\n  if (event.key === "ArrowDown") options[(index + 1) % options.length].focus();\n  else if (event.key === "ArrowUp") options[(index - 1 + options.length) % options.length].focus();\n  else if (event.key === "Enter" || event.key === " ") choose(options[index]);\n  else if (event.key === "Escape") { set(false); button.focus(); }\n  else return;\n  event.preventDefault();\n});\ndocument.addEventListener("click", (event) => { if (!root.contains(event.target)) set(false); });\n',
            "A compact trigger in the composer opening a list of models with their character and context size.",
        ),
        Item(
            "Model comparison",
            '<table class="mc"><caption>Compare models</caption><thead><tr><th></th><th>Opus</th><th class="hl">Sonnet</th><th>Haiku</th></tr></thead><tbody><tr><th scope="row">Quality</th><td>●●●●●</td><td class="hl">●●●●○</td><td>●●●○○</td></tr><tr><th scope="row">Speed</th><td>●●○○○</td><td class="hl">●●●●○</td><td>●●●●●</td></tr><tr><th scope="row">Input / M</th><td>$15</td><td class="hl">$3</td><td>$0.80</td></tr><tr><th scope="row">Context</th><td>200k</td><td class="hl">200k</td><td>200k</td></tr></tbody></table>',
            ".mc { width: min(480px, 100%); border-collapse: separate; border-spacing: 0; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); overflow: hidden; }\n.mc caption { text-align: left; margin-bottom: 8px; color: var(--muted); font-size: 13px; }\n.mc th, .mc td { padding: 10px 14px; text-align: center; border-bottom: 1px solid var(--border); font-variant-numeric: tabular-nums; }\n.mc th[scope=row] { text-align: left; font-weight: 500; color: var(--muted); }\n.mc tr:last-child > * { border-bottom: 0; }\n.mc .hl { background: color-mix(in srgb, var(--primary) 14%, transparent); }\n.mc td { color: var(--accent); letter-spacing: .1em; }\n.mc tr:nth-child(n+3) td { color: var(--fg); letter-spacing: 0; }\n",
            note="Models as columns, criteria as rows, the recommended column tinted.",
        ),
        Item(
            "Model performance card",
            '<article class="mp"><header><b>sonnet</b><span class="ok">Healthy</span></header><dl><div><dt>p50 latency</dt><dd>0.8s</dd></div><div><dt>p95 latency</dt><dd>2.4s</dd></div><div><dt>Tokens / s</dt><dd>74</dd></div><div><dt>Error rate</dt><dd>0.12%</dd></div></dl><svg viewBox="0 0 200 40" preserveAspectRatio="none" aria-label="Latency over the last hour" role="img"><polyline points="0,28 20,26 40,30 60,22 80,24 100,14 120,20 140,18 160,25 180,16 200,19"/></svg></article>',
            ".mp { width: 320px; padding: 16px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.mp header { display: flex; justify-content: space-between; align-items: center; font-family: var(--mono); }\n.ok { padding: 1px 9px; border-radius: 99px; background: color-mix(in srgb, var(--success) 20%, transparent); color: var(--success); font: 600 12px var(--font); }\n.mp dl { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 14px 0; }\n.mp dt { font-size: 12px; color: var(--muted); }\n.mp dd { margin: 0; font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums; }\n.mp svg { width: 100%; height: 40px; }\n.mp polyline { fill: none; stroke: var(--accent); stroke-width: 2; vector-effect: non-scaling-stroke; }\n",
            note="Latency percentiles, throughput and error rate for one model, with a recent trend.",
        ),
        Item(
            "AI confidence indicator",
            '<div class="cf"><p>The contract renews on <mark data-c="high">14 May 2027</mark> and the notice period is <mark data-c="low">60 days</mark>.</p><div class="lg"><span data-c="high">High confidence</span><span data-c="medium">Medium</span><span data-c="low">Low — check the source</span></div></div>',
            '.cf { width: min(480px, 100%); padding: 16px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.cf p { margin: 0 0 14px; line-height: 1.7; }\n.cf mark { padding: 1px 4px; border-radius: 4px; color: inherit; background: none; border-bottom: 2px solid var(--c); }\n[data-c=high] { --c: var(--success); }\n[data-c=medium] { --c: var(--warning); }\n[data-c=low] { --c: var(--danger); }\n.cf mark[data-c=low] { border-bottom-style: dashed; background: color-mix(in srgb, var(--danger) 12%, transparent); }\n.lg { display: flex; gap: 14px; font-size: 12px; color: var(--muted); }\n.lg span::before { content: ""; display: inline-block; width: 8px; height: 8px; margin-right: 6px; border-radius: 50%; background: var(--c); }\n',
            note="Uncertain spans are underlined in the answer itself; low confidence is dashed and says to check.",
        ),
        Item(
            "Citation panel",
            '<div class="cit"><p>Revenue grew 12.4% <button class="ref" data-n="1" aria-label="Source 1">1</button>, led by EMEA <button class="ref" data-n="2" aria-label="Source 2">2</button>.</p><ol><li id="s1"><b>Q3 financial report</b><small>p. 4 · finance.northwind.io</small></li><li id="s2"><b>Regional breakdown</b><small>Sheet “EMEA” · drive.northwind.io</small></li></ol></div>',
            ".cit { display: grid; gap: 12px; width: min(460px, 100%); }\n.cit p { margin: 0; line-height: 1.7; }\n.ref { min-width: 18px; height: 18px; padding: 0 5px; border: 0; border-radius: 6px; background: color-mix(in srgb, var(--accent) 22%, transparent); color: var(--accent); font-size: 11px; font-weight: 700; vertical-align: 2px; }\n.cit ol { margin: 0; padding: 0; list-style: none; counter-reset: s; display: grid; gap: 8px; }\n.cit li { counter-increment: s; display: grid; grid-template-columns: auto 1fr; column-gap: 10px; padding: 10px 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); transition: border-color .2s, background .2s; }\n.cit li::before { content: counter(s); grid-row: 1 / 3; align-self: center; display: grid; place-items: center; width: 22px; height: 22px; border-radius: 7px; background: var(--surface-2); font-size: 12px; font-weight: 700; }\n.cit small { color: var(--muted); }\n.cit li.on { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, var(--surface)); }\n",
            'const sources = document.querySelectorAll(".cit li");\nconst light = (number) => sources.forEach((source, i) => source.classList.toggle("on", i + 1 === number));\ndocument.querySelectorAll(".ref").forEach((ref) => {\n  const number = Number(ref.dataset.n);\n  ref.addEventListener("mouseenter", () => light(number));\n  ref.addEventListener("focus", () => light(number));\n  ref.addEventListener("mouseleave", () => light(0));\n  ref.addEventListener("blur", () => light(0));\n  ref.addEventListener("click", () => { light(number); document.getElementById(`s${number}`).scrollIntoView({ block: "nearest", behavior: "smooth" }); });\n});\n',
            "Numbered markers in the text light up and scroll to the matching source.",
        ),
        Item(
            "Source attribution",
            '<p class="sa">Generated from <a href="#"><i></i>Q3 report.pdf</a> <a href="#"><i></i>CRM export</a> and <a href="#"><i></i>2 more</a> · <span>Checked 14 May, 09:12</span></p>',
            ".sa { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin: 0; font-size: 13px; color: var(--muted); }\n.sa a { display: inline-flex; align-items: center; gap: 6px; padding: 2px 10px 2px 6px; border: 1px solid var(--border); border-radius: 99px; color: var(--fg); text-decoration: none; }\n.sa a:hover { border-color: var(--accent); }\n.sa i { width: 14px; height: 14px; border-radius: 4px; background: linear-gradient(135deg, var(--primary), var(--accent)); }\n",
            note="A line under an answer naming what it was built from and when that was read.",
        ),
        Item(
            "Source preview",
            '<p class="sp">Notice is <span class="src" tabindex="0">60 days<span class="card" role="tooltip"><small>Master agreement · §12.3</small>“Either party may terminate by giving not less than <mark>sixty (60) days</mark> written notice…”<a href="#">Open document →</a></span></span>.</p>',
            ".sp { margin-top: 120px; }\n.src { position: relative; border-bottom: 1px dashed var(--accent); cursor: help; }\n.card { position: absolute; left: 0; bottom: calc(100% + 10px); width: 300px; padding: 12px; display: grid; gap: 8px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); box-shadow: var(--shadow); font-size: 13px; line-height: 1.5; opacity: 0; translate: 0 6px; pointer-events: none; transition: opacity .15s .2s, translate .15s .2s; }\n.src:hover .card, .src:focus .card, .src:focus-within .card { opacity: 1; translate: 0 0; pointer-events: auto; }\n.card small { color: var(--muted); }\n.card mark { background: color-mix(in srgb, var(--warning) 35%, transparent); color: inherit; border-radius: 3px; }\n.card a { color: var(--accent); }\n",
            note="Hovering a claim shows the exact passage it came from, with the words highlighted.",
        ),
        box(
            "Retrieval results panel",
            "Retrieved passages",
            '<ul class="rr">'
            + "".join(
                f'<li><div><b>{t}</b><small>{s}</small></div><span class="score" style="--s:{sc}%"><i></i>{sc / 100:.2f}</span></li>'
                for t, s, sc in [
                    ("Termination clause", "master-agreement.pdf · p. 9", 92),
                    ("Renewal terms", "master-agreement.pdf · p. 7", 81),
                    ("Notice by email", "amendment-2.pdf · p. 2", 64),
                    ("Pricing schedule", "order-form.pdf · p. 1", 31),
                ]
            )
            + "</ul>",
            ".rr { margin: 0; padding: 6px; list-style: none; }\n.rr li { display: flex; justify-content: space-between; gap: 12px; align-items: center; padding: 10px; border-radius: 10px; }\n.rr li:hover { background: var(--surface-2); }\n.rr small { display: block; color: var(--muted); }\n.score { display: flex; align-items: center; gap: 8px; font: 12px var(--mono); color: var(--muted); }\n.score i { width: 60px; height: 5px; border-radius: 99px; background: linear-gradient(90deg, var(--accent) var(--s), var(--surface-2) var(--s)); }\n",
            "What the search returned, ranked, each with its relevance score.",
            aside="4 of 128 chunks",
        ),
        Item(
            "RAG context viewer",
            '<div class="rg"><details open><summary>System <span class="mono">1.2k tokens</span></summary><p>You answer questions about Northwind contracts…</p></details><details><summary>Retrieved context <span class="mono">3 chunks · 2.1k</span></summary><p>[1] Either party may terminate by giving not less than sixty (60) days…</p></details><details><summary>User question <span class="mono">14 tokens</span></summary><p>What is the notice period?</p></details></div>',
            '.rg { width: min(500px, 100%); display: grid; gap: 8px; }\n.rg details { border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.rg summary { display: flex; justify-content: space-between; padding: 10px 14px; cursor: pointer; font-weight: 600; list-style: none; }\n.rg summary::before { content: "▸"; margin-right: 8px; color: var(--muted); transition: rotate .15s; }\n.rg details[open] summary::before { rotate: 90deg; }\n.rg .mono { margin-left: auto; font: 12px var(--mono); color: var(--muted); }\n.rg p { margin: 0; padding: 0 14px 12px; font: 13px/1.6 var(--mono); color: var(--muted); white-space: pre-wrap; }\n',
            note="The assembled prompt, section by section, with the size of each part: what the model actually saw.",
        ),
        Item(
            "Knowledge source selector",
            '<fieldset class="ks"><legend>Answer from</legend>'
            + "".join(
                f'<label><input type="checkbox"{" checked" if on else ""}{" disabled" if st == "Syncing…" else ""}><span><b>{n}</b><small>{d}</small></span><em>{st}</em></label>'
                for n, d, st, on in [
                    ("Help centre", "412 articles", "Synced 2h ago", True),
                    ("Contracts", "38 PDFs", "Synced today", True),
                    ("Slack #support", "Last 90 days", "Syncing…", False),
                    ("Notion wiki", "Not connected", "Connect", False),
                ]
            )
            + "</fieldset>",
            ".ks { display: grid; gap: 8px; width: min(440px, 100%); border: 0; padding: 0; }\n.ks legend { margin-bottom: 8px; color: var(--muted); font-size: 13px; }\n.ks label { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); cursor: pointer; }\n.ks label:has(input:checked) { border-color: var(--primary); }\n.ks label:has(input:disabled) { opacity: .6; cursor: progress; }\n.ks input { width: 16px; height: 16px; accent-color: var(--primary); }\n.ks span { flex: 1; }\n.ks small { display: block; color: var(--muted); }\n.ks em { font-style: normal; font-size: 12px; color: var(--muted); }\n",
            note="Which bodies of knowledge an answer may draw on, each with how fresh it is.",
        ),
        Item(
            "Knowledge graph viewer",
            '<svg class="kg" viewBox="0 0 480 300" role="img" aria-label="Knowledge graph"><g class="edges"></g><g class="nodes"></g></svg>',
            ".kg { width: min(520px, 100%); border: 1px solid var(--border); border-radius: 16px; background: var(--surface); touch-action: none; }\n.kg line { stroke: var(--border); stroke-width: 1.5; }\n.kg line.hot { stroke: var(--accent); }\n.kg circle { fill: var(--surface-2); stroke: var(--primary); stroke-width: 2; cursor: grab; }\n.kg g.hot circle { fill: var(--primary); }\n.kg text { fill: var(--fg); font: 11px var(--font); text-anchor: middle; pointer-events: none; }\n",
            """\
const NS = "http://www.w3.org/2000/svg";
const nodes = [["Northwind", 240, 150], ["Contract", 120, 80], ["Renewal", 90, 210], ["Invoice", 360, 80], ["Dana", 380, 220], ["EMEA", 240, 260]].map(([id, x, y]) => ({ id, x, y }));
const links = [["Northwind", "Contract"], ["Contract", "Renewal"], ["Northwind", "Invoice"], ["Northwind", "Dana"], ["Northwind", "EMEA"], ["Dana", "EMEA"]];
const svg = document.querySelector(".kg");
const find = (id) => nodes.find((node) => node.id === id);
const edgeLayer = svg.querySelector(".edges"), nodeLayer = svg.querySelector(".nodes");
const edges = links.map(([a, b]) => { const line = document.createElementNS(NS, "line"); line.dataset.a = a; line.dataset.b = b; edgeLayer.append(line); return line; });
const groups = nodes.map((node) => {
  const group = document.createElementNS(NS, "g");
  const circle = document.createElementNS(NS, "circle");
  circle.setAttribute("r", "22");
  const text = document.createElementNS(NS, "text");
  text.textContent = node.id;
  text.setAttribute("dy", "4");
  group.append(circle, text);
  group.dataset.id = node.id;
  nodeLayer.append(group);
  return group;
});
const draw = () => {
  groups.forEach((group, i) => group.setAttribute("transform", `translate(${nodes[i].x} ${nodes[i].y})`));
  for (const line of edges) {
    const a = find(line.dataset.a), b = find(line.dataset.b);
    line.setAttribute("x1", a.x); line.setAttribute("y1", a.y); line.setAttribute("x2", b.x); line.setAttribute("y2", b.y);
  }
};
// Hovering a node lights it and what it is connected to.
const focus = (id) => {
  edges.forEach((line) => line.classList.toggle("hot", id !== null && (line.dataset.a === id || line.dataset.b === id)));
  groups.forEach((group) => group.classList.toggle("hot", group.dataset.id === id));
};
const point = (event) => { const p = new DOMPoint(event.clientX, event.clientY).matrixTransform(svg.getScreenCTM().inverse()); return [p.x, p.y]; };
let dragging = null;
nodeLayer.addEventListener("pointerdown", (event) => { const group = event.target.closest("g[data-id]"); if (group) { dragging = find(group.dataset.id); svg.setPointerCapture(event.pointerId); } });
svg.addEventListener("pointermove", (event) => {
  if (dragging) { [dragging.x, dragging.y] = point(event); draw(); return; }
  focus(event.target.closest?.("g[data-id]")?.dataset.id ?? null);
});
svg.addEventListener("pointerup", () => { dragging = null; });
draw();
""",
            "Entities and relations as an SVG graph: hover highlights neighbours, nodes can be dragged.",
        ),
        box(
            "AI reasoning timeline",
            "Thinking",
            '<ol class="tl"><li class="done"><b>Understand the question</b><small>Notice period for termination</small></li><li class="done"><b>Search the contracts</b><small>3 passages found</small></li><li class="run"><b>Compare amendments</b><small>Checking which clause is current…</small></li><li><b>Write the answer</b></li></ol>',
            TL,
            "The steps the model is taking, as steps: done, running, still to come.",
            aside="12s",
        ),
        box(
            "Agent activity stream",
            "Agent activity",
            '<ul class="as" aria-live="polite"></ul>',
            ".as { margin: 0; padding: 8px; list-style: none; height: 240px; overflow: auto; font-size: 13px; }\n.as li { display: grid; grid-template-columns: 62px 70px 1fr; gap: 8px; padding: 6px 8px; border-radius: 8px; animation: in .3s var(--ease); }\n.as time { color: var(--muted); font-family: var(--mono); font-size: 11px; }\n.as b { font: 600 11px var(--mono); text-transform: uppercase; }\n.as .think b { color: var(--muted); }\n.as .tool b { color: var(--accent); }\n.as .write b { color: var(--success); }\n@keyframes in { from { opacity: 0; translate: 0 6px; } }\n",
            "A typed, timestamped log of what an agent is doing as it does it.",
            'const list = document.querySelector(".as");\nconst script = [["think", "Planning the migration"], ["tool", "read_file schema.sql"], ["tool", "run_tests --only models"], ["think", "Two tests fail on nullable columns"], ["write", "Edited models/user.py"], ["tool", "run_tests --only models"], ["write", "All 42 tests pass"]];\nlet step = 0;\nconst timer = setInterval(() => {\n  if (step >= script.length) { clearInterval(timer); return; }\n  const [kind, text] = script[step++];\n  const row = document.createElement("li");\n  row.className = kind;\n  row.append(Object.assign(document.createElement("time"), { textContent: new Date().toLocaleTimeString([], { hour12: false }) }), Object.assign(document.createElement("b"), { textContent: kind }), Object.assign(document.createElement("span"), { textContent: text }));\n  list.append(row);\n  list.scrollTop = list.scrollHeight;\n}, 700);\n',
            aside="live",
        ),
        Item(
            "Agent status indicator",
            '<div class="ags">'
            + "".join(
                f'<span class="ag {s}"><i></i>{t}</span>'
                for s, t in [
                    ("idle", "Idle"),
                    ("thinking", "Thinking"),
                    ("working", "Using a tool"),
                    ("waiting", "Needs you"),
                    ("done", "Done"),
                    ("failed", "Failed"),
                ]
            )
            + "</div>",
            ".ags { display: flex; flex-wrap: wrap; gap: 10px; max-width: 460px; }\n.ag { display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface); font-size: 13px; }\n.ag i { width: 8px; height: 8px; border-radius: 50%; background: var(--c, var(--muted)); }\n.thinking { --c: var(--primary); }\n.thinking i { animation: breathe 1.4s ease-in-out infinite; }\n.working { --c: var(--accent); }\n.working i { border-radius: 2px; animation: turn 1s linear infinite; }\n.waiting { --c: var(--warning); border-color: var(--warning); }\n.waiting i { animation: blink 1s steps(2) infinite; }\n.done { --c: var(--success); }\n.failed { --c: var(--danger); }\n@keyframes breathe { 50% { scale: 1.6; opacity: .5; } }\n@keyframes turn { to { rotate: 360deg; } }\n@keyframes blink { 50% { opacity: .2; } }\n",
            note="Six agent states, each with its own colour and motion; 'needs you' is the loudest.",
        ),
        Item(
            "Agent orchestration view",
            '<div class="orc"><div class="lead n">Orchestrator<small>Plans and delegates</small></div><div class="workers">'
            + "".join(
                f'<div class="n {s}">{n}<small>{t}</small></div>'
                for n, t, s in [
                    ("Researcher", "Reading 12 sources", "run"),
                    ("Coder", "Waiting for research", ""),
                    ("Reviewer", "Idle", ""),
                ]
            )
            + "</div></div>",
            '.orc { display: grid; justify-items: center; gap: 34px; width: min(520px, 100%); }\n.n { position: relative; padding: 10px 16px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); text-align: center; font-weight: 600; }\n.n small { display: block; font-weight: 400; color: var(--muted); }\n.lead { border-color: var(--primary); }\n.workers { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; width: 100%; position: relative; }\n.workers::before { content: ""; position: absolute; left: 16.6%; right: 16.6%; top: -17px; border-top: 1px solid var(--border); }\n.workers .n::before { content: ""; position: absolute; left: 50%; top: -18px; height: 17px; border-left: 1px solid var(--border); }\n.lead::after { content: ""; position: absolute; left: 50%; bottom: -18px; height: 17px; border-left: 1px solid var(--border); }\n.n.run { border-color: var(--accent); box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 20%, transparent); }\n',
            note="A coordinator above its workers, connected, with the busy one ringed.",
        ),
        Item(
            "Multi-agent workspace",
            '<div class="maw">'
            + "".join(
                f'<section><header><i class="{s}"></i><b>{n}</b><small>{r}</small></header><p>{t}</p></section>'
                for n, r, s, t in [
                    (
                        "Scout",
                        "Research",
                        "run",
                        "Found 4 competitors with usage-based pricing; pulling their public rate cards.",
                    ),
                    (
                        "Quill",
                        "Writing",
                        "",
                        "Drafting section 2 from Scout’s notes. 340 words so far.",
                    ),
                    (
                        "Lint",
                        "Review",
                        "wait",
                        "Waiting for a draft to check claims against sources.",
                    ),
                ]
            )
            + "</div>",
            ".maw { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; width: min(680px, 100%); }\n.maw section { display: flex; flex-direction: column; gap: 10px; padding: 12px; min-height: 170px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.maw header { display: flex; align-items: center; gap: 8px; }\n.maw header small { margin-left: auto; color: var(--muted); }\n.maw i { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); }\n.maw i.run { background: var(--accent); animation: p 1.2s ease-in-out infinite; }\n.maw i.wait { background: var(--warning); }\n.maw p { margin: 0; color: var(--muted); font-size: 13px; }\n@keyframes p { 50% { opacity: .3; } }\n@media (max-width: 560px) { .maw { grid-template-columns: 1fr; } }\n",
            note="One column per agent showing its role, state and what it is doing now.",
        ),
        Item(
            "Agent workflow canvas",
            '<svg class="wf" viewBox="0 0 560 220" role="img" aria-label="Agent workflow"><defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 10 5 0 10z"/></marker></defs><path class="e done" d="M110 110H170"/><path class="e run" d="M290 110C320 110 310 60 340 60"/><path class="e" d="M290 110C320 110 310 160 340 160"/><path class="e" d="M460 60C490 60 480 110 500 110"/><path class="e" d="M460 160C490 160 480 110 500 110"/><g class="nd done" transform="translate(10 88)"><rect width="100" height="44" rx="10"/><text x="50" y="27">Trigger</text></g><g class="nd done" transform="translate(170 88)"><rect width="120" height="44" rx="10"/><text x="60" y="27">Classify</text></g><g class="nd run" transform="translate(340 38)"><rect width="120" height="44" rx="10"/><text x="60" y="27">Draft reply</text></g><g class="nd" transform="translate(340 138)"><rect width="120" height="44" rx="10"/><text x="60" y="27">Escalate</text></g><g class="nd" transform="translate(500 88)"><rect width="50" height="44" rx="10"/><text x="25" y="27">End</text></g></svg>',
            ".wf { width: min(600px, 100%); border: 1px solid var(--border); border-radius: 16px; background: radial-gradient(var(--border) 1px, transparent 1px) 0 0 / 18px 18px, var(--surface); }\n.wf .e { fill: none; stroke: var(--border); stroke-width: 2; marker-end: url(#ah); }\n.wf marker path { fill: var(--muted); }\n.wf .e.done { stroke: var(--success); }\n.wf .e.run { stroke: var(--accent); stroke-dasharray: 6 5; animation: flow .6s linear infinite; }\n.wf rect { fill: var(--surface-2); stroke: var(--border); stroke-width: 1.5; }\n.wf text { fill: var(--fg); font: 600 12px var(--font); text-anchor: middle; }\n.wf .done rect { stroke: var(--success); }\n.wf .run rect { stroke: var(--accent); filter: drop-shadow(0 0 6px var(--accent)); }\n@keyframes flow { to { stroke-dashoffset: -11; } }\n",
            note="Nodes and curved edges on a dotted canvas; finished paths are solid, the active one flows.",
        ),
        box(
            "Tool execution timeline",
            "Tool calls",
            '<ol class="tl tt"><li class="done"><b>search_docs</b><small>“notice period” · 3 results</small><span class="mono">0.4s</span></li><li class="done"><b>read_file</b><small>master-agreement.pdf, p. 9</small><span class="mono">1.1s</span></li><li class="fail"><b>read_file</b><small>amendment-3.pdf — not found</small><span class="mono">0.2s</span></li><li class="run"><b>read_file</b><small>amendment-2.pdf</small><span class="mono">…</span></li></ol>',
            TL
            + ".tt li { display: grid; grid-template-columns: 1fr auto; }\n.tt small { grid-column: 1; }\n.tt .mono { grid-row: 1 / 3; grid-column: 2; align-self: center; }\n.tt b { font-family: var(--mono); font-size: 13px; }\n",
            "Each tool call in order with its arguments in brief, outcome and duration.",
            aside="4 calls · 1.7s",
        ),
        Item(
            "Tool-call inspector",
            '<div class="ti box"><header><span class="spark">⚙</span><code>search_docs</code><small class="ok">200 · 412 ms</small></header><div class="tabs" role="tablist"><button role="tab" aria-selected="true" aria-controls="ti-in">Input</button><button role="tab" aria-selected="false" aria-controls="ti-out">Output</button></div><pre id="ti-in" role="tabpanel">{\n  "query": "notice period",\n  "top_k": 3\n}</pre><pre id="ti-out" role="tabpanel" hidden>[\n  { "id": "c-91", "score": 0.92 },\n  { "id": "c-88", "score": 0.81 },\n  { "id": "c-40", "score": 0.64 }\n]</pre></div>',
            BOX
            + '.ti code { font: 13px var(--mono); }\n.ti .ok { color: var(--success) !important; }\n.tabs { display: flex; gap: 2px; padding: 6px 6px 0; border-bottom: 1px solid var(--border); }\n.tabs button { padding: 7px 12px; border: 0; border-radius: 8px 8px 0 0; background: none; color: var(--muted); }\n.tabs button[aria-selected="true"] { background: var(--surface-2); color: var(--fg); }\n.ti pre { margin: 0; padding: 14px; font: 12px/1.6 var(--mono); max-height: 200px; overflow: auto; }\n',
            'const tabs = [...document.querySelectorAll(".ti [role=tab]")];\ntabs.forEach((tab) => tab.addEventListener("click", () => tabs.forEach((item) => {\n  const on = item === tab;\n  item.setAttribute("aria-selected", String(on));\n  document.getElementById(item.getAttribute("aria-controls")).hidden = !on;\n})));\n',
            "One call opened up: the exact input sent and output received, on tabs, with status and time.",
        ),
        Item(
            "Function execution card",
            '<details class="fx" open><summary><span class="st done">✓</span><code>create_invoice(customer="Northwind", amount=2400)</code><span class="mono">0.8s</span></summary><dl><dt>Returned</dt><dd><code>{ "id": "inv_2041", "status": "draft" }</code></dd></dl><footer><button>Approve and send</button><button class="g">Discard</button></footer></details>',
            ".fx { width: min(500px, 100%); border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.fx summary { display: flex; align-items: center; gap: 10px; padding: 12px 14px; cursor: pointer; list-style: none; }\n.fx code { font: 12px var(--mono); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.fx summary code { flex: 1; }\n.st { display: grid; place-items: center; flex: none; width: 20px; height: 20px; border-radius: 50%; font-size: 11px; }\n.st.done { background: color-mix(in srgb, var(--success) 25%, transparent); color: var(--success); }\n.mono { font: 12px var(--mono); color: var(--muted); }\n.fx dl { margin: 0; padding: 0 14px 12px; }\n.fx dt { font-size: 11px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }\n.fx dd { margin: 4px 0 0; padding: 8px 10px; border-radius: 8px; background: var(--surface-2); }\n.fx footer { display: flex; gap: 8px; padding: 10px 14px; border-top: 1px solid var(--border); }\n.fx footer button { height: 32px; padding: 0 12px; border: 0; border-radius: 8px; background: var(--primary); color: #fff; font-weight: 600; }\n.fx footer .g { background: var(--surface-2); color: var(--fg); }\n",
            note="A function the model called, what it returned, and a human approval before its effect goes out.",
        ),
        Item(
            "AI task progress",
            '<div class="tp"><header><b>Migrating the billing module</b><span class="mono"></span></header><div class="bar"><i></i></div><ol></ol></div>',
            BOX
            + '.tp { width: min(460px, 100%); padding: 16px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); }\n.tp header { display: flex; justify-content: space-between; margin-bottom: 10px; }\n.bar { height: 6px; border-radius: 99px; background: var(--surface-2); overflow: hidden; }\n.bar i { display: block; height: 100%; width: 0; background: linear-gradient(90deg, var(--primary), var(--accent)); transition: width .4s var(--ease); }\n.tp ol { margin: 14px 0 0; padding: 0; list-style: none; display: grid; gap: 8px; }\n.tp li { display: flex; gap: 10px; align-items: center; color: var(--muted); }\n.tp li::before { content: ""; width: 16px; height: 16px; border-radius: 50%; border: 2px solid var(--border); flex: none; }\n.tp li.done { color: var(--fg); }\n.tp li.done::before { border-color: var(--success); background: var(--success); }\n.tp li.now { color: var(--fg); }\n.tp li.now::before { border-color: var(--accent); border-top-color: transparent; animation: spin .8s linear infinite; }\n@keyframes spin { to { rotate: 360deg; } }\n',
            'const STEPS = ["Read the existing code", "Plan the changes", "Edit 6 files", "Run the test suite", "Summarise what changed"];\nconst list = document.querySelector(".tp ol");\nconst bar = document.querySelector(".tp .bar i");\nconst label = document.querySelector(".tp .mono");\nconst rows = STEPS.map((text) => { const row = Object.assign(document.createElement("li"), { textContent: text }); list.append(row); return row; });\nlet current = 0;\n// Progress comes from finished steps, never from a timer pretending to know.\nconst render = () => {\n  rows.forEach((row, i) => { row.className = i < current ? "done" : i === current ? "now" : ""; });\n  bar.style.width = `${(current / STEPS.length) * 100}%`;\n  label.textContent = current === STEPS.length ? "Done" : `${current} of ${STEPS.length}`;\n};\nconst timer = setInterval(() => { current += 1; render(); if (current === STEPS.length) clearInterval(timer); }, 1100);\nrender();\n',
            "A long task as a checklist: the bar is the share of steps finished, the current step spins.",
        ),
        Item(
            "AI generation progress",
            '<div class="gp"><div class="frame"><div class="scan"></div><span class="pct">0%</span></div><p class="mono"></p><button>Cancel</button></div>',
            BOX
            + ".gp { display: grid; justify-items: center; gap: 12px; }\n.frame { position: relative; display: grid; place-items: center; width: 260px; height: 170px; border-radius: 16px; overflow: hidden; background: var(--surface); border: 1px solid var(--border); }\n.scan { position: absolute; inset: 0; background: linear-gradient(100deg, transparent 30%, color-mix(in srgb, var(--primary) 35%, transparent) 50%, transparent 70%); background-size: 250% 100%; animation: sweep 1.6s linear infinite; }\n.pct { position: relative; font-size: 28px; font-weight: 700; font-variant-numeric: tabular-nums; }\n.gp p { margin: 0; }\n.gp button { border: 0; background: none; color: var(--muted); text-decoration: underline; }\n@keyframes sweep { from { background-position: 120% 0; } to { background-position: -120% 0; } }\n",
            'const STAGES = [[10, "Understanding the request"], [35, "Composing the layout"], [70, "Rendering details"], [95, "Finishing"], [100, "Ready"]];\nconst pct = document.querySelector(".pct");\nconst label = document.querySelector(".gp .mono");\nconst cancel = document.querySelector(".gp button");\nlet stage = 0;\nconst show = () => { pct.textContent = `${STAGES[stage][0]}%`; label.textContent = STAGES[stage][1]; };\nconst timer = setInterval(() => {\n  stage += 1;\n  show();\n  if (stage === STAGES.length - 1) { clearInterval(timer); document.querySelector(".scan").remove(); cancel.hidden = true; }\n}, 900);\ncancel.addEventListener("click", () => { clearInterval(timer); document.querySelector(".scan")?.remove(); label.textContent = "Cancelled"; cancel.hidden = true; });\nshow();\n',
            "A placeholder the size of the result, a percentage tied to named stages, and a way to cancel.",
        ),
        Item(
            "Generation history",
            '<div class="gh"><div class="big" aria-live="polite">Version 3</div><div class="strip" role="listbox" aria-label="Generations">'
            + "".join(
                f'<button role="option" aria-selected="{"true" if i == 3 else "false"}" style="--h:{h}">v{i}</button>'
                for i, h in [(1, 250), (2, 190), (3, 320), (4, 20)]
            )
            + "</div></div>",
            '.gh { display: grid; gap: 10px; width: 320px; }\n.big { display: grid; place-items: center; height: 170px; border-radius: 16px; font-weight: 700; background: linear-gradient(135deg, hsl(var(--h, 320) 70% 45%), hsl(calc(var(--h, 320) + 60) 70% 30%)); transition: background .3s; }\n.strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }\n.strip button { height: 54px; border: 2px solid transparent; border-radius: 10px; color: #fff; font-size: 12px; font-weight: 700; background: linear-gradient(135deg, hsl(var(--h) 70% 45%), hsl(calc(var(--h) + 60) 70% 30%)); opacity: .6; }\n.strip button[aria-selected="true"] { border-color: var(--fg); opacity: 1; }\n',
            'const big = document.querySelector(".big");\nconst options = [...document.querySelectorAll(".strip button")];\nconst choose = (option) => {\n  options.forEach((item) => item.setAttribute("aria-selected", String(item === option)));\n  big.style.setProperty("--h", option.style.getPropertyValue("--h"));\n  big.textContent = `Version ${option.textContent.slice(1)}`;\n};\noptions.forEach((option, index) => {\n  option.addEventListener("click", () => choose(option));\n  option.addEventListener("keydown", (event) => {\n    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;\n    if (step) { const next = options[(index + step + options.length) % options.length]; choose(next); next.focus(); }\n  });\n});\n',
            "Every attempt kept as a thumbnail; choosing one brings it back as the current result.",
        ),
        Item(
            "Regeneration controls",
            '<div class="rg2"><button class="nav" aria-label="Previous response">‹</button><span class="mono" aria-live="polite">2 / 3</span><button class="nav" aria-label="Next response">›</button><button class="re">↻ Regenerate</button><select aria-label="Regenerate with"><option>Same settings</option><option>Shorter</option><option>More detailed</option><option>Different model</option></select></div>',
            BOX
            + ".rg2 { display: flex; align-items: center; gap: 8px; padding: 6px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\n.rg2 .nav { width: 28px; height: 28px; border: 0; border-radius: 8px; background: var(--surface-2); }\n.rg2 .nav:disabled { opacity: .3; }\n.rg2 .re { height: 30px; padding: 0 12px; border: 0; border-radius: 8px; background: var(--primary); color: #fff; font-weight: 600; }\n.rg2 select { height: 30px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface-2); }\n",
            'let total = 3, current = 2;\nconst label = document.querySelector(".rg2 .mono");\nconst [previous, next] = document.querySelectorAll(".rg2 .nav");\nconst render = () => { label.textContent = `${current} / ${total}`; previous.disabled = current === 1; next.disabled = current === total; };\nprevious.addEventListener("click", () => { current -= 1; render(); });\nnext.addEventListener("click", () => { current += 1; render(); });\n// A new attempt is added after the others and shown; earlier ones are never lost.\ndocument.querySelector(".re").addEventListener("click", () => { total += 1; current = total; render(); });\nrender();\n',
            "Page through earlier attempts, make a new one, and choose how the new one should differ.",
        ),
        Item(
            "Prompt comparison",
            '<div class="cmp2"><section><header>Prompt A</header><p>Summarise the report.</p><footer><span>Clarity <b>3/5</b></span><span>312 tokens</span></footer></section><section class="win"><header>Prompt B <i>Better</i></header><p>Summarise the report for the board in three bullets, leading with risk.</p><footer><span>Clarity <b>5/5</b></span><span>188 tokens</span></footer></section></div>',
            ".cmp2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; width: min(600px, 100%); }\n.cmp2 section { display: flex; flex-direction: column; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.cmp2 header { display: flex; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border); font-weight: 600; }\n.cmp2 header i { font-style: normal; font-size: 12px; color: var(--success); }\n.cmp2 p { flex: 1; margin: 0; padding: 14px; font: 13px/1.6 var(--mono); }\n.cmp2 footer { display: flex; justify-content: space-between; padding: 10px 14px; border-top: 1px solid var(--border); font-size: 12px; color: var(--muted); }\n.cmp2 footer b { color: var(--fg); }\n.win { border-color: var(--success) !important; }\n@media (max-width: 520px) { .cmp2 { grid-template-columns: 1fr; } }\n",
            note="Two prompts side by side with the same measures under each, the better one marked.",
        ),
        Item(
            "Prompt diff viewer",
            '<div class="df"><div class="pair"><textarea aria-label="Before">Summarise the report in a few sentences for the team.</textarea><textarea aria-label="After">Summarise the report in three bullets for the board, leading with risk.</textarea></div><p class="res" aria-live="polite"></p></div>',
            DIFF_CSS
            + ".df { display: grid; gap: 10px; width: min(560px, 100%); }\n.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }\n.pair textarea { height: 90px; padding: 10px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); resize: none; font: 13px/1.5 var(--mono); }\n.res { margin: 0; padding: 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); line-height: 1.8; white-space: pre-wrap; }\n",
            DIFF_JS
            + 'const [before, after] = document.querySelectorAll(".pair textarea");\nconst result = document.querySelector(".res");\nconst update = () => renderDiff(result, before.value, after.value);\nbefore.addEventListener("input", update);\nafter.addEventListener("input", update);\nupdate();\n',
            "A word-level diff of two prompt versions, recomputed as either is edited.",
        ),
        Item(
            "Response diff viewer",
            '<div class="rd"><header><label><input type="radio" name="m" value="inline" checked> Inline</label><label><input type="radio" name="m" value="split"> Side by side</label></header><div class="view"></div></div>',
            DIFF_CSS
            + ".rd { width: min(560px, 100%); border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.rd header { display: flex; gap: 16px; padding: 10px 14px; border-bottom: 1px solid var(--border); font-size: 13px; }\n.view { padding: 14px; line-height: 1.8; }\n.view.split { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }\n.view p { margin: 0; }\n",
            DIFF_JS
            + 'const OLD = "Revenue grew 12% in Q3, driven by new customers in EMEA.";\nconst NEW = "Revenue grew 12.4% in Q3, driven mostly by expansion in EMEA and one large renewal.";\nconst view = document.querySelector(".view");\nconst render = (mode) => {\n  view.classList.toggle("split", mode === "split");\n  if (mode === "inline") { const p = document.createElement("p"); renderDiff(p, OLD, NEW); view.replaceChildren(p); return; }\n  // Side by side: each column shows only its own side of the changes.\n  const left = document.createElement("p"), right = document.createElement("p");\n  for (const [kind, text] of diffWords(OLD, NEW)) {\n    if (kind !== "ins") left.append(kind === "del" ? Object.assign(document.createElement("del"), { textContent: text }) : text);\n    if (kind !== "del") right.append(kind === "ins" ? Object.assign(document.createElement("ins"), { textContent: text }) : text);\n  }\n  view.replaceChildren(left, right);\n};\ndocument.querySelectorAll(".rd input").forEach((input) => input.addEventListener("change", () => render(input.value)));\nrender("inline");\n',
            "What changed between two answers, inline or in two columns.",
        ),
        Item(
            "AI feedback controls",
            '<div class="fb"><div class="row"><button aria-pressed="false" data-v="up" aria-label="Good response">👍</button><button aria-pressed="false" data-v="down" aria-label="Bad response">👎</button></div><form hidden><p>What went wrong?</p><label><input type="checkbox" name="r" value="wrong"> Not accurate</label><label><input type="checkbox" name="r" value="long"> Too long</label><label><input type="checkbox" name="r" value="unsafe"> Harmful or unsafe</label><textarea name="note" rows="2" placeholder="Anything else? (optional)" aria-label="More detail"></textarea><button>Send feedback</button></form><p class="ty" role="status"></p></div>',
            '.fb { display: grid; gap: 10px; width: min(360px, 100%); }\n.fb .row { display: flex; gap: 6px; }\n.fb .row button { width: 36px; height: 36px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }\n.fb .row button[aria-pressed="true"] { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 18%, transparent); }\n.fb form { display: grid; gap: 8px; padding: 14px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.fb form[hidden] { display: none; }\n.fb form p { margin: 0; font-weight: 600; }\n.fb textarea { padding: 8px 10px; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); resize: none; }\n.fb form button { justify-self: start; height: 34px; padding: 0 14px; border: 0; border-radius: 9px; background: var(--primary); color: #fff; font-weight: 600; }\n.ty { margin: 0; color: var(--success); font-size: 14px; min-height: 20px; }\n',
            'const buttons = [...document.querySelectorAll(".fb .row button")];\nconst form = document.querySelector(".fb form");\nconst thanks = document.querySelector(".ty");\nbuttons.forEach((button) => button.addEventListener("click", () => {\n  const on = button.getAttribute("aria-pressed") !== "true";\n  buttons.forEach((item) => item.setAttribute("aria-pressed", String(item === button && on)));\n  form.hidden = !(on && button.dataset.v === "down");  // only a thumbs-down asks why\n  thanks.textContent = on && button.dataset.v === "up" ? "Thanks for the feedback." : "";\n}));\nform.addEventListener("submit", (event) => {\n  event.preventDefault();\n  const data = new FormData(form);\n  const reasons = data.getAll("r");\n  form.hidden = true;\n  thanks.textContent = `Thanks — recorded${reasons.length ? ` (${reasons.join(", ")})` : ""}.`;\n});\n',
            "Thumbs up is one click; thumbs down opens reasons and an optional note.",
        ),
        Item(
            "AI thumbs controls",
            '<div class="th" role="group" aria-label="Rate this response"><button aria-pressed="false" aria-label="Good response"><svg viewBox="0 0 24 24" width="18" height="18"><path d="M7 11v9H4v-9zM7 11l4-8c1.700 0 2.500 1.200 2.500 2.500V9h5a2 2 0 0 1 2 2.300l-1.200 7A2 2 0 0 1 17.300 20H7"/></svg></button><button aria-pressed="false" aria-label="Bad response"><svg viewBox="0 0 24 24" width="18" height="18" style="rotate:180deg"><path d="M7 11v9H4v-9zM7 11l4-8c1.700 0 2.500 1.200 2.500 2.500V9h5a2 2 0 0 1 2 2.300l-1.200 7A2 2 0 0 1 17.300 20H7"/></svg></button></div>',
            '.th { display: inline-flex; gap: 2px; padding: 3px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }\n.th button { display: grid; place-items: center; width: 34px; height: 30px; border: 0; border-radius: 7px; background: none; }\n.th svg { fill: none; stroke: var(--muted); stroke-width: 1.8; stroke-linejoin: round; transition: stroke .15s, fill .15s; }\n.th button:hover { background: var(--surface-2); }\n.th button[aria-pressed="true"] svg { stroke: var(--primary); fill: color-mix(in srgb, var(--primary) 35%, transparent); animation: bump .3s var(--ease); }\n@keyframes bump { 40% { scale: 1.3; rotate: -8deg; } }\n',
            'const buttons = [...document.querySelectorAll(".th button")];\nbuttons.forEach((button) => button.addEventListener("click", () => {\n  const on = button.getAttribute("aria-pressed") !== "true";\n  buttons.forEach((item) => item.setAttribute("aria-pressed", String(item === button && on)));  // mutually exclusive, and can be undone\n}));\n',
            "Two mutually exclusive toggle buttons; pressing the active one clears it.",
        ),
        Item(
            "AI rating widget",
            '<form class="arw"><p>How useful was this answer?</p><div class="scale">'
            + "".join(
                f'<label><input type="radio" name="s" value="{i}"><span>{i}</span></label>'
                for i in range(1, 6)
            )
            + '</div><div class="ends"><span>Not useful</span><span>Very useful</span></div><output></output></form>',
            ".arw { display: grid; gap: 8px; width: 300px; padding: 14px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); }\n.arw p { margin: 0; font-weight: 600; }\n.scale { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; }\n.scale input { position: absolute; opacity: 0; }\n.scale span { display: grid; place-items: center; height: 38px; border: 1px solid var(--border); border-radius: 10px; cursor: pointer; font-weight: 600; }\n.scale input:checked + span { background: var(--primary); border-color: var(--primary); color: #fff; }\n.scale input:focus-visible + span { outline: 2px solid var(--accent); }\n.ends { display: flex; justify-content: space-between; font-size: 12px; color: var(--muted); }\n.arw output { font-size: 13px; color: var(--success); min-height: 18px; }\n",
            'const form = document.querySelector(".arw");\nform.addEventListener("change", () => { form.querySelector("output").textContent = `Saved: ${new FormData(form).get("s")} of 5. You can change it.`; });\n',
            "A five-point scale with worded ends; saves on choice and can be changed.",
        ),
        chips(
            "AI suggestion chips",
            "Suggested",
            ["Make it shorter", "Add an example", "Change the tone", "Translate to Spanish"],
            "Quick transformations of the last answer, one tap each.",
        ),
        chips(
            "Follow-up suggestions",
            "Ask a follow-up",
            [
                "Which region grew fastest?",
                "How does this compare to Q2?",
                "What drove the EMEA increase?",
            ],
            "Questions that continue the thread, shown under the answer.",
            '.sug div { flex-direction: column; align-items: flex-start; }\n.chipx::before { content: "↳"; color: var(--muted); }\n',
        ),
        Item(
            "Smart follow-up prompts",
            '<div class="sf"><p class="ans">EMEA revenue grew 18% while APAC fell 3%.</p><div class="list" aria-live="polite"></div></div>',
            BOX
            + ".sf { display: grid; gap: 10px; width: min(480px, 100%); }\n.ans { margin: 0; padding: 12px 14px; border-radius: 14px; background: var(--surface-2); }\n.list { display: flex; flex-wrap: wrap; gap: 8px; }\n",
            '// Follow-ups are built from what the answer mentions, so they are always about this answer.\nconst answer = document.querySelector(".ans").textContent;\nconst RULES = [\n  [/\\b(EMEA|APAC|Americas)\\b/g, (match) => `Break down ${match} by country`],\n  [/\\bfell\\b|\\bdropped\\b/, () => "Why did it fall?"],\n  [/\\bgrew\\b/, () => "What drove the growth?"],\n  [/\\d+%/, () => "Show this as a chart"],\n];\nconst prompts = new Set();\nfor (const [pattern, build] of RULES) for (const match of answer.match(pattern) ?? []) prompts.add(build(match));\ndocument.querySelector(".list").append(...[...prompts].slice(0, 5).map((text) => Object.assign(document.createElement("button"), { className: "chipx", textContent: text })));\n',
            "Follow-ups derived from entities and verbs in the answer itself rather than a fixed list.",
        ),
        Item(
            "Conversation branching",
            '<div class="br"><div class="m u">How should we price the Team plan?</div><div class="m a"><p></p><div class="sw"><button aria-label="Previous branch">‹</button><span class="mono"></span><button aria-label="Next branch">›</button></div></div></div>',
            BOX
            + ".br { display: grid; gap: 10px; width: min(460px, 100%); }\n.m { padding: 10px 14px; border-radius: 16px; }\n.m.u { justify-self: end; background: var(--primary); color: #fff; }\n.m.a { background: var(--surface-2); }\n.m.a p { margin: 0 0 8px; }\n.sw { display: flex; align-items: center; gap: 6px; }\n.sw button { width: 24px; height: 24px; border: 0; border-radius: 6px; background: var(--surface); }\n.sw button:disabled { opacity: .3; }\n",
            'const BRANCHES = ["Per seat, $24 a month, with a 20% annual discount.", "Usage-based: $0.02 per run with a $49 monthly minimum.", "A flat $299 a month for up to 20 seats, then per seat."];\nlet index = 0;\nconst text = document.querySelector(".m.a p");\nconst label = document.querySelector(".sw .mono");\nconst [previous, next] = document.querySelectorAll(".sw button");\nconst render = () => { text.textContent = BRANCHES[index]; label.textContent = `${index + 1} / ${BRANCHES.length}`; previous.disabled = index === 0; next.disabled = index === BRANCHES.length - 1; };\nprevious.addEventListener("click", () => { index -= 1; render(); });\nnext.addEventListener("click", () => { index += 1; render(); });\nrender();\n',
            "Alternative answers to the same message live side by side; arrows switch between them.",
        ),
        Item(
            "Conversation fork",
            '<svg class="fk" viewBox="0 0 420 200" role="img" aria-label="Conversation tree"><path d="M40 100H140"/><path d="M140 100C180 100 170 50 210 50H380"/><path class="alt" d="M140 100C180 100 170 150 210 150H300"/><g class="pt"><circle cx="40" cy="100" r="7"/><circle cx="140" cy="100" r="9" class="fork"/><circle cx="210" cy="50" r="7"/><circle cx="300" cy="50" r="7"/><circle cx="380" cy="50" r="7" class="now"/><circle cx="210" cy="150" r="7" class="alt"/><circle cx="300" cy="150" r="7" class="alt"/></g><text x="140" y="80">Forked here</text><text x="380" y="30">You are here</text><text x="300" y="178" class="alt">Earlier branch</text></svg>',
            ".fk { width: min(460px, 100%); }\n.fk path { fill: none; stroke: var(--primary); stroke-width: 2; }\n.fk path.alt { stroke: var(--border); stroke-dasharray: 5 4; }\n.fk circle { fill: var(--surface); stroke: var(--primary); stroke-width: 2; }\n.fk circle.alt { stroke: var(--border); }\n.fk circle.fork { fill: var(--primary); }\n.fk circle.now { fill: var(--accent); stroke: var(--accent); }\n.fk text { fill: var(--muted); font: 11px var(--font); text-anchor: middle; }\n",
            note="The conversation as a tree: where it split, which branch is live, which was left behind.",
        ),
        Item(
            "Message actions",
            '<div class="ma"><div class="bubble" tabindex="0">Revenue grew 12.4% quarter on quarter, led by EMEA.<div class="acts" role="toolbar" aria-label="Message actions"><button aria-label="Copy">⧉</button><button aria-label="Edit">✎</button><button aria-label="Regenerate">↻</button><button aria-label="Branch from here">⑂</button></div></div><p role="status"></p></div>',
            ".ma { display: grid; gap: 8px; margin-top: 30px; }\n.bubble { position: relative; max-width: 360px; padding: 12px 14px; border-radius: 16px; background: var(--surface-2); }\n.acts { position: absolute; right: 8px; top: -18px; display: flex; gap: 2px; padding: 3px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); box-shadow: var(--shadow); opacity: 0; translate: 0 4px; transition: opacity .15s, translate .15s; }\n.bubble:hover .acts, .bubble:focus .acts, .bubble:focus-within .acts { opacity: 1; translate: 0 0; }\n.acts button { width: 28px; height: 26px; border: 0; border-radius: 7px; background: none; }\n.acts button:hover { background: var(--surface-2); }\n.ma p { margin: 0; font-size: 13px; color: var(--muted); min-height: 18px; }\n",
            'const status = document.querySelector(".ma p");\nconst bubble = document.querySelector(".bubble");\ndocument.querySelector(".acts").addEventListener("click", async (event) => {\n  const button = event.target.closest("button");\n  if (!button) return;\n  const action = button.getAttribute("aria-label");\n  if (action === "Copy") {\n    try { await navigator.clipboard.writeText(bubble.firstChild.textContent.trim()); status.textContent = "Copied."; }\n    catch { status.textContent = "Select the text and copy it manually."; }\n  } else status.textContent = `${action} requested.`;\n});\n',
            "A small toolbar that appears over a message on hover and on keyboard focus.",
        ),
        Item(
            "Inline AI editing",
            '<div class="ie"><p class="doc" contenteditable="true" spellcheck="false">Our new export feature is really very good and lets you download all of your data in many formats quickly.</p><div class="tool" hidden><button data-a="shorter">Shorter</button><button data-a="formal">More formal</button><button data-a="fix">Fix grammar</button></div><p class="mono">Select some text to edit it with AI.</p></div>',
            BOX
            + ".ie { position: relative; width: min(480px, 100%); display: grid; gap: 10px; }\n.doc { margin: 0; padding: 16px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); line-height: 1.7; outline: none; }\n.doc mark { background: color-mix(in srgb, var(--accent) 25%, transparent); color: inherit; border-radius: 3px; }\n.tool { position: absolute; display: flex; gap: 2px; padding: 4px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface-2); box-shadow: var(--shadow); z-index: 2; }\n.tool[hidden] { display: none; }\n.tool button { padding: 5px 10px; border: 0; border-radius: 7px; background: none; font-size: 13px; }\n.tool button:hover { background: var(--surface); }\n.ie > .mono { margin: 0; }\n",
            '// Stand-ins for a model call: each returns a rewrite of the selected text.\nconst REWRITE = {\n  shorter: (text) => text.replace(/\\b(really|very|quite|all of)\\s+/gi, "").replace(/\\s+quickly/, ""),\n  formal: (text) => text.replace(/really very good/i, "highly effective").replace(/lets you/i, "enables you to"),\n  fix: (text) => text.replace(/\\s+/g, " ").trim(),\n};\nconst root = document.querySelector(".ie");\nconst doc = root.querySelector(".doc");\nconst tool = root.querySelector(".tool");\nlet range = null;\ndocument.addEventListener("selectionchange", () => {\n  const selection = document.getSelection();\n  if (!selection.rangeCount || selection.isCollapsed || !doc.contains(selection.anchorNode)) { tool.hidden = true; return; }\n  range = selection.getRangeAt(0).cloneRange();\n  const box = range.getBoundingClientRect(), base = root.getBoundingClientRect();\n  tool.hidden = false;\n  tool.style.left = `${Math.max(0, box.left - base.left)}px`;\n  tool.style.top = `${box.top - base.top - 44}px`;\n});\ntool.addEventListener("mousedown", (event) => event.preventDefault());  // keep the selection\ntool.addEventListener("click", (event) => {\n  const button = event.target.closest("button");\n  if (!button || !range) return;\n  const mark = Object.assign(document.createElement("mark"), { textContent: REWRITE[button.dataset.a](range.toString()) });\n  range.deleteContents();\n  range.insertNode(mark);  // the change is highlighted so it can be reviewed\n  document.getSelection().removeAllRanges();\n  tool.hidden = true;\n});\n',
            "Selecting text raises a small toolbar of rewrites; the replacement is highlighted for review.",
        ),
        Item(
            "AI autocomplete",
            '<div class="ac"><div class="wrap"><div class="ghost" aria-hidden="true"></div><textarea rows="3" aria-label="Message" aria-describedby="ach">Thanks for </textarea></div><p id="ach" class="mono">Tab accepts the suggestion · Esc dismisses it</p></div>',
            BOX
            + ".ac { display: grid; gap: 8px; width: min(460px, 100%); }\n.wrap { position: relative; }\n.wrap textarea, .ghost { width: 100%; padding: 12px 14px; border: 1px solid var(--border); border-radius: 12px; font: 15px/1.5 var(--font); white-space: pre-wrap; overflow-wrap: break-word; }\n.wrap textarea { position: relative; display: block; background: transparent; resize: none; outline: none; }\n.wrap textarea:focus { border-color: var(--primary); }\n.ghost { position: absolute; inset: 0; border-color: transparent; background: var(--surface); color: transparent; pointer-events: none; }\n.ghost b { color: var(--muted); font-weight: 400; }\n.ac .mono { margin: 0; }\n",
            '// A stand-in for a completion model: continues known openings.\nconst COMPLETIONS = [["thanks for ", "getting back to me so quickly."], ["i wanted to ", "follow up on our conversation from last week."], ["let me know ", "if you have any questions."], ["best ", "regards,"]];\nconst area = document.querySelector(".ac textarea");\nconst ghost = document.querySelector(".ghost");\nlet suggestion = "";\nconst suggest = () => {\n  const text = area.value;\n  const atEnd = area.selectionStart === text.length;\n  const found = atEnd ? COMPLETIONS.find(([start]) => text.toLowerCase().endsWith(start)) : null;\n  suggestion = found ? found[1] : "";\n  // The ghost repeats the typed text invisibly so the suggestion lands exactly after it.\n  ghost.replaceChildren(text, Object.assign(document.createElement("b"), { textContent: suggestion }));\n};\narea.addEventListener("input", suggest);\narea.addEventListener("keydown", (event) => {\n  if (!suggestion) return;\n  if (event.key === "Tab") { event.preventDefault(); area.value += suggestion; suggest(); }\n  else if (event.key === "Escape") { suggestion = ""; ghost.replaceChildren(area.value); }\n});\narea.addEventListener("click", suggest);\nsuggest();\n',
            "Greyed ghost text after the caret; Tab accepts it, Escape dismisses, typing on replaces it.",
        ),
    ),
)
