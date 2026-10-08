"""Patterns 401-420: overlays and focused interactions."""

from app.domains.references.vocabulary.base import BTN, BTN_GHOST, Item, Section

# The native <dialog>: focus trap, Escape, backdrop and inert background for free.
DLG = (
    BTN
    + BTN_GHOST
    + """\
dialog { width: min(440px, calc(100% - 32px)); padding: 0; border: 1px solid var(--border); border-radius: 18px; background: var(--surface);
  color: var(--fg); box-shadow: 0 30px 80px -20px rgb(0 0 0 / .8); }
dialog::backdrop { background: rgb(4 6 10 / .6); backdrop-filter: blur(3px); }
dialog[open] { animation: pop .22s var(--ease); }
dialog header { display: flex; justify-content: space-between; align-items: center; padding: 16px 18px 0; }
dialog h2 { margin: 0; font-size: 18px; }
dialog .body { padding: 10px 18px 18px; color: var(--muted); }
dialog footer { display: flex; justify-content: flex-end; gap: 8px; padding: 14px 18px; border-top: 1px solid var(--border); }
.close { width: 30px; height: 30px; border: 0; border-radius: 8px; background: var(--surface-2); }
@keyframes pop { from { opacity: 0; scale: .96; translate: 0 8px; } }
"""
)
OPEN_JS = """\
const dialog = document.querySelector("dialog");
const opener = document.querySelector(".open");
opener.addEventListener("click", () => dialog.showModal());
// A click on the backdrop lands on the dialog element itself.
dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });
dialog.addEventListener("close", () => opener.focus());
"""
SHEET = (
    BTN
    + """\
.stage { position: relative; width: min(620px, 100%); height: 400px; overflow: hidden; display: grid; place-items: center;
  border: 1px solid var(--border); border-radius: 18px; background: var(--surface); }
.scrim { position: absolute; inset: 0; background: rgb(4 6 10 / .55); opacity: 0; pointer-events: none; transition: opacity .25s; }
.stage.on .scrim { opacity: 1; pointer-events: auto; }
.sheet { position: absolute; background: var(--surface-2); border: 1px solid var(--border); transition: translate .32s var(--ease); padding: 18px; }
.sheet h3 { margin: 0 0 8px; }
.sheet p { margin: 0; color: var(--muted); }
"""
)
SHEET_JS = """\
const stage = document.querySelector(".stage");
const sheet = stage.querySelector(".sheet");
const opener = stage.querySelector(".open");
const set = (open) => {
  stage.classList.toggle("on", open);
  sheet.inert = !open;
  if (open) (sheet.querySelector("button, a, input") ?? sheet).focus(); else opener.focus();
};
opener.addEventListener("click", () => set(true));
stage.querySelector(".scrim").addEventListener("click", () => set(false));
sheet.querySelectorAll("[data-close]").forEach((button) => button.addEventListener("click", () => set(false)));
document.addEventListener("keydown", (event) => { if (event.key === "Escape" && stage.classList.contains("on")) set(false); });
sheet.inert = true;
"""
MENU = """\
.menu { margin: 0; padding: 6px; min-width: 190px; list-style: none; border: 1px solid var(--border); border-radius: 12px; background: var(--surface-2); box-shadow: var(--shadow); }
.menu li { display: flex; justify-content: space-between; gap: 16px; padding: 8px 10px; border-radius: 8px; cursor: pointer; outline: none; }
.menu li:hover, .menu li:focus { background: color-mix(in srgb, var(--primary) 22%, transparent); }
.menu li.sep { height: 1px; padding: 0; margin: 6px 4px; background: var(--border); pointer-events: none; }
.menu li.danger { color: var(--danger); }
.menu kbd { font: 11px var(--mono); color: var(--muted); }
"""
MENU_KEYS = """\
const moveIn = (menu, event) => {
  const items = [...menu.querySelectorAll('[role="menuitem"]')];
  const index = items.indexOf(document.activeElement);
  if (event.key === "ArrowDown") items[(index + 1) % items.length].focus();
  else if (event.key === "ArrowUp") items[(index - 1 + items.length) % items.length].focus();
  else if (event.key === "Home") items[0].focus();
  else if (event.key === "End") items.at(-1).focus();
  else return false;
  event.preventDefault();
  return true;
};
"""
PAL = """\
.pal { width: min(540px, calc(100% - 32px)); padding: 0; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); color: var(--fg);
  box-shadow: 0 30px 80px -20px rgb(0 0 0 / .8); margin-top: 12vh; }
.pal::backdrop { background: rgb(4 6 10 / .55); backdrop-filter: blur(4px); }
.pal label { display: flex; align-items: center; gap: 10px; height: 54px; padding: 0 16px; border-bottom: 1px solid var(--border); }
.pal input { flex: 1; border: 0; outline: 0; background: none; font-size: 16px; }
.pal ul { margin: 0; padding: 6px; list-style: none; max-height: 300px; overflow: auto; }
.pal li { display: flex; justify-content: space-between; gap: 12px; padding: 9px 10px; border-radius: 9px; cursor: pointer; }
.pal li[aria-selected="true"] { background: color-mix(in srgb, var(--primary) 22%, transparent); }
.pal li small { color: var(--muted); }
.pal h4 { margin: 8px 10px 4px; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.pal .none { padding: 18px; text-align: center; color: var(--muted); }
.pal footer { display: flex; gap: 14px; padding: 8px 14px; border-top: 1px solid var(--border); font-size: 12px; color: var(--muted); }
kbd { padding: 1px 6px; border: 1px solid var(--border); border-radius: 5px; font: 11px var(--mono); color: var(--muted); }
"""
VIEW = """\
.gal { display: flex; gap: 10px; }
.gal button { width: 110px; height: 80px; padding: 0; border: 0; border-radius: 12px; cursor: zoom-in; background: linear-gradient(135deg, hsl(var(--h) 70% 55%), hsl(calc(var(--h) + 50) 70% 30%)); }
.lb { width: 100%; height: 100%; max-width: none; max-height: none; margin: 0; padding: 0; border: 0; background: rgb(4 6 10 / .92); color: #fff; }
.lb[open] { display: grid; grid-template: 1fr auto / auto 1fr auto; align-items: center; }
.lb .pic { grid-column: 2; justify-self: center; width: min(70vw, 620px); aspect-ratio: 4 / 3; border-radius: 12px; background: linear-gradient(135deg, hsl(var(--h) 70% 55%), hsl(calc(var(--h) + 50) 70% 30%)); }
.lb .nav { width: 44px; height: 44px; margin: 0 14px; border: 0; border-radius: 50%; background: rgb(255 255 255 / .12); color: #fff; font-size: 20px; }
.lb .x { position: absolute; top: 14px; right: 14px; width: 38px; height: 38px; border: 0; border-radius: 50%; background: rgb(255 255 255 / .12); color: #fff; }
.lb figcaption { grid-column: 1 / -1; padding: 14px; text-align: center; color: rgb(255 255 255 / .8); }
"""

SECTION = Section(
    "patterns",
    "Overlays & Focused Interactions",
    401,
    (
        Item(
            "Modal",
            '<button class="btn open">Edit profile</button><dialog aria-labelledby="t"><form method="dialog"><header><h2 id="t">Edit profile</h2><button class="close" aria-label="Close">×</button></header><div class="body"><label>Display name<input value="Dana Whitfield" autofocus></label></div><footer><button class="btn btn-ghost" value="cancel">Cancel</button><button class="btn" value="save">Save</button></footer></form></dialog>',
            DLG
            + "dialog label { display: grid; gap: 6px; font-size: 13px; }\ndialog input { height: 40px; padding: 0 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); color: var(--fg); }\n",
            OPEN_JS,
            "A native <dialog> opened with showModal(): focus is trapped, Escape closes, the page behind is inert.",
        ),
        Item(
            "Confirmation modal",
            '<button class="btn open danger">Delete project</button><dialog role="alertdialog" aria-labelledby="t" aria-describedby="d"><form method="dialog"><header><h2 id="t">Delete “Apollo”?</h2></header><div class="body"><p id="d">This removes 34 files and cannot be undone. Type <b>Apollo</b> to confirm.</p><input aria-label="Type the project name to confirm" autocomplete="off"></div><footer><button class="btn btn-ghost" value="cancel" autofocus>Cancel</button><button class="btn danger" value="delete" disabled>Delete project</button></footer></form></dialog><p class="res" role="status"></p>',
            DLG
            + ".danger { background: var(--danger); color: #1a0606; }\ndialog p { margin: 0 0 12px; }\ndialog b { color: var(--fg); }\ndialog input { width: 100%; height: 40px; padding: 0 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); color: var(--fg); }\n.res { position: fixed; bottom: 16px; margin: 0; color: var(--muted); font-size: 13px; }\n",
            OPEN_JS
            + 'const field = dialog.querySelector("input");\nconst confirm = dialog.querySelector(\'[value="delete"]\');\nfield.addEventListener("input", () => { confirm.disabled = field.value !== "Apollo"; });\ndialog.addEventListener("close", () => {\n  document.querySelector(".res").textContent = dialog.returnValue === "delete" ? "Project deleted." : "Nothing was deleted.";\n  field.value = "";\n  confirm.disabled = true;\n});\n',
            "role=alertdialog, focus starts on the safe button, and the destructive one needs the name typed.",
        ),
        Item(
            "Full-screen modal",
            '<button class="btn open">Compose</button><dialog class="full" aria-labelledby="t"><form method="dialog"><header><button class="close" aria-label="Close">×</button><h2 id="t">New message</h2><button class="btn" value="send">Send</button></header><div class="body"><input placeholder="To" aria-label="To"><input placeholder="Subject" aria-label="Subject"><textarea placeholder="Write your message…" aria-label="Message"></textarea></div></form></dialog>',
            DLG
            + ".full { width: 100%; height: 100%; max-width: none; max-height: none; margin: 0; border: 0; border-radius: 0; }\n.full[open] { animation: rise .28s var(--ease); }\n.full form { display: grid; grid-template-rows: auto 1fr; height: 100%; }\n.full header { padding: 12px 16px; border-bottom: 1px solid var(--border); gap: 12px; }\n.full header h2 { flex: 1; }\n.full .body { display: grid; grid-template-rows: auto auto 1fr; gap: 0; padding: 0; }\n.full input, .full textarea { padding: 14px 18px; border: 0; border-bottom: 1px solid var(--border); background: none; color: var(--fg); outline: none; resize: none; }\n@keyframes rise { from { translate: 0 100%; } }\n",
            OPEN_JS,
            "Takes the whole viewport for a task that needs it, with its own header bar: close left, commit right.",
        ),
        Item(
            "Drawer",
            '<div class="stage"><button class="btn open">Open drawer</button><div class="scrim"></div><aside class="sheet dr" aria-label="Menu"><h3>Menu</h3><p>Navigation and settings.</p><button class="btn" data-close style="margin-top:16px">Close</button></aside></div>',
            SHEET
            + ".dr { inset: 0 auto 0 0; width: 260px; border-width: 0 1px 0 0; translate: -100% 0; }\n.stage.on .dr { translate: 0 0; }\n",
            SHEET_JS,
            "A panel from the leading edge over a scrim; inert while closed, Escape and scrim close it.",
        ),
        Item(
            "Side drawer",
            '<div class="stage"><button class="btn open">View order</button><div class="scrim"></div><aside class="sheet sd" aria-label="Order #2041"><h3>Order #2041</h3><p>3 items · $128.00 · In transit</p><button class="btn" data-close style="margin-top:16px">Done</button></aside></div>',
            SHEET
            + ".sd { inset: 0 0 0 auto; width: min(340px, 90%); border-width: 0 0 0 1px; translate: 100% 0; }\n.stage.on .sd { translate: 0 0; }\n",
            SHEET_JS,
            "From the trailing edge, wide enough for a record's details while the list stays in view behind.",
        ),
        Item(
            "Bottom sheet",
            '<div class="stage"><button class="btn open">Share</button><div class="scrim"></div><section class="sheet bs" aria-label="Share"><div class="grab" role="slider" aria-label="Drag to close" aria-valuemin="0" aria-valuemax="100" aria-valuenow="100" tabindex="0"></div><h3>Share this report</h3><p>Anyone with the link can view.</p><button class="btn" data-close style="margin-top:16px">Copy link</button></section></div>',
            SHEET
            + ".bs { inset: auto 0 0 0; border-width: 1px 0 0; border-radius: 20px 20px 0 0; translate: 0 100%; touch-action: none; }\n.stage.on .bs { translate: 0 var(--drag, 0px); }\n.bs.dragging { transition: none; }\n.grab { width: 44px; height: 5px; margin: -6px auto 14px; border-radius: 99px; background: var(--border); cursor: grab; }\n",
            SHEET_JS
            + 'const grab = sheet.querySelector(".grab");\nlet startY = null;\ngrab.addEventListener("pointerdown", (event) => { startY = event.clientY; sheet.classList.add("dragging"); grab.setPointerCapture(event.pointerId); });\ngrab.addEventListener("pointermove", (event) => { if (startY !== null) sheet.style.setProperty("--drag", `${Math.max(0, event.clientY - startY)}px`); });\ngrab.addEventListener("pointerup", (event) => {\n  const moved = event.clientY - startY;\n  startY = null;\n  sheet.classList.remove("dragging");\n  sheet.style.removeProperty("--drag");\n  if (moved > sheet.offsetHeight / 3) set(false);  // dragged far enough: close; otherwise it springs back\n});\ngrab.addEventListener("keydown", (event) => { if (event.key === "ArrowDown") set(false); });\n',
            "Rises from the bottom on phones; the handle drags it and a long enough drag dismisses.",
        ),
        Item(
            "Action sheet",
            '<div class="stage"><button class="btn open">Photo options</button><div class="scrim"></div><div class="sheet as" role="menu" aria-label="Photo options"><button role="menuitem" data-close>Take photo</button><button role="menuitem" data-close>Choose from library</button><button role="menuitem" class="d" data-close>Remove photo</button><button class="cancel" data-close>Cancel</button></div></div>',
            SHEET
            + ".as { inset: auto 10px 10px 10px; padding: 6px; border-radius: 16px; display: grid; gap: 2px; translate: 0 calc(100% + 20px); }\n.stage.on .as { translate: 0 0; }\n.as button { height: 48px; border: 0; border-radius: 11px; background: none; font-size: 16px; }\n.as button:hover, .as button:focus-visible { background: var(--surface); }\n.as .d { color: var(--danger); }\n.as .cancel { margin-top: 6px; background: var(--surface); font-weight: 700; }\n",
            SHEET_JS,
            "A short list of choices for one thing, destructive one in red, Cancel set apart at the bottom.",
        ),
        Item(
            "Popover",
            '<button class="btn" popovertarget="pop">Filters</button><div id="pop" popover class="pop"><h4>Filter by</h4><label><input type="checkbox" checked> Open</label><label><input type="checkbox"> Assigned to me</label><label><input type="checkbox"> Updated this week</label></div>',
            BTN
            + ".pop { inset: auto; margin: 0; top: calc(50% + 28px); left: 50%; translate: -50% 0; width: 240px; padding: 14px; border: 1px solid var(--border); border-radius: 14px; background: var(--surface-2); color: var(--fg); box-shadow: var(--shadow); }\n.pop:popover-open { display: grid; gap: 8px; animation: in .16s var(--ease); }\n.pop h4 { margin: 0 0 4px; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }\n@keyframes in { from { opacity: 0; translate: -50% -6px; } }\n",
            note="The popover attribute: opens in the top layer, closes on outside click and Escape, no script.",
        ),
        Item(
            "Tooltip",
            '<div class="row"><button class="tt" aria-describedby="tp1">Hover or focus me<span role="tooltip" id="tp1">Saves and closes the editor</span></button><button class="tt bottom" aria-describedby="tp2">⌘S<span role="tooltip" id="tp2">Save</span></button></div>',
            '.row { display: flex; gap: 20px; }\n.tt { position: relative; padding: 9px 14px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }\n.tt [role=tooltip] { position: absolute; left: 50%; bottom: calc(100% + 10px); translate: -50% 4px; padding: 5px 10px; border-radius: 8px; background: var(--fg); color: var(--bg); font-size: 12px; white-space: nowrap; opacity: 0; pointer-events: none; transition: opacity .12s .4s, translate .12s .4s; }\n.tt [role=tooltip]::after { content: ""; position: absolute; left: 50%; top: 100%; translate: -50% -50%; rotate: 45deg; width: 8px; height: 8px; background: inherit; }\n.tt.bottom [role=tooltip] { bottom: auto; top: calc(100% + 10px); translate: -50% -4px; }\n.tt.bottom [role=tooltip]::after { top: 0; }\n.tt:hover [role=tooltip], .tt:focus-visible [role=tooltip] { opacity: 1; translate: -50% 0; }\n',
            note="Appears after a short delay on hover or focus; tied to its trigger with aria-describedby.",
        ),
        Item(
            "Context menu",
            '<div class="zone" tabindex="0">Right-click anywhere in this area</div><ul class="menu cm" role="menu" hidden><li role="menuitem" tabindex="-1">Copy <kbd>⌘C</kbd></li><li role="menuitem" tabindex="-1">Paste <kbd>⌘V</kbd></li><li role="menuitem" tabindex="-1">Duplicate <kbd>⌘D</kbd></li><li class="sep" role="separator"></li><li role="menuitem" tabindex="-1" class="danger">Delete <kbd>⌫</kbd></li></ul>',
            MENU
            + ".zone { display: grid; place-items: center; width: min(460px, 100%); height: 240px; border: 1px dashed var(--border); border-radius: 16px; color: var(--muted); }\n.cm { position: fixed; z-index: 10; }\n.cm[hidden] { display: none; }\n",
            MENU_KEYS
            + 'const zone = document.querySelector(".zone");\nconst menu = document.querySelector(".cm");\nconst openAt = (x, y) => {\n  menu.hidden = false;\n  menu.style.left = `${Math.min(x, innerWidth - menu.offsetWidth - 8)}px`;\n  menu.style.top = `${Math.min(y, innerHeight - menu.offsetHeight - 8)}px`;\n  menu.querySelector(\'[role="menuitem"]\').focus();\n};\nconst close = () => { if (!menu.hidden) { menu.hidden = true; zone.focus(); } };\nzone.addEventListener("contextmenu", (event) => { event.preventDefault(); openAt(event.clientX, event.clientY); });\nzone.addEventListener("keydown", (event) => { if (event.key === "ContextMenu" || (event.shiftKey && event.key === "F10")) { event.preventDefault(); const box = zone.getBoundingClientRect(); openAt(box.left + 30, box.top + 30); } });\nmenu.addEventListener("keydown", (event) => { if (!moveIn(menu, event) && (event.key === "Escape" || event.key === "Enter")) close(); });\nmenu.addEventListener("click", close);\ndocument.addEventListener("pointerdown", (event) => { if (!menu.contains(event.target)) menu.hidden = true; });\n',
            "Opens at the pointer, stays inside the viewport, has shortcuts listed and full keyboard movement.",
        ),
        Item(
            "Dropdown menu",
            '<div class="dd"><button class="btn trig" aria-haspopup="menu" aria-expanded="false">Account ▾</button><ul class="menu" role="menu" hidden><li role="menuitem" tabindex="-1">Profile</li><li role="menuitem" tabindex="-1">Billing</li><li role="menuitem" tabindex="-1">Team</li><li class="sep" role="separator"></li><li role="menuitem" tabindex="-1" class="danger">Sign out</li></ul></div>',
            BTN
            + MENU
            + ".dd { position: relative; height: 260px; }\n.dd .menu { position: absolute; top: 48px; left: 0; transform-origin: top left; animation: in .14s var(--ease); }\n.dd .menu[hidden] { display: none; }\n@keyframes in { from { opacity: 0; scale: .96; } }\n",
            MENU_KEYS
            + 'const trigger = document.querySelector(".trig");\nconst menu = document.querySelector(".dd .menu");\nconst set = (open, focusTrigger = true) => {\n  menu.hidden = !open;\n  trigger.setAttribute("aria-expanded", String(open));\n  if (open) menu.querySelector(\'[role="menuitem"]\').focus(); else if (focusTrigger) trigger.focus();\n};\ntrigger.addEventListener("click", () => set(menu.hidden));\ntrigger.addEventListener("keydown", (event) => { if (event.key === "ArrowDown") { event.preventDefault(); set(true); } });\nmenu.addEventListener("keydown", (event) => {\n  if (moveIn(menu, event)) return;\n  if (event.key === "Escape" || event.key === "Enter" || event.key === "Tab") set(false);\n  // Typing a letter jumps to the first item starting with it.\n  else if (event.key.length === 1) [...menu.querySelectorAll(\'[role="menuitem"]\')].find((item) => item.textContent.trim().toLowerCase().startsWith(event.key.toLowerCase()))?.focus();\n});\nmenu.addEventListener("click", () => set(false));\ndocument.addEventListener("pointerdown", (event) => { if (!event.target.closest(".dd") && !menu.hidden) set(false, false); });\n',
            "The ARIA menu-button pattern: arrows, Home/End, type-ahead, Escape returning focus to the button.",
        ),
        Item(
            "Command palette",
            '<button class="btn open">Open palette <kbd>⌘K</kbd></button><dialog class="pal" aria-label="Command palette"><label><span aria-hidden="true">⌕</span><input placeholder="Type a command or search…" aria-label="Command" aria-controls="res" autocomplete="off"></label><ul id="res" role="listbox"></ul><footer><span><kbd>↑↓</kbd> move</span><span><kbd>↵</kbd> run</span><span><kbd>esc</kbd> close</span></footer></dialog><p class="ran" role="status"></p>',
            BTN
            + PAL
            + ".open kbd { margin-left: 8px; border-color: rgb(255 255 255 / .3); color: #fff; }\n.ran { position: fixed; bottom: 16px; margin: 0; color: var(--muted); font-size: 13px; }\n",
            'const COMMANDS = [["Actions", "Create project", "N"], ["Actions", "Invite teammate", "I"], ["Actions", "Export as CSV", "E"], ["Navigate", "Go to Dashboard", "G D"], ["Navigate", "Go to Settings", "G S"], ["Theme", "Switch to light mode", ""], ["Theme", "Switch to dark mode", ""]];\nconst dialog = document.querySelector(".pal");\nconst input = dialog.querySelector("input");\nconst list = document.getElementById("res");\nconst ran = document.querySelector(".ran");\nlet active = 0;\n// Letters in order, with a bonus for matching at word starts, so "gs" finds "Go to Settings".\nconst score = (text, query) => {\n  let at = -1, total = 0;\n  for (const char of query) {\n    at = text.indexOf(char, at + 1);\n    if (at < 0) return -1;\n    total += at === 0 || text[at - 1] === " " ? 3 : 1;\n  }\n  return total;\n};\nconst render = () => {\n  const query = input.value.toLowerCase().replace(/\\s/g, "");\n  const found = COMMANDS.map((command) => [command, score(command[1].toLowerCase(), query)]).filter(([, s]) => s >= 0).sort((a, b) => b[1] - a[1]).map(([command]) => command);\n  list.replaceChildren();\n  if (found.length === 0) { list.append(Object.assign(document.createElement("li"), { className: "none", textContent: "No matching command" })); return; }\n  active = Math.min(active, found.length - 1);\n  let group = "";\n  found.forEach(([section, name, keys], i) => {\n    if (!query && section !== group) { list.append(Object.assign(document.createElement("h4"), { textContent: section })); group = section; }\n    const item = document.createElement("li");\n    item.setAttribute("role", "option");\n    item.setAttribute("aria-selected", String(i === active));\n    item.dataset.name = name;\n    item.append(name, Object.assign(document.createElement("small"), { textContent: keys }));\n    list.append(item);\n  });\n  list.querySelector(\'[aria-selected="true"]\')?.scrollIntoView({ block: "nearest" });\n};\nconst run = (item) => { if (item) { ran.textContent = `Ran: ${item.dataset.name}`; dialog.close(); } };\nconst open = () => { input.value = ""; active = 0; render(); dialog.showModal(); };\ndocument.querySelector(".open").addEventListener("click", open);\ndocument.addEventListener("keydown", (event) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); if (dialog.open) dialog.close(); else open(); } });\ninput.addEventListener("input", () => { active = 0; render(); });\ninput.addEventListener("keydown", (event) => {\n  const options = [...list.querySelectorAll(\'[role="option"]\')];\n  if (event.key === "ArrowDown" || event.key === "ArrowUp") { event.preventDefault(); active = (active + (event.key === "ArrowDown" ? 1 : -1) + options.length) % options.length; render(); }\n  else if (event.key === "Enter") { event.preventDefault(); run(options[active]); }\n});\nlist.addEventListener("click", (event) => run(event.target.closest(\'[role="option"]\')));\ndialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });\n',
            "⌘/Ctrl+K opens a dialog with fuzzy-ranked commands, grouped when idle, driven entirely from the keyboard.",
        ),
        Item(
            "Spotlight search",
            '<button class="btn open">Search</button><dialog class="pal" aria-label="Search"><label><span aria-hidden="true">⌕</span><input placeholder="Search projects, people and files" aria-label="Search" autocomplete="off"></label><ul role="listbox"></ul></dialog>',
            BTN
            + PAL
            + ".pal li .k { display: grid; place-items: center; width: 26px; height: 26px; margin-right: 10px; border-radius: 8px; background: var(--surface-2); font-size: 12px; flex: none; }\n.pal li { justify-content: flex-start; align-items: center; }\n.pal li small { margin-left: auto; }\n.pal mark { background: none; color: var(--accent); font-weight: 700; }\n",
            'const INDEX = [["Project", "Apollo roadmap"], ["Project", "Gemini migration"], ["Person", "Dana Whitfield"], ["Person", "Mika Tanaka"], ["File", "q3-forecast.xlsx"], ["File", "apollo-brief.pdf"], ["File", "pricing-notes.md"]];\nconst dialog = document.querySelector(".pal");\nconst input = dialog.querySelector("input");\nconst list = dialog.querySelector("ul");\nlet active = 0, timer = null;\nconst render = () => {\n  const query = input.value.trim().toLowerCase();\n  const found = query ? INDEX.filter(([, name]) => name.toLowerCase().includes(query)) : [];\n  list.replaceChildren();\n  if (!query) { list.append(Object.assign(document.createElement("li"), { className: "none", textContent: "Start typing to search" })); return; }\n  if (found.length === 0) { list.append(Object.assign(document.createElement("li"), { className: "none", textContent: `Nothing found for “${input.value.trim()}”` })); return; }\n  let kind = "";\n  found.forEach(([type, name], i) => {\n    if (type !== kind) { list.append(Object.assign(document.createElement("h4"), { textContent: `${type}s` })); kind = type; }\n    const item = document.createElement("li");\n    item.setAttribute("role", "option");\n    item.setAttribute("aria-selected", String(i === active));\n    const at = name.toLowerCase().indexOf(query);\n    const label = document.createElement("span");\n    label.append(name.slice(0, at), Object.assign(document.createElement("mark"), { textContent: name.slice(at, at + query.length) }), name.slice(at + query.length));\n    item.append(Object.assign(document.createElement("span"), { className: "k", textContent: type[0] }), label, Object.assign(document.createElement("small"), { textContent: type }));\n    list.append(item);\n  });\n};\n// Wait for a pause in typing before searching: a real index is a network call.\ninput.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => { active = 0; render(); }, 120); });\ninput.addEventListener("keydown", (event) => {\n  const count = list.querySelectorAll(\'[role="option"]\').length;\n  if (!count || (event.key !== "ArrowDown" && event.key !== "ArrowUp")) return;\n  event.preventDefault();\n  active = (active + (event.key === "ArrowDown" ? 1 : -1) + count) % count;\n  render();\n});\ndocument.querySelector(".open").addEventListener("click", () => { input.value = ""; render(); dialog.showModal(); });\ndialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });\n',
            "Global search in a dialog: debounced, grouped by kind, with the matched letters highlighted.",
        ),
        Item(
            "Lightbox",
            '<div class="gal"><button style="--h:250" aria-label="Open image 1 of 3"></button><button style="--h:170" aria-label="Open image 2 of 3"></button><button style="--h:20" aria-label="Open image 3 of 3"></button></div><dialog class="lb" aria-label="Image viewer"><button class="x" aria-label="Close">×</button><button class="nav prev" aria-label="Previous image">‹</button><figure class="pic" style="margin:0"></figure><button class="nav next" aria-label="Next image">›</button><figcaption></figcaption></dialog>',
            VIEW,
            'const thumbs = [...document.querySelectorAll(".gal button")];\nconst dialog = document.querySelector(".lb");\nconst picture = dialog.querySelector(".pic");\nconst caption = dialog.querySelector("figcaption");\nlet index = 0;\nconst show = (next) => {\n  index = (next + thumbs.length) % thumbs.length;\n  picture.style.setProperty("--h", thumbs[index].style.getPropertyValue("--h"));\n  caption.textContent = `Image ${index + 1} of ${thumbs.length}`;\n};\nthumbs.forEach((thumb, i) => thumb.addEventListener("click", () => { show(i); dialog.showModal(); }));\ndialog.querySelector(".prev").addEventListener("click", () => show(index - 1));\ndialog.querySelector(".next").addEventListener("click", () => show(index + 1));\ndialog.querySelector(".x").addEventListener("click", () => dialog.close());\ndialog.addEventListener("keydown", (event) => { if (event.key === "ArrowLeft") show(index - 1); if (event.key === "ArrowRight") show(index + 1); });\ndialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });\ndialog.addEventListener("close", () => thumbs[index].focus());  // back to the thumbnail last viewed\n',
            "A thumbnail opens full-screen on a dark backdrop; arrows move through the set and focus returns to the thumbnail.",
        ),
        Item(
            "Image viewer",
            '<div class="iv" tabindex="0" aria-label="Image viewer. Scroll to zoom, drag to pan."><div class="img"></div></div><div class="tools"><button data-z="-1" aria-label="Zoom out">−</button><output>100%</output><button data-z="1" aria-label="Zoom in">+</button><button data-z="0">Reset</button></div>',
            ".iv { width: min(520px, 100%); height: 300px; overflow: hidden; border: 1px solid var(--border); border-radius: 16px; background: #06080c; cursor: grab; touch-action: none; }\n.iv:active { cursor: grabbing; }\n.iv .img { width: 100%; height: 100%; transform-origin: 0 0; background: radial-gradient(circle at 30% 30%, #f472b6, transparent 40%), radial-gradient(circle at 70% 60%, #22d3ee, transparent 45%), linear-gradient(135deg, #1e1b4b, #7c5cff); }\n.tools { display: flex; gap: 6px; align-items: center; margin-top: 10px; }\n.tools button { min-width: 34px; height: 32px; padding: 0 10px; border: 1px solid var(--border); border-radius: 9px; background: var(--surface); }\n.tools output { min-width: 52px; text-align: center; font-variant-numeric: tabular-nums; color: var(--muted); }\nbody { align-content: center; justify-items: center; }\n",
            'const view = document.querySelector(".iv");\nconst image = view.querySelector(".img");\nconst readout = document.querySelector(".tools output");\nconst MIN = 1, MAX = 6;\nlet scale = 1, x = 0, y = 0;\nconst apply = () => {\n  // Keep the image covering the frame: panning stops at its edges.\n  x = Math.min(0, Math.max(view.clientWidth * (1 - scale), x));\n  y = Math.min(0, Math.max(view.clientHeight * (1 - scale), y));\n  image.style.transform = `translate(${x}px, ${y}px) scale(${scale})`;\n  readout.textContent = `${Math.round(scale * 100)}%`;\n};\nconst zoomAt = (factor, cx, cy) => {\n  const next = Math.min(MAX, Math.max(MIN, scale * factor));\n  // The point under the cursor stays under the cursor.\n  x = cx - ((cx - x) / scale) * next;\n  y = cy - ((cy - y) / scale) * next;\n  scale = next;\n  apply();\n};\nview.addEventListener("wheel", (event) => { event.preventDefault(); const box = view.getBoundingClientRect(); zoomAt(event.deltaY < 0 ? 1.15 : 1 / 1.15, event.clientX - box.left, event.clientY - box.top); }, { passive: false });\nlet drag = null;\nview.addEventListener("pointerdown", (event) => { drag = [event.clientX - x, event.clientY - y]; view.setPointerCapture(event.pointerId); });\nview.addEventListener("pointermove", (event) => { if (drag) { x = event.clientX - drag[0]; y = event.clientY - drag[1]; apply(); } });\nview.addEventListener("pointerup", () => { drag = null; });\nview.addEventListener("keydown", (event) => {\n  const step = 40;\n  if (event.key === "+" || event.key === "=") zoomAt(1.25, view.clientWidth / 2, view.clientHeight / 2);\n  else if (event.key === "-") zoomAt(0.8, view.clientWidth / 2, view.clientHeight / 2);\n  else if (event.key === "ArrowLeft") { x += step; apply(); } else if (event.key === "ArrowRight") { x -= step; apply(); }\n  else if (event.key === "ArrowUp") { y += step; apply(); } else if (event.key === "ArrowDown") { y -= step; apply(); }\n});\ndocument.querySelector(".tools").addEventListener("click", (event) => {\n  const direction = event.target.dataset.z;\n  if (direction === undefined) return;\n  if (direction === "0") { scale = 1; x = y = 0; apply(); } else zoomAt(direction === "1" ? 1.4 : 1 / 1.4, view.clientWidth / 2, view.clientHeight / 2);\n});\napply();\n',
            "Wheel zooms about the cursor, dragging pans within the image's bounds, with buttons and keys for both.",
        ),
        Item(
            "Document preview",
            '<div class="dp"><header><b>Product requirements v4.docx</b><span>Page <output>1</output> of 3</span><button class="btn">Download</button></header><div class="pages" tabindex="0">'
            + "".join(
                f'<article data-p="{i}"><h3>{t}</h3><p></p><p></p><p class="s"></p><p></p></article>'
                for i, t in [(1, "1. Overview"), (2, "2. Requirements"), (3, "3. Milestones")]
            )
            + "</div></div>",
            BTN
            + ".dp { width: min(520px, 100%); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; background: var(--surface); }\n.dp header { display: flex; align-items: center; gap: 12px; padding: 10px 14px; border-bottom: 1px solid var(--border); font-size: 14px; }\n.dp header b { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }\n.dp header span { color: var(--muted); }\n.dp .btn { height: 32px; }\n.pages { height: 300px; overflow: auto; padding: 16px; background: #06080c; display: grid; gap: 16px; }\n.pages article { margin: 0 auto; width: min(360px, 100%); min-height: 260px; padding: 26px; border-radius: 4px; background: #f6f7fb; color: #1b2130; box-shadow: 0 6px 20px rgb(0 0 0 / .5); }\n.pages h3 { margin: 0 0 14px; }\n.pages p { height: 8px; margin: 0 0 10px; border-radius: 4px; background: #d5d9e6; }\n.pages p.s { width: 60%; }\n",
            'const pages = document.querySelector(".pages");\nconst current = document.querySelector(".dp output");\n// The page most in view is the current page.\nconst observer = new IntersectionObserver((entries) => {\n  for (const entry of entries) if (entry.isIntersecting) current.textContent = entry.target.dataset.p;\n}, { root: pages, threshold: 0.6 });\npages.querySelectorAll("article").forEach((page) => observer.observe(page));\n',
            "Pages on a dark desk in a scrolling pane, with the file name, the current page and a download.",
        ),
        Item(
            "PDF viewer",
            '<div class="pv"><header><button aria-label="Previous page">‹</button><span><input value="1" inputmode="numeric" aria-label="Page"> / <b>5</b></span><button aria-label="Next page">›</button><span class="sp"></span><button data-z="-1" aria-label="Zoom out">−</button><output>100%</output><button data-z="1" aria-label="Zoom in">+</button></header><div class="canvas"><div class="page"><h4></h4><i></i><i></i><i class="s"></i><i></i><i></i><i class="s"></i></div></div></div>',
            ".pv { width: min(520px, 100%); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; background: var(--surface); }\n.pv header { display: flex; align-items: center; gap: 6px; padding: 8px 10px; border-bottom: 1px solid var(--border); font-size: 14px; }\n.pv header button { width: 30px; height: 30px; border: 0; border-radius: 8px; background: var(--surface-2); }\n.pv header button:disabled { opacity: .3; }\n.pv header input { width: 36px; height: 28px; text-align: center; border: 1px solid var(--border); border-radius: 7px; background: var(--bg); }\n.pv .sp { flex: 1; }\n.pv output { min-width: 46px; text-align: center; color: var(--muted); font-variant-numeric: tabular-nums; }\n.canvas { height: 320px; overflow: auto; display: grid; place-items: start center; padding: 18px; background: #06080c; }\n.page { width: 240px; aspect-ratio: 1 / 1.414; padding: 22px; background: #f6f7fb; color: #1b2130; box-shadow: 0 6px 20px rgb(0 0 0 / .5); transform-origin: top center; transition: scale .15s; }\n.page h4 { margin: 0 0 14px; }\n.page i { display: block; height: 7px; margin-bottom: 9px; border-radius: 4px; background: #d5d9e6; }\n.page i.s { width: 55%; }\n",
            '// The frame of a PDF viewer: paging and zoom around one rendered page. Render the real page\n// into `.page` with a PDF library (pdf.js) or point an <iframe>/<object> at the file.\nconst TOTAL = 5;\nconst TITLES = ["Cover", "Summary", "Financials", "Forecast", "Appendix"];\nconst page = document.querySelector(".page");\nconst field = document.querySelector(".pv input");\nconst [previous, next] = document.querySelectorAll(".pv header > button");\nconst zoomLabel = document.querySelector(".pv output");\nlet number = 1, zoom = 1;\nconst render = () => {\n  page.querySelector("h4").textContent = `${number}. ${TITLES[number - 1]}`;\n  field.value = String(number);\n  previous.disabled = number === 1;\n  next.disabled = number === TOTAL;\n  page.style.scale = String(zoom);\n  zoomLabel.textContent = `${Math.round(zoom * 100)}%`;\n};\nconst go = (to) => { number = Math.min(TOTAL, Math.max(1, Number.isFinite(to) ? Math.round(to) : number)); render(); };\nprevious.addEventListener("click", () => go(number - 1));\nnext.addEventListener("click", () => go(number + 1));\nfield.addEventListener("change", () => go(Number(field.value)));\ndocument.querySelectorAll("[data-z]").forEach((button) => button.addEventListener("click", () => { zoom = Math.min(2, Math.max(0.5, zoom + Number(button.dataset.z) * 0.25)); render(); }));\nrender();\n',
            "The viewer's chrome: page field, previous and next, zoom. The page itself comes from a PDF renderer.",
        ),
        Item(
            "Video modal",
            '<button class="poster open" aria-label="Play product tour, 1 minute 24 seconds"><span>▶</span><small>1:24</small></button><dialog class="vm" aria-label="Product tour"><button class="close" aria-label="Close">×</button><div class="frame"><div class="vid"><span>Video plays here</span></div></div></dialog>',
            DLG
            + ".poster { position: relative; display: grid; place-items: center; width: 320px; aspect-ratio: 16 / 9; border: 0; border-radius: 16px; background: linear-gradient(135deg, #1e1b4b, #7c5cff 60%, #22d3ee); }\n.poster span { display: grid; place-items: center; width: 60px; height: 60px; border-radius: 50%; background: rgb(0 0 0 / .45); color: #fff; font-size: 20px; backdrop-filter: blur(6px); transition: scale .2s var(--ease); }\n.poster:hover span { scale: 1.1; }\n.poster small { position: absolute; right: 10px; bottom: 10px; padding: 1px 8px; border-radius: 6px; background: rgb(0 0 0 / .6); color: #fff; font: 12px var(--mono); }\n.vm { width: min(760px, calc(100% - 32px)); background: none; border: 0; box-shadow: none; overflow: visible; }\n.vm .close { position: absolute; top: -40px; right: 0; background: rgb(255 255 255 / .15); color: #fff; }\n.frame { aspect-ratio: 16 / 9; border-radius: 14px; overflow: hidden; background: #000; }\n.vid { display: grid; place-items: center; width: 100%; height: 100%; color: rgb(255 255 255 / .6); }\n",
            OPEN_JS
            + 'const frame = dialog.querySelector(".frame");\nconst slot = frame.innerHTML;\ndialog.querySelector(".close").addEventListener("click", () => dialog.close());\n// The player is created on open and removed on close, so nothing loads early and playback always stops.\ndialog.addEventListener("close", () => { frame.innerHTML = slot; });\n',
            "A poster with a play button opens the player in a dialog; closing removes the player so the sound stops.",
        ),
        Item(
            "Onboarding modal",
            '<button class="btn open">Start tour</button><dialog class="ob" aria-labelledby="ot"><div class="art"></div><div class="body"><h2 id="ot"></h2><p></p></div><footer><div class="dots" aria-hidden="true"></div><button class="btn btn-ghost skip">Skip</button><button class="btn next">Next</button></footer></dialog>',
            DLG
            + ".ob .art { height: 150px; border-radius: 17px 17px 0 0; background: linear-gradient(135deg, hsl(var(--h, 250) 70% 55%), hsl(calc(var(--h, 250) + 60) 70% 35%)); transition: background .3s; }\n.ob .body { padding: 18px 18px 6px; }\n.ob h2 { margin-bottom: 6px; }\n.ob p { margin: 0; min-height: 44px; }\n.ob footer { align-items: center; border-top: 0; }\n.dots { display: flex; gap: 6px; margin-right: auto; }\n.dots i { width: 7px; height: 7px; border-radius: 50%; background: var(--border); transition: background .2s, width .2s; }\n.dots i.on { width: 20px; border-radius: 99px; background: var(--primary); }\n",
            'const STEPS = [["Welcome to Northwind", "A quick look at the three things you will use most.", 250], ["Projects", "Everything lives in a project. Create one from the sidebar.", 180], ["Invite your team", "Work is better together. You can invite people at any time.", 330]];\nconst dialog = document.querySelector(".ob");\nconst dots = dialog.querySelector(".dots");\nconst next = dialog.querySelector(".next");\nlet step = 0;\nSTEPS.forEach(() => dots.append(document.createElement("i")));\nconst render = () => {\n  const [title, text, hue] = STEPS[step];\n  dialog.querySelector("h2").textContent = title;\n  dialog.querySelector("p").textContent = text;\n  dialog.querySelector(".art").style.setProperty("--h", hue);\n  [...dots.children].forEach((dot, i) => dot.classList.toggle("on", i === step));\n  next.textContent = step === STEPS.length - 1 ? "Get started" : "Next";\n};\ndocument.querySelector(".open").addEventListener("click", () => { step = 0; render(); dialog.showModal(); });\nnext.addEventListener("click", () => { if (step === STEPS.length - 1) dialog.close(); else { step += 1; render(); } });\ndialog.querySelector(".skip").addEventListener("click", () => dialog.close());\n',
            "A few illustrated steps with progress dots; Skip is always there and the last step's button changes.",
        ),
        Item(
            "Cookie dialog",
            '<section class="ck" role="dialog" aria-labelledby="ct" aria-describedby="cd"><h2 id="ct">Your privacy</h2><p id="cd">We use cookies that are needed for the site to work, and, if you agree, cookies that measure how it is used.</p><details><summary>Choose</summary><label><input type="checkbox" checked disabled> Necessary <small>always on</small></label><label><input type="checkbox" name="analytics"> Analytics</label><label><input type="checkbox" name="marketing"> Marketing</label></details><footer><button class="btn btn-ghost" data-c="reject">Reject optional</button><button class="btn btn-ghost" data-c="save">Save choices</button><button class="btn" data-c="accept">Accept all</button></footer></section><p class="res" role="status"></p>',
            DLG
            + ".ck { position: fixed; left: 16px; bottom: 16px; width: min(420px, calc(100% - 32px)); padding: 18px; border: 1px solid var(--border); border-radius: 16px; background: var(--surface); box-shadow: var(--shadow); }\n.ck h2 { margin: 0 0 6px; font-size: 16px; }\n.ck p { margin: 0 0 10px; color: var(--muted); font-size: 14px; }\n.ck details { margin-bottom: 12px; }\n.ck summary { cursor: pointer; color: var(--primary); font-size: 14px; }\n.ck label { display: flex; gap: 8px; align-items: center; margin-top: 8px; font-size: 14px; }\n.ck small { color: var(--muted); }\n.ck footer { display: flex; flex-wrap: wrap; gap: 8px; }\n.ck footer .btn { height: 36px; flex: 1; }\n.res { color: var(--muted); font-size: 14px; }\n",
            'const KEY = "consent.v1";\nconst banner = document.querySelector(".ck");\nconst result = document.querySelector(".res");\nconst store = (choice) => { try { localStorage.setItem(KEY, JSON.stringify(choice)); } catch { /* asked again next visit */ } };\nconst stored = () => { try { return JSON.parse(localStorage.getItem(KEY)); } catch { return null; } };\nconst finish = (choice) => { store(choice); banner.remove(); result.textContent = `Analytics ${choice.analytics ? "on" : "off"}, marketing ${choice.marketing ? "on" : "off"}.`; };\nif (stored()) finish(stored());\nbanner.querySelector("footer").addEventListener("click", (event) => {\n  const action = event.target.dataset.c;\n  if (!action) return;\n  const boxes = banner.querySelectorAll("input[name]");\n  // Nothing optional is on until the person says so; rejecting is as easy as accepting.\n  if (action === "accept") finish({ analytics: true, marketing: true });\n  else if (action === "reject") finish({ analytics: false, marketing: false });\n  else finish(Object.fromEntries([...boxes].map((box) => [box.name, box.checked])));\n});\n',
            "Optional cookies are off by default, rejecting is as prominent as accepting, and the choice is remembered.",
        ),
    ),
)
