# Architecture

How a sentence typed by a user becomes interface on screen, and what guarantees hold along
the way.

```
User → AI → UI operations → Validation → UI state → Versioning → PostgreSQL → React renderer
```

## 1. The one piece of state: the UI document

A workspace's interface is one document. Everything — the assistant, the editor, version
history — reads and writes this same structure.

```jsonc
{
  "schema_version": "2.0",
  "page":   { "type": "page", "id": "page", "title": "...", "components": [ ... ] },  // WHAT
  "theme":  { "mode": "light", "colors": { "primary": "#2563EB", ... }, "radius": "md", ... },
  "design": { "framework": "shadcn", "design_system": "modern_minimal" }              // HOW
}
```

- **`page`** is a tree of semantic components (`metric`, `chart`, `table`, `form`, …). It is
  framework-agnostic: nothing in it names a UI library.
- **`theme`** is design tokens. Colours are `#RRGGBB` only; everything else is an enum.
- **`design`** selects the framework adapter and the design system (shape/typography preset).

Changing `theme` or `design` never touches `page`. That is what makes "make it dark" or
"use a Material style" a change of configuration rather than a regeneration.

Every component has:

| Field | Purpose |
| --- | --- |
| `id` | Stable, unique, descriptive (`revenue_metric`). How users, the assistant and the editor refer to it. Never an index. |
| `type` | One of the registered component types. |
| own fields | Typed per component; unknown fields are rejected. |
| `layout` | `{span: 1–12, height: auto|sm|md|lg|xl}` — intent, not pixels. |
| `style` | `{tone, emphasis}` — token names, not CSS. |
| `data_source` | A binding to a dataset by name (charts, tables, metrics). |
| actions | `{type, payload}` naming an allowlisted backend action. |
| `visible_when` | A declarative condition on a form control. |

**Layout** is a 12-column flow grid in every container: children fill left to right and
wrap. A component's `span` is its width; order is position. There are no x/y coordinates,
so components cannot overlap and the same document works at any width (the layout engine
collapses spans on small canvases).

**Data** is never stored in a document. Components bind to datasets; the backend resolves
the rows whenever a document is served and sends them next to it (`data: {dataset: rows}`).
A saved version is therefore pure design, and figures always come from the data layer.

Source of truth: `backend/app/domains/generative_ui/{schemas,document}.py`. Mirror:
`frontend/src/generative-ui/schema/validators.ts`.

## 2. The mutation language

Small changes are never made by regenerating the document. They are **operations**:

| Operation | Effect |
| --- | --- |
| `CREATE` | Add a component (`parent_id`, and at most one of `before` / `after` / `index`). |
| `DELETE` | Remove a component and its children. |
| `MOVE` | Reorder among siblings or move into another container/tab. |
| `RESIZE` | Change `span` and/or `height`. |
| `STYLE` | Set or clear style tokens. |
| `UPDATE` | Shallow-merge a component's own fields (`null` removes). Cannot touch id, type, layout, style or children. |
| `REORDER` | Set the complete order of a container's children. |
| `GROUP` / `UNGROUP` | Wrap siblings in a section/card, or dissolve one. |
| `REPLACE` | Swap a component in place (e.g. table → chart, keeping the binding). |
| `SET_THEME` | A preset and/or token patch. |
| `SET_FRAMEWORK` / `SET_DESIGN_SYSTEM` | Change `design` (and the design system's shape tokens). |

The assistant may also return one of two **version operations**, which are requests to the
version engine rather than edits: `RESTORE_VERSION` and `COMPARE_VERSIONS`.

There are **two engines with identical semantics**, both working on plain JSON:

- `backend/.../mutation_engine.py` — authoritative; runs before anything is persisted.
- `frontend/.../mutation/mutationEngine.ts` — instant feedback for direct manipulation,
  per-step previews of proposals.

They are kept identical by test: the backend exports mutation cases with the results its
engine computed, and the frontend engine must reproduce them exactly.

Direct manipulation and the assistant produce the *same operations*. Dragging a card and
saying "move the revenue card" both end as a `MOVE`.

## 3. From instruction to proposal

```
POST /ui/generate[/stream]           POST /ui/mutate[/stream]
(no UI yet, or a full redesign)      (change the current UI)
        │                                    │
  intent (LLM) ─► plan (domain)        one LLM call with: current document, layout map,
        │                              selected component, version history, datasets
  retrieve data                              │
        │                                    ▼
  generate (LLM) ──────────────►  parse ─► schema ─► apply (engine) ─► validate document
        │                                    │ fail: send findings back (bounded repairs)
        ▼                                    ▼
                  ProposalRead  (nothing saved)
```

Validation pipeline (`validator.py`, `semantic_rules.py`, `mutator.py`):

| Stage | Rejects |
| --- | --- |
| JSON parsing | Non-JSON, `NaN`/`Infinity` |
| Schema | Unknown component/operation types, unknown or missing fields, wrong types, bad ids, non-hex colours |
| Operation | Unknown targets, moving a container into itself, incomplete reorders, protected fields |
| Registry | Components or actions not registered, unavailable frameworks, unknown design systems |
| Semantic | Duplicate ids, unknown datasets/fields, components with no data, dangling action targets, unsafe navigation, markup or script URLs in text, unreadable theme contrast, excessive size/depth |

A **proposal** is the validated result plus everything needed to review it: the resulting
document, its data, per-operation summaries, a schema-based list of changes, and the ids of
affected components. It is not stored. The streaming variants send `progress` events
(stage and character count — never partial content) and then the same proposal.

## 4. Approval and the version engine

```
proposal ── Preview (read-only canvas) ── Apply ──► POST /workspaces/{id}/versions
                                    └── Reject ──► discarded; nothing changed
```

`VersionService` (`versioning.py`) is the only code that changes what a workspace's UI is:

1. Lock the workspace row (`SELECT … FOR UPDATE`).
2. **Stale check**: the request's `base_version_id` must equal the workspace's current
   version, otherwise `409 VERSION_CONFLICT` and nothing is written.
3. Re-validate from scratch: apply the operations to the base version (or validate the
   whole document). Client input is never trusted because it came from a proposal.
4. Append a `ui_versions` row (number = previous + 1, `parent_version_id` = base) and point
   `workspaces.current_version_id` at it.

Versions are **immutable**: the repository has no update or delete, and a database trigger
rejects updates to a version's content. **Restore** appends a copy of the old version as
the newest one — history is `V1 → … → V7 → V8(copy of V3)`, never rewound.

**Compare** is a schema-based diff (`diff.py`) by stable component id: theme, framework,
added, removed, replaced, moved, resized, restyled, updated.

The editor's **undo/redo** is separate: an in-memory stack of unsaved operations on the
working copy, cleared when a version is saved or loaded.

## 5. Rendering

```
UI document
   └─ ThemeProvider        tokens → CSS variables (--g-*), scoped to the canvas
       └─ RendererProvider  adapter for design.framework, data rows, runtime state, actions
           └─ ComponentRenderer   type → component registry → semantic component (GChart, …)
               └─ adapter view    presentational component of the active framework
```

- **Semantic components** (`components/semantic/G*.tsx`) own behaviour: read the node,
  resolve data, wire actions.
- **Adapters** (`components/adapters/<framework>/`) own looks only. `shadcn` is complete;
  `material` overrides some components and falls back for the rest. Adding a framework is
  adding an adapter — the document, the engine and the prompts do not change.
- A component type with no registry entry renders a placeholder; nothing from it is
  interpreted. Text is always rendered as text. There is no `dangerouslySetInnerHTML`, no
  `eval`, no injected CSS (enforced by lint rules).
- Unchanged subtrees keep their object identity across edits, so only edited components
  re-render.

**Actions** in a generated UI (`filter`, `sort`, `refresh`, `export`, `navigate`, `submit`,
`search`, `generate`) are requests to `POST /actions/execute`. The backend runs only
registered handlers with typed payloads. `generate` hands an instruction to the assistant,
which returns a proposal like any other.

## 6. Persistence and identity

```
PostgreSQL → API → TanStack Query cache → workspace store → renderer
```

Loading a workspace: fetch workspace → fetch current version → validate schema → hydrate
store → render. The browser keeps only preferences and the access token in `localStorage`;
no workspace content.

| Table | Holds |
| --- | --- |
| `users` | Email, scrypt password hash |
| `workspaces` | Owner, title, `current_version_id` |
| `ui_versions` | Immutable versions: page, theme, design, description, source, provenance, parent |
| `conversations` | Messages, with the proposal each assistant reply described |
| `ui_actions` | Audit log of executed actions (form submissions are read from here) |
| `data_sources` | Registered sources; configuration without secrets |

Access: every request carries a bearer token; workspaces and data sources are scoped to
their owner (someone else's workspace is a 404). Secrets for data sources live in the
server's environment and are referenced by name.

## 7. Failure model

Every failure a client sees is `{success: false, error: {code, message, request_id, details?}}`
with a stable `code`. Lower layers translate at the source (`core/exceptions.py`):

| Source | Becomes |
| --- | --- |
| Integrity violation | `409 CONFLICT` (or `VERSION_CONFLICT`, `EMAIL_ALREADY_REGISTERED`) |
| Database unreachable / pool exhausted | `503 DATABASE_UNAVAILABLE` + `Retry-After` |
| Other database errors | `500 DATABASE_ERROR` (detail only in logs) |
| LLM timeout / 429 / 5xx / transport | retried with backoff, then next provider |
| LLM 401/403, bad request, unusable body | not retried; next provider |
| All providers failed | `502 LLM_ALL_PROVIDERS_FAILED` with each provider's failure kind |
| Model output invalid after repairs | `502 UI_SCHEMA_INVALID` with the validator's findings |
| Data source unreachable | `502 DATA_SOURCE_ERROR` |
| Bad/expired token | `401 INVALID_TOKEN` / `TOKEN_EXPIRED` |
| Over budget | `429 RATE_LIMIT_EXCEEDED` + `Retry-After` |
| Anything unexpected | `500 INTERNAL_ERROR`, stack trace in logs only |

The frontend never leaves the canvas half-updated: operations are applied to a copy and
adopted only if the result validates; an invalid version or proposal is reported, not
rendered; a stale write opens a "workspace changed — reload latest?" dialog.

## 8. Applications

An application is not a second system. It is the same UI document with two additions, so
versioning, diffing, validation and the mutation engine apply unchanged.

```
UIDocument
├── page.components: [ screen, screen, … ]      a screen = id, title, route, width, children
├── theme, design                                as before, with more tokens
└── application                                  absent for a single view
    ├── name, category, description, target_users, goals, features
    ├── navigation   style (sidebar|topbar|bottom|minimal|none), brand, home, items, action
    ├── entities     name, fields, sample records      ← the data model, shared by screens
    ├── interactions what a user can do, and where
    ├── assets       id → an image stored by this backend (never an external URL)
    └── design_direction   style, mood, imagery, layout, effects, and why
```

**From a sentence to an application.** `POST /generation/jobs` runs a pipeline of
specialised stages, each a small model call with a strict schema and a repair loop:

```
understand ─► ApplicationPlanner ─► DesignDirector ─► DataPlanner ─► ScreenPlanner
   (blueprint: screens, features)   (style, palette,   (entities,    (per screen: purpose,
                                     navigation, mood)  records)      patterns, content)
        ─► AssetPlanner ─► InteractionPlanner ─► ScreenGenerator × N ─► assemble
           (image briefs)   (actions, routes)     (one screen each,      (ids, navigation,
                                                   validated alone)       assets, entities)
        ─► DesignQualityEvaluator ─► bounded refinement ─► validate ─► proposal
```

No stage emits code, HTML or CSS: every output is parsed into a schema whose only free
text is content. Design decisions are tokens and names from registries the platform owns:

| Registry | Holds | Used by |
| --- | --- | --- |
| Component registry | 41 types: primitives, `screen`, and patterns with variants | validator, prompts, renderer |
| Pattern registry | `hero.split`, `collection.feed`, `kanban`, … with when-to-use notes and example compositions | deterministic retrieval per screen type and brief |
| Design registry | 19 visual styles (tokens, mood, imagery, effects, suitable palettes and navigation), 20 palettes, icons, effects | DesignDirector, restyle edits, Design menu |
| Action registry | allowlisted actions incl. `navigate`, `record_create/update/delete` | InteractionPlanner, action executor |

Different products look different because the DesignDirector picks a style, palette,
navigation, imagery and effects for the product in front of it, and the ScreenPlanner
picks patterns and variants per screen from what was retrieved — there are no page
templates to fall back on. The design review is deterministic (hierarchy, repetition,
empty or placeholder content, uniform grids, broken links, unused data) and its findings
drive at most `APP_REFINEMENT_PASSES` rounds of screen regeneration.

**Images.** The AssetPlanner writes briefs (subject, style, usage); the asset service
resolves each through an `ImageProvider` — generate, search, or built-in artwork — stores
the bytes, and the document refers to the result by asset id. A provider failing falls
through to the next and finally to built-in artwork, so an image never breaks a build.

**Failure.** Stages retry with the validator's findings; rate limits are waited out. A
screen that cannot be generated becomes a marked placeholder and can be generated again on
its own. If nothing usable results, the job fails with the standard error body and no
version is created. Jobs are rows (`generation_jobs`); progress is written by the pipeline
as it happens; a restart marks unfinished jobs failed.

**Editing an application** is routed by scope before any model call that writes UI:

| Scope | Example | What happens |
| --- | --- | --- |
| Application | "Make the entire application more premium" | `SET_DESIGN_SYSTEM` + `SET_THEME` + `UPDATE_APPLICATION`; no screen is touched |
| Screen | "Redesign the dashboard", "Add a settings screen" | one screen is generated and `REPLACE`d, or `CREATE`d with `UPSERT_ENTITIES` and `SET_NAVIGATION` |
| Component | "Make this half width" | ordinary operations, with only the screen on show in the prompt |

**Running it.** The frontend matches the current path against the screens' routes, renders
that screen inside the shell, evaluates bindings (`where` by value or route parameter,
`sort`, `group_by`, `limit`) and dispatches actions. Navigation is local. Record actions
are executed by the backend against the entity's schema and stored in `workspace_records`,
an overlay on the version's sample records: versions stay immutable, and using an
application never creates one.

## 9. Product invariants and where they are enforced

| Invariant | Enforced by |
| --- | --- |
| The model never produces executable code | Strict schemas (no free-form fields), semantic content rule, prompts; lint bans raw HTML/eval in the frontend |
| The UI schema is framework-agnostic | `design.framework` is the only reference to a framework; adapters live only in the frontend |
| Components have stable ids | Schema pattern + uniqueness rule; engine addresses by id only |
| Approved changes create immutable versions | `VersionService` appends; repository has no update; database trigger |
| Restoring creates a new version | `VersionService.restore` |
| Edits are structured mutations | `/ui/mutate` returns operations; one model call, no regeneration |
| Both sides validate mutations | `mutationValidator.ts` and `DocumentMutator` |
| The browser is not the source of truth | Stores are hydrated from the API; e2e asserts `localStorage` holds no content |
| Framework/theme changes keep the UI | Engine handlers for `SET_*` never touch `page`; tested on both sides |
| Stale writes are rejected | `ensure_current` under a row lock; unique `(workspace_id, version_number)` |
| An application's screens stay connected | Semantic rules: unique routes, navigation and `navigate` targets must exist, deleting a screen prunes navigation |
| Images come only from this backend | Asset URL pattern in both schemas; ids must be listed in `application.assets` |
| A partial failure never saves a broken version | Per-screen validation, placeholders, final validation before the proposal |
| Using an application never rewrites history | Record overlay per workspace; versions untouched |
| Reference code (third-party components and the design vocabulary) is never run | `reference_components` is read only by `/references`; no pipeline stage, prompt or renderer imports it |
| Unknown components/actions are rejected | Discriminated unions, registries, action allowlist |
