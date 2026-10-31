# Bug Audit (2026-10-31)

Full-project audit of v1.0 (commit `d114c30`) and the fixes that followed. "Verified" = how the fix was checked:
**T** automated test in `api-1/tests`, **E2E** Playwright run against the real backend, **PG** manual run on real Postgres,
**R** code review only.

## Fixed

| # | Sev | Bug (v1.0) | Fix | Verified |
|---|---|---|---|---|
| 1 | 🔴 | Frontend hardcoded `user_id/thread_id = default_user`: all users shared one chat and the owner's Gmail/Calendar | Identity from JWT; per-user threads; per-user Google tokens | T, E2E |
| 2 | 🔴 | Chat/approve/history/upload/logs had no auth; `user_id` trusted from body | `get_current_user` on every endpoint | T |
| 3 | 🔴 | Code interpreter ran arbitrary code with all secrets in env | Off by default; no secrets in env, `-I`, rlimits, temp dir. **Still not a sandbox** (see SECURITY.md) | T |
| 4 | 🔴 | `analyze_image` opened any server path | Only bare names inside `UPLOAD_DIR/<user_id>/` | T |
| 5 | 🔴 | Hardcoded fallback JWT secret | Random per-process secret when unset | R |
| 6 | 🔴 | Vector memory shared across users | `user_id` metadata + filtered search | R |
| 7 | 🔴 | History delete used user input in a Redis `SCAN` glob | `checkpointer.adelete_thread(key)`, thread id regex | T |
| 8 | 🟠 | CORS `*` with credentials | Configurable origins, credentials off | R |
| 9 | 🔴 | Substring approval matching: "no, don't do it" → CONFIRM | Whole-word classifier, negatives win, unclear re-asks | T (+ mutation check) |
| 10 | 🔴 | Streaming endpoint could never resume a tool interrupt | `Command(resume=...)` on all paths | T, E2E |
| 11 | 🔴 | `update_state` while paused wiped the pending interrupt | Never edit state while paused | T |
| 12 | 🟠 | Trimming with `RemoveMessage` split tool calls from results | Stored history untouched; `context_window()` for model input | T |
| 13 | 🔴 | Sync `RedisSaver` raises `NotImplementedError` in async code; memory fallback lost approvals | Async Postgres/Redis savers in lifespan | PG |
| 14 | 🟠 | Approval logs written under `user_id` instead of thread | Logged under the thread key | T |
| 15 | 🟡 | `/chat/approve` returned no reply | Returns the agent's final reply / next pause | T |
| 16 | 🟡 | EDIT args sent as Python repr + `ast.literal_eval` | JSON dict resume value | T |
| 17 | 🟡 | Only the first interrupt handled | All pending interrupts answered | R |
| 18 | 🟠 | `send_email` by draft id showed no recipient/subject/body | Draft fetched for the preview; edits send a new message | R |
| 19 | 🟠 | Workers went straight to END: no multi-agent chaining | Workers return to supervisor, hop cap | T |
| 20 | 🟠 | Vision used a text-only model | `GROQ_VISION_MODEL` (vision model) | R (not run against Groq) |
| 21 | 🟠 | No Google OAuth in the app | Per-user OAuth endpoints + Connect Google button | R (not run against Google) |
| 22 | 🟠 | No current date; events without `timeZone`; free/busy hardcoded UTC | `now_context()` in prompts, `DEFAULT_TIMEZONE` | T (timeZone sent) |
| 23 | 🟡 | Nested multipart email bodies came back empty | Recursive walk, charset, HTML fallback | T |
| 24 | 🟠 | No approval UI, history never loaded, stream unused | ApprovalCard, history + pending on load, streaming chat | E2E |
| 25 | 🟡 | Dashboard data hardcoded | `/system/status` + audit log | E2E |
| 27 | 🟡 | Frontend read `error.message`, FastAPI sends `detail` → "API Error" | `errorMessage()` parses `detail` | E2E |
| 28 | 🟡 | `refresh_token` stored as "undefined" | Removed; 401 → logout | E2E |
| 29 | 🟡 | Upload 400s became 500 | Proper status codes | T |
| 30 | 🟡 | Failed memory save reported success | `add_to_memory` raises → 503 | T |
| 31 | 🟡 | No upload size limit; blocking calls on event loop | `MAX_UPLOAD_MB`, `run_in_threadpool` | T |
| 32 | 🟡 | History showed tool outputs as assistant messages | Only user/assistant text | T |
| 33 | 🟡 | Stale `next` from a crashed run treated as pending approval | Only real interrupts count | T |
| 34 | 🟡 | `9**9**9` hung the calculator | Exponent and magnitude caps | T |
| 35 | 🔵 | `ast.Num` removed in Python 3.14 | `ast.Constant` only | T |
| 36 | 🔵 | Weather location not URL-encoded | `quote()` | R |
| 37 | 🟡 | `+psycopg` URL but only psycopg2 installed | `psycopg[binary,pool]` pinned | PG |
| 38 | 🔵 | Empty `DATABASE_URL` became `"?sslmode=require"` | URL normalisation in one place | R |
| 39 | 🔵 | Registration race → 500 | `IntegrityError` → 400 | R |
| 40 | 🔵 | bcrypt ≥5 raises on >72-byte passwords; no policy | 8–72 byte validation | T |
| 41 | 🔵 | Deprecated `datetime.utcnow` | timezone-aware now | R |
| 42 | 🟡 | Unpinned requirements | Pinned + `requirements-dev.txt` | T |
| 43 | 🔵 | ~30 one-off patch scripts in the repo | Deleted | — |
| 44 | 🔵 | Dead `ai/agent.py`; fixed fallback tool-call id | Deleted; unique ids | T |
| 45 | 🔵 | `ChatGroq(...)` copied 9 times | `get_llm()` factory | — |
| 46 | 🔵 | "Tests" called the live Render URL | Real pytest suite (46 tests) | T |
| 47 | 🔵 | Chroma binaries and `.env.local` committed | Untracked, ignored | — |
| 48 | 🔵 | README endpoints/model/setup wrong | README + docs updated | — |
| 49 | 🔵 | 6 eslint errors | 0 errors, `npm run check` | E2E/lint |

### Found and fixed during the fix work

| Bug | Fix |
|---|---|
| Missing `TAVILY_API_KEY` crashed the whole app at import | Lazy Tavily client; tool reports itself unavailable |
| `CREATE EXTENSION vector` in the same transaction as `create_all`: without pgvector no tables (auth broken) | Separate transaction; `PGVECTOR_AVAILABLE` flag |
| Supervisor routing JSON streamed to the user as tokens | Tokens from the supervisor node are filtered |
| Tool calls after an approval were not audited (only the streaming path logged) | Shared `iter_events()` for every path |
| Paused tool attempt stayed "in progress" forever in the activity panel | Logged as `awaiting_approval`, hidden once resumed |
| Pause message contained markdown the UI does not render | Plain text |
| Landing page kept its own theme state | Uses the shared theme |

## Partially fixed / open

| # | Item | Status |
|---|---|---|
| 26 | Theme toggle ignored by dashboard | **Fixed** for dashboard and auth pages; landing page visuals remain dark-only by design choice |
| 3 | Code interpreter isolation | Mitigated and off by default; needs an external sandbox to be safe for multi-user use |
| — | `create_react_agent` is deprecated in LangGraph 1.x (removed in 2.0) | Pinned to 1.2.x; migrate to `langchain.agents.create_agent` before upgrading |
| — | Rate limiting, JWT in localStorage, no refresh/revocation, no email verification | Open — see SECURITY.md "Known gaps" |
| — | No endpoint to list a user's threads | Open — UI remembers the current thread only |
| — | Uploaded images on local disk | Lost on Render redeploys unless `UPLOAD_DIR` is a persistent disk |
| — | Real-provider behaviour (Groq 8B routing quality, Gmail, Calendar, Tavily, vision, OAuth round trip) | Not exercised in automated tests; verify on staging |
