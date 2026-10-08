# Generative UI Platform — Frontend

React + TypeScript single-page app: the workspace where a generated interface is viewed,
edited by hand and changed by talking to the assistant.

The app renders **data**. A UI document from the backend is validated, then drawn by this
codebase's own components. Nothing received from the model or the server is executed, and
nothing is injected as HTML or CSS.

## Stack

React 19 · TypeScript (strict) · Vite · React Router · TanStack Query (server state) ·
Zustand (editor state) · Zod (runtime validation) · Tailwind CSS 4 with CSS-variable design
tokens · Recharts (lazy-loaded) · dnd-kit · Radix primitives for dialogs and tabs.

## Setup

```bash
npm install
cp .env.example .env        # VITE_API_BASE_URL, default http://localhost:8000
npm run dev                 # http://localhost:5173
```

The backend must allow this origin (`CORS_ORIGINS`). Only `VITE_*` variables reach the
browser; never put a secret in them.

| Script | Does |
| --- | --- |
| `npm run dev` / `build` / `preview` | Vite |
| `npm run typecheck` | `tsc -b` |
| `npm run lint` | ESLint (also bans raw HTML rendering and `eval`) |
| `npm test` | Vitest unit and component tests |
| `npm run contract` | Re-export the backend contract and regenerate API types |
| `npm run e2e` | Browser journey against running services |

## Structure

```
src/
├── app/                    App, router, providers, shell
├── components/             The application's own UI primitives and feedback states
├── generative-ui/          The runtime that turns a UI document into React
│   ├── schema/             Zod validators, types, tree helpers, contract assertions,
│   │                       generated/ (OpenAPI + fixtures exported by the backend)
│   ├── mutation/           Operation types, engine, validator, descriptions
│   ├── history/            Undo/redo of unsaved edits, version helpers
│   ├── theme/              Tokens → CSS variables, colour maths, ThemeProvider
│   ├── registry/           Component, framework, theme, icon, effect and capability registries
│   ├── renderer/           ComponentRenderer, LayoutRenderer, runtime state, actions
│   ├── runtime/            In-app router, application runtime, declarative row selection
│   ├── assets/             Asset ids → URLs on the connected backend
│   ├── effects/            Hooks behind effect tokens (reveal, spotlight, parallax, counter)
│   ├── generative.css      Surfaces, typography, shell, effects — all from theme tokens
│   ├── components/
│   │   ├── semantic/       GMetric, GChart, GTable, GScreen, … (behaviour)
│   │   ├── patterns/       Hero, pricing, gallery, collection, kanban, record pages, …
│   │   ├── application/    The shell around screens (sidebar, top, bottom, minimal)
│   │   └── adapters/       shadcn/ (complete), material/ (partial) (looks)
│   └── workspace/          Canvas, editable element, layout engine, selection, toolbar
├── features/
│   ├── auth/               Sign-in page, route guard
│   ├── workspace/          Workspace page, canvas area, inspector, design menu, persistence
│   ├── chat/               Assistant dock, proposal card, operation and change previews
│   ├── version-history/    History panel, comparison dialog
│   ├── generation/         Empty state, suggestions, job follower, progress view
│   └── settings/           Preferences, runtime check, data sources
├── services/api/           Typed HTTP client, SSE stream reader, endpoint modules
└── stores/                 workspace, editor, chat, auth, preferences, toasts
```

## How it works

**State.** `workspaceStore` holds the saved version (`base`), the working copy with
undo/redo (`history`) and whatever is being previewed. Direct manipulation and the
assistant both change the working copy through one function, `applyOperations`, which
adopts a result only if it validates. Nothing about a workspace is kept in the browser;
`localStorage` holds preferences and the access token only.

**Applications.** A document whose page holds `screen` components and an `application`
section is an application. The canvas then shows one screen at a time inside a shell built
from `application.navigation`. Routes (`/jobs/:jobId`) are matched against the document at
run time (`runtime/router.ts`); the current path lives in the URL (`?at=`), so a reload
opens the same screen. Components bind to the application's entities by name, with
declarative `where` / `sort` / `group_by` / `limit` (`runtime/rows.ts`) — a record page is a
binding filtered by a route parameter. Navigation between screens is local and works in a
preview; record actions go to the backend and the rows that come back replace the dataset
for every component bound to it. Images are referenced by asset id and can only load from
the connected backend's asset endpoint.

**Building.** In an empty workspace an instruction starts a generation job
(`features/generation/followJob.ts` polls it). The canvas shows the stage, percentage and
sentence the server reports. Opening a workspace resumes a job still running, or offers
again a finished proposal that was never decided. The proposal card summarises the whole
application (screens, design, data, interactions, design review) with *Preview
application*, *Apply application*, *Regenerate* and *Reject*.

**Editing levels.** With an application open, an instruction goes with the screen on show
and any selected component, and the backend decides its scope: the whole application
(restyle), one screen (redesign, add) or components. The suggestions under the input name
all three.

**Proposals.** The assistant returns a proposal, never a saved change. *Preview* shows it
on a read-only canvas, *Apply* sends it to the versions API (which re-validates it),
*Reject* discards it. For edits, each operation can be kept or dropped; the preview is
recomputed locally with the mutation engine.

**Modes.** *View* is the live UI: controls work and actions run. *Edit* adds selection,
drag to reorder or move between containers, resize handles that snap to the 12-column grid
and height presets, an inspector, and keyboard editing (`Delete`, `Alt+←/→`). Actions never
run in edit or preview mode.

**Selection as context.** The selected component's id is sent with an instruction, so
"make this wider" is unambiguous.

**Versions.** The history panel previews any version read-only, compares it with the
current one (schema-based), or restores it — which appends a copy, never rewinds.

**Conflicts.** Every write names the version it started from. If the server has moved on,
a dialog offers to reload the latest version; nothing is overwritten.

**Frameworks and themes.** `design.framework` picks an adapter at render time; themes are
tokens turned into CSS variables scoped to the canvas, so the editor's own chrome is
unaffected. Switching either never changes the component tree.

### Adding things

| To add | Do |
| --- | --- |
| A framework | Implement a `FrameworkAdapter`, register it in `registry/frameworkRegistry.ts`, mark it available in the backend's `design_registry.py`. See `components/adapters/README.md`. |
| A component | Backend schema + registry first; then `npm run contract`, add the Zod schema, a semantic component, an adapter view, and a `componentRegistry` entry. The contract tests fail until all are present. |
| An operation | Backend model + engine handler; then mirror both in `mutation/`. Parity tests compare the two engines. |

## The contract with the backend

- `services/api/schema.d.ts` is generated from the backend's OpenAPI document.
- `schema/contract.ts` asserts at compile time that this app's document, theme, component
  types and operation types match those generated types.
- `tests/unit/schema.test.ts` and `mutationEngine.test.ts` run backend-exported fixtures:
  every component example must parse, and every mutation case must produce exactly the
  document the backend's engine produced.

Run `npm run contract` after any backend change to schemas, operations or endpoints.

## End-to-end run

Three scripts, all against the running stack:

- `npm run e2e` — a single view: the journey described below.
- `npm run e2e:app` — an application: one sentence → proposal with real progress → explore
  the preview → approve → navigate, open a record, move a card, submit a form → reload →
  redesign the dashboard (only it changes) → restyle the whole product (no screen changes) →
  restore the original → edit directly → change the navigation style → mobile width.
- `npm run e2e:showcase -- "<prompt>" …` — builds each prompt with whatever model the
  backend is configured with and photographs every screen. Asserts nothing; it is for
  judging design quality.

`tests/e2e/journey.mjs` drives the real stack in the Chrome installed on your machine
(sign up → generate → approve → theme → move → replace → reload → restore → compare →
framework switch → manual edit → conflict → filter → mobile → data upload → sign out/in).

```bash
# terminal 1: scripted model stand-in        (backend/)  poetry run python -m scripts.dev_llm
# terminal 2: API with GROQ_API_KEY=dev, GROQ_BASE_URL=http://127.0.0.1:8787, LLM_FALLBACK_PROVIDERS=groq
#                                            (backend/)  poetry run uvicorn app.main:app
# terminal 3: web app                        (frontend/) npm run dev
npm run e2e          # E2E_BASE_URL / E2E_API_URL override the defaults
```

The journey uses the stand-in so it is deterministic; with a real model the wording of
replies and exact operations vary.

## Accessibility

Landmarks and labelled regions, a skip link, focus-visible outlines, labelled form
controls, focus-trapped dialogs, tables with headers and captions, `role="img"` summaries
for charts, live regions for toasts and progress, keyboard-operable selection and editing,
`prefers-reduced-motion` respected. Theme validation rejects text/background pairs below
WCAG AA contrast.

## Known limitations

- **Drag and drop** moves a component among siblings or onto a component in another
  container; there is no free-form canvas positioning by design (layout is a flow grid).
- **Charts** in jsdom tests render without dimensions; chart drawing is verified in the
  browser journey.
- **REST and PostgreSQL data sources** are registered through the API; the settings page
  offers CSV/JSON upload only.
- **Form submissions** are stored and exposed by the API; there is no screen listing them.
- **Kanban drag and drop** uses native drag events (mouse); touch and keyboard users move a
  card with its "Move to …" button.
- **A rejected first build** is offered again after a reload (the server keeps the finished
  job; "rejected" is not recorded).
- **Pattern components are framework-neutral.** The two adapters restyle the primitives
  (cards, buttons, inputs, tabs…); heroes, boards and the like follow the theme tokens only.
- **Bundle size**: the main chunk is ~225 kB gzipped; charts and the editor are split out.
