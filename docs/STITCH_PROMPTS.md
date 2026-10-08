# Stitch prompts — Generative UI Workspace

How to use: start a **Web** project in Stitch. Paste **Prompt 0** first to set the product
and visual direction, then generate one screen per prompt, in order. Each screen prompt is
self-contained, so it also works on its own. Labels and copy match what the app already
says, so the designs line up with the working features.

Two things to keep in mind while designing:

- **The canvas content is an example.** The dashboard inside the canvas is generated at
  runtime from data and themed by the user. Stitch should design the *editor around it*
  and show a believable sample inside it, not treat the dashboard as fixed layout.
- **The editor chrome is neutral on purpose.** The generated UI can be any theme (light,
  dark, violet…), so the surrounding app stays quiet and never competes with it.

---

## Prompt 0 — Product overview and visual direction

```
Design a desktop web app called "Generative UI". It is a conversational workspace for
building interfaces: the user describes what they want ("Create a sales dashboard"), an AI
assistant proposes it, the user previews and approves it, and keeps changing it by typing
instructions or by editing it directly. Every approved change is saved as a numbered
version that can be previewed, compared and restored.

It is a professional design/workspace tool, in the spirit of Linear, Figma and Vercel. It
is NOT a chatbot and NOT a generic admin dashboard. The generated interface (the canvas)
dominates the screen; the AI is a slim command bar docked at the bottom, not a chat page.

Visual direction:
- Calm, neutral, precise. Light theme by default with an optional dark theme.
- Neutrals: page background #F6F6F7, panels white, borders #E4E4E7, text #18181B,
  secondary text #71717A, canvas backdrop #ECECEF.
- One accent only: indigo #4F46E5, with a soft tint #EEF2FF for selected states.
- Semantic colours used sparingly: success #15803D, warning #B45309, danger #DC2626.
- Typography: system sans (Inter-like), 14px base, semibold headings with tight tracking,
  11px uppercase labels for section headers. Monospace only for ids and dataset names.
- Shape: 6–8px radius on controls, 12px on cards and panels, 1px hairline borders.
  Shadows only on floating things (popovers, dialogs, toasts).
- Dense but breathable: 32–36px controls, 48px top toolbar, 224px left sidebar,
  320px right panel.
- Icons: thin outline icons (Lucide style), 14–16px.
- No gradients, no glassmorphism, no illustrations, no decorative animation, no oversized
  rounded cards, no emoji.

Global layout: a slim left sidebar (logo "Generative UI", nav items "Workspaces" and
"Settings", a "Recent" list of workspace names, and at the bottom the signed-in user's
email with a small sign-out icon) plus a main area to the right.

Accessibility: visible focus rings in the accent colour, AA text contrast, every icon
button has a text label or tooltip.
```

---

## Screen 1 — Sign in / Create account

```
Design the sign-in screen for "Generative UI", a professional workspace tool. Neutral
light background #F6F6F7, a single centered white card, 380px wide, 12px radius, 1px
border #E4E4E7, subtle shadow.

Inside the card, top to bottom:
- Small logo mark (a 2x2 block glyph, dark with one indigo tile) and the name
  "Generative UI".
- Heading "Sign in".
- Helper text: "Your workspaces and their version history are private to your account."
- Field "Email" (email input).
- Field "Password" (password input).
- An inline error line in red, shown below the fields: "Incorrect email or password."
- Full-width primary button, indigo #4F46E5: "Sign in".
- Footer text: "New here?" followed by a text link "Create an account".

Also show the second state of the same card for registration: heading "Create your
account", password label "Password (at least 8 characters)", primary button "Create
account", footer "Already have an account? Sign in".

No social login buttons, no illustration, no marketing copy. Calm and minimal.
```

---

## Screen 2 — Workspaces list

```
Design the "Workspaces" page of "Generative UI", a professional tool where each workspace
is one AI-built interface with its version history.

Layout: slim left sidebar (logo "Generative UI"; nav "Workspaces" active, "Settings";
section label "RECENT" with three workspace names; user email and a sign-out icon at the
bottom) and a main content area, max width 1024px, generous top padding.

Main area:
- Header row: title "Workspaces" with subtitle "Each workspace is one interface you build
  by describing it, with its full version history." On the right a primary indigo button
  with a plus icon: "New workspace".
- A responsive grid of workspace cards, 3 per row. Each card: white, 12px radius, 1px
  border, title in semibold (e.g. "Sales Dashboard", "Support Overview", "Feedback
  Form"), and a bottom meta row with a small grey version badge ("v8") and "Updated 2
  hours ago". One card shows an amber "Empty" badge instead of a version. A trash icon
  appears in the card's top-right corner on hover.

Also design the empty state variant: a dashed-border panel with a small grid icon, the
heading "No workspaces yet", the text "Create one and describe the interface you need.",
and the "New workspace" button.

Also include the delete confirmation dialog: title "Delete “Sales Dashboard”?", text "The
workspace, its conversation and every version are deleted permanently.", buttons "Cancel"
and a red "Delete".

Neutral palette, indigo accent #4F46E5, hairline borders, no gradients.
```

---

## Screen 3 — New workspace (empty state)

```
Design the empty state of a workspace in "Generative UI", an AI workspace for building
interfaces. This is what the user sees before anything has been generated.

Layout:
- Left sidebar (logo, "Workspaces", "Settings", "Recent" list, user email at bottom).
- Top toolbar, 48px, white with a bottom border: a back arrow, an editable workspace name
  showing the placeholder "Untitled workspace"; in the centre a segmented control "View |
  Edit" (View selected, Edit disabled); on the right a "Design" button with a palette
  icon (disabled), a 3-way icon segmented control for Desktop / Tablet / Mobile width,
  and a history clock icon button.
- Main canvas area with a light grey backdrop. Centered in it: a small indigo-tinted
  rounded square with a dashboard icon, the heading "Describe what you want to build",
  the paragraph "Type below and the assistant drafts an interface from your data. You
  review it before anything is saved, then keep shaping it by talking or by editing it
  directly.", and a 2x2 grid of clickable example-prompt cards:
  "Create a sales dashboard with revenue, orders and monthly sales."
  "Compare sales across regions with a chart and a table."
  "Show revenue by product as a donut chart with key metrics."
  "Build a feedback form with name, email and comments."
- Docked at the bottom, full width of the main area: the assistant command bar. A single
  rounded input, max width 768px, centered, placeholder "Describe what you want to
  build…", with a small chevron-up button (show conversation) and a square indigo send
  button with an up-arrow.

The command bar is a slim control surface, not a chat window. Neutral palette, one indigo
accent, no illustrations.
```

---

## Screen 4 — Workspace, view mode (the main screen)

```
Design the main screen of "Generative UI": a workspace showing an AI-generated dashboard
in view mode. The generated interface must dominate the screen.

Layout:
- Left sidebar, 224px: logo "Generative UI", nav "Workspaces" and "Settings", "RECENT"
  list with "Sales Dashboard" highlighted, user email and sign-out icon at the bottom.
- Top toolbar, 48px, white: back arrow; workspace name "Sales Dashboard"; a small grey
  version badge "v4". Centre: segmented control "View | Edit" with View selected. Right:
  "Design" button with palette icon; Desktop / Tablet / Mobile icon segmented control
  (Desktop selected); a history clock icon button.
- Canvas: a light grey backdrop (#ECECEF) with one large rounded white frame inside it
  holding the generated dashboard. Sample content inside the frame:
  - Page title "Sales Dashboard", subtitle "Q3 2025 performance".
  - A row of four metric cards: "Revenue ₹17.66M", "Orders 1.65K", "Avg. order value
    ₹10.74K", "Top region North".
  - A row with a line chart card "Monthly revenue" (7 of 12 columns) and a donut chart
    card "Revenue by product" with a legend (5 of 12 columns).
  - A "Region" dropdown filter set to "All".
  - A table card "Sales by region" with columns Region, Revenue, Orders and four rows.
- Assistant dock at the bottom of the main area: a centered rounded command input, max
  width 768px, placeholder "Describe a change, or ask to go back to a version…", a
  chevron-up button, an indigo send button. Under it a row of small pill suggestions:
  "Make it dark", "Put the chart above the table", "Add a region filter", "Use a more
  compact design", "Undo the last change".
- A small success toast top-right: "Saved as version 4."

The dashboard inside the frame uses a clean blue-and-white theme; the editor around it is
neutral grey with an indigo accent, so the two are visually distinct. No clutter.
```

---

## Screen 5 — Proposal awaiting approval (preview)

```
Design the "proposal preview" state of the "Generative UI" workspace. The user typed
"Make it dark" and the assistant has proposed a change that is NOT saved yet.

Keep the same shell: left sidebar, 48px top toolbar ("Sales Dashboard", badge "v1",
"View | Edit" segmented control, a disabled "Design" button, device width toggle, history
icon).

Differences:
- Directly under the toolbar, a full-width banner in soft indigo (#EEF2FF) with an eye
  icon and the text "Proposed changes — a preview. Nothing is saved until you apply it."
  On the right of the banner: a primary button "Apply" and a secondary button "Exit
  preview".
- The canvas frame now shows the same sales dashboard in a dark theme (deep navy
  background, dark cards, light text, blue accents) so it is obvious this is a preview of
  the result. One or two components have a dashed accent outline to show they are
  affected.
- Above the command input in the bottom dock, a proposal card (white, 1px border, 8px
  radius): a sparkle icon, the assistant's sentence "I'll change the theme to slate
  dark.", and a small indigo badge "Changes" on the right. Below it a label "2 proposed
  changes" and a checklist where each row has a checkbox, a number and a summary:
  "1. Change theme to slate_dark" (checked) and "2. Resize “Monthly revenue” to 12 of 12
  columns wide" (unchecked, shown struck through and greyed). Then a button row: "Hide
  preview" (eye-off icon), primary "Apply 1 of 2", ghost "Reject", and on the far right
  the muted note "Not saved until you apply".

Also show a small variant of the proposal card for a version restore: text "I'll restore
version 3. The versions after it stay in the history.", badge "Restore version", a short
change list ("Bar chart “Sales by region” replaced with table"), and buttons "Preview",
primary "Restore version 3", "Reject".

And a one-line "working" state for the dock: a pulsing indigo dot with "Writing the
changes… (1,240 characters)".
```

---

## Screen 6 — Edit mode with inspector

```
Design the edit mode of the "Generative UI" workspace, where the user manipulates the
generated dashboard directly.

Shell: left sidebar; top toolbar with "Sales Dashboard", version badge "v6" and an amber
badge "2 unsaved changes"; centre segmented control "View | Edit" with Edit selected;
right side: undo and redo icon buttons, a divider, "Design" button, device width toggle,
history icon, then a ghost "Discard" button and a primary indigo "Save version" button.

Canvas (narrower because a right panel is open): the sales dashboard with one component
selected, the "Monthly revenue" line chart. The selected component has a solid 2px indigo
outline, a small indigo label tab on its top-left reading "Chart · monthly_revenue_chart"
with a drag grip icon at its left, a pill-shaped resize handle centered on the right edge
and another centered on the bottom edge. Another component shows a faint dashed outline as
if hovered.

Right panel, 320px, white, titled "Inspector" with a close icon. Sections separated by
hairlines, each with an 11px uppercase label:
- "CHART": breadcrumb "Page › Monthly revenue"; "Id monthly_revenue_chart" in a monospace
  chip; a button with a sparkle icon "Ask the assistant about this".
- "LAYOUT": a slider labelled "Width — 7 of 12 columns"; a row of five small toggle
  buttons "3/12", "4/12", "6/12", "8/12", "Full"; a "Height" dropdown set to "md"; two
  buttons "↑ Earlier" and "↓ Later".
- "STYLE": dropdown "Tone" (Default) and dropdown "Emphasis" (Default).
- "CONTENT": text input "Title" with "Monthly revenue"; dropdown "Chart type" set to
  "line".
- A red ghost button with a trash icon: "Delete component".

Bottom dock: the command input shows a small indigo chip above the text field, "About
monthly_revenue_chart ✕", with the placeholder "Describe a change to the selected
component…". Suggestion pills: "Make this half width", "Move this to the top", "Remove
this". Above the input, a notice bar: "Save or discard your edits before asking the
assistant, so it works on what you see." with buttons "Discard" and "Save version".
```

---

## Screen 7 — Version history panel

```
Design the version history view of the "Generative UI" workspace.

Shell: left sidebar; top toolbar ("Sales Dashboard", badge "v5", "View | Edit" with View
selected, "Design", device toggle, history icon button in its active/pressed state).
The canvas shows the sales dashboard; the bottom assistant dock is visible with its
command input.

Right panel, 320px, white, titled "Version history" with a close icon. A vertical list of
versions, newest first, separated by hairlines. Each item has: "Version N" in semibold, a
one-line description, a muted meta line "source · relative time", and for non-current
versions a row of three small secondary buttons with icons: "Preview", "Compare",
"Restore".

Items:
- "Version 5" with an indigo "Current" badge and a 2px indigo left border. Description
  "Restored from Version 3". Meta "Restore · just now". No action buttons.
- "Version 4" — "Replace “Sales by region” with a bar chart" — "AI edit · 5 minutes ago".
- "Version 3" — "Move “Revenue” after “Top region”" — "AI edit · 12 minutes ago". This
  one is highlighted with a soft indigo background and a grey "Previewing" badge, and its
  first button reads "Stop preview".
- "Version 2" — "Change theme to slate_dark" — "AI edit · 20 minutes ago".
- "Version 1" — "Generated “Sales Dashboard”" — "AI generated · 1 hour ago".

Because Version 3 is being previewed, show a banner under the toolbar: "Version 3 —
read-only. Your current version is unchanged." with buttons "Compare with current",
primary "Restore this version", and "Back to current".

Make it clear that history is append-only: restoring adds a new version at the top
instead of removing later ones.
```

---

## Screen 8 — Dialogs and popovers (one board)

```
Design a board of four overlays for "Generative UI", a professional workspace tool. Each
is shown over a dimmed app background. White surfaces, 12px radius, 1px border, soft
shadow, indigo #4F46E5 primary buttons, neutral secondary buttons.

1) Compare versions dialog (560px wide). Title "Version 1 → Version 5". Subtitle "What is
different in the current version compared with version 1." A label "3 changes" and a list
where each row has a small outline icon and a sentence: "Theme changed from light to
dark", "Colour palette changed", "Items reordered in “Sales Dashboard”". Footer button
"Close".

2) Restore confirmation dialog (420px). Title "Restore version 3?". Text "A copy of that
version becomes the newest version and the current one. Nothing in the history is changed
or removed." Buttons "Cancel" and primary "Restore".

3) Version conflict dialog (420px). Title "Workspace changed". Text "This workspace is
now at version 8, saved from somewhere else. Your change was not saved, and nothing was
overwritten. Reload the latest version to continue; unsaved edits and the pending
proposal will be discarded." Buttons "Keep looking" and primary "Reload latest version".

4) Design popover (320px, anchored under a "Design" toolbar button). Three sections with
11px uppercase labels:
- "THEME": a 2-column grid of six selectable chips, each with a small two-tone circular
  swatch and a name: "Blue & White" (selected, indigo border), "Slate Dark", "Emerald",
  "Violet Night", "Mono Minimal", "Warm Sand".
- "DESIGN SYSTEM": a radio list with name and one-line description: "Modern Minimal —
  Flat surfaces, hairline borders, medium radius." (selected, with a check), "Soft",
  "Material", "Compact Pro", "Editorial".
- "COMPONENT FRAMEWORK": a radio list: "shadcn/ui" (selected) and "Material", followed by
  the muted note "Switching framework re-renders the same UI. Nothing is regenerated."
```

---

## Screen 9 — Settings

```
Design the Settings page of "Generative UI".

Layout: left sidebar (logo; nav "Workspaces" and "Settings" with Settings active;
"RECENT" list; user email and sign-out icon at the bottom) and a single scrolling column
of cards, max width 768px, with the page title "Settings". Each card is white, 12px
radius, 1px border, with a semibold title and a muted one-line description.

Cards in order:
1) "Appearance" — "How this application looks. Generated UIs have their own themes." A
   two-option segmented control: "Light | Dark".
2) "New workspaces" — "The look the first generated UI of a workspace starts with. It can
   be changed at any time." Three dropdowns in a row: "Theme", "Design system",
   "Component framework", each set to "Default".
3) "Frameworks" — "Adapters that can render a UI document. Switching between available
   ones never changes the document." A list with name, description and a status badge:
   "shadcn/ui" green badge "20 components"; "Material" green badge "9 components"; "MUI",
   "Mantine", "React Aria", "Aceternity UI" each with a grey badge "Planned".
4) "Runtime check" — "Whether this frontend can render everything the connected backend
   may generate." A two-column definition list: Backend (a URL in monospace), Schema
   version "2.0", Components "20 supported here · 20 registered on the backend",
   Operations (a comma-separated list in caps). Below it a green line with a check icon:
   "Frontend and backend agree on the UI vocabulary."
5) "Data" — "Datasets the assistant can build interfaces from. Charts, tables and metrics
   bind to them by name."
   - Sub-section "AVAILABLE DATASETS": rows with a monospace dataset name, a description,
     and a muted line of fields, e.g. "sales_by_region — Revenue and order totals per
     sales region." / "region (string) · revenue (number) · orders (number)". Show five
     or six rows including "support_tickets".
   - Sub-section "YOUR DATA SOURCES": one row "Support tickets", a grey badge "file
     upload", the dataset name, and a trash icon button.
   - A bordered form "Add a dataset from CSV or JSON": input "Name" (placeholder "Support
     tickets"); helper "The assistant will know it as support_tickets."; a monospace
     textarea "Rows (CSV with a header row, or a JSON list of records)" with sample CSV;
     a primary button "Add dataset" and a secondary button with an upload icon "Choose a
     file"; a muted footnote that REST API and PostgreSQL sources are registered through
     the API and their credentials stay on the server.

Neutral palette, hairline borders, indigo accent, compact and tidy.
```

---

## Screen 10 — Tablet and mobile preview widths

```
Design two variants of the "Generative UI" workspace showing the device-width preview.
The editor shell stays desktop-sized (left sidebar, 48px top toolbar, bottom assistant
command bar); only the canvas frame in the middle changes width, centered on a light grey
backdrop.

Variant A, "Tablet width" selected in the toolbar's device toggle: the canvas frame is
about 700px wide. Inside it the sales dashboard reflows: metric cards two per row, the
line chart and the donut chart each full width, then the "Region" filter and the "Sales
by region" table.

Variant B, "Mobile width" selected: the canvas frame is about 390px wide and tall, like a
phone. Everything stacks in one column: page title, four metric cards one under another,
the "Region" dropdown, the "Monthly revenue" chart, the "Revenue by product" donut chart,
then the table with horizontal scroll.

Show the dashboard in a dark theme in variant B to make clear the generated UI's theme is
independent of the neutral light editor around it.
```

---

## Optional — Marketing landing page

The app has no public landing page today: visitors go straight to sign-in. Use this only
if you want one; it would be new work.

```
Design a landing page for "Generative UI", a conversational workspace for building
interfaces. Tone: precise, confident, for product and data teams. Same restrained look as
the app: white and light grey, near-black text, one indigo accent #4F46E5, no gradients,
no stock illustrations.

Sections:
1) Top nav: logo "Generative UI", links "Product", "How it works", "Security", and
   buttons "Sign in" and primary "Get started".
2) Hero: headline "Describe the interface. Approve the change. Keep every version."
   Subhead: "An AI workspace that builds dashboards and forms from your data, as
   structured UI you can edit, theme and roll back. No generated code." Primary button
   "Create a workspace", secondary "See how it works". Below, a large product screenshot
   of the workspace: a sales dashboard on the canvas with the assistant command bar
   docked beneath it and a proposal card reading "I'll change the theme to slate dark."
   with "Preview", "Apply", "Reject".
3) Three feature columns with small outline icons: "Change it by talking" (move, resize,
   replace, restyle with plain instructions), "Nothing saves without you" (preview every
   proposal, accept or reject each change), "Every version kept" (preview, compare and
   restore; history is never rewritten).
4) "How it works" as four numbered steps in a row: Describe → Preview → Apply → Iterate.
5) A split section "Edit by hand too": screenshot of edit mode with a selected chart and
   the inspector panel; bullets for drag to reorder, resize on a 12-column grid, undo and
   redo.
6) "Built to be trusted": four short points — the AI produces a validated schema, never
   code; your data is bound, not copied; themes and frameworks change without rebuilding
   the UI; private workspaces per account.
7) Footer with product links and a small copyright line.
```
