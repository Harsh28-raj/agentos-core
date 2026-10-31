# AgentOS Core — Documentation Index

Each file is self-contained. **Load only the file your task needs** — this is cheaper than reading the code.

| File | Read it when you need to… |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Understand the whole system in 2 minutes: components, request lifecycle, diagrams |
| [BACKEND.md](BACKEND.md) | Find which backend file does what (one line per file) and backend conventions |
| [API.md](API.md) | Call or change an HTTP endpoint: paths, auth, request/response shapes, SSE events |
| [AGENTS_AND_TOOLS.md](AGENTS_AND_TOOLS.md) | Change routing, prompts, a worker agent, or add a tool/agent |
| [HITL.md](HITL.md) | Touch anything about approvals: interrupt(), resume values, chat "yes/no" parsing |
| [DATA_AND_STATE.md](DATA_AND_STATE.md) | Work with the database, checkpointer, thread keys, long-term memory, uploads |
| [FRONTEND.md](FRONTEND.md) | Change the React app: file map, data flow, theme, components |
| [CONFIGURATION.md](CONFIGURATION.md) | Look up an environment variable |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Run locally, deploy to Render/Vercel/Neon, set up Google OAuth, upgrade from v1.0 |
| [SECURITY.md](SECURITY.md) | Reason about auth, isolation, secrets, the code interpreter, prompt injection |
| [TESTING.md](TESTING.md) | Run or write tests (fake LLMs, approval flows, browser e2e) |
| [BUG_AUDIT.md](BUG_AUDIT.md) | See the 49-bug audit, what was fixed, and what is still open |

## 30-second summary

- **Monorepo**: `api-1/` = FastAPI + LangGraph backend (Python 3.11+), `frontend/` = React 19 + Vite + Tailwind 4 SPA.
- **Flow**: browser → `POST /api/v1/chat/stream` (JWT) → supervisor LangGraph → worker agent (research / coder / vision / gmail / calendar) → tools. Side-effecting tools (`send_email`, `create_calendar_event`) call `interrupt()` and wait for human approval.
- **State**: Postgres holds users, audit logs, encrypted Google tokens, pgvector memory and LangGraph checkpoints (paused approvals survive restarts).
- **LLM**: Groq (`GROQ_MODEL`, default `llama-3.1-8b-instant`).
- **Every request is authenticated**; the user id always comes from the JWT, never from the request body.

## Conventions for contributors (human or AI)

- Backend tests: `cd api-1 && pip install -r requirements-dev.txt && pytest` (no API keys needed).
- Frontend checks: `cd frontend && npm run check` (lint + typecheck + build).
- New env vars go in `api-1/app/core/config.py` **and** [CONFIGURATION.md](CONFIGURATION.md) **and** `api-1/.env.example`.
- New endpoints must depend on `get_current_user` and scope data by `user.id` (see [SECURITY.md](SECURITY.md)).
- Keep these docs in sync when you change behaviour they describe.
