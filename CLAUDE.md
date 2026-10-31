# AgentOS Core — guide for AI assistants

Multi-agent assistant: FastAPI + LangGraph backend (`api-1/`), React + Vite frontend (`frontend/`).

**Start with `docs/README.md`** — it maps every task to one small doc. Read only the doc you need instead of the code:
architecture → `docs/ARCHITECTURE.md`, backend file map → `docs/BACKEND.md`, endpoints → `docs/API.md`,
agents/tools → `docs/AGENTS_AND_TOOLS.md`, approvals → `docs/HITL.md`, DB/checkpoints → `docs/DATA_AND_STATE.md`,
frontend → `docs/FRONTEND.md`, env vars → `docs/CONFIGURATION.md`, security rules → `docs/SECURITY.md`,
tests → `docs/TESTING.md`, known issues → `docs/BUG_AUDIT.md`.

## Commands
- Backend tests (no keys needed): `cd api-1 && pip install -r requirements-dev.txt && pytest`
- Backend dev server: `cd api-1 && uvicorn app.main:app --reload --port 10000`
- Frontend checks: `cd frontend && npm run check` · dev server: `npm run dev`

## Rules that must not be broken
1. User identity comes only from the JWT (`Depends(get_current_user)`); scope every query/key/path by `user.id`.
2. Never call `update_state` on a paused thread and never delete stored messages; resume approvals with `Command(resume=...)`.
3. Side-effecting tools must call `interrupt()` with a full preview before acting (`docs/HITL.md`).
4. New env vars go in `app/core/config.py`, `api-1/.env.example` and `docs/CONFIGURATION.md`.
5. Keep `docs/` in sync with behaviour changes; add tests for new endpoints and approval paths.
