# Support Desk: AI-assisted customer support

A ticketing system for a small SaaS product. Customers open tickets and reply to them.
Support agents triage, assign, discuss (with internal notes) and resolve them. An OpenAI
integration helps agents work faster: it classifies new tickets, summarises conversations,
searches the knowledge base semantically and drafts replies.

AI is optional. Without an `OPENAI_API_KEY`, or with AI switched off by an admin, the ticketing
system still works; only the AI features go away. AI never sends anything to a customer. A
suggested reply only reaches the customer after an agent puts it in the reply box, edits it if
needed, and clicks send.

![Agent working on a ticket](docs/screenshots/ticket-workspace.png)

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Quick start with Docker](#quick-start-with-docker)
- [Local development](#local-development)
- [Environment variables](#environment-variables)
- [Database and migrations](#database-and-migrations)
- [Running tests](#running-tests)
- [AI configuration](#ai-configuration)
- [API documentation](#api-documentation)
- [Security notes](#security-notes)
- [Screenshots](#screenshots)

## Features

**Customers**
- Register, log in, open tickets, reply, close their own tickets
- Dashboard with open / pending (waiting on them) / resolved counts and recent tickets
- Ticket history. Internal notes and AI triage data are never returned to customers by the API.

**Agents**
- Queue views: open, mine, urgent, waiting for customer, recently resolved
- Filters for status, priority, category and assignee, plus full-text search and pagination
- Assign tickets (to themselves or colleagues), change status/priority/category
- Reply to customers or add internal notes; the conversation marks customer replies, agent
  replies and internal notes differently
- Knowledge base search from the ticket page, and a view of the customer's other tickets
- AI: re-run analysis, summarise the conversation, stream a suggested reply, ask the copilot

Agents can work on unassigned tickets and tickets assigned to them. Tickets assigned to someone
else are read-only for them apart from internal notes.

**Admins**
- Everything agents can do, on any ticket
- Manage users and roles, ticket categories and knowledge base documents (.txt, .md, .pdf)
- Analytics: ticket totals, average resolution time, tickets by category/priority, AI requests
- AI usage report (requests and tokens by operation, model, day and user)
- Settings: turn AI features and automatic ticket analysis on or off

## Architecture

```text
 Browser (React + Vite)
        │  REST + JSON, Server-Sent Events for streamed AI replies
        ▼
 nginx ── serves the built frontend, proxies /api (unbuffered)
        │
        ▼
 FastAPI ──────────────────────────────┐
   routers → services → SQLAlchemy     │ app/ai/*: only place that calls OpenAI
        │                              ▼
        ▼                          OpenAI API
 PostgreSQL 16 + pgvector          (chat completions, embeddings)
   tickets, messages, events,
   knowledge chunks + embeddings,
   ai_usage, settings
```

How requests flow:

- **Creating a ticket** saves the ticket and a `TICKET_CREATED` event, returns `201`, then runs
  AI analysis in a FastAPI background task. If OpenAI is missing, slow, failing or returns
  invalid JSON, the error is logged and the ticket keeps empty AI fields.
- **Analysis** asks for a strict JSON schema (category, priority, sentiment, summary). The result
  is validated with Pydantic and checked against the active categories before anything is saved.
- **Knowledge base**: uploads are validated (type, size, content), text is extracted (pypdf for
  PDFs), cleaned and split into heading-aware chunks of about 1,000 characters. Chunks are
  embedded in a background task and stored in a `vector(1536)` column with an HNSW index.
  Search uses cosine similarity when possible and falls back to PostgreSQL full-text search.
- **Suggested replies / copilot** retrieve the most relevant chunks for the ticket, build a
  prompt from the ticket, its conversation, limited customer details and those chunks, and
  stream the answer back as SSE. The model never gets general database access; it only sees
  what the backend puts in the prompt.
- **AI errors** are separate exception types: `AIUnavailableError` becomes `503` and
  `AIServiceError` (timeouts, provider errors, unusable output) becomes `502`. Normal ticket
  endpoints never raise them.

## Tech stack

| Area | Choice |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router 6, Axios, React Hook Form, Tailwind CSS |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, PyJWT, bcrypt |
| Database | PostgreSQL 16 with pgvector |
| AI | OpenAI Python SDK (`gpt-4o-mini`, `text-embedding-3-small` by default); no LangChain |
| Tests | pytest (against a real Postgres), Vitest + React Testing Library |
| Tooling | Ruff, Docker Compose, GitHub Actions |

## Project structure

```text
.
├── client/                     React app
│   ├── src/
│   │   ├── components/         shared UI; components/ticket/ holds the ticket page pieces
│   │   ├── context/            AuthContext (current user + token)
│   │   ├── hooks/              small data hooks (tickets, categories, agents, AI status)
│   │   ├── pages/              one file per route; pages/admin/ for admin screens
│   │   ├── services/           API calls (axios; fetch for SSE streams)
│   │   ├── tests/              React Testing Library tests
│   │   ├── types/              API types
│   │   └── utils/              formatting, error messages, SSE parsing
│   ├── Dockerfile, nginx.conf
├── server/                     FastAPI app
│   ├── app/
│   │   ├── main.py             app setup, routers, error handlers
│   │   ├── config.py           settings from environment variables
│   │   ├── database.py         engine, session, Base
│   │   ├── models/             SQLAlchemy models
│   │   ├── schemas/            Pydantic request/response models
│   │   ├── routers/            API endpoints
│   │   ├── dependencies/       auth, role checks, ticket access, AI rate limit
│   │   ├── services/           ticket rules, knowledge processing, analytics, settings
│   │   ├── ai/                 OpenAI client, prompts, analysis, embeddings, suggestions, usage
│   │   └── cli.py              create-user, import-knowledge, seed-demo
│   ├── alembic/                migrations
│   ├── sample_data/knowledge/  example support articles
│   └── tests/                  pytest suite (OpenAI is faked)
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Quick start with Docker

Requirements: Docker with Compose v2.

```bash
cp .env.example .env
# set SECRET_KEY (required) and optionally OPENAI_API_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

docker compose up --build
```

Services:

| Service | URL |
|---|---|
| Frontend | http://localhost:8080 |
| API | http://localhost:8000/api (also proxied at http://localhost:8080/api) |
| API docs | http://localhost:8080/api/docs |
| PostgreSQL | localhost:5432 (`POSTGRES_PORT` to change) |

The backend container runs `alembic upgrade head` on start. Data is kept in the `postgres_data`
volume (`docker compose down -v` removes it).

Create accounts and sample articles:

```bash
# demo accounts: admin@example.com, agent@example.com, customer@example.com (password123)
# plus the articles in server/sample_data/knowledge
docker compose exec backend python -m app.cli seed-demo

# or create real accounts (prompts for a password)
docker compose exec backend python -m app.cli create-user --email you@company.com --name "Your Name" --role ADMIN
```

Customers can also sign up at `/register`. Registration always creates a `CUSTOMER`; agents and
admins are created by an admin on the Users page or with the CLI.

If a port is already taken, set `FRONTEND_PORT`, `BACKEND_PORT` or `POSTGRES_PORT` in `.env`.

## Local development

Requirements: Python 3.11, Node 20+, and PostgreSQL with pgvector. The simplest way to get
the database is to run only that service from Compose:

```bash
docker compose up -d postgres
```

### Backend

```bash
cd server
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env            # set SECRET_KEY; DATABASE_URL points at localhost:5432
alembic upgrade head
python -m app.cli seed-demo     # optional
uvicorn app.main:app --reload   # http://localhost:8000, docs at /api/docs
```

### Frontend

```bash
cd client
npm install
npm run dev                     # http://localhost:5173
```

The Vite dev server proxies `/api` to `http://localhost:8000`. Set `VITE_PROXY_TARGET` to proxy
somewhere else, or `VITE_API_URL` to call an API on another origin directly (that origin must be
listed in the backend's `CORS_ORIGINS`).

## Environment variables

Backend (`server/.env` for local runs, root `.env` for Docker Compose):

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://support:support@localhost:5432/support` | Compose builds this from the `POSTGRES_*` values |
| `SECRET_KEY` | none (required) | Signs JWTs. Use a long random string. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `720` | Token lifetime |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated list |
| `OPENAI_API_KEY` | empty | Empty = AI features disabled |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Must support JSON schema output |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Must be a `text-embedding-3-*` model (see below) |
| `OPENAI_TIMEOUT_SECONDS` | `30` | Per request; one retry |
| `AI_REQUESTS_PER_MINUTE` | `20` | Per user, per API process |
| `MAX_UPLOAD_SIZE_MB` | `5` | Knowledge base uploads |
| `LOG_LEVEL` | `INFO` | |

Compose only: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `FRONTEND_PORT`,
`BACKEND_PORT`, `POSTGRES_PORT`.

Frontend (optional): `VITE_API_URL` (default `/api`), `VITE_PROXY_TARGET` (dev server only).

Secrets (`OPENAI_API_KEY`, `DATABASE_URL`, `SECRET_KEY`) are only read by the backend and are
never sent to the browser. `.env` files are git-ignored.

## Database and migrations

Tables: `users`, `categories`, `tickets`, `ticket_messages`, `ticket_assignments`,
`ticket_events`, `knowledge_documents`, `knowledge_chunks`, `ai_usage`, `system_settings`.

- `tickets.search_vector` is a generated `tsvector` column with a GIN index, used for ticket search.
- `knowledge_chunks.embedding` is `vector(1536)` with an HNSW (`vector_cosine_ops`) index.
- `ticket_events.metadata` is JSONB (e.g. `{"from": "OPEN", "to": "RESOLVED"}`).
- Priority is a PostgreSQL enum declared from `LOW` to `URGENT`, so sorting by priority works.

Migrations are written by hand in `server/alembic/versions/`:

```bash
cd server
alembic upgrade head                    # apply
alembic downgrade -1                    # roll back one
alembic revision -m "add something"     # new migration
alembic revision --autogenerate -m "…"  # review the output carefully; generated columns and
                                        # vector indexes may need manual edits
```

Migration `0006` runs `CREATE EXTENSION IF NOT EXISTS vector`, which needs a database role that
is allowed to create extensions (the default user in the pgvector image is a superuser).

## Running tests

### Backend

The tests run against a real PostgreSQL + pgvector server, because they exercise full-text
search, generated columns and vector similarity queries. The suite drops and recreates a
`support_test` database, applies the Alembic migrations and truncates tables between tests.
OpenAI is replaced with a fake client (`tests/fakes.py`), so no API key or network is needed.

```bash
docker compose up -d postgres
cd server
TEST_DATABASE_URL=postgresql+psycopg://support:support@localhost:5432/support_test pytest
ruff check . && ruff format --check .
```

`TEST_DATABASE_URL` defaults to the URL above. The user needs permission to create databases.

### Frontend

```bash
cd client
npm test              # watch mode
npm test -- --run     # single run, as in CI
npm run typecheck
```

CI (`.github/workflows/ci.yml`) runs Ruff and pytest (with a `pgvector/pgvector:pg16` service
container) plus type checking, tests and a production build of the frontend.

## AI configuration

Set `OPENAI_API_KEY` and restart the backend. Everything AI-related lives in `server/app/ai/`:

| Module | Purpose |
|---|---|
| `client.py` | OpenAI client, error mapping, availability checks |
| `prompts.py` | All prompt text and prompt builders |
| `ticket_analysis.py` | Classification (category, priority, sentiment, summary) and conversation summaries |
| `embeddings.py` | Batched embeddings for chunks and search queries |
| `response_suggestions.py` | Context retrieval (RAG), suggested replies, copilot, SSE streaming |
| `usage.py` | Writes an `ai_usage` row for every API call |

Behaviour worth knowing:

- **Turning AI off**: admins can disable all AI features, or only automatic analysis of new
  tickets, on the Settings page. The ticket page hides AI tools and explains why.
- **Invalid output** from the classifier (bad JSON, unknown category, empty summary) is rejected;
  nothing is written to the ticket.
- **Knowledge search without AI** uses PostgreSQL full-text search. The same fallback is used if
  embedding the query fails or the user has hit the AI rate limit.
- **Documents uploaded while AI was off** are searchable by keyword. Admins can generate their
  embeddings later from the Knowledge base page.
- **Prompt injection**: customer text and articles are wrapped in tags and the prompts tell the
  model to treat them as data. Drafts still always go through an agent.
- **Token usage** is stored exactly as the API reports it. Embedding calls only report input
  tokens, and a stream stopped early may report none. Those values stay `NULL` and the usage
  page lists them separately instead of estimating.
- **Rate limiting** is an in-memory sliding window per user (`AI_REQUESTS_PER_MINUTE`). With
  several API processes, each keeps its own count.
- **Embedding size** is fixed at 1536 by the database column. The API requests that size, which
  the `text-embedding-3-*` models support. Switching to a different size needs a migration and
  re-embedding.

## API documentation

Interactive docs (Swagger UI) are served at `/api/docs`, and the OpenAPI schema at
`/api/openapi.json`. Authenticated requests use `Authorization: Bearer <token>` from
`/api/auth/login` or `/api/auth/register`.

| Method | Path | Who |
|---|---|---|
| POST | `/api/auth/register`, `/api/auth/login` | anyone |
| GET | `/api/auth/me` | signed in |
| GET/POST/PATCH | `/api/users`, `/api/users/{id}` | admin |
| GET | `/api/users/agents` | agent, admin |
| POST | `/api/tickets` | customer |
| GET | `/api/tickets` (`search`, `status`, `priority`, `category`, `assigned_agent`=`me`/`unassigned`/id, `customer_id`, `sort`, `order`, `page`, `page_size`) | signed in (customers see only their own) |
| GET | `/api/tickets/stats` | signed in |
| GET/PATCH | `/api/tickets/{id}` | owner or staff (customers may only set `CLOSED`) |
| DELETE | `/api/tickets/{id}` | admin |
| GET/POST | `/api/tickets/{id}/messages` | owner or staff (`is_internal` is staff only) |
| POST | `/api/tickets/{id}/assign` | agent, admin |
| GET | `/api/tickets/{id}/events` | owner or staff |
| GET/POST/PATCH | `/api/categories` | read: signed in, write: admin |
| GET/POST/DELETE | `/api/knowledge/documents[/{id}]` | read: staff, write: admin |
| POST | `/api/knowledge/documents/{id}/embed` | admin |
| GET | `/api/knowledge/search?q=` | agent, admin |
| GET | `/api/ai/status` | agent, admin |
| POST | `/api/ai/tickets/{id}/analyze`, `/summarize` | agent, admin |
| POST | `/api/ai/tickets/{id}/suggest-response` (+ `/stream`) | agent, admin |
| POST | `/api/ai/tickets/{id}/copilot` (+ `/stream`) | agent, admin |
| GET | `/api/admin/analytics`, `/api/admin/ai-usage` | admin |
| GET/PATCH | `/api/admin/settings` | admin |

Errors use FastAPI's `{"detail": ...}` shape with the usual status codes (400, 401, 403, 404,
409, 413, 422, 429). AI failures add a `code`: `ai_unavailable` (503) or `ai_error` (502).

Streaming endpoints return `text/event-stream` with these events:

```text
event: sources   data: {"sources": [{"document_id": 3, "document_title": "Password Reset Guide", "section": null}]}
event: delta     data: {"text": "Hi John, "}
event: delta     data: {"text": "reset links are valid for 30 minutes…"}
event: done      data: {}
```

If the provider fails part way through, an `error` event is sent instead of `done`.

## Security notes

- Passwords are hashed with bcrypt. JWTs are signed with `SECRET_KEY` (HS256) and expire.
- Role checks are FastAPI dependencies (`require_roles`, `require_staff`, `require_admin`).
  Ticket access is checked on every ticket route. Customers get `404` for tickets that aren't
  theirs, so ticket ids can't be probed.
- Internal notes, their history events, and AI triage fields are filtered out on the backend
  for customers, not just hidden in the UI.
- Uploads are limited by extension and size, and checked by content (PDF header, UTF-8 text).
  Only the extracted text is stored; the uploaded file itself is not kept or served back.
  The knowledge base is only readable by staff.
- The OpenAI key stays on the server. Logs record AI error types and status codes, not request
  bodies or keys.

## Screenshots

The screenshots were taken against a local mock of the OpenAI API, so the AI-generated text in
them is placeholder output rather than real model responses.

| | |
|---|---|
| ![Agent queue](docs/screenshots/agent-queue.png) Agent queue | ![Customer dashboard](docs/screenshots/customer-dashboard.png) Customer dashboard |
| ![Admin analytics](docs/screenshots/admin-analytics.png) Admin analytics | ![Knowledge base](docs/screenshots/knowledge-base.png) Knowledge base search |
