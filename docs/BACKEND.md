# Backend (`api-1/`)

FastAPI + LangGraph, Python 3.11+ (tested on 3.13). Entry point: `uvicorn app.main:app --port 10000`.

## File map

### `app/`
| File | Responsibility |
|---|---|
| `main.py` | Creates the app, CORS, includes routers. Lifespan: `init_db()`, opens the checkpointer, builds `app.state.graph` (None → chat endpoints return 503) |

### `app/core/` — cross-cutting
| File | Responsibility |
|---|---|
| `config.py` | **Every** environment variable, parsed once. Import `from app.core import config` |
| `security.py` | bcrypt hashing, JWT create/decode (random secret if `JWT_SECRET_KEY` unset), Fernet encrypt/decrypt for Google tokens |
| `deps.py` | `get_db`, `get_current_user` → `CurrentUser(id: str, email)`. The only source of user identity |
| `hitl.py` | `classify_approval(text)` (chat reply → CONFIRM/REJECT/None) and `resolve_approval(resume_value)` (used inside tools) |

### `app/db/`
| File | Responsibility |
|---|---|
| `models.py` | SQLAlchemy models: `User`, `EpisodicLog`, `UserToken` |
| `postgres.py` | Normalises `DATABASE_URL` into async (asyncpg), sync (psycopg3) and libpq URLs; SSL except for localhost; SQLite supported for tests. `init_db()` creates tables + pgvector (separate transaction) and sets `PGVECTOR_AVAILABLE`. `log_episodic_event()` |
| `vector_store.py` | Lazy PGVector store (FastEmbed `bge-small-en-v1.5`). `add_to_memory(text, user_id)` / `search_memory(query, user_id)`; always filtered by user; raise on failure |

### `app/ai/`
| File | Responsibility |
|---|---|
| `llm.py` | `get_llm()`, `get_vision_llm()`, `now_context()` (date/timezone line for prompts), `context_window()` (safe history tail), `agent_prompt()` (prompt callable for workers) |
| `llm_wrapper.py` | `FallbackLLMWrapper`: converts tool calls that small Llama models print as JSON text into real tool calls |
| `checkpointer.py` | `open_checkpointer()` → AsyncPostgresSaver / AsyncRedisSaver / MemorySaver, with fallback to memory |
| `agents/supervisor.py` | `build_supervisor_graph(checkpointer, llm=None, worker_llm=None)`, router prompt, hop limit, `MEMBERS` |
| `agents/*_agent.py` | `build_<name>_agent(llm=None)` → `create_react_agent` with tools + system prompt |
| `tools/__init__.py` | `web_search_tool` (Tavily, lazy), `remember_fact`, `recall_fact` (user-scoped), re-exports calculator/weather |
| `tools/gmail.py` | `search_emails`, `read_email_content`, `draft_email`, `send_email` (**interrupt**), `extract_body()` |
| `tools/calendar_tools.py` | `check_calendar_availability`, `create_calendar_event` (**interrupt**) |
| `tools/google_auth.py` | Loads/refreshes a user's encrypted Google credentials; `gmail_service`, `calendar_service`, `is_connected`, `user_id_from(config)` |
| `tools/code_interpreter.py` | `python_code_interpreter` — disabled unless `ENABLE_CODE_INTERPRETER`; no secrets in env, rlimits |
| `tools/vision.py` | `analyze_image(file_name)` — only files in `UPLOAD_DIR/<user_id>/`; `describe_image_bytes()` |
| `tools/calculator.py` | AST-based safe arithmetic with exponent/magnitude caps |
| `tools/weather.py` | wttr.in current weather |

### `app/routers/`
| File | Endpoints (all under `/api/v1`) |
|---|---|
| `auth.py` | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| `chat.py` | `POST /chat`, `POST /chat/stream`, `POST /chat/approve`, `GET/DELETE /chat/history/{thread_id}`. Helpers: `session_key`, `graph_config`, `pending_interrupts`, `resume_command`, `iter_events`, `run_turn`, `resolve_input` |
| `upload.py` | `POST /upload` (PDF/image → memory; images saved for the vision agent) |
| `logs.py` | `GET /logs/{thread_id}` (+ legacy `/api/logs/{thread_id}`) |
| `system.py` | `GET /system/status` (real tool availability for the dashboard) |
| `integrations.py` | Google OAuth: `GET /integrations/google/status`, `POST .../authorize`, `GET .../callback`, `DELETE /integrations/google` |

### Other
| File | Purpose |
|---|---|
| `tests/` | pytest suite, see [TESTING.md](TESTING.md) |
| `generate_token.py` | Local OAuth flow writing `token.json` (dev only) |
| `migrate_token.py --email you@x.com` | Store `token.json` for one AgentOS user (fallback to the in-app Connect Google button) |
| `requirements.txt` / `requirements-dev.txt` | Pinned runtime / test dependencies |
| `.env.example` | Template of all env vars |

## Conventions

- **Identity**: never accept `user_id` from a request. Use `user: CurrentUser = Depends(get_current_user)`.
- **Thread key**: always `session_key(user, thread_id)`; `thread_id` must match `^[A-Za-z0-9_-]{1,64}$`.
- **Tools** get the user from `config["configurable"]["user_id"]` (add a `config: RunnableConfig = None` parameter; LangChain injects it and hides it from the model).
- **Side effects** that need approval: call `interrupt({...payload...})` *before* the side effect, then
  `approved, edits = resolve_approval(value)`. Anything before `interrupt()` re-runs on resume, so keep it read-only.
- **Async everywhere** in routers; blocking work (PDF parsing, vision call, Google SDK) goes through `run_in_threadpool` or runs inside tools (LangGraph runs sync tools in a thread).
- **Errors to users**: `friendly_error()` in `chat.py`; never return raw exception text from chat endpoints.
- **Logging**: `logging.getLogger(__name__)`, not `print` (a couple of startup warnings still print).
