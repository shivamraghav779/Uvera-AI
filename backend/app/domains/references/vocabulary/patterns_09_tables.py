"""Patterns 301-330: tables and data collections."""

from app.domains.references.vocabulary.base import Item, Section

DATA = [
    ("Northwind", "Dana Whitfield", "Active", 74200, "2026-05-02"),
    ("Acme Labs", "Mika Tanaka", "Trial", 4100, "2026-05-11"),
    ("Globex", "Ravi Shah", "Active", 38400, "2026-04-19"),
    ("Initech", "Sam Okafor", "Churned", 0, "2026-02-27"),
    ("Umbrella", "Zoe Lindqvist", "Active", 21900, "2026-03-30"),
    ("Hooli", "Ana Costa", "Trial", 1200, "2026-05-13"),
]
HEAD = ["Company", "Owner", "Status", "Revenue", "Renewal"]
T = """\
.tw { width: min(640px, 100%); border: 1px solid var(--border); border-radius: 14px; background: var(--surface); overflow: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
caption { caption-side: top; text-align: left; padding: 12px 14px; font-weight: 600; border-bottom: 1px solid var(--border); }
th, td { padding: 10px 14px; text-align: left; white-space: nowrap; border-bottom: 1px solid var(--border); }
thead th { font-size: 12px; font-weight: 600; color: var(--muted); background: var(--surface-2); }
tbody tr:last-child > * { border-bottom: 0; }
tbody tr:hover { background: color-mix(in srgb, var(--surface-2) 60%, transparent); }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.st { padding: 1px 9px; border-radius: 99px; font-size: 12px; font-weight: 600; --c: var(--muted); background: color-mix(in srgb, var(--c) 20%, transparent); color: var(--c); }
.st.Active { --c: var(--success); }
.st.Trial { --c: var(--warning); }
.st.Churned { --c: var(--danger); }
"""


def money(value: int) -> str:
    return f"${value:,}"


def body(extra_first: str = "", extra_last: str = "") -> str:
    return "".join(
        f'<tr data-status="{s}">{extra_first}<td>{c}</td><td>{o}</td><td><span class="st {s}">{s}</span></td><td class="num">{money(r)}</td><td>{d}</td>{extra_last}</tr>'
        for c, o, s, r, d in DATA
    )


def head(extra_first: str = "", extra_last: str = "") -> str:
    cells = "".join(
        f'<th scope="col"{' class="num"' if h == "Revenue" else ""}>{h}</th>' for h in HEAD
    )
    return f"<thead><tr>{extra_first}{cells}{extra_last}</tr></thead>"


def table(
    caption: str = "Accounts",
    first_h: str = "",
    last_h: str = "",
    first: str = "",
    last: str = "",
    foot: str = "",
) -> str:
    return f'<div class="tw"><table><caption>{caption}</caption>{head(first_h, last_h)}<tbody>{body(first, last)}</tbody>{foot}</table></div>'


# The same rows for scripts that build or reorder the table themselves.
JS_DATA = "const DATA = " + str([list(row) for row in DATA]).replace("'", '"') + ";\n"
JS_ROW = """\
const cell = (text, cls) => { const td = document.createElement("td"); if (cls) td.className = cls; td.textContent = text; return td; };
const rowOf = ([company, owner, status, revenue, renewal]) => {
  const tr = document.createElement("tr");
  const badge = Object.assign(document.createElement("span"), { className: `st ${status}`, textContent: status });
  const statusCell = document.createElement("td");
  statusCell.append(badge);
  tr.append(cell(company), cell(owner), statusCell, cell(`$${revenue.toLocaleString("en-US")}`, "num"), cell(renewal));
  return tr;
};
"""
LI = """\
.lv { width: min(460px, 100%); margin: 0; padding: 0; list-style: none; border: 1px solid var(--border); border-radius: 14px; background: var(--surface); overflow: hidden; }
.lv li { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-bottom: 1px solid var(--border); }
.lv li:last-child { border-bottom: 0; }
.lv li:hover { background: var(--surface-2); }
.lv .ic { flex: none; display: grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; background: var(--surface-2); font-weight: 700; font-size: 13px; }
.lv .gr { flex: 1; min-width: 0; }
.lv b { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lv small { color: var(--muted); }
"""

SECTION = Section(
    "patterns",
    "Tables & Data",
    301,
    (
        Item(
            "Data table",
            table(),
            T,
            note="A real table: caption, column headers with scope, numbers right-aligned in tabular figures.",
        ),
        Item(
            "Sortable table",
            '<div class="tw"><table><caption>Accounts</caption><thead><tr>'
            + "".join(
                f'<th scope="col" aria-sort="none"{' class="num"' if h == "Revenue" else ""}><button data-i="{i}">{h}</button></th>'
                for i, h in enumerate(HEAD)
            )
            + "</tr></thead><tbody></tbody></table></div>",
            T
            + 'thead button { all: unset; cursor: pointer; display: inline-flex; gap: 6px; align-items: center; }\nthead button::after { content: "↕"; opacity: .35; }\nth[aria-sort=ascending] button::after { content: "↑"; opacity: 1; color: var(--primary); }\nth[aria-sort=descending] button::after { content: "↓"; opacity: 1; color: var(--primary); }\nthead button:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 4px; }\n',
            JS_DATA
            + JS_ROW
            + 'const tbody = document.querySelector("tbody");\nconst headers = [...document.querySelectorAll("thead th")];\nlet sorted = { column: -1, direction: 1 };\nconst render = () => {\n  const rows = [...DATA];\n  if (sorted.column >= 0) rows.sort((a, b) => {\n    const x = a[sorted.column], y = b[sorted.column];\n    return (typeof x === "number" ? x - y : String(x).localeCompare(String(y))) * sorted.direction;\n  });\n  tbody.replaceChildren(...rows.map(rowOf));\n  headers.forEach((th, i) => th.setAttribute("aria-sort", i !== sorted.column ? "none" : sorted.direction === 1 ? "ascending" : "descending"));\n};\nheaders.forEach((th, i) => th.querySelector("button").addEventListener("click", () => {\n  sorted = { column: i, direction: sorted.column === i ? -sorted.direction : 1 };\n  render();\n}));\nrender();\n',
            "Header buttons cycle ascending and descending; aria-sort tells assistive tech which column and how.",
        ),
        Item(
            "Filterable table",
            '<div class="ft"><div class="fl" role="group" aria-label="Filter by status">'
            + "".join(
                f'<button aria-pressed="{"true" if s == "All" else "false"}" data-s="{s}">{s}</button>'
                for s in ["All", "Active", "Trial", "Churned"]
            )
            + '<span class="n" aria-live="polite"></span></div>'
            + table()
            + "</div>",
            T
            + '.ft { display: grid; gap: 10px; width: min(640px, 100%); }\n.fl { display: flex; gap: 6px; align-items: center; }\n.fl button { padding: 5px 12px; border: 1px solid var(--border); border-radius: 99px; background: var(--surface); color: var(--muted); font-size: 13px; }\n.fl button[aria-pressed="true"] { background: var(--fg); color: var(--bg); border-color: var(--fg); }\n.fl .n { margin-left: auto; color: var(--muted); font-size: 13px; }\n',
            'const buttons = [...document.querySelectorAll(".fl button")];\nconst rows = [...document.querySelectorAll("tbody tr")];\nconst count = document.querySelector(".fl .n");\nconst apply = (status) => {\n  let shown = 0;\n  rows.forEach((row) => { row.hidden = status !== "All" && row.dataset.status !== status; if (!row.hidden) shown += 1; });\n  buttons.forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.s === status)));\n  count.textContent = `${shown} of ${rows.length}`;\n};\nbuttons.forEach((button) => button.addEventListener("click", () => apply(button.dataset.s)));\napply("All");\n',
            "Filter pills above the table; the number of rows shown is always stated.",
        ),
        Item(
            "Searchable table",
            '<div class="ft"><input type="search" placeholder="Search accounts" aria-label="Search accounts">'
            + table()
            + '<p class="none" hidden>No accounts match.</p></div>',
            T
            + ".ft { display: grid; gap: 10px; width: min(640px, 100%); }\n.ft input { height: 40px; padding: 0 14px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); }\nmark { background: color-mix(in srgb, var(--warning) 45%, transparent); color: inherit; border-radius: 3px; }\n.none { margin: 0; text-align: center; color: var(--muted); }\n",
            'const rows = [...document.querySelectorAll("tbody tr")];\nconst cells = rows.map((row) => [...row.querySelectorAll("td")].filter((td) => !td.querySelector("span")).map((td) => [td, td.textContent]));\nconst none = document.querySelector(".none");\ndocument.querySelector(".ft input").addEventListener("input", (event) => {\n  const query = event.target.value.trim().toLowerCase();\n  let shown = 0;\n  rows.forEach((row, r) => {\n    row.hidden = query !== "" && !row.textContent.toLowerCase().includes(query);\n    if (!row.hidden) shown += 1;\n    for (const [td, text] of cells[r]) {\n      const at = query ? text.toLowerCase().indexOf(query) : -1;\n      if (at < 0) { td.textContent = text; continue; }\n      td.replaceChildren(text.slice(0, at), Object.assign(document.createElement("mark"), { textContent: text.slice(at, at + query.length) }), text.slice(at + query.length));\n    }\n  });\n  none.hidden = shown > 0;\n});\n',
            "Typing narrows the rows and highlights the matching text in each.",
        ),
        Item(
            "Expandable table rows",
            '<div class="tw"><table><caption>Accounts</caption>'
            + head('<th><span class="vh">Details</span></th>')
            + "<tbody>"
            + "".join(
                f'<tr><td><button class="ex" aria-expanded="false" aria-controls="d{i}" aria-label="Details for {c}">›</button></td><td>{c}</td><td>{o}</td><td><span class="st {s}">{s}</span></td><td class="num">{money(r)}</td><td>{d}</td></tr><tr class="detail" id="d{i}" hidden><td></td><td colspan="5">Plan: Team · 12 seats · Last invoice paid on {d}.</td></tr>'
                for i, (c, o, s, r, d) in enumerate(DATA[:4])
            )
            + "</tbody></table></div>",
            T
            + '.vh { position: absolute; clip-path: inset(50%); width: 1px; height: 1px; overflow: hidden; }\n.ex { width: 24px; height: 24px; border: 0; border-radius: 6px; background: var(--surface-2); transition: rotate .2s var(--ease); }\n.ex[aria-expanded="true"] { rotate: 90deg; }\n.detail td { background: var(--bg); color: var(--muted); white-space: normal; }\n.detail:hover { background: none; }\n',
            'document.querySelector("tbody").addEventListener("click", (event) => {\n  const button = event.target.closest(".ex");\n  if (!button) return;\n  const detail = document.getElementById(button.getAttribute("aria-controls"));\n  detail.hidden = !detail.hidden;\n  button.setAttribute("aria-expanded", String(!detail.hidden));\n});\n',
            "A disclosure button per row reveals a detail row beneath it.",
        ),
        Item(
            "Nested table",
            '<div class="tw"><table><caption>Orders by account</caption><thead><tr><th scope="col">Account</th><th scope="col" class="num">Orders</th><th scope="col" class="num">Total</th></tr></thead><tbody><tr><th scope="row">Northwind</th><td class="num">2</td><td class="num">$7,400</td></tr><tr class="sub"><td colspan="3"><table><thead><tr><th scope="col">Order</th><th scope="col">Date</th><th scope="col" class="num">Amount</th></tr></thead><tbody><tr><td>#2041</td><td>2026-05-02</td><td class="num">$4,900</td></tr><tr><td>#2017</td><td>2026-04-11</td><td class="num">$2,500</td></tr></tbody></table></td></tr><tr><th scope="row">Globex</th><td class="num">1</td><td class="num">$3,100</td></tr><tr class="sub"><td colspan="3"><table><thead><tr><th scope="col">Order</th><th scope="col">Date</th><th scope="col" class="num">Amount</th></tr></thead><tbody><tr><td>#2033</td><td>2026-04-19</td><td class="num">$3,100</td></tr></tbody></table></td></tr></tbody></table></div>',
            T
            + ".sub > td { padding: 0 0 0 28px; background: var(--bg); }\n.sub table { border-left: 2px solid var(--border); }\n.sub thead th { background: none; }\n.sub:hover { background: none; }\ntbody th { font-weight: 600; }\n",
            note="Child rows are a table of their own inside the parent row, with their own headers.",
        ),
        Item(
            "Tree table",
            '<div class="tw"><table role="treegrid" aria-label="Files"><thead><tr><th scope="col">Name</th><th scope="col" class="num">Size</th><th scope="col">Modified</th></tr></thead><tbody></tbody></table></div>',
            T
            + 'td .tg { display: inline-grid; place-items: center; width: 20px; height: 20px; margin-right: 4px; border: 0; background: none; color: var(--muted); transition: rotate .15s; }\ntr[aria-expanded="true"] .tg { rotate: 90deg; }\ntd .leaf { display: inline-block; width: 24px; }\n',
            'const TREE = [\n  { name: "src", size: "", date: "2026-05-12", children: [\n    { name: "components", size: "", date: "2026-05-12", children: [{ name: "Button.tsx", size: "2 KB", date: "2026-05-10" }, { name: "Card.tsx", size: "3 KB", date: "2026-05-12" }] },\n    { name: "index.ts", size: "1 KB", date: "2026-05-01" },\n  ] },\n  { name: "README.md", size: "4 KB", date: "2026-04-22" },\n];\nconst tbody = document.querySelector("tbody");\nconst open = new Set(["src"]);\nconst render = () => {\n  tbody.replaceChildren();\n  const walk = (nodes, level, path) => nodes.forEach((node) => {\n    const id = `${path}/${node.name}`.slice(1);\n    const row = document.createElement("tr");\n    row.setAttribute("aria-level", String(level));\n    const name = document.createElement("td");\n    name.style.paddingLeft = `${14 + (level - 1) * 20}px`;\n    if (node.children) {\n      row.setAttribute("aria-expanded", String(open.has(id)));\n      const toggle = Object.assign(document.createElement("button"), { className: "tg", textContent: "›" });\n      toggle.setAttribute("aria-label", `${open.has(id) ? "Collapse" : "Expand"} ${node.name}`);\n      toggle.addEventListener("click", () => { if (open.has(id)) open.delete(id); else open.add(id); render(); });\n      name.append(toggle);\n    } else name.append(Object.assign(document.createElement("span"), { className: "leaf" }));\n    name.append(node.name);\n    const size = Object.assign(document.createElement("td"), { className: "num", textContent: node.size });\n    row.append(name, size, Object.assign(document.createElement("td"), { textContent: node.date }));\n    tbody.append(row);\n    if (node.children && open.has(id)) walk(node.children, level + 1, `/${id}`);\n  });\n  walk(TREE, 1, "");\n};\nrender();\n',
            "A hierarchy in the first column with expand and collapse; rows carry their level.",
        ),
        Item(
            "Sticky-column table",
            '<div class="tw sc"><table><caption>Monthly revenue</caption><thead><tr><th scope="col">Account</th>'
            + "".join(
                f'<th scope="col" class="num">{m}</th>'
                for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
            )
            + "</tr></thead><tbody>"
            + "".join(
                f'<tr><th scope="row">{c}</th>'
                + "".join(
                    f'<td class="num">{money((r // 12 + 300 * ((i * 7 + j * 3) % 5)) if r else 0)}</td>'
                    for j in range(10)
                )
                + "</tr>"
                for i, (c, _, _, r, _) in enumerate(DATA)
            )
            + "</tbody></table></div>",
            T
            + ".sc { width: min(520px, 100%); }\n.sc th:first-child { position: sticky; left: 0; z-index: 1; background: var(--surface); box-shadow: 1px 0 0 var(--border); font-weight: 600; }\n.sc thead th:first-child { background: var(--surface-2); z-index: 2; }\n",
            note="The first column stays put while the rest scroll sideways under it.",
        ),
        Item(
            "Sticky-header table",
            '<div class="tw sh"><table><caption>Accounts</caption>'
            + head()
            + "<tbody>"
            + body() * 3
            + "</tbody></table></div>",
            T
            + ".sh { max-height: 260px; }\n.sh thead th { position: sticky; top: 0; z-index: 1; box-shadow: 0 1px 0 var(--border); }\n.sh caption { display: none; }\n",
            note="Column headers stay visible while the body scrolls inside a fixed height.",
        ),
        Item(
            "Virtualized table",
            '<div class="vt" tabindex="0" aria-label="10,000 rows"><div class="hd"><span>#</span><span>Event</span><span>User</span><span class="num">Latency</span></div><div class="vp"><div class="spacer"><div class="win"></div></div></div><p class="info" aria-live="off"></p></div>',
            ".vt { width: min(560px, 100%); border: 1px solid var(--border); border-radius: 14px; background: var(--surface); overflow: hidden; font-size: 14px; }\n.hd, .vt .r { display: grid; grid-template-columns: 70px 1fr 120px 90px; gap: 10px; padding: 0 14px; align-items: center; }\n.hd { height: 36px; background: var(--surface-2); color: var(--muted); font-size: 12px; font-weight: 600; }\n.vp { height: 260px; overflow: auto; }\n.spacer { position: relative; }\n.win { position: absolute; left: 0; right: 0; top: 0; }\n.vt .r { height: 34px; border-bottom: 1px solid var(--border); white-space: nowrap; }\n.num { text-align: right; font-variant-numeric: tabular-nums; }\n.info { margin: 0; padding: 8px 14px; border-top: 1px solid var(--border); color: var(--muted); font-size: 12px; }\n",
            'const TOTAL = 10000, ROW = 34, OVERSCAN = 6;\nconst viewport = document.querySelector(".vp");\nconst spacer = document.querySelector(".spacer");\nconst win = document.querySelector(".win");\nconst info = document.querySelector(".info");\nconst EVENTS = ["page_view", "checkout", "sign_up", "search", "export"];\nspacer.style.height = `${TOTAL * ROW}px`;  // the scrollbar is as long as all the rows\nconst render = () => {\n  const first = Math.max(0, Math.floor(viewport.scrollTop / ROW) - OVERSCAN);\n  const last = Math.min(TOTAL, Math.ceil((viewport.scrollTop + viewport.clientHeight) / ROW) + OVERSCAN);\n  win.style.transform = `translateY(${first * ROW}px)`;\n  // Only the rows near the viewport exist in the document.\n  win.replaceChildren(...Array.from({ length: last - first }, (_, k) => {\n    const i = first + k;\n    const row = Object.assign(document.createElement("div"), { className: "r" });\n    for (const [text, cls] of [[i + 1, ""], [EVENTS[i % EVENTS.length], ""], [`user_${(i * 7919) % 1000}`, ""], [`${40 + (i * 37) % 400} ms`, "num"]])\n      row.append(Object.assign(document.createElement("span"), { textContent: text, className: cls }));\n    return row;\n  }));\n  info.textContent = `Rows ${first + 1}–${last} of ${TOTAL.toLocaleString()} rendered`;\n};\nlet queued = false;\nviewport.addEventListener("scroll", () => { if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; render(); }); } }, { passive: true });\nrender();\n',
            "Ten thousand rows, a few dozen in the document: only the window near the viewport is rendered.",
        ),
        Item(
            "Editable table",
            '<div class="tw"><table><caption>Team</caption><thead><tr><th scope="col">Name</th><th scope="col">Role</th><th scope="col" class="num">Seats</th></tr></thead><tbody>'
            + "".join(
                f'<tr><td><input value="{n}" aria-label="Name"></td><td><select aria-label="Role">'
                + "".join(
                    f"<option{' selected' if x == r else ''}>{x}</option>"
                    for x in ["Admin", "Editor", "Viewer"]
                )
                + f'</select></td><td class="num"><input type="number" min="1" max="99" value="{s}" aria-label="Seats"></td></tr>'
                for n, r, s in [
                    ("Dana Whitfield", "Admin", 4),
                    ("Mika Tanaka", "Editor", 2),
                    ("Ravi Shah", "Viewer", 1),
                ]
            )
            + '</tbody><tfoot><tr><td colspan="3"><button class="add">+ Add row</button><span class="dirty" hidden>Unsaved changes</span></td></tr></tfoot></table></div>',
            T
            + "td input, td select { width: 100%; height: 32px; padding: 0 8px; border: 1px solid transparent; border-radius: 7px; background: none; }\ntd input:hover, td select:hover { border-color: var(--border); }\ntd input:focus, td select:focus { outline: none; border-color: var(--primary); background: var(--bg); }\ntd.num input { text-align: right; }\ntd { padding: 4px 6px; }\ntfoot td { padding: 8px 14px; }\n.add { border: 0; background: none; color: var(--primary); font-weight: 600; }\n.dirty { float: right; color: var(--warning); font-size: 13px; }\n",
            'const tbody = document.querySelector("tbody");\nconst dirty = document.querySelector(".dirty");\ntbody.addEventListener("input", () => { dirty.hidden = false; });\ndocument.querySelector(".add").addEventListener("click", () => {\n  const row = tbody.rows[0].cloneNode(true);\n  row.querySelectorAll("input").forEach((input) => { input.value = input.type === "number" ? "1" : ""; });\n  tbody.append(row);\n  row.querySelector("input").focus();\n  dirty.hidden = false;\n});\n// Enter moves down the column, like a spreadsheet.\ntbody.addEventListener("keydown", (event) => {\n  if (event.key !== "Enter" || event.target.tagName !== "INPUT") return;\n  const cell = event.target.closest("td");\n  cell.parentElement.nextElementSibling?.cells[cell.cellIndex].querySelector("input, select")?.focus();\n});\n',
            "Every cell is a quiet input that only looks like one when hovered or focused.",
        ),
        Item(
            "Inline editing",
            '<dl class="ie"><div><dt>Name</dt><dd><span class="val" tabindex="0" role="button" aria-label="Edit name">Northwind Trading</span></dd></div><div><dt>Owner</dt><dd><span class="val" tabindex="0" role="button" aria-label="Edit owner">Dana Whitfield</span></dd></div></dl>',
            '.ie { display: grid; gap: 4px; width: min(380px, 100%); margin: 0; }\n.ie div { display: grid; grid-template-columns: 90px 1fr; align-items: center; min-height: 40px; }\n.ie dt { color: var(--muted); font-size: 13px; }\n.ie dd { margin: 0; }\n.val { display: inline-block; padding: 6px 8px; margin-left: -8px; border-radius: 8px; cursor: text; }\n.val:hover, .val:focus-visible { background: var(--surface-2); outline: none; }\n.val::after { content: " ✎"; color: var(--muted); opacity: 0; }\n.val:hover::after, .val:focus-visible::after { opacity: 1; }\n.ie input { width: 100%; height: 34px; padding: 0 8px; margin-left: -8px; border: 1px solid var(--primary); border-radius: 8px; background: var(--bg); outline: none; }\n',
            'const edit = (value) => {\n  const input = Object.assign(document.createElement("input"), { value: value.textContent });\n  input.setAttribute("aria-label", value.getAttribute("aria-label"));\n  let done = false;\n  const finish = (save) => {\n    if (done) return;\n    done = true;\n    if (save && input.value.trim()) value.textContent = input.value.trim();  // an empty value is not accepted\n    input.replaceWith(value);\n    value.focus();\n  };\n  input.addEventListener("keydown", (event) => { if (event.key === "Enter") finish(true); if (event.key === "Escape") finish(false); });\n  input.addEventListener("blur", () => finish(true));\n  value.replaceWith(input);\n  input.select();\n};\ndocument.querySelectorAll(".val").forEach((value) => {\n  value.addEventListener("click", () => edit(value));\n  value.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); edit(value); } });\n});\n',
            "Text becomes a field on click; Enter or leaving saves, Escape puts the old value back.",
        ),
        Item(
            "Bulk selection table",
            table(
                first_h='<th><input type="checkbox" class="all" aria-label="Select all rows"></th>',
                first='<td><input type="checkbox" aria-label="Select row"></td>',
                foot='<tfoot><tr><td colspan="6" class="sel" aria-live="polite"></td></tr></tfoot>',
            ),
            T
            + "input[type=checkbox] { width: 16px; height: 16px; accent-color: var(--primary); }\ntr.on { background: color-mix(in srgb, var(--primary) 12%, transparent); }\n.sel { color: var(--muted); font-size: 13px; }\n",
            'const all = document.querySelector(".all");\nconst boxes = [...document.querySelectorAll("tbody input")];\nconst summary = document.querySelector(".sel");\nlet last = null;\nconst update = () => {\n  const count = boxes.filter((box) => box.checked).length;\n  boxes.forEach((box) => box.closest("tr").classList.toggle("on", box.checked));\n  all.checked = count === boxes.length;\n  all.indeterminate = count > 0 && count < boxes.length;  // some, not all\n  summary.textContent = count ? `${count} of ${boxes.length} selected` : "Nothing selected";\n};\nall.addEventListener("change", () => { boxes.forEach((box) => { box.checked = all.checked; }); update(); });\nboxes.forEach((box, index) => box.addEventListener("click", (event) => {\n  // Shift-click selects everything between this row and the last one clicked.\n  if (event.shiftKey && last !== null) for (let i = Math.min(index, last); i <= Math.max(index, last); i += 1) boxes[i].checked = box.checked;\n  last = index;\n  update();\n}));\nupdate();\n',
            "Row checkboxes, a header checkbox with an indeterminate state, and shift-click ranges.",
        ),
        Item(
            "Row actions",
            table(
                last_h='<th><span class="vh">Actions</span></th>',
                last='<td class="ra"><button aria-label="Edit">✎</button><button aria-label="More actions" aria-haspopup="menu">⋯</button></td>',
            ),
            T
            + ".vh { position: absolute; clip-path: inset(50%); width: 1px; height: 1px; overflow: hidden; }\n.ra { text-align: right; }\n.ra button { width: 28px; height: 28px; border: 0; border-radius: 7px; background: none; color: var(--muted); opacity: 0; transition: opacity .12s; }\ntr:hover .ra button, .ra button:focus-visible { opacity: 1; }\n.ra button:hover { background: var(--surface-2); color: var(--fg); }\n@media (hover: none) { .ra button { opacity: 1; } }\n",
            note="Actions in a trailing column appear on row hover and on focus, and are always visible on touch screens.",
        ),
        Item(
            "Column selector",
            '<div class="ft"><details class="cols"><summary>Columns</summary><div>'
            + "".join(
                f'<label><input type="checkbox" value="{i}" checked{" disabled" if i == 0 else ""}> {h}</label>'
                for i, h in enumerate(HEAD)
            )
            + "</div></details>"
            + table()
            + "</div>",
            T
            + ".ft { display: grid; gap: 10px; width: min(640px, 100%); }\n.cols { position: relative; justify-self: end; }\n.cols summary { padding: 6px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); cursor: pointer; list-style: none; }\n.cols div { position: absolute; right: 0; top: calc(100% + 6px); z-index: 3; display: grid; gap: 6px; padding: 12px; min-width: 160px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); box-shadow: var(--shadow); }\n",
            'const table = document.querySelector("table");\ndocument.querySelectorAll(".cols input").forEach((box) => box.addEventListener("change", () => {\n  const index = Number(box.value);\n  for (const row of table.rows) if (row.cells[index]) row.cells[index].hidden = !box.checked;\n}));\n',
            "A checklist that shows and hides columns; the identifying column cannot be hidden.",
        ),
        Item(
            "Column resizing",
            table(),
            T
            + 'thead th { position: relative; }\n.grip { position: absolute; top: 0; right: -4px; width: 8px; height: 100%; cursor: col-resize; z-index: 1; }\n.grip::after { content: ""; position: absolute; left: 3px; top: 25%; height: 50%; width: 2px; border-radius: 2px; background: var(--border); }\n.grip:hover::after, .grip.on::after { background: var(--primary); }\ntable { table-layout: fixed; }\ntd, th { overflow: hidden; text-overflow: ellipsis; }\n',
            'const MIN = 70;\ndocument.querySelectorAll("thead th").forEach((th) => {\n  th.style.width = `${th.offsetWidth}px`;  // fix the starting widths so one column can change alone\n  const grip = Object.assign(document.createElement("span"), { className: "grip" });\n  grip.setAttribute("role", "separator");\n  grip.setAttribute("aria-orientation", "vertical");\n  grip.setAttribute("aria-label", `Resize ${th.textContent}`);\n  grip.tabIndex = 0;\n  const resize = (width) => { th.style.width = `${Math.max(MIN, width)}px`; };\n  grip.addEventListener("pointerdown", (event) => {\n    const startX = event.clientX, startWidth = th.offsetWidth;\n    grip.setPointerCapture(event.pointerId);\n    grip.classList.add("on");\n    const move = (e) => resize(startWidth + e.clientX - startX);\n    const up = () => { grip.classList.remove("on"); grip.removeEventListener("pointermove", move); };\n    grip.addEventListener("pointermove", move);\n    grip.addEventListener("pointerup", up, { once: true });\n  });\n  grip.addEventListener("keydown", (event) => { if (event.key === "ArrowLeft") resize(th.offsetWidth - 10); if (event.key === "ArrowRight") resize(th.offsetWidth + 10); });\n  th.append(grip);\n});\n',
            "A grip on each header edge: drag, or focus it and use the arrow keys.",
        ),
        Item(
            "Column reordering",
            table(),
            T
            + "thead th { cursor: grab; user-select: none; }\nthead th.drag { opacity: .4; }\nthead th.over { box-shadow: inset 3px 0 0 var(--primary); }\n",
            'const table = document.querySelector("table");\nconst headRow = table.tHead.rows[0];\nlet from = -1;\n[...headRow.cells].forEach((th) => { th.draggable = true; });\nheadRow.addEventListener("dragstart", (event) => { from = event.target.closest("th").cellIndex; event.target.closest("th").classList.add("drag"); event.dataTransfer.effectAllowed = "move"; });\nheadRow.addEventListener("dragover", (event) => {\n  event.preventDefault();\n  const over = event.target.closest("th");\n  [...headRow.cells].forEach((th) => th.classList.toggle("over", th === over));\n});\nconst clear = () => [...headRow.cells].forEach((th) => th.classList.remove("over", "drag"));\nheadRow.addEventListener("dragend", clear);\nheadRow.addEventListener("drop", (event) => {\n  event.preventDefault();\n  const to = event.target.closest("th")?.cellIndex ?? -1;\n  clear();\n  if (to < 0 || to === from) return;\n  // Move the same cell in every row so headers and data stay aligned.\n  for (const row of table.rows) {\n    if (row.cells.length <= Math.max(from, to)) continue;\n    row.insertBefore(row.cells[from], to > from ? row.cells[to].nextSibling : row.cells[to]);\n  }\n});\n',
            "Drag a header onto another to move its whole column.",
        ),
        Item(
            "Table density control",
            '<div class="ft"><div class="dn" role="radiogroup" aria-label="Density">'
            + "".join(
                f'<label><input type="radio" name="d" value="{v}"{" checked" if v == "normal" else ""}><span>{t}</span></label>'
                for v, t in [("compact", "Compact"), ("normal", "Normal"), ("relaxed", "Relaxed")]
            )
            + "</div>"
            + table()
            + "</div>",
            T
            + ".ft { display: grid; gap: 10px; width: min(640px, 100%); }\n.dn { display: inline-flex; justify-self: end; padding: 3px; border-radius: 10px; background: var(--surface-2); }\n.dn input { position: absolute; opacity: 0; }\n.dn span { display: block; padding: 4px 12px; border-radius: 7px; font-size: 13px; color: var(--muted); cursor: pointer; }\n.dn input:checked + span { background: var(--surface); color: var(--fg); }\n.dn input:focus-visible + span { outline: 2px solid var(--accent); }\n.tw { --pad: 10px; }\n.tw th, .tw td { padding-block: var(--pad); transition: padding .2s var(--ease); }\n.tw[data-density=compact] { --pad: 4px; font-size: 13px; }\n.tw[data-density=relaxed] { --pad: 16px; }\n",
            'const wrap = document.querySelector(".tw");\ndocument.querySelectorAll(".dn input").forEach((input) => input.addEventListener("change", () => { wrap.dataset.density = input.value; }));\n',
            "Three row heights from one custom property.",
        ),
        Item(
            "Table pagination",
            '<div class="ft"><div class="tw"><table><caption>Events</caption><thead><tr><th scope="col">#</th><th scope="col">Event</th><th scope="col" class="num">Latency</th></tr></thead><tbody></tbody></table></div><div class="pg"><label>Rows per page <select><option>5</option><option>10</option><option>20</option></select></label><span class="range" aria-live="polite"></span><button aria-label="Previous page">‹</button><button aria-label="Next page">›</button></div></div>',
            T
            + ".ft { display: grid; gap: 10px; width: min(520px, 100%); }\n.pg { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--muted); }\n.pg select { height: 28px; border: 1px solid var(--border); border-radius: 7px; background: var(--surface); }\n.range { margin-left: auto; font-variant-numeric: tabular-nums; }\n.pg button { width: 30px; height: 30px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); }\n.pg button:disabled { opacity: .35; }\n",
            'const ROWS = Array.from({ length: 47 }, (_, i) => [i + 1, ["page_view", "checkout", "sign_up", "search"][i % 4], `${40 + (i * 37) % 400} ms`]);\nconst tbody = document.querySelector("tbody");\nconst size = document.querySelector(".pg select");\nconst range = document.querySelector(".range");\nconst [previous, next] = document.querySelectorAll(".pg button");\nlet page = 0;\nconst render = () => {\n  const per = Number(size.value), pages = Math.ceil(ROWS.length / per);\n  page = Math.min(page, pages - 1);\n  const slice = ROWS.slice(page * per, (page + 1) * per);\n  tbody.replaceChildren(...slice.map((cells) => { const tr = document.createElement("tr"); cells.forEach((text, i) => { const td = document.createElement("td"); td.textContent = text; if (i === 2) td.className = "num"; tr.append(td); }); return tr; }));\n  range.textContent = `${page * per + 1}–${page * per + slice.length} of ${ROWS.length}`;\n  previous.disabled = page === 0;\n  next.disabled = page >= pages - 1;\n};\nprevious.addEventListener("click", () => { page -= 1; render(); });\nnext.addEventListener("click", () => { page += 1; render(); });\nsize.addEventListener("change", () => { page = 0; render(); });\nrender();\n',
            "Rows per page, the range shown out of the total, previous and next.",
        ),
        Item(
            "Table footer summary",
            table(
                foot=f'<tfoot><tr><th scope="row" colspan="3">Total ({len(DATA)} accounts)</th><td class="num">{money(sum(r for _, _, _, r, _ in DATA))}</td><td></td></tr><tr><th scope="row" colspan="3">Average</th><td class="num">{money(sum(r for _, _, _, r, _ in DATA) // len(DATA))}</td><td></td></tr></tfoot>'
            ),
            T
            + "tfoot th, tfoot td { border-top: 2px solid var(--border); border-bottom: 0; background: var(--surface-2); font-weight: 700; }\ntfoot tr + tr th, tfoot tr + tr td { border-top: 1px solid var(--border); font-weight: 500; color: var(--muted); }\n",
            note="Totals and averages in a real <tfoot>, aligned under the column they summarise.",
        ),
        Item(
            "Data grid",
            '<div class="dg" role="grid" aria-label="Accounts" aria-rowcount="7" aria-colcount="5"></div><p class="where" aria-live="polite"></p>',
            ".dg { display: grid; grid-template-columns: 1.2fr 1.2fr .8fr .8fr 1fr; width: min(620px, 100%); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: var(--surface); font-size: 14px; }\n.dg > div { padding: 9px 12px; border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; outline: none; }\n.dg > div:nth-child(5n) { border-right: 0; }\n.dg .h { background: var(--surface-2); color: var(--muted); font-size: 12px; font-weight: 600; }\n.dg > div:focus { box-shadow: inset 0 0 0 2px var(--primary); background: color-mix(in srgb, var(--primary) 10%, transparent); }\n.where { margin: 8px 0 0; color: var(--muted); font-size: 13px; }\nbody { align-content: center; justify-items: center; }\n",
            JS_DATA
            + 'const HEAD = ["Company", "Owner", "Status", "Revenue", "Renewal"];\nconst grid = document.querySelector(".dg");\nconst where = document.querySelector(".where");\nconst COLS = HEAD.length;\nconst cells = [];\n[HEAD, ...DATA].forEach((row, r) => row.forEach((value, c) => {\n  const cell = document.createElement("div");\n  cell.textContent = typeof value === "number" ? `$${value.toLocaleString("en-US")}` : value;\n  cell.setAttribute("role", r === 0 ? "columnheader" : "gridcell");\n  cell.tabIndex = r === 1 && c === 0 ? 0 : -1;  // one tab stop for the whole grid\n  if (r === 0) cell.className = "h";\n  grid.append(cell);\n  cells.push(cell);\n}));\nconst focus = (index) => {\n  if (index < COLS || index >= cells.length) return;\n  cells.forEach((cell) => { if (cell.tabIndex === 0) cell.tabIndex = -1; });\n  cells[index].tabIndex = 0;\n  cells[index].focus();\n  where.textContent = `${HEAD[index % COLS]}, row ${Math.floor(index / COLS)}`;\n};\ngrid.addEventListener("keydown", (event) => {\n  const index = cells.indexOf(document.activeElement);\n  const column = index % COLS;\n  const move = { ArrowRight: column < COLS - 1 ? 1 : 0, ArrowLeft: column > 0 ? -1 : 0, ArrowDown: COLS, ArrowUp: -COLS, Home: -column, End: COLS - 1 - column }[event.key];\n  if (move === undefined) return;\n  event.preventDefault();\n  focus(index + move);\n});\ngrid.addEventListener("click", (event) => { const index = cells.indexOf(event.target); if (index >= COLS) focus(index); });\n',
            "A grid with one tab stop and arrow-key movement between cells (the ARIA grid pattern).",
        ),
        Item(
            "Spreadsheet grid",
            '<div class="ss"><div class="fx"><span class="ref">A1</span><input aria-label="Cell value"></div><div class="sheet" role="grid"></div></div>',
            ".ss { width: min(520px, 100%); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; background: var(--surface); font: 13px var(--mono); }\n.fx { display: flex; border-bottom: 1px solid var(--border); }\n.ref { width: 52px; padding: 8px; text-align: center; background: var(--surface-2); color: var(--muted); border-right: 1px solid var(--border); }\n.fx input { flex: 1; padding: 0 10px; border: 0; outline: 0; background: none; font: inherit; }\n.sheet { display: grid; grid-template-columns: 36px repeat(4, 1fr); }\n.sheet > div { height: 30px; padding: 6px 8px; border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); overflow: hidden; white-space: nowrap; text-align: right; }\n.sheet .hd { background: var(--surface-2); color: var(--muted); text-align: center; }\n.sheet .on { box-shadow: inset 0 0 0 2px var(--primary); }\n.sheet .err { color: var(--danger); }\n",
            'const COLS = ["A", "B", "C", "D"], ROWS = 5;\nconst raw = { A1: "120", B1: "80", C1: "=A1+B1", A2: "45", B2: "15", C2: "=A2+B2", C3: "=SUM(C1:C2)" };\nconst sheet = document.querySelector(".sheet");\nconst input = document.querySelector(".fx input");\nconst ref = document.querySelector(".ref");\nlet active = "A1";\n// Values: numbers, +,-,*,/ over cell references, and SUM over a range. No eval.\nconst valueOf = (id, seen = new Set()) => {\n  const text = (raw[id] ?? "").trim();\n  if (!text.startsWith("=")) return text === "" ? 0 : Number(text);\n  if (seen.has(id)) return NaN;  // a cell that depends on itself\n  seen.add(id);\n  const formula = text.slice(1).toUpperCase();\n  const sum = formula.match(/^SUM\\(([A-D])(\\d):([A-D])(\\d)\\)$/);\n  if (sum) {\n    let total = 0;\n    for (let c = COLS.indexOf(sum[1]); c <= COLS.indexOf(sum[3]); c += 1) for (let r = Number(sum[2]); r <= Number(sum[4]); r += 1) total += valueOf(`${COLS[c]}${r}`, new Set(seen));\n    return total;\n  }\n  const tokens = formula.match(/[A-D]\\d|\\d+(?:\\.\\d+)?|[+\\-*/]/g);\n  if (!tokens || tokens.join("") !== formula.replace(/\\s/g, "")) return NaN;\n  let result = NaN, operator = "+";\n  tokens.forEach((token, i) => {\n    if (i % 2 === 1) { operator = token; return; }\n    const value = /^[A-D]/.test(token) ? valueOf(token, new Set(seen)) : Number(token);\n    result = i === 0 ? value : operator === "+" ? result + value : operator === "-" ? result - value : operator === "*" ? result * value : result / value;\n  });\n  return result;\n};\nconst render = () => {\n  sheet.replaceChildren();\n  sheet.append(Object.assign(document.createElement("div"), { className: "hd" }), ...COLS.map((c) => Object.assign(document.createElement("div"), { className: "hd", textContent: c })));\n  for (let r = 1; r <= ROWS; r += 1) {\n    sheet.append(Object.assign(document.createElement("div"), { className: "hd", textContent: String(r) }));\n    for (const c of COLS) {\n      const id = `${c}${r}`;\n      const value = raw[id] === undefined || raw[id] === "" ? "" : valueOf(id);\n      const cell = Object.assign(document.createElement("div"), { textContent: Number.isNaN(value) ? "#ERR" : String(value) });\n      cell.dataset.id = id;\n      cell.className = `${id === active ? "on" : ""} ${Number.isNaN(value) ? "err" : ""}`;\n      sheet.append(cell);\n    }\n  }\n  ref.textContent = active;\n  input.value = raw[active] ?? "";\n};\nsheet.addEventListener("click", (event) => { const id = event.target.dataset.id; if (id) { active = id; render(); input.focus(); } });\ninput.addEventListener("input", () => { raw[active] = input.value; });\ninput.addEventListener("keydown", (event) => {\n  if (event.key !== "Enter") return;\n  const row = Math.min(ROWS, Number(active.slice(1)) + 1);\n  active = `${active[0]}${row}`;  // Enter commits and moves down\n  render();\n});\ninput.addEventListener("blur", render);\nrender();\n',
            "Cells, a formula bar, cell references, + − × ÷ and SUM, with circular references reported, all without eval.",
        ),
        Item(
            "Kanban board",
            '<div class="kb">'
            + "".join(
                f'<section data-col="{k}"><header>{t} <span></span></header><ul>'
                + "".join(f'<li draggable="true" tabindex="0">{c}</li>' for c in cards)
                + "</ul></section>"
                for k, t, cards in [
                    ("todo", "To do", ["Write launch post", "Update pricing page"]),
                    ("doing", "In progress", ["Fix checkout bug"]),
                    ("done", "Done", ["Design review", "Set up analytics"]),
                ]
            )
            + '</div><p class="say" role="status"></p>',
            ".kb { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; width: min(640px, 100%); }\n.kb section { padding: 10px; border-radius: 14px; background: var(--surface); border: 1px solid var(--border); min-height: 220px; }\n.kb section.over { border-color: var(--primary); background: color-mix(in srgb, var(--primary) 8%, var(--surface)); }\n.kb header { display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 13px; font-weight: 600; color: var(--muted); }\n.kb ul { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; min-height: 40px; }\n.kb li { padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface-2); cursor: grab; font-size: 14px; }\n.kb li.drag { opacity: .4; }\n.kb li:focus-visible { outline: 2px solid var(--accent); }\n.say { position: fixed; bottom: 14px; margin: 0; font-size: 13px; color: var(--muted); }\n",
            'const board = document.querySelector(".kb");\nconst columns = [...board.querySelectorAll("section")];\nconst say = document.querySelector(".say");\nlet card = null;\nconst count = () => columns.forEach((column) => { column.querySelector("header span").textContent = String(column.querySelectorAll("li").length); });\nboard.addEventListener("dragstart", (event) => { card = event.target.closest("li"); card.classList.add("drag"); event.dataTransfer.effectAllowed = "move"; });\nboard.addEventListener("dragend", () => { card?.classList.remove("drag"); columns.forEach((column) => column.classList.remove("over")); card = null; });\ncolumns.forEach((column) => {\n  column.addEventListener("dragover", (event) => { event.preventDefault(); columns.forEach((item) => item.classList.toggle("over", item === column)); });\n  column.addEventListener("drop", (event) => {\n    event.preventDefault();\n    if (!card) return;\n    // Drop before the card under the pointer, or at the end of the column.\n    const before = [...column.querySelectorAll("li:not(.drag)")].find((item) => event.clientY < item.getBoundingClientRect().top + item.offsetHeight / 2);\n    column.querySelector("ul").insertBefore(card, before ?? null);\n    count();\n  });\n});\n// Keyboard: arrow left/right moves the focused card to the neighbouring column.\nboard.addEventListener("keydown", (event) => {\n  const item = event.target.closest("li");\n  const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;\n  if (!item || !step) return;\n  const target = columns[columns.indexOf(item.closest("section")) + step];\n  if (!target) return;\n  target.querySelector("ul").append(item);\n  item.focus();\n  count();\n  say.textContent = `Moved to ${target.querySelector("header").firstChild.textContent.trim()}.`;\n});\ncount();\n',
            "Cards dragged between columns, with arrow keys as the keyboard path and live column counts.",
        ),
        Item(
            "List view",
            '<ul class="lv">'
            + "".join(
                f'<li><span class="ic">{c[0]}</span><div class="gr"><b>{c}</b><small>{o}</small></div><span class="st {s}">{s}</span></li>'
                for c, o, s, _, _ in DATA[:5]
            )
            + "</ul>",
            LI
            + ".st { padding: 1px 9px; border-radius: 99px; font-size: 12px; font-weight: 600; --c: var(--muted); background: color-mix(in srgb, var(--c) 20%, transparent); color: var(--c); }\n.st.Active { --c: var(--success); }\n.st.Trial { --c: var(--warning); }\n.st.Churned { --c: var(--danger); }\n",
            note="One line of identity, one of detail, one trailing fact: the default row.",
        ),
        Item(
            "Compact list",
            '<ul class="lv cp">'
            + "".join(
                f"<li><b>{c}</b><small>{o}</small><span>{money(r)}</span></li>"
                for c, o, _, r, _ in DATA
            )
            + "</ul>",
            LI
            + ".cp li { padding: 6px 12px; gap: 10px; font-size: 13px; }\n.cp b { flex: none; width: 110px; }\n.cp small { flex: 1; }\n.cp span { font-variant-numeric: tabular-nums; }\n",
            note="Single-line rows for scanning many items; nothing wraps.",
        ),
        Item(
            "Detailed list",
            '<ul class="lv dt">'
            + "".join(
                f'<li><span class="ic">{c[0]}</span><div class="gr"><b>{c}</b><small>Owned by {o} · renews {d}</small><p>Team plan with 12 seats. Last contacted two weeks ago about the annual upgrade.</p><div class="tg"><span>Enterprise</span><span>EMEA</span></div></div><strong>{money(r)}</strong></li>'
                for c, o, _, r, d in DATA[:3]
            )
            + "</ul>",
            LI
            + ".dt li { align-items: flex-start; padding: 14px; }\n.dt p { margin: 6px 0 8px; color: var(--muted); font-size: 14px; }\n.tg { display: flex; gap: 6px; }\n.tg span { padding: 1px 8px; border-radius: 6px; background: var(--surface-2); font-size: 12px; color: var(--muted); }\n.dt strong { font-variant-numeric: tabular-nums; }\n",
            note="Rows that carry a paragraph and tags: fewer per screen, less clicking through.",
        ),
        Item(
            "Timeline list",
            '<ol class="tml">'
            + "".join(
                f"<li><time>{t}</time><div><b>{h}</b><p>{p}</p></div></li>"
                for t, h, p in [
                    ("09:14", "Order placed", "3 items · $128.00"),
                    ("09:15", "Payment authorised", "Visa ending 4242"),
                    ("11:40", "Packed", "Warehouse Bristol"),
                    ("15:02", "Handed to courier", "Tracking NW-88412"),
                ]
            )
            + "</ol>",
            '.tml { width: min(420px, 100%); margin: 0; padding: 0; list-style: none; }\n.tml li { display: grid; grid-template-columns: 54px 1fr; gap: 0 18px; position: relative; padding-bottom: 20px; }\n.tml li:last-child { padding-bottom: 0; }\n.tml time { font: 12px var(--mono); color: var(--muted); padding-top: 2px; text-align: right; }\n.tml div { position: relative; padding-left: 18px; border-left: 2px solid var(--border); margin-left: -9px; }\n.tml li:last-child div { border-color: transparent; }\n.tml div::before { content: ""; position: absolute; left: -7px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--primary); box-shadow: 0 0 0 3px var(--bg); }\n.tml p { margin: 2px 0 0; color: var(--muted); font-size: 14px; }\n',
            note="Times in a left gutter, a rail, and events hanging from it in order.",
        ),
        Item(
            "Activity list",
            '<ul class="lv al">'
            + "".join(
                f'<li><span class="ic">{i}</span><div class="gr"><p><b>{n}</b> {a} <b>{o}</b></p><small>{t}</small></div></li>'
                for i, n, a, o, t in [
                    ("DW", "Dana", "approved", "Invoice #2041", "2 minutes ago"),
                    ("MT", "Mika", "commented on", "Pricing page", "14 minutes ago"),
                    ("RS", "Ravi", "uploaded", "q3-forecast.xlsx", "1 hour ago"),
                    ("SO", "Sam", "invited", "3 people", "Yesterday"),
                ]
            )
            + "</ul>",
            LI
            + ".al .ic { border-radius: 50%; }\n.al p { margin: 0; }\n.al p b { display: inline; }\n",
            note="Sentences, not columns: actor, verb, object, then when.",
        ),
        Item(
            "Master-detail list",
            '<div class="md"><ul role="listbox" aria-label="Accounts">'
            + "".join(
                f'<li role="option" tabindex="{0 if i == 0 else -1}" aria-selected="{"true" if i == 0 else "false"}" data-o="{o}" data-r="{money(r)}" data-d="{d}" data-s="{s}"><b>{c}</b><small>{s}</small></li>'
                for i, (c, o, s, r, d) in enumerate(DATA[:5])
            )
            + '</ul><article aria-live="polite"><h3></h3><dl><div><dt>Owner</dt><dd class="o"></dd></div><div><dt>Revenue</dt><dd class="r"></dd></div><div><dt>Renewal</dt><dd class="d"></dd></div></dl></article></div>',
            '.md { display: grid; grid-template-columns: 200px 1fr; width: min(580px, 100%); height: 280px; border: 1px solid var(--border); border-radius: 14px; overflow: hidden; background: var(--surface); }\n.md ul { margin: 0; padding: 6px; list-style: none; border-right: 1px solid var(--border); overflow: auto; }\n.md li { padding: 9px 10px; border-radius: 9px; cursor: pointer; outline: none; }\n.md li small { display: block; color: var(--muted); }\n.md li:hover { background: var(--surface-2); }\n.md li[aria-selected="true"] { background: color-mix(in srgb, var(--primary) 20%, transparent); }\n.md li:focus-visible { box-shadow: inset 0 0 0 2px var(--accent); }\n.md article { padding: 20px; }\n.md h3 { margin: 0 0 16px; font-size: 22px; }\n.md dl { display: grid; gap: 12px; margin: 0; }\n.md dt { font-size: 12px; color: var(--muted); }\n.md dd { margin: 0; font-weight: 600; }\n@media (max-width: 480px) { .md { grid-template-columns: 1fr; height: auto; } .md ul { border-right: 0; border-bottom: 1px solid var(--border); } }\n',
            'const options = [...document.querySelectorAll(".md li")];\nconst detail = document.querySelector(".md article");\nconst select = (option) => {\n  options.forEach((item) => { item.setAttribute("aria-selected", String(item === option)); item.tabIndex = item === option ? 0 : -1; });\n  detail.querySelector("h3").textContent = option.querySelector("b").textContent;\n  detail.querySelector(".o").textContent = option.dataset.o;\n  detail.querySelector(".r").textContent = option.dataset.r;\n  detail.querySelector(".d").textContent = option.dataset.d;\n};\noptions.forEach((option, index) => {\n  option.addEventListener("click", () => select(option));\n  option.addEventListener("keydown", (event) => {\n    const step = event.key === "ArrowDown" ? 1 : event.key === "ArrowUp" ? -1 : 0;\n    if (!step) return;\n    event.preventDefault();\n    const next = options[Math.min(options.length - 1, Math.max(0, index + step))];\n    select(next);\n    next.focus();\n  });\n});\nselect(options[0]);\n',
            "Choosing a row fills the pane beside it; arrow keys move the selection.",
        ),
        Item(
            "Comparison matrix",
            '<div class="tw"><table class="cm"><caption>Plans</caption><thead><tr><th></th><th scope="col">Free</th><th scope="col" class="best">Team</th><th scope="col">Enterprise</th></tr></thead><tbody>'
            + "".join(
                f'<tr><th scope="row">{f}</th>'
                + "".join(
                    f"<td{' class="best"' if i == 1 else ''}>{v}</td>" for i, v in enumerate(vals)
                )
                + "</tr>"
                for f, vals in [
                    ("Projects", ["3", "Unlimited", "Unlimited"]),
                    ("Seats", ["1", "Up to 50", "Unlimited"]),
                    (
                        "SSO",
                        [
                            '<span class="no" aria-label="No">—</span>',
                            '<span class="yes" aria-label="Yes">✓</span>',
                            '<span class="yes" aria-label="Yes">✓</span>',
                        ],
                    ),
                    (
                        "Audit log",
                        [
                            '<span class="no" aria-label="No">—</span>',
                            '<span class="no" aria-label="No">—</span>',
                            '<span class="yes" aria-label="Yes">✓</span>',
                        ],
                    ),
                    ("Support", ["Community", "Email", "Dedicated"]),
                ]
            )
            + "</tbody></table></div>",
            T
            + ".cm th, .cm td { text-align: center; }\n.cm tbody th { text-align: left; font-weight: 500; color: var(--muted); }\n.cm .best { background: color-mix(in srgb, var(--primary) 12%, transparent); }\n.cm thead .best { color: var(--fg); box-shadow: inset 0 3px 0 var(--primary); }\n.yes { color: var(--success); font-weight: 700; }\n.no { color: var(--muted); }\n",
            note="Options across, criteria down; ticks and dashes carry spoken labels, the recommended column is tinted.",
        ),
    ),
)
