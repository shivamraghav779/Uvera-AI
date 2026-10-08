# Generative UI Platform

A conversational workspace where you describe a product — *"Build me a modern AI recruitment
SaaS"* — and get a working, multi-screen application: navigation, connected screens, realistic
data, images and interactions, in a visual style chosen for that product. The assistant
proposes it as **structured data**, and you keep shaping it by talking (to the whole
application, one screen or one component) or by editing it directly. Every approved change
becomes an immutable version you can preview, compare and restore.

The model never writes code. It writes a UI document and operations on that document; the
platform validates them and renders them with its own components.

```
User ── natural language / direct manipulation
          │
          ▼
   Assistant (LLM)  ──►  UI document  or  operations  (data, never code)
          │
          ▼
   Validation  (schema → registries → semantic rules; backend is authoritative)
          │
          ▼
   Proposal ── preview ── approve ──►  Version engine ──►  PostgreSQL (immutable versions)
          │
          ▼
   Renderer:  UI document → component registry → framework adapter → React
```

| Part | What it is | Docs |
| --- | --- | --- |
| [`backend/`](backend/) | FastAPI, async SQLAlchemy, PostgreSQL. Auth, AI orchestration, validation, versioning, data access. | [backend/README.md](backend/README.md) |
| [`frontend/`](frontend/) | React + TypeScript + Vite. Workspace editor, renderer, mutation engine, adapters. | [frontend/README.md](frontend/README.md) |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | How a request becomes UI, the contracts between the two sides, and where each product invariant is enforced. | |
| [`docs/DESIGN.md`](docs/DESIGN.md) | The application's visual design reference, and how palettes for generated UIs are chosen. | |

## Quick start

Requirements: Python 3.12+, [Poetry](https://python-poetry.org/) 2, Node 20+, PostgreSQL 14+.

```bash
# 1. Backend
cd backend
poetry install
cp .env.example .env              # set GROQ_API_KEY and/or COHERE_API_KEY, and SECRET_KEY
createdb generative_ui            # or: docker compose up -d db
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload            # http://localhost:8000/docs

# 2. Frontend (second terminal)
cd frontend
npm install
cp .env.example .env
npm run dev                                          # http://localhost:5173
```

Open http://localhost:5173, create an account, create a workspace and type
*"Build me a modern AI recruitment SaaS."* (a whole application) or
*"Create a sales dashboard with revenue, orders and monthly sales."* (a single view).

Upgrading an existing checkout: run `poetry run alembic upgrade head` again (migration
`0004` adds applications, their data, images and generation jobs).

Images for generated applications are generated or searched for by the backend through
keyless public services by default (Pollinations, Openverse), which means the image
*descriptions* the pipeline writes are sent to them. Set `IMAGE_GENERATION_PROVIDER=none`
and `IMAGE_SEARCH_PROVIDER=none` in `backend/.env` to keep everything local; images then
become built-in abstract artwork.

Or everything in containers: `cd backend && docker compose up --build`.

### No API key? Use the scripted stand-in

`backend/scripts/dev_llm.py` imitates the Groq API for a fixed set of phrases so the whole
product can be exercised offline. It is **not** a model.

```bash
cd backend && poetry run python -m scripts.dev_llm          # 127.0.0.1:8787
# in backend/.env:  GROQ_API_KEY=dev   GROQ_BASE_URL=http://127.0.0.1:8787
```

## Checks

```bash
# backend
cd backend
poetry run pytest                         # unit + integration (integration needs PostgreSQL)
poetry run ruff check app tests scripts && poetry run mypy

# frontend
cd frontend
npm run typecheck && npm run lint && npm test && npm run build

# end to end in a real browser (services running; see frontend/README.md)
npm run e2e          # a single view: generate, edit, version, restore
npm run e2e:app      # an application: build, use, reload, redesign, restyle, restore
```

## Keeping the two sides in step

The backend owns the contract. After changing schemas, operations, registries or endpoints:

```bash
cd frontend && npm run contract
```

This exports the OpenAPI document and contract fixtures from the backend and regenerates the
TypeScript API types. If the vocabularies have drifted, the frontend stops compiling
(`schema/contract.ts`) or its contract tests fail — including cases whose expected results
were computed by the backend's mutation engine.

## What is and is not here

Implemented: application generation as a background job with real progress stages and
resume after reload (product blueprint → design direction → data model → screen plans →
images → screens → design review and bounded refinement), 41 component types including
designed patterns (hero, feature grid, pricing, kanban, record pages, …), 19 visual styles,
20 palettes, effects and motion as tokens, an image engine with provider fallback, in-app
routing, record actions, three editing levels (application, screen, component), accounts
(email + password, bearer tokens), per-user workspaces, rate limiting,
generation and edits through proposals, live progress streaming, immutable versions with
restore and compare, stale-write protection, direct manipulation, token themes, two framework
adapters, uploaded/REST/SQL data sources, Groq and Cohere with retries and fallback.

A local **reference component library** (`backend/README.md`, "Reference component
library") holds the source of open-source UI components (UI Layouts, Magic UI, Bootstrap; optionally
21st.dev through its API) for people extending the pattern set, together with the
project's own **design vocabulary**: 500 UI patterns, 500 effects and six combination
recipes, each as runnable, browser-checked HTML/CSS/JS. It is never rendered or
shown to the model.

Not here yet (the seams exist, the features do not): designing from a reference screenshot,
and semantic (embedding) retrieval of patterns — pattern retrieval is deterministic, by
screen type and keywords.

Known limits are listed honestly in each README ("Known limitations").
