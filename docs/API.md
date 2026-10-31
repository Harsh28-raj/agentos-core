# HTTP API

Base URL: `http://localhost:10000` (local) · Swagger UI at `/docs`. All paths below are prefixed with **`/api/v1`**.
Except `register`, `login` and the OAuth `callback`, **every endpoint requires** `Authorization: Bearer <access_token>`
(missing/invalid → `401`). Errors are `{"detail": "..."}` (validation errors: `{"detail": [{"msg": ...}]}`).

`thread_id` everywhere must match `^[A-Za-z0-9_-]{1,64}$` (else `422`). Threads are private to the calling user.

## Auth

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/auth/register` | `{email, password}` (8–72 bytes) | `201 {message, user: {id, email}}`; `400` "Email already registered" |
| POST | `/auth/login` | `{email, password}` (email case-insensitive) | `{access_token, token_type: "bearer", user: {id, email}}`; `401` |
| GET | `/auth/me` | — | `{id, email}` |

Tokens are HS256 JWTs (`sub` = email), valid `ACCESS_TOKEN_EXPIRE_DAYS` (7). There is no refresh token.

## Chat

### `POST /chat` — non-streaming
Body: `{message: str (1–8000), thread_id?: str = "default"}`

Responses (always `200`):
```jsonc
{"reply": "Hello!"}                                     // finished
{"reply": "⏸️ Awaiting your approval before executing: create_event",
 "hitl_interrupt": true, "interrupt_data": {...}, "pending_count": 1}   // paused, see HITL.md
{"reply": "⚠️ Something went wrong ...", "error": true} // failure (friendly message)
```
If the thread is paused, `message` is treated as the approval answer ("yes" / "no" / unclear → re-ask).

### `POST /chat/stream` — Server-Sent Events
Same body. Response `text/event-stream`, one JSON object per `data:` line:

| `type` | Fields | Meaning |
|---|---|---|
| `thinking` | `content` | Run started |
| `route` | `agent`, `content` | Supervisor handed off to a worker |
| `tool_start` | `tool`, `input`, `content` | Tool began |
| `tool_end` | `tool`, `output` (≤150 chars), `content` | Tool finished |
| `token` | `content` | Streamed model text (workers only; router JSON is never streamed) |
| `hitl_pause` | `content`, `tool`, `pending_args`, `pending_count` | **Final** — waiting for approval |
| `done` | `reply`, `tokens: {input, output, total}` | **Final** — authoritative final answer |
| `error` | `content` | **Final** — friendly error |

### `POST /chat/approve`
Body: `{thread_id, action: "CONFIRM"|"REJECT"|"EDIT", updated_args?: {...}, feedback_message?: str}`
- `EDIT` requires `updated_args` (only the fields to change, e.g. `{"subject": "New"}`) → `400` otherwise.
- No pending action → `409`.
- Response: `{status: "resumed"|"rejected", message, reply, [hitl_interrupt, interrupt_data, pending_count]}`
  (another approval can follow if the agent chains a second risky action).

### `GET /chat/history/{thread_id}`
`{history: [{role: "user"|"assistant", content}], pending: <pause payload>|null}` — only messages the user saw
(no tool messages). `pending` lets the UI restore the approval card after a reload.

### `DELETE /chat/history/{thread_id}`
Deletes all checkpoints of that thread and its audit rows. `{status: "success", message}`.

## Upload — `POST /upload`
`multipart/form-data` field `file`: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`, max `MAX_UPLOAD_MB` (10).
- PDF → text extracted; image → described by `GROQ_VISION_MODEL` and saved to `UPLOAD_DIR/<user_id>/<uuid>.<ext>`.
- Text is embedded into the caller's long-term memory.
- `200 {status, message, content_length, stored_file}` · `400` bad type/empty · `413` too large · `422` unreadable · `503` memory unavailable.

## Logs — `GET /logs/{thread_id}?limit=200`
Audit trail of one of the caller's threads, oldest first:
`{thread_id, logs: [{id, run_id, tool_name, tool_input, tool_output, status, action_taken, original_args, modified_args, human_feedback, latency_ms, reasoning_steps, created_at}]}`.
`status` ∈ `started`, `completed`, `awaiting_approval`. HITL rows have `tool_name` `HITL_CONFIRM|HITL_REJECT|HITL_EDIT`.
Legacy alias: `GET /api/logs/{thread_id}` (no `/v1`).

## System — `GET /system/status`
```json
{"llm": {"status": "ONLINE", "model": "llama-3.1-8b-instant"}, "checkpointer": "postgres",
 "tools": [{"name": "Web Search", "status": "ONLINE", "detail": "Tavily"}, ...], "active_tools": 6}
```

## Google integration
| Method | Path | Notes |
|---|---|---|
| GET | `/integrations/google/status` | `{configured, connected}` |
| POST | `/integrations/google/authorize` | `{url}` → frontend sets `window.location` to it; `503` if OAuth not configured |
| GET | `/integrations/google/callback` | Google redirects here (no JWT; signed `state`). Stores encrypted token, redirects to `FRONTEND_URL/dashboard?google=connected|error` |
| DELETE | `/integrations/google` | Removes the stored token |

## Health
`GET /` → `{"status": "AgentOS Backend is running smoothly! 🚀"}` (no `/api/v1` prefix, no auth).
