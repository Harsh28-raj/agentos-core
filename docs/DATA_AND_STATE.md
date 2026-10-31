# Data and State

## Where state lives

| What | Store | Key / scope |
|---|---|---|
| Users | Postgres `users` | `id` (int), `email` unique |
| Conversation + paused approvals | LangGraph checkpointer (Postgres tables created by `AsyncPostgresSaver.setup()`) | thread key `agentos_new:<user_id>_<thread_id>` |
| Audit trail (tool calls, approvals) | Postgres `episodic_logs` | `thread_id` column = the same thread key |
| Google OAuth tokens | Postgres `user_tokens` (Fernet-encrypted JSON) | `(user_id, service_name='google')` unique |
| Long-term memory (facts, uploaded docs) | pgvector collection `agent_memory` (langchain-postgres tables) | metadata `user_id`; every search filters on it |
| Uploaded images | Local disk `UPLOAD_DIR/<user_id>/<uuid>.<ext>` | per user folder |
| Frontend session | `localStorage`: `access_token`, `theme`, `agentos_thread_<user_id>` | per browser |

## Tables (`app/db/models.py`)

```
users          id PK, email UNIQUE, hashed_password (bcrypt), created_at
episodic_logs  id PK, thread_id (idx), run_id, tool_name, tool_input JSON, tool_output JSON,
               reasoning_steps JSON, status, latency_ms, created_at, action_taken,
               original_args JSON, modified_args JSON, human_feedback TEXT
user_tokens    id PK, user_id (idx), service_name, encrypted_data TEXT, updated_at,
               UNIQUE(user_id, service_name)   -- only on newly created tables
```
No migration tool: `init_db()` runs `create_all` and `ALTER TABLE episodic_logs ADD COLUMN IF NOT EXISTS ...`
for the HITL columns. Timestamps are naive UTC (`created_at + 'Z'` when displaying).

## Checkpointer selection (`app/ai/checkpointer.py`)

`CHECKPOINTER=auto` (default): Postgres if `DATABASE_URL` is Postgres → else Redis if `REDIS_URL` → else memory.
- **Postgres**: `AsyncPostgresSaver` over a psycopg `AsyncConnectionPool` (`autocommit`, `prepare_threshold=0` for PgBouncer/Neon).
  Verified: an approval paused in one process is resumable after a restart.
- **Redis**: `AsyncRedisSaver` — needs **Redis Stack** (RediSearch/RedisJSON). Plain Redis fails `FT.INFO` and falls back to memory.
- **Memory**: development only; everything is lost on restart. Logged as a warning.
- If the chosen store is unreachable at startup the app logs an error and falls back to memory (it does not crash).

## Thread model

- `thread_id` is chosen by the client (`default`, or `t_<random>` from the New conversation button) and is
  only meaningful together with the authenticated user id.
- `DELETE /chat/history/{thread_id}` → `checkpointer.adelete_thread(key)` + delete its `episodic_logs`.
- There is no endpoint listing a user's threads yet (the UI remembers the current one in localStorage).

## Context size

Stored history grows forever per thread; what the models see is `context_window(messages, CONTEXT_WINDOW_MESSAGES=12)`:
the tail of the history, starting at a `HumanMessage` (so tool call/result pairs stay intact), always including the
latest user message and everything after it.

## Long-term memory

- Embeddings: FastEmbed `BAAI/bge-small-en-v1.5` (CPU, downloaded on first use; first memory call is slow).
- Requires the `vector` extension; `PGVECTOR_AVAILABLE` reflects whether `CREATE EXTENSION` succeeded.
- `add_to_memory` / `search_memory` raise `MemoryUnavailable` or DB errors; tools turn them into messages,
  `/upload` returns `503`.
