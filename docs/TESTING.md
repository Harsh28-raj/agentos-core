# Testing

## Backend — pytest (no API keys, no network)

```bash
cd api-1
pip install -r requirements-dev.txt
pytest            # 46 tests, ~40 s
```

`tests/conftest.py` sets the environment **before** importing the app: SQLite (`aiosqlite`) database, in-memory
checkpointer, dummy Groq key, code interpreter off, temp upload dir. Fixtures:

| Fixture | Provides |
|---|---|
| `llms` | `(router_llm, worker_llm)` — two `ScriptedChatModel`s. Push responses onto `.script`; each call pops one. Items: `str`, `AIMessage`, or `callable(messages)`. `.calls` records prompts |
| `client` | `TestClient` with `app.state.graph = build_supervisor_graph(MemorySaver(), llm=router_llm, worker_llm=worker_llm)` |
| `make_user()` | Registers + logs in a fresh user → `{email, id, headers}` |
| `calendar` (test_api.py) | Patches `calendar_service` with a `MagicMock` so no Google call happens |

Helpers: `route("calendar_agent")` → router JSON; `tool_call(name, args)` → `AIMessage` with a tool call.

Typical approval test:
```python
def test_x(client, llms, make_user, calendar):
    router_llm, worker_llm = llms
    user = make_user()
    router_llm.script += [route("calendar_agent")]
    worker_llm.script += [tool_call("create_calendar_event", EVENT)]
    res = client.post("/api/v1/chat", json={"message": "book it", "thread_id": "t1"}, headers=user["headers"]).json()
    assert res["hitl_interrupt"]
    worker_llm.script += ["Booked!"]; router_llm.script += [route("FINISH")]
    client.post("/api/v1/chat/approve", json={"thread_id": "t1", "action": "CONFIRM"}, headers=user["headers"])
    calendar.events.return_value.insert.assert_called_once()
```
A test fails loudly if a model is called more times than scripted ("ran out of responses").

### What is covered
- `test_units.py`: approval classifier (incl. the old false positives), `resolve_approval`, `context_window`,
  calculator guards, nested multipart email bodies, code interpreter off/env stripping/timeout, image path traversal.
- `test_api.py`: auth on every endpoint, registration rules, routing/finish, hop limit, same-worker guard,
  unparseable router output, every approval path (chat yes/no/unclear, approve CONFIRM/REJECT/EDIT, streaming
  resume and pause), cross-user isolation, tools receive the authenticated user id, delete only own thread,
  invalid thread ids, upload validation and honest memory failure, system status, crash recovery, audit logging.

### Not covered automatically
Real Groq behaviour (routing quality of the 8B model), Gmail/Calendar/Tavily/vision APIs, Google OAuth round trip,
pgvector memory (needs the extension). Check these manually against a staging deployment.

## Against real Postgres

The Postgres checkpointer was verified manually: pause an approval, restart the process, approve → the tool runs.
To repeat it, point `DATABASE_URL` at a local Postgres and run the app twice (see `DEPLOYMENT.md` for a docker command).

## Frontend

```bash
cd frontend
npm run check     # eslint + tsc + vite build
```
There is no frontend unit-test suite. The dashboard was verified end-to-end with Playwright against the real
backend using rule-based fake LLMs: register (incl. server validation message) → login → live tool status →
streamed reply → approval card → reload keeps history and pending approval → edit + approve → tool activity
and episodic memory panels update → theme toggle → new conversation → invalid token logs out.
