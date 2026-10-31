# Architecture

## Components

```
┌──────────────── frontend/ (Vercel) ────────────────┐
│ React SPA: Landing · Login/Register · Dashboard     │
│ Dashboard = ChatPanel (+ApprovalCard) · ToolStatus  │
│             · TaskBoard (tool activity) · Memory    │
└───────────────┬─────────────────────────────────────┘
                │ HTTPS, Authorization: Bearer <JWT>, SSE for chat
┌───────────────▼──────────── api-1/ (Render) ────────┐
│ FastAPI app (app/main.py)                            │
│  routers: auth · chat · upload · logs · system ·     │
│           integrations (Google OAuth)                │
│  app.state.graph = supervisor LangGraph              │
│     supervisor ─▶ research_agent  (web, weather, calc, memory)
│        ▲   │  ─▶ coder_agent     (python interpreter, opt-in)
│        │   │  ─▶ vision_agent    (uploaded images)
│        │   │  ─▶ gmail_agent     (search/read/draft/send*)
│        └───┴──── calendar_agent  (availability/create*)
│                       * = pauses with interrupt() for approval
└───────┬───────────────┬───────────────┬─────────────┘
        │               │               │
   Groq API       Postgres (Neon)   Google / Tavily / wttr.in
   (LLMs)         users, episodic_logs, user_tokens,
                  pgvector memory, LangGraph checkpoints
```

## Request lifecycle (streaming chat)

1. `ChatPanel` → `POST /api/v1/chat/stream {message, thread_id}` with the JWT.
2. `get_current_user` resolves the user; the LangGraph thread key is `agentos_new:<user_id>_<thread_id>`
   and `configurable.user_id = <user_id>` (tools read it from `RunnableConfig`).
3. `resolve_input`: if the thread has a pending `interrupt()`, the message is parsed as an approval
   (`classify_approval`) and turned into `Command(resume=...)`; an unclear answer re-asks.
   Otherwise the message becomes a new `HumanMessage`.
4. `iter_events` runs `graph.astream_events(...)` and emits SSE events: `thinking`, `route`, `tool_start`,
   `tool_end`, `token`, then exactly one of `hitl_pause` / `done` (or `error`). Tool calls are written
   to `episodic_logs` here.
5. The supervisor routes → a worker runs (ReAct loop with tools) → reports back → supervisor decides
   `FINISH` or another worker (max `MAX_AGENT_HOPS` worker runs per user message).
6. If a tool called `interrupt()`, the checkpoint is saved and the UI shows an **ApprovalCard**.
   `POST /api/v1/chat/approve {action: CONFIRM|REJECT|EDIT}` (or typing "yes"/"no") resumes exactly at the
   `interrupt()` line. See [HITL.md](HITL.md).

## Graph topology

```
START → supervisor ─┬─▶ research_agent ─┐
                    ├─▶ coder_agent ────┤
                    ├─▶ vision_agent ───┤   (wrapped: only the final answer is added to history)
                    ├─▶ gmail_agent ────┤   (direct subgraph: its tool messages and interrupts are checkpointed)
                    ├─▶ calendar_agent ─┤
                    │                   └──▶ back to supervisor
                    └─▶ FINISH → END
```

## Key design decisions

| Decision | Why |
|---|---|
| Gmail/Calendar are direct subgraph nodes | LangGraph can only resume an `interrupt()` inside a subgraph if the subgraph is a node of the parent |
| History is never deleted to save tokens; `context_window()` trims what the model sees | Deleting messages split tool calls from tool results and corrupted threads |
| Router sees a plain-text transcript (`_router_view`) | Avoids sending tool-call history to a model call without tools |
| Async checkpointer opened in the FastAPI lifespan | The whole API is async; sync savers raise `NotImplementedError` |
| Approvals parsed on whole words, negatives win | Substring matching approved "no, don't do it" |
| Everything keyed by authenticated user id | v1.0 shared one thread and one Google account between all users |

## Repository layout

```
api-1/            backend (see BACKEND.md)
  app/            application package
  tests/          pytest suite (fake LLMs, no keys needed)
  generate_token.py / migrate_token.py   local Google token helpers
frontend/         React SPA (see FRONTEND.md)
docs/             this documentation
CLAUDE.md         short entry point for AI assistants
```
