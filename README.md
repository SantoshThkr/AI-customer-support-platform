# Support Desk

AI-assisted customer support platform for a small SaaS product.

Customers can create support tickets and reply to them. Support agents can triage, assign, discuss and resolve tickets. AI helps with ticket classification, conversation summaries, knowledge-base search and reply suggestions.

AI is optional. The ticketing system still works without an OpenAI API key or when AI is disabled by an admin. AI never sends a message directly to a customer; an agent must review and send the final reply.

## Features

### Customers

* Register, login and manage their own tickets
* Reply to and close tickets
* View ticket history and dashboard
* Internal notes and AI triage data are hidden from customers

### Agents

* Open, assigned, urgent and waiting-ticket views
* Search, filtering and pagination
* Assign tickets and update status, priority and category
* Reply to customers and add internal notes
* Search the knowledge base
* View customer ticket history
* AI ticket analysis, summaries, reply suggestions and copilot

### Admins

* Manage users, roles and ticket categories
* Manage knowledge-base documents
* View ticket and AI usage analytics
* Enable or disable AI features
* Enable or disable automatic ticket analysis

## Architecture

```text
React + Vite
     ↓
nginx
     ↓
FastAPI
 ┌───┼──────────────┐
 ↓   ↓              ↓
DB  OpenAI       RAG Search
     ↓
PostgreSQL + pgvector
```

REST APIs handle normal application requests. Server-Sent Events are used for streamed AI replies.

The backend keeps AI-related code in `server/app/ai/`. Tickets are stored normally even when AI analysis fails. Knowledge documents are processed into chunks and embeddings for semantic search, with PostgreSQL full-text search as a fallback.

## Tech Stack

**Frontend**

* React 18
* TypeScript
* Vite
* React Router
* Axios
* React Hook Form
* Tailwind CSS

**Backend**

* Python 3.11
* FastAPI
* SQLAlchemy
* Pydantic
* Alembic
* PyJWT
* bcrypt

**Database**

* PostgreSQL 16
* pgvector

**AI**

* OpenAI Python SDK
* GPT-4o-mini
* text-embedding-3-small
* No LangChain

**Testing & Tools**

* pytest
* Vitest
* React Testing Library
* Ruff
* Docker Compose
* GitHub Actions

## Project Structure

```text
.
├── client/
│   └── src/
│       ├── components/
│       ├── context/
│       ├── hooks/
│       ├── pages/
│       ├── services/
│       ├── tests/
│       ├── types/
│       └── utils/
│
├── server/
│   ├── app/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   ├── dependencies/
│   │   ├── services/
│   │   └── ai/
│   ├── alembic/
│   ├── sample_data/
│   └── tests/
│
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## Setup

### Docker

```bash
cp .env.example .env
docker compose up --build
```

Open:

```text
Frontend → http://localhost:8080
API      → http://localhost:8000/api
Docs     → http://localhost:8080/api/docs
```

Create demo data:

```bash
docker compose exec backend python -m app.cli seed-demo
```

Or create an admin account:

```bash
docker compose exec backend python -m app.cli create-user \
  --email you@company.com \
  --name "Your Name" \
  --role ADMIN
```

### Local development

Requirements:

* Python 3.11
* Node.js 20+
* PostgreSQL with pgvector

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Start the backend:

```bash
cd server
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

cp .env.example .env
alembic upgrade head

uvicorn app.main:app --reload
```

Start the frontend:

```bash
cd client
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and proxies `/api` to the FastAPI server.

## AI Configuration

Set `OPENAI_API_KEY` in the backend environment.

Main AI features:

* Ticket classification
* Priority and sentiment detection
* Conversation summaries
* Knowledge-base embeddings
* Semantic search
* Suggested replies
* Agent copilot
* Streaming AI responses
* AI usage tracking

AI can be disabled by an admin. Invalid AI output is rejected, and normal ticket operations continue when AI is unavailable. Knowledge search can fall back to PostgreSQL full-text search.

## Environment Variables

Important backend settings:

| Variable                      | Purpose                     |
| ----------------------------- | --------------------------- |
| `DATABASE_URL`                | PostgreSQL connection       |
| `SECRET_KEY`                  | JWT signing key             |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime              |
| `CORS_ORIGINS`                | Allowed frontend origins    |
| `OPENAI_API_KEY`              | Enables AI features         |
| `OPENAI_CHAT_MODEL`           | Chat model                  |
| `OPENAI_EMBEDDING_MODEL`      | Embedding model             |
| `OPENAI_TIMEOUT_SECONDS`      | AI request timeout          |
| `AI_REQUESTS_PER_MINUTE`      | Per-user AI rate limit      |
| `MAX_UPLOAD_SIZE_MB`          | Knowledge-base upload limit |

Secrets are backend-only and `.env` files are ignored by Git.

## Database

The main tables are:

```text
users
categories
tickets
ticket_messages
ticket_assignments
ticket_events
knowledge_documents
knowledge_chunks
ai_usage
system_settings
```

`pgvector` is used for knowledge-base embeddings, while ticket search also uses PostgreSQL full-text search.

Run migrations:

```bash
cd server

alembic upgrade head
```

## API

Main endpoints:

```text
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me

POST   /api/tickets
GET    /api/tickets
GET    /api/tickets/{id}
PATCH  /api/tickets/{id}

GET    /api/tickets/{id}/messages
POST   /api/tickets/{id}/messages
POST   /api/tickets/{id}/assign

GET    /api/knowledge/documents
POST   /api/knowledge/documents
DELETE /api/knowledge/documents/{id}
GET    /api/knowledge/search

POST   /api/ai/tickets/{id}/analyze
POST   /api/ai/tickets/{id}/summarize
POST   /api/ai/tickets/{id}/suggest-response
POST   /api/ai/tickets/{id}/copilot

GET    /api/admin/analytics
GET    /api/admin/ai-usage
GET    /api/admin/settings
```

Interactive API documentation:

```text
http://localhost:8000/api/docs
```

AI streaming endpoints return `text/event-stream`.

## Testing

Backend:

```bash
docker compose up -d postgres

cd server
pytest
ruff check .
ruff format --check .
```

Frontend:

```bash
cd client
npm test
npm test -- --run
npm run typecheck
```

Backend tests use PostgreSQL + pgvector, while OpenAI calls are replaced with a fake client. CI runs backend and frontend checks on pushes and pull requests.

## Security

* Passwords are hashed with bcrypt.
* JWT authentication and role checks are enforced by the backend.
* Ticket access is checked on every request.
* Customers cannot access internal notes or AI triage data.
* Knowledge-base uploads are validated for size, type and content.
* OpenAI credentials stay on the server.
* AI requests do not receive general database access.
* AI-generated replies always require agent review.
* Secrets are not committed to the repository.

## Screenshots

Screenshots are included in `docs/screenshots/`.

The current screenshots use placeholder AI output from a local OpenAI mock.
