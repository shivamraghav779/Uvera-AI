# Generative UI Platform — Backend

FastAPI service that owns everything the platform must be able to trust: accounts,
persistence, AI orchestration, validation, versioning, data access and action execution.

The language model never produces code. It produces a **UI document** or **operations** on
one; both are validated here before they are returned, and again before they are saved.
See [../docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) for the full picture.

## Layers

| Layer | Lives in | Knows about |
| --- | --- | --- |
| API | `app/api`, `app/middleware` | HTTP, status codes, dependency wiring, SSE. No business logic. |
| Domain / application | `app/domains` | Use cases, the UI schema, mutation engine, validation, versioning. Depends on interfaces. |
| Infrastructure | `app/ai/llm`, `app/ai/search`, `app/database`, repositories, data providers | Groq, Cohere, Google, PostgreSQL, external data. |

`app/api/dependencies.py` is the composition root.

```
app/
├── main.py                 Application factory, middleware order, lifespan
├── core/                   Settings, exceptions, logging, security (hashing, tokens), rate limiting
├── api/                    Routers (v1), envelopes, dependency wiring, SSE streaming
├── domains/
│   ├── users/              Accounts and sign-in
│   ├── workspaces/         A persistent UI and its pointer to the current version
│   ├── conversation/       Messages
│   ├── generative_ui/      UI document, registries, operations, mutation engine, validator,
│   │                       diff, version engine, proposal service
│   ├── actions/            Action allowlist, handlers, audit log, form submissions
│   └── data_sources/       Registered sources and the providers that read them
├── ai/
│   ├── llm/                LLMProvider, Groq, Cohere, retries, fallback chain, factory
│   ├── prompts/            Versioned prompts (intent, generation, mutation)
│   ├── orchestration/      Generation agent, mutation executor, completion with progress
│   └── search/             SearchProvider, Google
├── database/               Engine/session, declarative base, model registry
└── middleware/             Request id, request logging, error translation
scripts/
├── export_contract.py      OpenAPI + contract fixtures for the frontend
└── dev_llm.py              Scripted stand-in for the Groq API (not a model)
```

## Setup

```bash
pipx install poetry && poetry install
cp .env.example .env            # see "Configuration"
createdb generative_ui          # or: docker compose up -d db
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

Docs: `http://localhost:8000/docs` (Swagger), `/redoc`, `/openapi.json`.

### Configuration

All settings come from the environment (`.env` in development; see `.env.example`).

| Variable | Meaning |
| --- | --- |
| `APP_ENV` | `development`, `test`, `staging`, `production` |
| `DATABASE_URL` | `postgresql+asyncpg://…` |
| `AUTH_REQUIRED` | Require sign-in. Must be `true` in production. `false` gives one shared anonymous user (local development). |
| `SECRET_KEY` | Signs access tokens. Mandatory (32+ chars) in production. |
| `RATE_LIMIT_PER_MINUTE`, `AI_RATE_LIMIT_PER_MINUTE`, `AUTH_RATE_LIMIT_PER_MINUTE` | Per-caller budgets; `0` disables. |
| `DEFAULT_LLM_PROVIDER`, `LLM_FALLBACK_PROVIDERS` | `groq` / `cohere`; fallbacks tried in order. |
| `GROQ_API_KEY`, `GROQ_MODEL`, `COHERE_API_KEY`, `COHERE_MODEL` | Provider credentials and models. |
| `LLM_MAX_RETRIES`, `LLM_RETRY_BACKOFF_SECONDS` | Retries per provider for transient failures. |
| `LLM_MAX_REPAIR_ATTEMPTS` | How often invalid model output is sent back with the validator's findings. |
| `DATASOURCE_SECRET_<NAME>` | Secret behind a data source's `credentials_ref`. |
| `ENABLE_MOCK_DATA` | Demo sales dataset; refused in production. |
| `GOOGLE_API_KEY`, `GOOGLE_SEARCH_ENGINE_ID` | Optional; enables the `search` action. |

Production refuses to start with unsafe settings (no secret key, auth off, mock data,
prompt logging, private-host data sources).

**Models change.** Providers retire model ids; a retired id answers `404` and the fallback
takes over. Check `GET https://api.groq.com/openai/v1/models` and set `GROQ_MODEL`
accordingly.

## API

Base path `/api/v1`. Every response is `{"success": true, "data": …}` or
`{"success": false, "error": {"code", "message", "request_id", "details"?}}` and carries
`X-Request-ID`. Protected routes need `Authorization: Bearer <token>`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness and database status (public) |
| GET | `/auth/config` | Whether sign-in is required (public) |
| POST | `/auth/register`, `/auth/login` | Create an account / sign in → access token |
| GET | `/auth/me` | Current user |
| GET, POST | `/workspaces` | List / create |
| GET, PATCH, DELETE | `/workspaces/{id}` | Read / rename / delete |
| GET | `/workspaces/{id}/versions` | Version history, newest first |
| POST | `/workspaces/{id}/versions` | **Persist an approved change** (document or operations) |
| GET | `/workspaces/{id}/versions/{vid}` | A version's document and data |
| POST | `/workspaces/{id}/versions/{vid}/restore` | Restore (appends a copy) |
| GET | `/workspaces/{id}/versions/{vid}/compare?with=` | Schema-based diff |
| GET, POST | `/workspaces/{id}/messages` | Conversation |
| GET | `/workspaces/{id}/submissions` | Stored form submissions |
| POST | `/ui/generate`, `/ui/generate/stream` | Propose a new UI |
| POST | `/ui/mutate`, `/ui/mutate/stream` | Propose changes, or check client operations |
| POST | `/generation/jobs` | **Start building** an application (or a single view, or one screen again) in the background |
| GET | `/generation/jobs?workspace_id=` | A workspace's latest job (resume after a reload) |
| GET | `/generation/jobs/{id}` | Status, stage, percent, detail and, when ready, the proposal |
| POST | `/generation/jobs/{id}/cancel` | Stop a running job |
| GET | `/workspaces/{id}/application` | Summary and graph (navigation, transitions, shared data) of the current application |
| GET, POST | `/workspaces/{id}/assets` | Images of a workspace / add one |
| GET | `/assets/{id}/content` | An image's bytes (public, immutable, `nosniff` + restrictive CSP) |
| DELETE | `/workspaces/{id}/records` | Reset the application's data to its sample records |
| GET | `/ui/patterns` | Pattern, effect and icon registries (public) |
| GET | `/references`, `/references/facets`, `/references/{id}` | Browse the reference component library (see below) |
| POST | `/ui/validate` | Validate a document |
| GET | `/ui/components`, `/ui/frameworks`, `/ui/themes`, `/ui/capabilities` | Registries (public) |
| POST | `/actions/execute` | Run an allowlisted action |
| GET, POST | `/data-sources` | List / register |
| GET | `/data-sources/datasets` | Datasets available to the caller |
| DELETE | `/data-sources/{id}` | Remove |

### Propose, then persist

`/ui/generate` and `/ui/mutate` return a **proposal** and save nothing. To apply one:

```jsonc
POST /workspaces/{id}/versions
{
  "base_version_id": "<the version the proposal was made against, or null for the first>",
  "source": "ai_mutation",              // ai_generation | ai_mutation | manual_edit
  "proposal_id": "…", "instruction": "Make it dark",
  "operations": [ { "type": "SET_THEME", "preset": "slate_dark" } ]   // or "document": {…}
}
```

The server re-validates everything. If `base_version_id` is no longer current it answers
`409 VERSION_CONFLICT` with the current version in `details` and writes nothing.

The `/stream` variants are server-sent events: `progress` (`{stage, characters}`), then
one `proposal` (same envelope) or `error` (standard envelope).

### Building an application

`POST /generation/jobs` answers `202` with a job and runs the pipeline in the process
(asyncio tasks behind a `JobRunner` protocol; no broker). Poll the job: `stage` moves through
`understanding → planning → designing → generating_assets → generating_screens → assembling
→ validating → ready` (or `failed`), each reported by the pipeline when it gets there. The
result is a proposal like any other; nothing is saved until it is posted to `/versions`.

The pipeline (`app/ai/orchestration/application/`) is a chain of small model calls with
strict structured output, never one large one: application blueprint, design direction,
data model with sample records, screen plans (with patterns retrieved from the pattern
registry), image briefs, interactions, then each screen on its own. Each screen is validated
alone; a screen that still fails after repair becomes a placeholder and the rest of the
application is kept (`kind: "screen"` generates one again later). A deterministic design
review (`domains/generation/quality.py`) scores the result and asks for a bounded number of
screen refinements. A missing image falls back to built-in artwork. Jobs interrupted by a
restart are marked failed at startup.

Edits to an application are routed (`editing.py`): a restyle changes design tokens only, a
screen redesign replaces one screen, a new screen adds one and links it, everything else is
ordinary operations with only the relevant screen in the prompt.

Records a user changes in a running application (`record_create|update|delete` actions) are
stored per workspace and layered over the version's sample records, so versions stay
immutable and a restore does not undo the user's data.

## Reference component library

Source code of UI components published elsewhere, plus this project's own design
vocabulary, stored in `reference_components` as design reference for building this
platform's own patterns. It is **reading material**:
nothing in it is rendered or executed, the model never sees it, and generated UIs still
use only the component registry. Every row keeps its author, licence, a link to the
original and (for registries) the commit it was read at.

```bash
poetry run python -m scripts.import_references all            # every source it has access to
poetry run python -m scripts.import_references ui_layouts     # or magic_ui, bootstrap, vocabulary, twenty_first
poetry run python -m scripts.import_references twenty_first --code 20
```

| Source | Licence | How it is read |
| --- | --- | --- |
| `ui_layouts` — [ui-layouts.com](https://www.ui-layouts.com) | MIT | The shadcn registry in its GitHub repository (archive download, or `--path` to a checkout) |
| `magic_ui` — [magicui.design](https://magicui.design) | MIT | Same |
| `bootstrap` — [getbootstrap.com](https://getbootstrap.com) | MIT (docs CC BY 3.0) | Its GitHub repository: example pages, each documentation page with the stylesheet partial behind it, and the stylesheet foundation (variables, mixins, custom properties) |
| `vocabulary` — this repository | Project | `app/domains/references/vocabulary/`: 500 UI patterns, 500 effects and 6 combination recipes, each written here as runnable HTML, CSS and vanilla JavaScript (see below) |
| `twenty_first` — [21st.dev](https://21st.dev) | per author; none stated | Its official API with `TWENTYFIRST_API_KEY` (create one at 21st.dev/mcp). A curated set of searches stores metadata and links; `--code N` also fetches source for up to N components and stops by itself when the key's allowance ends |

21st.dev's terms forbid crawling the site, redistributing its components without a link
back, and using them to train models, so the importer only calls the API, stores the link
with every entry, and the library is kept away from the model. Components from 21st.dev
have no stated licence: treat them as inspiration and ask the author before reusing code.
[uiguideline.com](https://www.uiguideline.com) publishes design guidance (anatomy, naming),
not code, and states no licence, so nothing is copied from it; read it there.

Importing again updates what changed and leaves the rest alone. Browse with
`GET /references?source=&kind=&category=&q=&with_code=` and open one, with its files, by id.

### The design vocabulary

`source=vocabulary` holds 1,006 entries written in this repository: UI patterns 1–500
(`kind=component`, 15 sections), effects 1–500 (`kind=effect`, 19 sections) and six
recipes that combine four effects on one component (`kind=recipe`). The slug carries the
number from the original list (`effects/211-glassmorphism`), `category` is the section,
and `description` says what the entry is for.

Each entry is framework-neutral and has no dependencies. Its files are `index.html` (a
complete page that can be opened as it is), `markup.html`, `styles.css` and, where it
needs one, `script.js` (wrapped in its own scope, so several entries can share a page).
All of them use one set of design tokens (`vocabulary/base.py`), and interactive entries
handle keyboard use and `prefers-reduced-motion`.

A section is a Python module exporting `SECTION`; adding an `Item` to it and re-running
the import is all it takes to add an entry. Every entry is checked in a real browser:

```bash
poetry run python -m scripts.export_vocabulary /tmp/vocabulary           # pages + index.json
cd ../frontend && node tests/e2e/vocabulary.mjs /tmp/vocabulary --sheets /tmp/sheets
```

The check opens each page in Chrome and fails on a script or console error, a page that
renders nothing, sideways overflow, or a CSS rule the browser discarded; `--sheets` also
writes contact sheets to look over. `tests/unit/domains/test_vocabulary.py` asserts that
all 1,000 numbered items and the six recipes are present, in order, with real code.

A few effects rely on features that are not in every browser, and say so in their
description: SVG filters on `backdrop-filter` (Chromium), `-webkit-box-reflect`
(Chromium and Safari) and the View Transitions API (with an instant swap as fallback).

## Data sources

Generated UIs bind to datasets by name. A caller sees the demo dataset (outside
production) plus the datasets of the sources they registered.

| Type | Configuration | Notes |
| --- | --- | --- |
| `file_upload` | `dataset`, `format` (`csv`/`json`), `content` | Parsed once; rows stored with the source (≤ 500 rows). |
| `rest_api` | `dataset`, `url` (https), `records_path?`, `credentials_ref?`, `auth_scheme?` | Fetched per request. Private/loopback addresses and redirects are refused. |
| `postgresql` | `credentials_ref`, `datasets: [{name, query}]` | Single `SELECT` only; run in a `READ ONLY` transaction with a timeout and row cap. |

Credentials are never accepted in a request or stored: `credentials_ref: "WAREHOUSE"` makes
the server read `DATASOURCE_SECRET_WAREHOUSE`. A source is read once before it is saved, so
an unreachable or unreadable source is rejected with `502 DATA_SOURCE_ERROR`.

## Errors

`app/core/exceptions.py` is the complete catalogue. Low-level failures are translated where
they occur — database errors in `middleware/error_handler.py`, LLM failures in
`ai/llm/http.py` (classified as timeout, transport, rate-limited, unavailable,
authentication, bad request, bad response), data source failures in the providers — so a
client only ever sees a stable code. Driver messages, SQL, upstream error bodies and stack
traces go to the log, never to the response. The table of mappings is in the architecture
document.

## Tests and checks

```bash
poetry run pytest                              # everything
poetry run pytest tests/unit                   # no database needed
poetry run ruff check app tests scripts && poetry run ruff format --check app tests scripts
poetry run mypy
poetry run alembic check                       # models and migrations agree
```

Integration tests use `TEST_DATABASE_URL`; the database is created if missing and **its
schema is dropped and rebuilt from the migrations on each run** (the name must contain
`test`). No test calls a real provider: provider classes run against a mocked HTTP
transport, including streaming, retries and fallback.

## Security notes

- Passwords: scrypt (salted, parameters stored with the hash). Tokens: HS256 JWT with expiry.
- Sign-in failures do not reveal whether an email is registered; credential endpoints have
  their own rate limit.
- Authentication is established before any other dependency of a protected route runs.
- Model output and client input pass the same validation; "it came from a proposal" grants
  nothing.
- Actions are an allowlist with typed payloads. Navigation accepts in-app paths and https.
- Logs redact secret-looking keys; prompts and payloads are not logged unless
  `LOG_PROMPTS=true` (refused in production).

## Known limitations

- **Rate limits are per process.** With several instances the effective limit multiplies;
  `RateLimiter` is the seam for a shared store.
- **No token revocation or refresh.** A token is valid until it expires
  (`ACCESS_TOKEN_TTL_MINUTES`) or its account is deleted. No password reset or email
  verification.
- **REST data sources** resolve the host before the request; DNS rebinding between the
  check and the request is not defended against.
- **Dataset size** is capped at 500 rows per dataset; there is no pagination or server-side
  aggregation for large sources.
- **Metric values** bound to data are computed in the frontend from the rows it receives.
- **Generation jobs run in the API process.** A restart ends running jobs (they are marked
  failed and can be started again); several instances would need the `JobRunner` seam
  filled with a shared queue.
- **Images are stored in PostgreSQL** (one row each, loaded only when served). Fine for
  tens of images per workspace; object storage is the next step beyond that.
- **Model quotas decide speed.** On free tiers the pipeline waits out rate limits
  (`LLM_RATE_LIMIT_*`); an eight-screen application took about two minutes in testing.
- **Docker** files are provided but were not built on the development machine (no Docker).
