# Security

## Model

- **Authentication**: email + bcrypt password → HS256 JWT (`Authorization: Bearer`). Every endpoint except
  register/login/OAuth callback/health depends on `get_current_user`, which also checks the user still exists.
- **Authorization = isolation by user id**. The user id comes only from the JWT and is used for:
  thread keys (`agentos_new:<uid>_<thread>`), audit-log rows, vector-memory metadata filters, upload folders,
  Google token rows, and `RunnableConfig.configurable.user_id` that tools read. Tests cover cross-user access.
- **Secrets**: only from environment variables. Google tokens are Fernet-encrypted at rest (`ENCRYPTION_KEY`).
  No hardcoded fallback JWT secret: an unset `JWT_SECRET_KEY` produces a random per-process key.
- **CORS**: `CORS_ORIGINS` (default `*`) with `allow_credentials=False`; auth never uses cookies.
- **OAuth state**: a 10-minute JWT `{uid, purpose: "google_oauth"}`; the callback rejects anything else.
- **Input validation**: pydantic models (message ≤ 8000 chars, thread id regex, password 8–72 bytes),
  upload type and size checks, calculator exponent/magnitude caps, weather location URL-encoded.

## Human approval for side effects

Sending email and creating calendar events always pause for approval (see [HITL.md](HITL.md)). Free-text
answers are parsed conservatively (any negative word rejects, anything unclear re-asks). Every decision is audited.

## Prompt injection

Emails, web results and memories are untrusted. Mitigations: email bodies are labelled untrusted in the tool
result, the research/gmail prompts tell the model not to follow instructions in web pages, memories or emails, risky tools require human approval with a full preview (recipient/subject/body are shown even
when sending a draft), and the code interpreter is off by default. This reduces but does not eliminate the risk —
a manipulated agent can still *propose* a harmful email; the human approval is the real control.

## Code interpreter (`ENABLE_CODE_INTERPRETER`)

**Off by default.** When enabled, model-written Python runs as a subprocess of the API server with:
`python -I` (isolated mode), an environment containing only `PATH/HOME/LANG` (no API keys), a throw-away
working directory, `RLIMIT_CPU` = timeout, 512 MB address space, 10 MB max file size, its own session, stdin closed,
output truncated to 4000 chars.

**It is not a sandbox**: the code can still use the network and read any file the server user can read
(including `/proc/<pid>/environ` of the server process and a `.env` file on disk). Enable it only for trusted,
single-user deployments, or replace `run_python()` with an isolated runner (container/gVisor/Firecracker/E2B).

## Uploads and vision

`analyze_image` accepts only a bare file name and resolves it inside `UPLOAD_DIR/<user_id>/`; traversal and
other extensions are rejected (tested). Uploads are limited to `MAX_UPLOAD_MB` and to PDF/PNG/JPG/WEBP.

## Known gaps (not yet addressed)

| Gap | Impact | Suggested fix |
|---|---|---|
| No rate limiting on `/auth/*` and chat | Brute force, Groq quota exhaustion | slowapi / reverse-proxy limits |
| JWT stored in `localStorage` | Readable by any XSS on the frontend origin | httpOnly cookie + CSRF protection |
| No token revocation / refresh | Logout is client-side only; tokens live 7 days | short-lived access + refresh tokens, deny-list |
| No email verification / password reset | Anyone can register any address | verification email flow |
| Code interpreter is not isolated | See above | external sandbox |
| `CORS_ORIGINS` defaults to `*` | Fine with bearer tokens, but tighten in production | set the Vercel origin |

## Checklist for new code

- [ ] Endpoint depends on `get_current_user` and scopes every query by `user.id`.
- [ ] No user-controlled value is used in a file path, key pattern or SQL string.
- [ ] Side-effecting tool uses `interrupt()` + `resolve_approval()` with a complete preview.
- [ ] Errors returned to clients do not leak stack traces or secrets (`friendly_error`).
- [ ] New secrets are env vars documented in [CONFIGURATION.md](CONFIGURATION.md).
